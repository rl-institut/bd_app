from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml
from oemof.tools import economics

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR.parent / "data"

CONFIG_FILE = "config.yaml"
with (APP_DIR / CONFIG_FILE).open("r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

TABULA_DATA = pd.read_csv(DATA_DIR / "tabula" / "tabula_housing_types.csv", index_col=0).fillna("")

# COSTS
COSTS_RENOVATION = pd.read_csv(DATA_DIR / "costs" / "costs_renovation.csv", index_col=0).fillna("")
COSTS_TECHNOLOGIES = pd.read_csv(DATA_DIR / "costs" / "costs_technologies.csv", index_col=0, header=[0, 1]).fillna("")

SCENARIO_MAX = 3  # maximum of renovation scenario flow instances


def map_elevation(angle: int) -> int:
    """
    Map elevation angle to discrete value.

    Possible angles are {0, 10, 20, 30, 40, 45, 50, 60, 70, 80, 90}.
    """
    if angle > 90:  # noqa: PLR2004
        error_msg = "Elevation angle is greater than 90°."
        raise ValueError(error_msg)
    if angle < 0:
        error_msg = "Elevation angle is lower than 0°."
        raise ValueError(error_msg)
    if 40 <= angle <= 50:  # noqa: PLR2004
        # This enables special angle of 45°
        return round(angle / 5) * 5
    return round(angle / 10) * 10


def get_ep_cost(technology: str, capacity: int | None = None) -> float:
    """
    Return annualized capacity costs plus OPEX for a given capacity.

    If no capacity is given, mean values are used for capacity costs.
    "Real" costs are calculated in postprocessing, using optimized capacity.
    """
    if capacity is None:
        capex = COSTS_TECHNOLOGIES.loc[technology, "capex_kW"].sum() / len(
            COSTS_TECHNOLOGIES.loc[technology, "capex_kW"],
        )
        opex = COSTS_TECHNOLOGIES.loc[technology, "opex_kW_annual"].sum() / len(
            COSTS_TECHNOLOGIES.loc[technology, "opex_kW_annual"],
        )
    else:
        capex = COSTS_TECHNOLOGIES.loc[technology, ("capex_kW", str(capacity))]
        opex = COSTS_TECHNOLOGIES.loc[technology, ("opex_kW_annual", str(capacity))]

    annuity = economics.annuity(capex, CONFIG["lifetime"], CONFIG["wacc"] / 100)
    return annuity + opex
