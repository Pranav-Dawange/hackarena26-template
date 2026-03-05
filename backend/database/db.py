"""
database/db.py — MongoDB Connection Manager
---------------------------------------------
Uses PyMongo to connect to MongoDB.  The connection is stored as an app
extension (app.db) so every module can import it without circular imports.

Usage
-----
    from database.db import get_db
    db = get_db()
    db.nodes.find_one({"node_id": "NODE-001"})
"""

import sys
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from flask import Flask, current_app, g
from utils.logger import get_logger

logger = get_logger(__name__)

# Module-level client — shared across all requests in the same process
_client: MongoClient | None = None


def init_db(app: Flask) -> None:
    """
    Initialise the MongoDB client and attach it to the Flask app.
    Also creates required indexes on startup.
    """
    global _client
    uri     = app.config["MONGO_URI"]
    db_name = app.config["MONGO_DB_NAME"]

    try:
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        # Force an actual connection test
        _client.admin.command("ping")
        logger.info("Connected to MongoDB at %s (db: %s)", uri, db_name)
    except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
        logger.critical("Cannot connect to MongoDB: %s", exc)
        sys.exit(1)

    db = _client[db_name]
    app.db = db
    _ensure_indexes(db)


def get_db():
    """Return the database bound to the current Flask app context."""
    return current_app.db


def _ensure_indexes(db) -> None:
    """Create indexes for fast queries — safe to call multiple times."""
    # nodes: unique node_id, fast status lookups
    db.nodes.create_index([("node_id", ASCENDING)], unique=True)
    db.nodes.create_index([("status", ASCENDING)])

    # metrics: time-series queries by node and timestamp
    db.metrics.create_index([("node_id", ASCENDING), ("timestamp", DESCENDING)])

    # sensor_data: time-series queries
    db.sensor_data.create_index(
        [("node_id", ASCENDING), ("timestamp", DESCENDING)]
    )

    # events: recent events feed
    db.events.create_index([("timestamp", DESCENDING)])
    db.events.create_index([("node_id", ASCENDING)])

    logger.info("MongoDB indexes verified.")
