import json
import os

import requests

URL = "http://localhost:8000/oemof/simulate"
SCENARIO = "oeprom"
PARAMETERS = {"renovation_scenario": "scenario1"}
SESSION_ID = os.environ["SESSION_ID"]  # look up in browser and store in env var SESSION_ID

data = {"scenario": SCENARIO, "parameters": json.dumps(PARAMETERS)}
response = requests.post(URL, data=data, headers={"Cookie": f"sessionid={SESSION_ID}"}, timeout=90)
print(response.status_code, response.text)  # noqa: T201
