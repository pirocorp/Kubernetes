"""Ensure running Debezium task, logical replication slot and four Kafka topics."""
import json
import subprocess
import urllib.request

def compose(*args):
    cmd = subprocess.run(["docker", "compose", "exec", "-T", *args],
                         capture_output=True, text=True, check=True)
    return cmd.stdout.strip()

with urllib.request.urlopen(
    "http://127.0.0.1:8083/connectors/m15-retail-postgres/status", timeout=10
) as res:
    status = json.load(res)
assert status["connector"]["state"] == "RUNNING", status
assert len(status["tasks"]) == 1 and status["tasks"][0]["state"] == "RUNNING", status
print("PASS real Debezium Connect source task")

slot = compose("legacy-db", "psql", "-U", "retail", "-d", "retail", "-Atc",
               "SELECT slot_name || ':' || plugin FROM pg_replication_slots WHERE slot_name='m15_retail_slot'")
assert "m15_retail_slot:pgoutput" in slot, slot
print("PASS PostgreSQL logical replication slot pgoutput")

topics = compose("kafka", "/opt/kafka/bin/kafka-topics.sh",
                 "--bootstrap-server", "localhost:19092", "--list").splitlines()
for name in ("customer", "sale", "line_item", "product"):
    expected = "retailcdc.public." + name
    assert expected in topics, (expected, topics)
print("PASS four actual CDC Kafka topics:", ", ".join(t for t in topics if t.startswith("retailcdc.")))
