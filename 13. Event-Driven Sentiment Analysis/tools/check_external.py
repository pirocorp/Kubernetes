"""Verify Kafka-integrated persistence through PostgreSQL and InfluxDB."""
import argparse
import json
import os
import subprocess
import urllib.error
import urllib.request


def check_postgres(min_count):
    p = subprocess.run(
        ["docker", "compose", "exec", "-T", "postgres", "psql", "-U", "globex",
         "-d", "globex", "-Atc", "SELECT count(*) FROM approved_reviews"],
        capture_output=True, text=True, check=True
    )
    count = int(p.stdout.strip())
    assert count >= min_count, ("PostgreSQL approved review count", count)
    print("PASS PostgreSQL approved reviews:", count)


def check_influx():
    token = os.getenv("INFLUX_TOKEN", "")
    assert len(token) >= 16, "Source .env first"
    query = 'from(bucket:"review_sentiment") |> range(start: -1h) |> filter(fn:(r) => r._measurement == "review_sentiment" and r._field == "score") |> limit(n: 1)'
    req = urllib.request.Request(
        "http://127.0.0.1:8086/api/v2/query?org=globex",
        method="POST", data=query.encode(),
        headers={"Authorization": "Token " + token,
                 "Content-Type": "application/vnd.flux",
                 "Accept": "application/csv"})
    with urllib.request.urlopen(req, timeout=10) as response:
        data = response.read().decode()
        assert response.status == 200 and "review_sentiment" in data, data[:500]
    print("PASS InfluxDB real sentiment score record")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--minimum-approved", type=int, default=3)
    args = parser.parse_args()
    check_postgres(args.minimum_approved)
    check_influx()
    print("PASS persistence integration across PostgreSQL and InfluxDB")
