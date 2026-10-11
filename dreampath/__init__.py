"""DreamPath AI: stream, package and progress guidance for engineering students."""
import logging

from flask import Flask, jsonify, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix

from . import db, routes_api, routes_auth, routes_pages, security
from .icons import banner, icon, thumb
from .config import build_config
from .meter import PHASES, TIERS

ERROR_TITLES = {
    400: "Bad request", 403: "Not allowed", 404: "Page not found", 405: "Method not allowed",
    409: "Action needed", 413: "Request too large", 429: "Slow down", 500: "Server error",
}


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(build_config())
    if test_config:
        app.config.update(test_config)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    if app.config["TRUST_PROXY"]:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    security.init_security(app)

    @app.template_filter("duration")
    def duration(minutes) -> str:
        """90 -> "1 h 30 min", 300 -> "5 h", 45 -> "45 min"."""
        minutes = int(minutes)
        hours, rest = divmod(minutes, 60)
        if not hours:
            return f"{rest} min"
        return f"{hours} h" if not rest else f"{hours} h {rest} min"

    app.jinja_env.globals.update(icon=icon, thumb=thumb, banner=banner)

    @app.context_processor
    def template_globals():
        return {"TIERS": TIERS, "PHASE_NAMES": PHASES}

    for blueprint in (routes_pages.bp, routes_auth.bp, routes_api.bp):
        app.register_blueprint(blueprint)

    @app.get("/healthz")
    def healthz():
        """Liveness probe for hosting platforms. Touches nothing sensitive."""
        return jsonify(status="ok")

    with app.app_context():
        db.init_db()

    register_error_handlers(app)
    return app


def _render_error(code: int, message: str | None):
    message = message or "Something went wrong on our side. Please try again."
    if request.path.startswith("/api/"):
        return jsonify(error=message), code
    return render_template("error.html", code=code, title=ERROR_TITLES.get(code, "Error"), message=message), code


def register_error_handlers(app: Flask) -> None:
    def http_error(error):
        return _render_error(error.code, error.description)

    for code in (400, 403, 404, 405, 409, 413, 429):
        app.register_error_handler(code, http_error)

    @app.errorhandler(500)
    def server_error(_error):
        app.logger.exception("Unhandled server error")
        return _render_error(500, None)
