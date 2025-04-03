from pathlib import Path

import yaml

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR.parent / "data"

CONFIG_FILE = "config.yaml"
with (APP_DIR / CONFIG_FILE).open("r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

SCENARIO_MAX = 3  # maximum of renovation scenario flow instances

DEFAULT_ELECTRICITY_EEC = 2
