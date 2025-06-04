import inspect
import json

import numpy as np
import pandas as pd
from django.http import HttpRequest
from django_oemof.simulation import SimulationError
from oemof import solph
from pyomo.environ import BuildAction
from pyomo.environ import Constraint

from . import flows
from . import models
from . import settings

# As inf cannot be set, we instead use a very large value
OEMOF_INF_EQUIVALENT = 100000000


def init_parameters(scenario: str, parameters: dict, request: HttpRequest) -> dict:
    """Set up structure of parameters used in hooks."""
    structure = {"flow_data": {}, "renovation_data": {}, "oeprom": {}, "config": settings.CONFIG}
    parameters.update(structure)
    return parameters


def init_flow_data(scenario: str, parameters: dict, request: HttpRequest) -> dict:
    """Read flow data from session."""

    # For debugging:
    if "django_htmx_flow" in parameters:
        parameters["flow_data"] = parameters.pop("django_htmx_flow")
        return parameters

    # alternativ in settings.py ne Liste anlegen, mit allen Flows, die dann in views und hier genutzt werden kann
    all_flows = [
        (name, flow())
        for name, flow in inspect.getmembers(flows, inspect.isclass)
        if name.endswith("Flow") and name not in {"Flow", "RenovationRequestFlow"}
    ]
    flow_data = request.session.get("django_htmx_flow", {})

    for name, flow in all_flows:
        if not flow.finished(request):
            message = f"Flow '{name}' is not completed."
            raise SimulationError(message)

    # check if at least one RenovationRequestFlow instance is finished
    scenario_id = 1
    while scenario_id <= settings.SCENARIO_MAX:
        flow = flows.RenovationRequestFlow(prefix=f"scenario{scenario_id}")
        if flow.finished(request):
            scenario_id += 1
            break
        message = "No completed 'RenovationRequestFlow' scenarios found."
        raise SimulationError(message)

    parameters["flow_data"] = flow_data
    return parameters


def init_renovation_scenario(
    scenario: str,
    parameters: dict,
    request: HttpRequest,
) -> dict:
    """Extract current renovation scenario from flow."""
    if "renovation_scenario" not in parameters:
        error_msg = "No renovation scenario given. Must be set in parameters as 'renovation_scenario'."
        raise KeyError(error_msg)
    renovation_scenario = parameters.pop("renovation_scenario")

    scenario_keys = [key for key in parameters["flow_data"] if key.startswith(renovation_scenario)]
    if len(scenario_keys) == 0:
        error_msg = f"No renovation scenario '{renovation_scenario}' found in flow data."
        raise KeyError(error_msg)

    # Chosen renovation scenario keys are renamed to "scenario_<key_name>", removing scenario ID
    scenario_data = {}
    for key in scenario_keys:
        new_key = key.replace(renovation_scenario, "scenario")
        scenario_data[new_key] = parameters["flow_data"].pop(key)

    # Remove all other scenarios as well
    scenario_keys = [key for key in parameters["flow_data"] if key.startswith("scenario")]
    for key in scenario_keys:
        del parameters["flow_data"][key]

    parameters["flow_data"].update(scenario_data)
    return parameters


def init_tabula_data(scenario: str, parameters: dict, request: HttpRequest) -> dict:
    """Get tabula building."""

    building_type = settings.CONFIG["building_type"][parameters["flow_data"]["building_type"]]

    # Get nearest available year using absolut difference
    year_diff = [
        abs(year - parameters["flow_data"]["construction_year"]) for year in settings.CONFIG["construction_years"]
    ]
    year_index = int(np.argmin(year_diff)) + 1
    if building_type == "TH" and year_index == 1:
        # There is no building data for "DE.N.TH.01."
        year_index = 2

    building_reference = f"DE.N.{building_type}.{year_index:02}."
    parameters["tabula_data"] = settings.TABULA_DATA[building_reference].to_dict()

    # Set flow temperature depending on heating system (i.e. radiators/floorheating)
    parameters["tabula_data"]["flow_temperature"] = settings.CONFIG["flow_temperature"][
        parameters["tabula_data"]["HeatingSystem_Emission"]
    ]

    # Set available roof area
    parameters["tabula_data"]["roof_area_available"] = (
        float(parameters["tabula_data"]["roof_area_tabula"]) * settings.CONFIG["roof_usage"]
    )

    return parameters


