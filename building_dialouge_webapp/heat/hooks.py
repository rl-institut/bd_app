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
    parameters["oeprom"] = {
        "load_electricity": {
            "profile": electricity_profile,
            "amount": electricity_amount,
        },
        "load_hotwater": {"profile": hotwater_profile, "amount": hotwater_amount},
        "load_heat": {"amount": heat_amount},
    }
    return parameters


def set_up_volatiles(scenario: str, parameters: dict, request: HttpRequest) -> dict:
    """Set up PV and solar-thermal profiles and capacities."""

    pv_profile = pd.Series(
        models.Photovoltaic.objects.get(
            elevation_angle=parameters["flow_data"]["elevation"],
            direction_angle=parameters["flow_data"]["direction"],
        ).profile,
    )
    pv_full_load_hours = pv_profile.sum()
    pv_measure = next(
        (
            measure
            for measure in parameters["renovation_data"]["additionalMeasures"]
            if measure["name"] == "PV-Anlage + Speicher + Ladesäule"
        ),
        None,
    )
    if not pv_measure:
        error_msg = "Could not find PV measure in renovation data."
        raise SimulationError(error_msg)
    pv_capacity = pv_measure["reductionFinalEnergy"] / pv_full_load_hours

    sth_profile = pd.Series(
        models.Solarthermal.objects.get(
            type="heat",
            temperature=parameters["flow_data"]["flow_temperature"],
            elevation_angle=parameters["flow_data"]["elevation"],
            direction_angle=parameters["flow_data"]["direction"],
        ).profile,
    )
    sth_full_load_hours = sth_profile.sum()
    sth_measure = next(
        (
            measure
            for measure in parameters["renovation_data"]["resultsMeasuresAccordingBEG"]["measures"]
            if measure["name"] == "Thermische Solaranlage"
        ),
        None,
    )
    if not sth_measure:
        error_msg = "Could not find Solarthermal measure in renovation data."
        raise SimulationError(error_msg)
    sth_capacity = sth_measure["reductionFinalEnergy"] / sth_full_load_hours

    parameters["oeprom"] = {
        "volatile_PV": {"profile": pv_profile, "capacity": pv_capacity},
        "volatile_STH": {"profile": sth_profile, "capacity": sth_capacity},
    }
    return parameters


def set_up_heatpump(scenario: str, parameters: dict, request: HttpRequest) -> dict:
    """Set up heatpump."""


def unpack_oeprom(scenario: str, parameters: dict, request: HttpRequest) -> dict:
    return parameters["oeprom"]
