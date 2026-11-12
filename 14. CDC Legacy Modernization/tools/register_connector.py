"""Register one Debezium PostgreSQL source connector. No source-app code changes."""
import json
import os
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8083"
PASSWORD = os.getenv("PG_PASSWORD", "")
if len(PASSWORD) < 16:
    raise SystemExit("Source .env first (PG_PASSWORD missing)")

configuration = {
    "name": "m14-retail-postgres",
    "config": {
        "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
        "plugin.name": "pgoutput",
        "database.hostname": "legacy-db",
        "database.port": "5432",
        "database.user": "retail",
        "database.password": PASSWORD,
        "database.dbname": "retail",
        "topic.prefix": "retailcdc",
        "table.include.list": "public.customer,public.product,public.sale,public.line_item",
        "slot.name": "m14_retail_slot",
        "publication.name": "m14_retail_pub",
        "publication.autocreate.mode": "filtered",
        "snapshot.mode": "initial",
        "tombstones.on.delete": "true",
        "decimal.handling.mode": "string",
        "heartbeat.interval.ms": "5000",
        "tasks.max": "1"
    }
}

def request(path, method="GET", payload=None):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        method=method,
        headers={"Content-Type": "application/json"} if payload is not None else {})
    try:
        with urllib.request.urlopen(req, timeout=6) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)

for attempt in range(60):
    try:
        response_code, connectors = request("/connectors")
        if response_code == 200:
            break
    except (OSError, TimeoutError, ValueError):
        pass
    time.sleep(2)
else:
    raise SystemExit("Kafka Connect not ready on localhost:8083; inspect docker compose logs connect")

if configuration["name"] in connectors:
    print("Retaining existing m14-retail-postgres connector (not overwriting user config)")
else:
    code, body = request("/connectors", "POST", configuration)
    if code not in (200, 201):
        raise SystemExit(f"Connector registration HTTP {code}: {body}")
    print("Debezium connector registered")

for attempt in range(60):
    status, body = request("/connectors/m14-retail-postgres/status")
    if status == 200:
        connector_state = body.get("connector", {}).get("state")
        tasks = [task.get("state") for task in body.get("tasks", [])]
        if connector_state == "RUNNING" and tasks and all(t == "RUNNING" for t in tasks):
            print("PASS actual Debezium connector + task RUNNING")
            break
        if connector_state == "FAILED" or "FAILED" in tasks:
            raise SystemExit(f"Debezium connector failed; inspect Connect logs: {body}")
    time.sleep(2)
else:
    raise SystemExit("Debezium connector did not reach RUNNING")
