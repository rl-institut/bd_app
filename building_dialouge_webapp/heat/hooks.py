import inspect
import json

import numpy as np
import pandas as pd
from django.http import HttpRequest
from django_oemof.simulation import SimulationError

from . import flows
from . import models
from .settings import CONFIG
from .settings import DATA_DIR
from .settings import SCENARIO_MAX
from .settings import TABULA_DATA
from .settings import map_elevation


def init_parameters(scenario: str, parameters: dict, request: HttpRequest) -> dict:
    """Set up structure of parameters used in hooks."""
    structure = {"flow_data": {}, "renovation_data": {}, "oeprom": {}}
    parameters.update(structure)
    return parameters


def init_flow_data(scenario: str, parameters: dict, request: HttpRequest) -> dict:
    """Read flow data from session."""
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
    while scenario_id <= SCENARIO_MAX:
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
    renovation_scenario = parameters["renovation_scenario"]

    scenario_keys = [key for key in parameters["flow_data"] if key.startswith(renovation_scenario)]
    if len(scenario_keys) == 0:
        error_msg = f"No renovation scenario '{renovation_scenario}' found in flow data."
        raise KeyError(error_msg)

    # Chosen renovation scenario keys are renamed to "scenario_<key_name>", removing scenario ID
    for key in scenario_keys:
        new_key = key.replace(renovation_scenario, "scenario")
        parameters["flow_data"][new_key] = parameters["flow_data"][key]
    return parameters


def init_tabula_data(scenario: str, parameters: dict, request: HttpRequest) -> dict:
    """Get tabula building."""

    building_type = CONFIG["building_type"][parameters["flow_data"]["building_type"]]

    # Get nearest available year using absolut difference
    year_diff = [abs(year - parameters["flow_data"]["construction_year"]) for year in CONFIG["construction_years"]]
    year_index = int(np.argmin(year_diff)) + 1
    if building_type == "TH" and year_index == 1:
        # There is no building data for "DE.N.TH.01."
        year_index = 2

    building_reference = f"DE.N.{building_type}.{year_index:02}."
    parameters["tabula_data"] = TABULA_DATA[building_reference].to_dict()

    # Set flow temperature depending on heating system (i.e. radiators/floorheating)
    parameters["tabula_data"]["flow_temperature"] = CONFIG["flow_temperature"][
        parameters["tabula_data"]["HeatingSystem_Emission"]
    ]

    # Set available roof area
    parameters["tabula_data"]["roof_area_available"] = (
        parameters["tabula_data"]["roof_area_tabula"] * CONFIG["roof_usage"]
    )

    return parameters


def init_roof(scenario: str, parameters: dict, request: HttpRequest) -> dict:
    """Calculate elevation and direction angles of roof."""
    if parameters["flow_data"]["flat_roof"] == "exists":
        parameters["flow_data"]["elevation"] = 0
        parameters["flow_data"]["direction"] = 0
    else:
        parameters["flow_data"]["elevation"] = map_elevation(
            parameters["flow_data"]["roof_inclination"],
        )
        parameters["flow_data"]["direction"] = CONFIG["orientation"][parameters["flow_data"]["roof_orientation"]]
    return parameters


def init_renovation_data(scenario: str, parameters: dict, request: HttpRequest) -> dict:
    """Get renovation data from KfW based on flow data."""
    # Get cluster ID from KfW clustering
    # TODO: Get cluster ID from lookup table. Currently hardcoded.
    # https://github.com/rl-institut/bd_app/issues/90
    cluster_id = 1

    with (DATA_DIR / "renovations" / f"{cluster_id}.json").open(
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
            eec=CONFIG["default_energy_efficiency_class"],
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
    hotwater_amount = parameters["flow_data"]["number_persons"] * CONFIG["hotwater_energy_consumption_per_person"]
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
    parameters["oeprom"]["volatile_PV"] = {}
    parameters["oeprom"]["volatile_STH"] = {}
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
        st_capacity = parameters["flow_data"]["solar_thermal_area"] / CONFIG["sth_density"]
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
            pv_area_available = parameters["tabula_data"]["roof_area_available"] * CONFIG["roof_usage_pv_share"]
        else:
            pv_area_available = parameters["tabula_data"]["roof_area_available"]
        pv_capacity_max = pv_area_available / CONFIG["pv_density"]
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
                - parameters["flow_data"]["pv_capacity"] * CONFIG["pv_density"],
                0,
            )
        elif "pv" in parameters["flow_data"]["scenario-secondary_heating"]:
            # Share available roof area across PV and STH
            sth_area_available = parameters["tabula_data"]["roof_area_available"] * (1 - CONFIG["roof_usage_pv_share"])
        else:
            sth_area_available = parameters["tabula_data"]["roof_area_available"]
        sth_capacity_max = sth_area_available / CONFIG["sth_density"]
        parameters["oeprom"]["volatile_STH"]["capacity_potential"] = sth_capacity_max
        parameters["oeprom"]["volatile_STH"]["expandable"] = True

    return parameters


def set_up_heatpumps(scenario: str, parameters: dict, request: HttpRequest) -> dict:
    """Set up heatpumps."""

    # Get temperature type from flow temperature
    type_temperature = f"VL{parameters['tabula_data']['flow_temperature']}C"

    if parameters["flow_data"]["energy_source"] == "air_heat_pump" or (
        parameters["flow_data"]["scenario-primary_heating"] == "heat_pump"
        and parameters["flow_data"]["scenario-heat_pump_type"] == "air_heat_pump"
    ):
        heatpump_air_cop = pd.Series(
            models.Heatpump.objects.get(
                type="air",
                type_temperature=type_temperature,
            ).profile,
        )
        parameters["oeprom"]["conversion_heatpump_air"] = {"expandable": True, "efficiency": heatpump_air_cop}

    if parameters["flow_data"]["energy_source"] == "geothermal_pump" or (
        parameters["flow_data"]["scenario-primary_heating"] == "heat_pump"
        and parameters["flow_data"]["scenario-heat_pump_type"] == "geothermal_pump"
    ):
        heatpump_water_cop = pd.Series(
            models.Heatpump.objects.get(
                type="water",
                type_temperature=type_temperature,
            ).profile,
        )
        parameters["oeprom"]["conversion_heatpump_water"] = {"expandable": True, "efficiency": heatpump_water_cop}

    if parameters["flow_data"]["energy_source"] == "groundwater" or (
        parameters["flow_data"]["scenario-primary_heating"] == "heat_pump"
        and parameters["flow_data"]["scenario-heat_pump_type"] == "groundwater"
    ):
        heatpump_brine_cop = pd.Series(
            models.Heatpump.objects.get(
                type="brine",
                type_temperature=type_temperature,
            ).profile,
        )
        parameters["oeprom"]["conversion_heatpump_brine"] = {"expandable": True, "efficiency": heatpump_brine_cop}

    return parameters


def unpack_oeprom(scenario: str, parameters: dict, request: HttpRequest) -> dict:
    return parameters["oeprom"]
