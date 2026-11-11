"""Test Knative-style CloudEvent HTTP callbacks (not a live Knative control plane)."""
import datetime
import json
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:5080"
payload = {"productId": "callback-1", "category": "clothing", "text": "I love this excellent item"}
def post(path, item):
    req = urllib.request.Request(BASE + path, method="POST", data=json.dumps(item).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req,timeout=10) as response:
        return response.status, json.load(response) if path == "/reviews" else None

status, response = post("/reviews", payload)
assert status == 202
ident = response["reviewId"]
review = {**payload, "id": ident, "submittedAt": datetime.datetime.now(
    datetime.timezone.utc).isoformat().replace("+00:00", "Z")}
event = {"specversion": "1.0", "id": "event-fixture-1", "source": "/globex/reviews",
         "type": "globex.review.submitted", "time": datetime.datetime.now(
          datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
         "datacontenttype": "application/json", "data": review}

# Structured outer KafkaSource CloudEvent wraps the original Kafka JSON event.
wrapped = {"specversion":"1.0", "id":"source-1", "source":"/kafka",
           "type":"dev.knative.kafka.event", "data":event}
assert post("/events/moderation", wrapped)[0] == 202
# Also verify the direct structured CloudEvent body style.
assert post("/events/sentiment", event)[0] == 202

for attempt in range(30):
    with urllib.request.urlopen(BASE + "/reviews/" + ident, timeout=5) as r:
        result = json.load(r)
    if result["moderation"] == "approved" and result["sentiment"] == "positive":
        break
    time.sleep(0.2)
else:
    raise SystemExit(f"Knative-style HTTP callback processing did not complete: {result}")
print("PASS wrapped KafkaSource CloudEvent -> moderation and direct CloudEvent -> sentiment")
print("NOTE: this validates HTTP callback contracts; it does NOT install a real Knative Broker/Trigger.")
