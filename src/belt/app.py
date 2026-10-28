from __future__ import annotations

import logging

from flask import Flask, redirect, url_for
from flask.typing import ResponseReturnValue


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    logging.basicConfig(level=logging.INFO)

    from belt.bench import bp as bench_bp
    from belt.records import bp as records_bp
    from belt.transactions import bp as transactions_bp

    app.register_blueprint(records_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(bench_bp)

    @app.route("/")
    def home() -> ResponseReturnValue:
        return redirect(url_for("records.index"))

    @app.route("/healthz")
    def healthz() -> str:
        return "ok"

    return app