def init_roof(scenario: str, parameters: dict, request: HttpRequest) -> dict:
    """Calculate elevation and direction angles of roof."""
    if parameters["flow_data"]["flat_roof"] == "exists":
        parameters["flow_data"]["elevation"] = 0
        parameters["flow_data"]["direction"] = 0
    else:
        parameters["flow_data"]["elevation"] = settings.map_elevation(
            parameters["flow_data"]["roof_inclination"],
        )
        parameters["flow_data"]["direction"] = settings.CONFIG["orientation"][
            parameters["flow_data"]["roof_orientation"]
        ]

        # This is necessary due to missing data for elevation angle of 45°; only 0, 120, 240, 360 are available
        if parameters["flow_data"]["elevation"] == 45:  # noqa: PLR2004
            parameters["flow_data"]["direction"] = round(parameters["flow_data"]["direction"] / 120) * 120
    return parameters


def init_renovation_data(scenario: str, parameters: dict, request: HttpRequest) -> dict:
    """Get renovation data from KfW based on flow data."""
    # Get cluster ID from KfW clustering
    # TODO: Get cluster ID from lookup table. Currently hardcoded.
    # https://github.com/rl-institut/bd_app/issues/90
    cluster_id = 1

    with (settings.DATA_DIR / "renovations" / f"{cluster_id}.json").open(
        "r",
        encoding="utf-8",
    ) as f:
        parameters["renovation_data"] = json.load(f)
    return parameters


def set_up_loads(
    scenario: str,
    parameters: dict,
    request: HttpRequest,
) -> dict:
    """Set up electricity, heat and hotwater consumption (profiles & amount)."""
    electricity_profile = pd.Series(
        models.Load.objects.get(
            number_people=parameters["flow_data"]["number_persons"],
            eec=settings.CONFIG["default_energy_efficiency_class"],
        ).profile,
    )
    electricity_amount = (
        parameters["renovation_data"]["energyConsumptionElectricityAsIs"]
        - parameters["renovation_data"]["resultsMeasuresAccordingBEG"]["reductionFinalEnergyElectricity"]
    )
    hotwater_profile = pd.Series(
        models.Hotwater.objects.get(
            number_people=parameters["flow_data"]["number_persons"],
        ).profile,
    )
    hotwater_amount = (
        parameters["flow_data"]["number_persons"] * settings.CONFIG["hotwater_energy_consumption_per_person"]
    )
    heat_amount = (
        parameters["renovation_data"]["energyConsumptionHeatingAsIs"]
        - parameters["renovation_data"]["resultsMeasuresAccordingBEG"]["reductionFinalEnergyHeating"]
        - hotwater_amount
    )
    parameters["oeprom"].update(
        {
            "load_electricity": {
                "profile": electricity_profile,
                "amount": electricity_amount,
            },
            "load_hotwater": {"profile": hotwater_profile, "amount": hotwater_amount},
            "load_heat": {"amount": heat_amount},
        },
    )
    return parameters


