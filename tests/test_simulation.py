import requests

response = requests.post("http://localhost:8000/oemof/simulate", data={"scenario": "oeprom"}, timeout=90)
