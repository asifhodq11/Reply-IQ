# ============================================================
# ReplyIQ Backend — Application Factory
# ============================================================

from flask import Flask, request
from .config import config_map
from .extensions import limiter, cors, talisman
from .utils.logger import log_event


def create_app(config_name="development"):
    """Assembles the Flask application."""

    app = Flask(__name__)

    # Load completely isolated environment config
    app.config.from_object(config_map[config_name])

    # 1. Attach Extensions
    limiter.init_app(app)

    # Enable CORS locked strictly to FRONTEND_URL
    cors.init_app(app, origins=[app.config["FRONTEND_URL"]])

    # Enforce security headers & HTTPS
    talisman.init_app(app, force_https=app.config.get("FORCE_HTTPS", False))

    # 2. Register Blueprints
    from .routes.auth import auth_bp
    from .routes.reviews import reviews_bp
    from .routes.approvals import approvals_bp
    from .routes.settings import settings_bp
    from .routes.payments import payments_bp
    from .routes.health import health_bp

    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(reviews_bp, url_prefix="/api/v1/reviews")
    app.register_blueprint(approvals_bp, url_prefix="/api/v1/approve")
    app.register_blueprint(settings_bp, url_prefix="/api/v1/settings")
    app.register_blueprint(payments_bp, url_prefix="/api/v1/payments")

    # Health endpoint sits at /api/v1/health (no prefix section needed if defined on root of bp)
    app.register_blueprint(health_bp, url_prefix="/api/v1")

    # 3. Register Global Error Handlers
    from werkzeug.exceptions import HTTPException
    from .utils.errors import build_error, build_error_from_exception
    from .utils.exceptions import ReplyIQError
    from marshmallow import ValidationError as MarshmallowValidationError

    @app.errorhandler(ReplyIQError)
    def handle_replyiq_error(exc):
        log_event("expected_error", code=exc.error_code, status=exc.http_status)
        return build_error_from_exception(exc)

    @app.errorhandler(429)
    def handle_rate_limit(exc):
        log_event("rate_limit_hit", path=request.path, ip=request.remote_addr)
        return build_error("RATE_LIMIT_EXCEEDED")

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc):
        log_event("http_exception", code=exc.code, path=request.path)
        code_map = {
            404: "REVIEW_NOT_FOUND",
            405: "VALIDATION_ERROR",
            400: "VALIDATION_ERROR",
        }
        error_code = code_map.get(exc.code, "SERVER_ERROR")
        return build_error(error_code, status=exc.code)

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc):
        import traceback

        log_event(
            "unhandled_exception",
            exception_type=type(exc).__name__,
            exception_message=str(exc),
            path=request.path,
            traceback=traceback.format_exc(),
        )
        return build_error("SERVER_ERROR")

    @app.errorhandler(MarshmallowValidationError)
    def handle_marshmallow_error(exc):
        log_event("validation_error", fields=str(exc.messages))
        return build_error("VALIDATION_ERROR", details={"fields": exc.messages})

    # Log initial startup (Event 1 from JSON Logger Requirements)
    # We delay the import subtly or just pass no params to avoid errors during test setup
    log_event("app_started", environment=config_name, version="1.0.0")

    return app
