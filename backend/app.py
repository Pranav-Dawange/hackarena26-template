"""
app.py — SignalSevak Backend Entry Point
-----------------------------------------
Initialises the Flask application, registers all route blueprints,
configures CORS, and starts the development server.
"""

from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from database.db import init_db
from utils.logger import get_logger
from routes.node_routes import node_bp
from routes.metrics_routes import metrics_bp
from routes.alert_routes import alert_bp

logger = get_logger(__name__)


def create_app(config_class: type = Config) -> Flask:
    """Application factory — returns a configured Flask instance."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ── Cross-Origin Resource Sharing ─────────────────────────────────────
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    # ── Database ──────────────────────────────────────────────────────────
    init_db(app)

    # ── Blueprints ────────────────────────────────────────────────────────
    app.register_blueprint(node_bp,    url_prefix="/api")
    app.register_blueprint(metrics_bp, url_prefix="/api")
    app.register_blueprint(alert_bp,   url_prefix="/api")

    # ── Global error handlers ─────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(_err):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(err):
        logger.error("Internal server error: %s", err)
        return jsonify({"error": "Internal server error"}), 500

    # ── Health-check ping ─────────────────────────────────────────────────
    @app.route("/ping")
    def ping():
        return jsonify({"status": "ok", "service": "SignalSevak Backend"}), 200

    logger.info("SignalSevak backend initialised.")
    return app


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = create_app()
    app.run(
        host=app.config.get("HOST", "0.0.0.0"),
        port=app.config.get("PORT", 5000),
        debug=app.config.get("DEBUG", False),
    )
