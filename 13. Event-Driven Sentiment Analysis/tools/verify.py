"""Real HTTP acceptance checks for Module 13 local, Kafka and Knative modes."""
import argparse
import json
import os
import time
import urllib.error
import urllib.request


def request(base, method, path, payload=None):
    body = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    if os.getenv("INGEST_KEY") and path.startswith("/reviews"):
        headers["X-Api-Key"] = os.environ["INGEST_KEY"]
    req = urllib.request.Request(
        base.rstrip("/") + path, method=method, data=body, headers=headers
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode()


def get_json(base, path):
    code, body = request(base, "GET", path)
    return code, json.loads(body)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-url", default="http://127.0.0.1:5080")
    p.add_argument("--timeout", type=int, default=40)
    p.add_argument("--expect-model", default="demo-lexicon-v1")
    args = p.parse_args()
    base = args.base_url

    health, body = request(base, "GET", "/healthz")
    assert health == 200 and body.strip() == "ok", (health, body)
    print("PASS healthz")
    status, _ = request(base, "GET", "/reviews/not-a-real-uuid")
    assert status == 404, status
    status, _ = request(base, "POST", "/reviews",
                        {"productId": "p1", "category": "invalid", "text": "great"})
    assert status == 400, status
    status, _ = request(base, "POST", "/reviews",
                        {"productId": "p1", "category": "clothing", "text": ""})
    assert status == 400, status
    print("PASS validation and unknown review cases")

    samples = [
        ("clothing", "I love this great shirt", "approved", "positive"),
        ("bags", "This bag is broken and terrible", "approved", "negative"),
        ("clothing", "This is spam and should be denied", "denied", "neutral"),
        ("electronics", "The product arrived", "approved", "neutral"),
    ]
    ids = []
    for i, (category, text, _, _) in enumerate(samples):
        code, raw = request(base, "POST", "/reviews", {
            "productId": f"sample-{i}",
            "category": category,
            "text": text
        })
        assert code == 202, (code, raw)
        payload = json.loads(raw)
        assert payload["status"] == "queued" and payload["reviewId"]
        ids.append(payload["reviewId"])

    for ident, (_, _, expected_moderation, expected_sentiment) in zip(ids, samples):
        deadline = time.monotonic() + args.timeout
        while time.monotonic() < deadline:
            code, record = get_json(base, "/reviews/" + ident)
            assert code == 200, (code, record)
            if record["moderation"] != "pending" and record["sentiment"] != "pending":
                break
            time.sleep(0.2)
        assert record["moderation"] == expected_moderation, record
        assert record["sentiment"] == expected_sentiment, record
        print("PASS review", ident, expected_moderation, expected_sentiment)

    code, approved = get_json(base, "/reviews/approved")
    assert code == 200 and isinstance(approved, list), (code, approved)
    for ident in ids[:2] + ids[3:]:
        assert any(review["id"] == ident for review in approved), (ident, approved)
    assert not any(review["id"] == ids[2] for review in approved), approved
    print("PASS moderation approval/denial and approved persistence view")

    code, sentiments = get_json(base, "/metrics/sentiment")
    assert code == 200 and isinstance(sentiments, list), (code, sentiments)
    assert sum(item["count"] for item in sentiments) >= 4, sentiments
    assert any(item["category"] == "clothing" for item in sentiments), sentiments
    print("PASS sentiment series by category")

    code, events = get_json(base, "/events")
    assert code == 200 and isinstance(events, list), (code, events)
    types = {event["type"] for event in events}
    assert {"globex.review.submitted", "globex.review.moderated",
            "globex.review.denied", "globex.review.sentiment"} <= types, types
    assert all(e["specversion"] == "1.0" and e["id"] and e["source"]
               for e in events), events
    assert any(e["type"] == "globex.review.sentiment" and
               e["data"]["model"] == args.expect_model for e in events), events
    print("PASS CloudEvents envelope and model source:", args.expect_model)
    print("ALL MODULE 13 HTTP ACCEPTANCE CHECKS PASSED")


if __name__ == "__main__":
    main()
