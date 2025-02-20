import json

from django.http import HttpRequest
from settings import DATA_DIR


def read_flow_data(scenario: str, parameters: dict, request: HttpRequest) -> dict:
    """Read flow data from session."""

    # Check if all flows are entered ready
    # Check if all flowa are valid
    # Gather data from all flows in one dict
    # Return dict
    return {}


def get_renovation_data(flow_data: dict) -> dict:
    """Get renovation data from KfW based on flow data."""
    # Get cluster ID from KfW clustering
    # TODO: Get cluster ID from lookup table. Currently hardcoded.
    # https://github.com/rl-institut/bd_app/issues/90
    cluster_id = 1

    with (DATA_DIR / "renovations" / f"{cluster_id}.json").open("r", encoding="utf-8") as f:
        return json.load(f)
