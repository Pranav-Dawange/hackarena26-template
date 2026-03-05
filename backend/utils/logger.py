"""
utils/logger.py — Centralised Logging Setup
--------------------------------------------
Configures a structured logger that writes to both the console and a
rotating log file.  Call get_logger(__name__) in any module.
"""

import logging
import os
from logging.handlers import RotatingFileHandler


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger.  The root logger is configured once on first
    call so all subsequent loggers inherit the same handlers and level.
    """
    root = logging.getLogger()

    # Only configure the root logger once
    if root.handlers:
        return logging.getLogger(name)

    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_file  = os.environ.get("LOG_FILE", "logs/signalsevak.log")

    root.setLevel(log_level)

    # ── Console handler ───────────────────────────────────────────────────
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    root.addHandler(console_handler)

    # ── Rotating file handler ─────────────────────────────────────────────
    try:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=3
        )
        file_handler.setFormatter(fmt)
        root.addHandler(file_handler)
    except OSError as exc:
        root.warning("Could not open log file %s: %s", log_file, exc)

    return logging.getLogger(name)
