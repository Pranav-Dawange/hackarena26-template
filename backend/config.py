"""
config.py — Application Configuration
---------------------------------------
All tuneable parameters are loaded from environment variables (via .env).
Never hard-code secrets here; reference them through os.environ.
"""

import os
from dotenv import load_dotenv

# Load .env file from the project root (backend/ parent)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))


class Config:
    # ── Flask ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    DEBUG: bool     = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    HOST: str       = os.environ.get("HOST", "0.0.0.0")
    PORT: int       = int(os.environ.get("PORT", 5000))

    # ── MongoDB ────────────────────────────────────────────────────────────
    MONGO_URI: str  = os.environ.get(
        "MONGO_URI", "mongodb://localhost:27017/signalsevak"
    )
    MONGO_DB_NAME: str = os.environ.get("MONGO_DB_NAME", "signalsevak")

    # ── CORS ───────────────────────────────────────────────────────────────
    CORS_ORIGINS: list = os.environ.get("CORS_ORIGINS", "*").split(",")

    # ── Alert thresholds ───────────────────────────────────────────────────
    # RSSI values below this (dBm) trigger a weak-signal alert
    RSSI_ALERT_THRESHOLD: int   = int(os.environ.get("RSSI_ALERT_THRESHOLD", -80))
    # Packet-loss percentage above this triggers an alert
    PACKET_LOSS_THRESHOLD: float = float(
        os.environ.get("PACKET_LOSS_THRESHOLD", 20.0)
    )
    # Seconds since last heartbeat before a node is considered offline
    NODE_OFFLINE_TIMEOUT: int   = int(os.environ.get("NODE_OFFLINE_TIMEOUT", 60))

    # ── Logging ────────────────────────────────────────────────────────────
    LOG_LEVEL: str  = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE: str   = os.environ.get("LOG_FILE", "logs/signalsevak.log")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    MONGO_URI = "mongodb://localhost:27017/signalsevak_test"
