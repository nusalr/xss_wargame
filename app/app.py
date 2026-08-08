from flask import Blueprint, current_app, jsonify, redirect, render_template, request, url_for

from .bot import BotBusyError, BotTimeoutError, BotVisitError

web = Blueprint("web", __name__)


@web.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@web.get("/")
def index():
    return render_template("index.html")


@web.get("/vuln")
def vuln():
    param = request.args.get("param", "")
    return render_template("vuln.html", param=param)


@web.get("/memo")
def memo():
    store = current_app.extensions["memo_store"]
    value = request.args.get("memo")
    notice = None
    if value is not None:
        if not value:
            notice = "Empty memos are not saved."
        elif store.add(value):
            notice = "Memo saved."
        else:
            notice = "Memo is too long."
    return render_template("memo.html", memos=store.list(), notice=notice)


@web.route("/flag", methods=["GET", "POST"])
def flag():
    message = None
    message_kind = "info"

    if request.method == "POST":
        param = request.form.get("param", "")
        if not param:
            message = "Please enter a value."
            message_kind = "error"
        elif len(param) > current_app.config["MAX_PARAM_LENGTH"]:
            message = "Input is too long."
            message_kind = "error"
        else:
            limiter = current_app.extensions["submission_limiter"]
            client_key = request.remote_addr or "unknown"
            if not limiter.allow(client_key):
                message = "Too many reports. Please wait and try again."
                message_kind = "error"
            else:
                try:
                    current_app.extensions["admin_visitor"].visit(param)
                    message = "Admin visited your page."
                    message_kind = "success"
                except BotBusyError:
                    message = "Admin bot is busy. Try again."
                    message_kind = "error"
                except BotTimeoutError:
                    message = "Admin bot timed out. Try again."
                    message_kind = "error"
                except BotVisitError:
                    current_app.logger.exception("Admin bot visit failed")
                    message = "Admin bot encountered an internal error."
                    message_kind = "error"

    return render_template("flag.html", message=message, message_kind=message_kind)


@web.route("/submit", methods=["GET", "POST"])
def submit():
    incorrect = False
    if request.method == "POST":
        submitted_flag = request.form.get("flag", "").strip()
        if submitted_flag == current_app.config["FLAG"]:
            return redirect(url_for("web.success"))
        incorrect = True
    return render_template("submit.html", incorrect=incorrect)


@web.get("/success")
def success():
    return render_template("success.html")


@web.get("/health")
def health():
    return jsonify(status="ok")