def set_up_volatiles(  # noqa: C901
    scenario: str,
    parameters: dict,
    request: HttpRequest,
) -> dict:
    """Set up PV and solar-thermal profiles and capacities."""
    parameters["oeprom"]["volatile_PV"] = {"capacity_cost": settings.get_ep_cost("volatile_PV")}
    parameters["oeprom"]["volatile_STH"] = {"capacity_cost": settings.get_ep_cost("volatile_STH")}
    parameters["oeprom"]["load_STH"] = {}

    if parameters["flow_data"]["pv_exists"] == "True" or "pv" in parameters["flow_data"]["scenario-secondary_heating"]:
        pv_profile = pd.Series(
            models.Photovoltaic.objects.get(
                elevation_angle=parameters["flow_data"]["elevation"],
                direction_angle=parameters["flow_data"]["direction"],
            ).profile,
        )
        parameters["oeprom"]["volatile_PV"]["profile"] = pv_profile

    if (
        parameters["flow_data"]["solar_thermal_exists"] == "True"
        or "solar" in parameters["flow_data"]["scenario-secondary_heating"]
    ):
        sth_profile = pd.Series(
            models.Solarthermal.objects.get(
                type="heat",
                temperature=parameters["tabula_data"]["flow_temperature"],
                elevation_angle=parameters["flow_data"]["elevation"],
                direction_angle=parameters["flow_data"]["direction"],
            ).profile,
        )
        parameters["oeprom"]["volatile_STH"]["profile"] = sth_profile
        sth_load_profile = pd.Series(
            models.Solarthermal.objects.get(
                type="load",
                temperature=parameters["tabula_data"]["flow_temperature"],
                elevation_angle=parameters["flow_data"]["elevation"],
                direction_angle=parameters["flow_data"]["direction"],
            ).profile,
        )
        parameters["oeprom"]["load_STH"]["profile"] = sth_load_profile

    # Set existing PV and solarthermal capacities
    if parameters["flow_data"]["pv_exists"] == "True" and "pv_capacity" in parameters["flow_data"]:
        parameters["oeprom"]["volatile_PV"]["capacity"] = parameters["flow_data"]["pv_capacity"]
    if parameters["flow_data"]["solar_thermal_exists"] == "True" and "solar_thermal_area" in parameters["flow_data"]:
        st_capacity = parameters["flow_data"]["solar_thermal_area"] / settings.CONFIG["sth_density"]
        parameters["oeprom"]["volatile_STH"]["capacity"] = st_capacity
        parameters["oeprom"]["load_STH"]["amount"] = st_capacity

    # Prepare optimization of PV in scenario
    if (
        parameters["flow_data"]["pv_exists"] == "False"
        and "pv" in parameters["flow_data"]["scenario-secondary_heating"]
    ):
        if parameters["flow_data"]["solar_thermal_exists"] == "True":
            # Calculate remaining area for PV
            pv_area_available = max(
                parameters["tabula_data"]["roof_area_available"] - parameters["flow_data"]["solar_thermal_area"],
                0,
            )
        elif "solar" in parameters["flow_data"]["scenario-secondary_heating"]:
            # Share available roof area across PV and STH
            pv_area_available = (
                parameters["tabula_data"]["roof_area_available"] * settings.CONFIG["roof_usage_pv_share"]
            )
        else:
            pv_area_available = parameters["tabula_data"]["roof_area_available"]
        pv_capacity_max = pv_area_available / settings.CONFIG["pv_density"]
        parameters["oeprom"]["volatile_PV"]["capacity_potential"] = pv_capacity_max
        parameters["oeprom"]["volatile_PV"]["expandable"] = True

    # Prepare optimization of STH in scenario
    if (
        parameters["flow_data"]["solar_thermal_exists"] == "False"
        and "solar" in parameters["flow_data"]["scenario-secondary_heating"]
    ):
        if parameters["flow_data"]["pv_exists"] == "True":
            # Calculate remaining area for STH
            sth_area_available = max(
                parameters["tabula_data"]["roof_area_available"]
                - parameters["flow_data"]["pv_capacity"] * settings.CONFIG["pv_density"],
                0,
            )
        elif "pv" in parameters["flow_data"]["scenario-secondary_heating"]:
            # Share available roof area across PV and STH
            sth_area_available = parameters["tabula_data"]["roof_area_available"] * (
                1 - settings.CONFIG["roof_usage_pv_share"]
            )
        else:
            sth_area_available = parameters["tabula_data"]["roof_area_available"]
        sth_capacity_max = sth_area_available / settings.CONFIG["sth_density"]
        parameters["oeprom"]["volatile_STH"]["capacity_potential"] = sth_capacity_max
        parameters["oeprom"]["volatile_STH"]["expandable"] = True
        # Set fix load amount (instead of coupling amount to optimized STH capacity) depending on number of persons
        parameters["oeprom"]["load_STH"]["amount"] = (
            settings.CONFIG["sth_area_per_person"] / settings.CONFIG["sth_density"]
        )

    return parameters


