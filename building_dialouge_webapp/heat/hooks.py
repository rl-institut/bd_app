import inspect
import json

from django.http import HttpRequest
from django_oemof.simulation import SimulationError

from . import flows
from .settings import DATA_DIR
from .settings import SCENARIO_MAX


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

    return {"flow_data": flow_data}


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


def calculate_energy_demand(
    scenario: str,
    parameters: dict,
    request: HttpRequest,
) -> dict:
    # Energy demand
    data = {
        "oeprom": {
            "load_electricity": {"amount": 100},
            "volatile_PV": {"capacity": 1000},
        },
    }
    return data


def unpack_oeprom(scenario: str, parameters: dict, request: HttpRequest) -> dict:
    return parameters["oeprom"]
