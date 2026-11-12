#!/usr/bin/env bash
# Runs inside the dedicated one-shot Kafka initialization container.
# Create each known CDC topic before Kafka Connect and C# subscribe to them.
set -euo pipefail
ready=false
for attempt in $(seq 1 60); do
  if /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:19092 --list >/dev/null 2>&1; then
    ready=true
    break
  fi
  sleep 2
done
if test "$ready" != true; then
  echo "Kafka broker did not become ready in time" >&2
  exit 1
fi
for topic in retailcdc.public.customer retailcdc.public.product retailcdc.public.sale retailcdc.public.line_item; do
  /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:19092 \
    --create --if-not-exists --topic "$topic" --partitions 1 --replication-factor 1
done
echo "PASS: all four CDC topics exist before source and projection clients start"
