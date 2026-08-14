import logging
import os
import secrets
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from hmac import compare_digest
from sqlite3 import IntegrityError
from functools import wraps
from logging.handlers import RotatingFileHandler
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from flask import (
    abort,
    Flask,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
    Response,
)

from log_dashboard import build_daily_status, build_log_dashboard
from models import (
    STATUS_DONE,
    STATUS_LABELS,
    STATUS_OPTIONS,
    SPRING_TASK_SUGGESTIONS,
    create_task,
    create_user,
    delete_task,
    get_task,
    get_tasks,
    get_user,
    get_user_by_username,
    init_db,
    update_task,
    verify_user,
)

APP_DIR = Path(__file__).resolve().parent
LOG_DIR = APP_DIR / "logs"
LOG_FILE = LOG_DIR / "taskboard.log"
ASSET_VERSION = int((APP_DIR / "static" / "main.js").stat().st_mtime)
MIN_PASSWORD_LENGTH = 6
USERNAME_MAX_LENGTH = 40
TASK_TITLE_MAX_LENGTH = 200
CSRF_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _has_log_file_handler(logger: logging.Logger, log_file: Path) -> bool:
    target = str(log_file)
    return any(
        isinstance(handler, RotatingFileHandler)
        and getattr(handler, "baseFilename", None) == target
        for handler in logger.handlers
    )


def configure_local_logging(flask_app: Flask) -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )

    for logger in (flask_app.logger, logging.getLogger("werkzeug")):
        if not _has_log_file_handler(logger, LOG_FILE):
            file_handler = RotatingFileHandler(
                LOG_FILE,
                maxBytes=1_000_000,
                backupCount=5,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.INFO)
            logger.addHandler(file_handler)
        logger.setLevel(logging.INFO)

    return LOG_FILE


def _get_secret_key() -> tuple[str, bool]:
    secret_key = os.environ.get("TASKBOARD_SECRET")
    if secret_key:
        return secret_key, False
    return secrets.token_hex(32), True


def _clean_log_value(value: str, max_length: int = 160) -> str:
    return value.replace("\r", " ").replace("\n", " ")[:max_length]


def get_remote_addr() -> str:
    remote_addr = request.headers.get("X-Forwarded-For", request.remote_addr or "-")
    return remote_addr.split(",")[0].strip()


app = Flask(__name__)
REQUEST_COUNT = Counter(
    "taskboard_http_requests_total",
    "Total number of HTTP requests",
     ["method", "endpoint", "status"]
)
REQUEST_DURATION = Histogram(
    "taskboard_http_request_duration_seconds",
    "HTTP request duration in seconds"
)

local_log_file = configure_local_logging(app)
secret_key, generated_secret = _get_secret_key()
app.config.update(
    SECRET_KEY=secret_key,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("TASKBOARD_COOKIE_SECURE") == "1",
)
app.logger.info("Taskboard local logging enabled at %s", local_log_file)
if generated_secret:
    app.logger.warning(
        "TASKBOARD_SECRET is not set; using a temporary development secret. "
        "Sessions will be reset when the app restarts."
    )

init_db()


@app.before_request
def mark_request_start():
    g.request_started_at = perf_counter()
    g.request_id = uuid4().hex[:12]


def csrf_token() -> str:
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


@app.before_request
def protect_state_changes():
    if request.method not in CSRF_METHODS:
        return

    expected_token = session.get("_csrf_token", "")
    provided_token = request.headers.get("X-CSRF-Token") or request.form.get(
        "csrf_token", ""
    )
    if expected_token and provided_token and compare_digest(
        expected_token, provided_token
    ):
        return

    app.logger.warning(
        "CSRF validation failed: request_id=%s method=%s path=%s user_id=%s",
        getattr(g, "request_id", "-"),
        request.method,
        request.path,
        session.get("user_id", "anonymous"),
    )
    abort(400, description="Invalid CSRF token")


@app.after_request
def log_request(response):
    REQUEST_COUNT.labels(
     method=request.method,
     endpoint=request.endpoint or "unknown",
     status=str(response.status_code)
     ).inc()
    started_at = getattr(g, "request_started_at", None)
    elapsed_ms = (perf_counter() - started_at) * 1000 if started_at else 0
    if started_at:
       REQUEST_DURATION.observe(elapsed_ms / 1000)
    user_agent = _clean_log_value(request.headers.get("User-Agent", "-"), 120)
    app.logger.info(
        "%s %s -> %s in %.1f ms from %s user_id=%s request_id=%s endpoint=%s user_agent=%s",
        request.method,
        request.path,
        response.status_code,
        elapsed_ms,
        get_remote_addr(),
        session.get("user_id", "anonymous"),
        getattr(g, "request_id", "-"),
        request.endpoint or "-",
        user_agent,
    )
    return response


@app.teardown_request
def log_request_exception(error):
    if error is not None:
        app.logger.error(
            "Unhandled error during %s %s",
            request.method,
            request.path,
            exc_info=(type(error), error, error.__traceback__),
        )


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_user(user_id)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not get_current_user():
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


@app.context_processor
def inject_user():
    return {
        "current_user": get_current_user(),
        "daily_status": build_daily_status(LOG_DIR),
        "status_labels": STATUS_LABELS,
        "status_options": STATUS_OPTIONS,
        "asset_version": ASSET_VERSION,
        "csrf_token": csrf_token,
    }


