import os
from flask import Flask, jsonify, request

app = Flask(__name__)


@app.get("/")
def index():
    return jsonify(service="m09-source", version=os.getenv("APP_VERSION", "v1"))


@app.get("/healthz")
def healthz():
    return "ok\n"


@app.get("/echo")
def echo():
    return jsonify(message=request.args.get("message", ""))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
