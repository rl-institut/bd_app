import requests

URL = "http://localhost:8000/oemof/simulate"
SCENARIO = "oeprom"
PARAMETERS = {}  # if changing session data while testing: PARAMETERS = {"flow_data": ""}
SESSION_ID = "m9v0y72ld1f47bz8cwzqza2bypuo9u86"  # look up in browser

data = {"scenario": SCENARIO, "parameters": PARAMETERS}
response = requests.post(URL, data=data, headers={"Cookie": f"sessionid={SESSION_ID}"})  # Noqa: S113
print(response.status_code, response.text)  # Noqa: T201
