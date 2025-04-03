from pathlib import Path

import pandas as pd
import yaml

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR.parent / "data"

CONFIG_FILE = "config.yaml"
with (APP_DIR / CONFIG_FILE).open("r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

TABULA_FILE = DATA_DIR / "tabula" / "tabula_housing_types.csv"
TABULA_DATA = pd.read_csv(TABULA_FILE, index_col=0)

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
