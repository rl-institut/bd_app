import inspect
import json

from django.http import HttpRequest
from django_oemof.simulation import SimulationError

from . import flows
from .settings import DATA_DIR
from .settings import SCENARIO_MAX


def set_up_parameters_structure(scenario: str, parameters: dict, request: HttpRequest) -> dict:
    """Set up structure of parameters used in hooks."""
    structure = {"flow_data": {}, "renovation_data": {}, "oeprom": {}}
    parameters.update(structure)
    return parameters


def read_flow_data(scenario: str, parameters: dict, request: HttpRequest) -> dict:
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


def get_renovation_data(scenario: str, parameters: dict, request: HttpRequest) -> dict:
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


def set_profiles(
    scenario: str,
    parameters: dict,
    request: HttpRequest,
) -> dict:
    parameters["oeprom"] = {
        "load_electricity": {"profile": 100},
        "volatile_PV": {"capacity": 1000},
    }
    return parameters


def unpack_oeprom(scenario: str, parameters: dict, request: HttpRequest) -> dict:
    return parameters["oeprom"]
