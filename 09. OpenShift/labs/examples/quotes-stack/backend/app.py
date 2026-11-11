import os
import pymysql
from pymysql.cursors import DictCursor
from flask import Flask, jsonify

app = Flask(__name__)


def connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "m09-qdb"),
        port=3306,
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASSWORD"],
        database=os.environ["MYSQL_DATABASE"],
        connect_timeout=3,
        cursorclass=DictCursor,
    )


@app.get("/healthz")
def healthz():
    return "ok\n", 200


@app.get("/readyz")
def readyz():
    try:
        with connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return "ready\n", 200
    except (pymysql.MySQLError, OSError):
        return "db unavailable\n", 503


@app.get("/version")
def version():
    return jsonify(version=os.getenv("APP_VERSION", "v1"))


@app.get("/quotes")
def quotes():
    try:
        with connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, text FROM quotes ORDER BY id")
                rows = cur.fetchall()
        return jsonify(quotes=rows, version=os.getenv("APP_VERSION", "v1"))
    except (pymysql.MySQLError, OSError):
        return jsonify(error="database unavailable"), 503


@app.get("/quotes/random")
def random_quote():
    try:
        with connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, text FROM quotes ORDER BY RAND() LIMIT 1")
                row = cur.fetchone()
        return jsonify(row or {})
    except (pymysql.MySQLError, OSError):
        return jsonify(error="database unavailable"), 503


@app.get("/quotes/<int:quote_id>")
def quote_by_id(quote_id):
    try:
        with connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, text FROM quotes WHERE id=%s", (quote_id,))
                row = cur.fetchone()
        if row is None:
            return jsonify(error="quote not found"), 404
        return jsonify(row)
    except (pymysql.MySQLError, OSError):
        return jsonify(error="database unavailable"), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
