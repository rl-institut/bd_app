import json

from django.http import HttpRequest

from .settings import DATA_DIR


def read_flow_data(scenario: str, parameters: dict, request: HttpRequest) -> dict:
    """Read flow data from session."""

    flow_data = request.session.get("django_htmx_flow", {})
    # Check if all flows are entered ready
    # Check if all flowa are valid
    # Gather data from all flows in one dict
    # Return dict
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