def set_up_heatpumps(scenario: str, parameters: dict, request: HttpRequest) -> dict:
    """Set up heatpumps."""

    # Get temperature type from flow temperature
    type_temperature = f"VL{parameters['tabula_data']['flow_temperature']}C"

    if (
        parameters["flow_data"]["scenario-primary_heating"] == "heat_pump"
        and parameters["flow_data"]["scenario-heat_pump_type"] == "air_heat_pump"
    ):
        heatpump_air_cop = pd.Series(
            models.Heatpump.objects.get(
                medium="air",
                type_temperature=type_temperature,
            ).profile,
        )
        parameters["oeprom"]["conversion_heatpump_air"] = {
            "expandable": True,
            "efficiency": heatpump_air_cop,
            "capacity_cost": settings.get_ep_cost("air_heat_pump"),
        }

    if (
        parameters["flow_data"]["scenario-primary_heating"] == "heat_pump"
        and parameters["flow_data"]["scenario-heat_pump_type"] == "geothermal_pump"
    ):
        heatpump_water_cop = pd.Series(
            models.Heatpump.objects.get(
                medium="water",
                type_temperature=type_temperature,
            ).profile,
        )
        parameters["oeprom"]["conversion_heatpump_water"] = {
            "expandable": True,
            "efficiency": heatpump_water_cop,
            "capacity_cost": settings.get_ep_cost("geothermal_pump"),
        }

    if (
        parameters["flow_data"]["scenario-primary_heating"] == "heat_pump"
        and parameters["flow_data"]["scenario-heat_pump_type"] == "groundwater"
    ):
        heatpump_brine_cop = pd.Series(
            models.Heatpump.objects.get(
                medium="brine",
                type_temperature=type_temperature,
            ).profile,
        )
        parameters["oeprom"]["conversion_heatpump_brine"] = {
            "expandable": True,
            "efficiency": heatpump_brine_cop,
            "capacity_cost": settings.get_ep_cost("groundwater"),
        }

    return parameters


def set_up_conversion_technologies(
    scenario: str,
    parameters: dict,
    request: HttpRequest,
) -> dict:
    """Set up conversion technologies if selected in renovation scenario."""

    # Capacity of district heating is set to "infinity" and not optimized
    if parameters["flow_data"]["scenario-primary_heating"] == "district_heating":
        parameters["oeprom"]["district_heating"] = {"capacity": OEMOF_INF_EQUIVALENT}

    # Heating system is optimized
    technologies = {
        "wood_pellets": "conversion_pk",
        "wood_chips": "conversion_hgk",
        "firewood": "conversion_shk",
        "gas_heating": "conversion_boiler",
        "heating_rod": "conversion_ehz",
        "bhkw": "backpressure_bhkw",
    }
    for technology, oemof_technology in technologies.items():
        if parameters["flow_data"]["scenario-primary_heating"] == technology:
            parameters["oeprom"][oemof_technology] = {
                "expandable": True,
                "capacity_cost": settings.get_ep_cost(technology),
            }
    # Bivalent system HP + Oil/Gas
    # Set lowest capacity for secondary heating
    if "oil_heating" in parameters["flow_data"]["scenario-secondary_heating"]:
        parameters["oeprom"]["conversion_boiler"] = {
            "expandable": True,
            "capacity_cost": settings.get_ep_cost("oil_heating", 10),
            "capacity_potential": 10,
        }
    return parameters


