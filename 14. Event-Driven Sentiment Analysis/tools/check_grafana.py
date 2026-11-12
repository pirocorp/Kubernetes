"""Verify the real provisioned Globex Grafana datasource and dashboard."""
import base64
import json
import os
import time
import urllib.error
import urllib.request

password = os.getenv("GRAFANA_PASSWORD", "")
if len(password) < 16:
    raise SystemExit("Source your local .env before checking Grafana")
authorization = base64.b64encode(("admin:" + password).encode()).decode()
base = "http://127.0.0.1:3300"
def query(path):
    req = urllib.request.Request(base + path, headers={"Authorization": "Basic " + authorization})
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.load(response)

for attempt in range(30):
    try:
        data = query("/api/datasources/uid/globex-sentiment")
        doc = query("/api/dashboards/uid/m14-globex-sentiment")
        assert data["type"] == "influxdb" and data["uid"] == "globex-sentiment", data
        dash = doc["dashboard"]
        assert dash["uid"] == "m14-globex-sentiment" and len(dash["panels"]) >= 2, dash
        print("PASS Grafana real InfluxDB datasource and 2-panel provisioned dashboard")
        break
    except (urllib.error.URLError, KeyError, AssertionError, ValueError) as ex:
        if attempt == 29:
            raise SystemExit(f"Grafana provisioning not ready: {ex}") from ex
        time.sleep(2)
