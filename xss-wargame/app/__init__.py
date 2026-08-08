import logging
import os

from flask import Flask

from .app import web
from .bot import AdminBot
from .limits import SubmissionLimiter
from .storage import MemoStore


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        FLAG=os.getenv("FLAG") or f"FL{{{os.urandom(16).hex()}}}",
        INTERNAL_BASE_URL=os.getenv("INTERNAL_BASE_URL", "http://127.0.0.1:8000"),
        MAX_MEMOS=50,
        MAX_MEMO_LENGTH=500,
        MAX_PARAM_LENGTH=1_000,
        REPORT_LIMIT=5,
        REPORT_WINDOW_SECONDS=60,
        BOT_NAVIGATION_TIMEOUT_MS=4_000,
        BOT_SCRIPT_WAIT_MS=1_500,
    )
    if test_config:
        app.config.update(test_config)

    if not os.getenv("FLAG") and not app.config.get("TESTING"):
        logging.getLogger(__name__).warning(
            "FLAG is not set; using a randomly generated local-only flag."
        )

    app.extensions["memo_store"] = MemoStore(
        max_items=app.config["MAX_MEMOS"],
        max_length=app.config["MAX_MEMO_LENGTH"],
    )
    app.extensions["submission_limiter"] = SubmissionLimiter(
        limit=app.config["REPORT_LIMIT"],
        window_seconds=app.config["REPORT_WINDOW_SECONDS"],
    )
    app.extensions["admin_visitor"] = app.config.get("ADMIN_VISITOR") or AdminBot(
        base_url=app.config["INTERNAL_BASE_URL"],
        flag=app.config["FLAG"],
        navigation_timeout_ms=app.config["BOT_NAVIGATION_TIMEOUT_MS"],
        script_wait_ms=app.config["BOT_SCRIPT_WAIT_MS"],
    )

    app.register_blueprint(web)
    return app


__all__ = ["create_app"]