@app.route("/")
@login_required
def index():
    user = get_current_user()
    tasks = get_tasks(user["id"])
    grouped = {status: [] for status in STATUS_OPTIONS}
    for task in tasks:
        grouped.setdefault(task["status"], []).append(task)
    total = len(tasks)
    done_count = len(grouped.get(STATUS_DONE, []))
    columns = [
        {
            "status": status,
            "label": STATUS_LABELS.get(status, status.title()),
            "tasks": grouped.get(status, []),
        }
        for status in STATUS_OPTIONS
    ]
    return render_template(
        "index.html",
        columns=columns,
        total=total,
        done=done_count,
        suggestions=SPRING_TASK_SUGGESTIONS,
    )


@app.route("/logs")
@login_required
def logs_dashboard():
    dashboard = build_log_dashboard(
        LOG_DIR,
        filters={
            "level": request.args.get("level", ""),
            "q": request.args.get("q", ""),
        },
    )
    return render_template("logs.html", dashboard=dashboard)


@app.route("/tasks", methods=["POST"])
@login_required
def add_task():
    title = request.form.get("title", "").strip()[:TASK_TITLE_MAX_LENGTH]
    if title:
        user = get_current_user()
        task_id = create_task(title, user["id"])
        app.logger.info("Task created: task_id=%s user_id=%s", task_id, user["id"])
    return redirect(url_for("index"))


@app.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    user = get_current_user()
    task = get_task(task_id, user["id"])
    if not task:
        app.logger.warning(
            "Task edit requested for missing task_id=%s user_id=%s",
            task_id,
            user["id"],
        )
        return redirect(url_for("index"))
    if request.method == "POST":
        title = request.form.get("title", "").strip()[:TASK_TITLE_MAX_LENGTH]
        status = request.form.get("status") or task["status"]
        if status not in STATUS_OPTIONS:
            status = task["status"]
        if title:
            update_task(task_id, user["id"], title=title, status=status)
            app.logger.info(
                "Task updated: task_id=%s user_id=%s status=%s title_changed=%s",
                task_id,
                user["id"],
                status,
                title != task["title"],
            )
        return redirect(url_for("index"))
    return render_template("edit_task.html", task=task)


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
@login_required
def delete_task_route(task_id):
    user = get_current_user()
    delete_task(task_id, user["id"])
    app.logger.info("Task deleted: task_id=%s user_id=%s", task_id, user["id"])
    return redirect(url_for("index"))


@app.route("/api/tasks/<int:task_id>", methods=["PATCH"])
@login_required
def api_update_task(task_id):
    user = get_current_user()
    task = get_task(task_id, user["id"])
    if not task:
        app.logger.warning(
            "API update requested for missing task_id=%s user_id=%s",
            task_id,
            user["id"],
        )
        return jsonify({"error": "task not found"}), 404
    payload = request.get_json(silent=True) or {}
    updates = {}
    if "title" in payload and isinstance(payload["title"], str):
        title = payload["title"].strip()[:TASK_TITLE_MAX_LENGTH]
        if title:
            updates["title"] = title
    if "status" in payload and payload["status"] in STATUS_OPTIONS:
        updates["status"] = payload["status"]
    if not updates:
        app.logger.warning(
            "API update ignored with no valid fields: task_id=%s user_id=%s",
            task_id,
            user["id"],
        )
        return jsonify({"error": "nothing to update"}), 400
    update_task(task_id, user["id"], **updates)
    app.logger.info(
        "Task API updated: task_id=%s user_id=%s fields=%s",
        task_id,
        user["id"],
        ",".join(sorted(updates.keys())),
    )
    return jsonify({"status": "ok"})


@app.route("/register", methods=["GET", "POST"])
def register():
    if get_current_user():
        return redirect(url_for("index"))
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()[:USERNAME_MAX_LENGTH]
        password = request.form.get("password", "")
        if not username or not password:
            error = "Enter a username and password."
        elif len(password) < MIN_PASSWORD_LENGTH:
            error = f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
        else:
            try:
                create_user(username, password)
                user = get_user_by_username(username)
                session.clear()
                session["user_id"] = user["id"]
                app.logger.info("User registered: user_id=%s", user["id"])
                return redirect(url_for("index"))
            except IntegrityError:
                app.logger.warning(
                    "Registration failed: duplicate username=%s request_id=%s",
                    _clean_log_value(username, USERNAME_MAX_LENGTH),
                    getattr(g, "request_id", "-"),
                )
                error = "That username is already taken."
    return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    if get_current_user():
        return redirect(url_for("index"))
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()[:USERNAME_MAX_LENGTH]
        password = request.form.get("password", "")
        user = verify_user(username, password)
        if not user:
            app.logger.warning(
                "Login failed: username=%s remote_addr=%s request_id=%s",
                _clean_log_value(username, USERNAME_MAX_LENGTH),
                get_remote_addr(),
                getattr(g, "request_id", "-"),
            )
            error = "Invalid username or password."
        else:
            session.clear()
            session["user_id"] = user["id"]
            app.logger.info("User logged in: user_id=%s", user["id"])
            return redirect(url_for("index"))
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    user_id = session.get("user_id", "anonymous")
    session.clear()
    app.logger.info("User logged out: user_id=%s", user_id)
    return redirect(url_for("login"))

@app.route("/metrics")
def metrics():
    return Response(
        generate_latest(),
        mimetype=CONTENT_TYPE_LATEST
    )


if __name__ == "__main__":
    app.run(debug=os.environ.get("TASKBOARD_DEBUG") == "1")