def set_up_hotwater_supply(
    scenario: str,
    parameters: dict,
    request: HttpRequest,
) -> dict:
    """Either supply hot water via instantaneous water heater or freshwater station."""
    if parameters["flow_data"]["hotwater_supply"] == "instantaneous_water_heater":
        parameters["oeprom"]["conversion_dle"] = {"capacity": OEMOF_INF_EQUIVALENT}
    else:
        parameters["oeprom"]["conversion_fws"] = {"capacity": OEMOF_INF_EQUIVALENT}
    return parameters


def set_up_storages(scenario: str, parameters: dict, request: HttpRequest) -> dict:
    """Set up heat storage and battery storage if PV is selected."""
    # Always optimize heat storage
    parameters["oeprom"]["storage_heat"] = {
        "expandable": True,
        "capacity_cost": settings.get_ep_cost("storage_heat"),
    }

    # Set up battery
    # Existing battery
    if "battery_exists" in parameters["flow_data"] and parameters["flow_data"]["battery_exists"] == "True":
        storage_capacity = parameters["flow_data"]["battery_capacity"]
        parameters["oeprom"]["storage_lion"] = {
            "storage_capacity": storage_capacity,
            "capacity": storage_capacity * settings.CONFIG["battery_c_rate"],
            "capacity_cost": settings.get_ep_cost("storage_lion"),
        }
    elif parameters["flow_data"]["pv_exists"] == "True":
        storage_capacity = (
            parameters["flow_data"]["pv_capacity"] * settings.CONFIG["battery_storage_capacity_per_pv_capacity"]
        )
        parameters["oeprom"]["storage_lion"] = {
            "storage_capacity": storage_capacity,
            "capacity": storage_capacity * settings.CONFIG["battery_c_rate"],
            "capacity_cost": settings.get_ep_cost("storage_lion"),
        }
    elif "pv" in parameters["flow_data"]["scenario-secondary_heating"]:
        parameters["oeprom"]["storage_lion"] = {
            "expandable": True,
            "invest_relation_input_capacity": settings.CONFIG["battery_c_rate"],
            "capacity_cost": settings.get_ep_cost("storage_lion"),
        }

    return parameters


def debug_input_data(scenario: str, energysystem, request: HttpRequest):
    _ = solph.processing.parameter_as_dict(
        energysystem,
        exclude_attrs=["bus", "from_bus", "to_bus", "from_node", "to_node"],
    )
    return energysystem


def couple_battery_storage_to_pv_capacity(scenario: str, model, request: HttpRequest):
    """Set constraint in model which couples battery storage to PV capacity in a fix relation."""
    if model.es.groups["volatile_PV"].investment is not None:
        pv_flow = next((f, n) for f, n in model.InvestmentFlowBlock.INVESTFLOWS if f.label == "volatile_PV")
        storageblock = model.GenericInvestmentStorageBlock

        def _limit_lion_storage_to_pv_capacity(block):
            """Bound lion battery storage capacity to pv capacity"""
            for n in storageblock.INVESTSTORAGES:
                if n.label != "storage_lion":
                    continue
                for p in model.PERIODS:
                    expr = (
                        storageblock.total[n, p]
                        == model.InvestmentFlowBlock.invest[pv_flow[0], pv_flow[1], 0]
                        * settings.CONFIG["battery_storage_capacity_per_pv_capacity"]
                    )
                    storageblock.limit_storage_rule.add((n, p), expr)

        storageblock.limit_storage_rule = Constraint(storageblock.INVESTSTORAGES, model.PERIODS, noruleinit=True)
        storageblock.limit_storage_rule_build = BuildAction(rule=_limit_lion_storage_to_pv_capacity)
    return model


def unpack_oeprom(scenario: str, parameters: dict, request: HttpRequest) -> dict:
    return parameters["oeprom"]
