import os
import math
from datetime import datetime, timedelta, timezone

from flask import Flask, jsonify, request
from pymongo import MongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError

app = Flask(__name__)

LIMIT = 5
WINDOW_SECONDS = 60

# Works on any computer with a local MongoDB server.
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)

db = client["rate_limiter_db"]
counters = db["request_counters"]


@app.route("/")
def home():
    return jsonify({"message": "MongoDB Rate Limiter is running"})


@app.route("/api/data")
def get_data():
    client_id = request.headers.get("X-Client-ID", "demo-client").strip()

    if not client_id:
        return jsonify({"error": "Client ID cannot be empty"}), 400

    now = datetime.now(timezone.utc)

    # Start of the current fixed 60-second window.
    window_start = datetime.fromtimestamp(
        (int(now.timestamp()) // WINDOW_SECONDS) * WINDOW_SECONDS,
        tz=timezone.utc
    )

    window_end = window_start + timedelta(seconds=WINDOW_SECONDS)

    query = {
        "clientId": client_id,
        "windowStart": window_start
    }

    update = {
        "$inc": {"requestCount": 1},
        "$setOnInsert": {
            "expiresAt": window_end + timedelta(seconds=60)
        }
    }

    # Atomically increment or create the current counter.
    try:
        record = counters.find_one_and_update(
            query,
            update,
            upsert=True,
            return_document=ReturnDocument.AFTER
        )
    except DuplicateKeyError:
        # Handles a simultaneous first request for the same window.
        record = counters.find_one_and_update(
            query,
            {"$inc": {"requestCount": 1}},
            return_document=ReturnDocument.AFTER
        )

    count = record["requestCount"]

    if count > LIMIT:
        retry_after = max(
            1, math.ceil((window_end - now).total_seconds())
        )
        response = jsonify({
            "message": "Too Many Requests",
            "retryAfterSeconds": retry_after
        })
        response.status_code = 429
        response.headers["Retry-After"] = str(retry_after)
        return response

    return jsonify({
        "message": "Request allowed",
        "requestCount": count,
        "remaining": LIMIT - count
    }), 200


if __name__ == "__main__":
    # Verify MongoDB is available and create required indexes.
    client.admin.command("ping")

    counters.create_index(
        [("clientId", 1), ("windowStart", 1)],
        unique=True
    )

    counters.create_index(
        "expiresAt",
        expireAfterSeconds=0
    )

    app.run(host="127.0.0.1", port=5000, debug=False)