import os
import sqlite3
from functools import wraps

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from models import (
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

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("TASKBOARD_SECRET", "spring-list-key")

init_db()


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
    return {"current_user": get_current_user()}


@app.route("/")
@login_required
def index():
    user = get_current_user()
    tasks = get_tasks(user["id"])
    pending_tasks = [task for task in tasks if not task["done"]]
    done_tasks = [task for task in tasks if task["done"]]
    total = len(tasks)
    done_count = len(done_tasks)
    return render_template(
        "index.html",
        pending_tasks=pending_tasks,
        done_tasks=done_tasks,
        total=total,
        done=done_count,
        suggestions=SPRING_TASK_SUGGESTIONS,
    )


@app.route("/tasks", methods=["POST"])
@login_required
def add_task():
    title = request.form.get("title", "").strip()
    if title:
        user = get_current_user()
        create_task(title, user["id"])
    return redirect(url_for("index"))


@app.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    user = get_current_user()
    task = get_task(task_id, user["id"])
    if not task:
        return redirect(url_for("index"))
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        done = request.form.get("done") == "on"
        if title:
            update_task(task_id, user["id"], title=title, done=done)
        return redirect(url_for("index"))
    return render_template("edit_task.html", task=task)


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
@login_required
def delete_task_route(task_id):
    user = get_current_user()
    delete_task(task_id, user["id"])
    return redirect(url_for("index"))


@app.route("/api/tasks/<int:task_id>", methods=["PATCH"])
@login_required
def api_update_task(task_id):
    user = get_current_user()
    task = get_task(task_id, user["id"])
    if not task:
        return jsonify({"error": "task not found"}), 404
    payload = request.get_json(silent=True) or {}
    updates = {}
    if "title" in payload and isinstance(payload["title"], str):
        updates["title"] = payload["title"].strip()
    if "done" in payload:
        updates["done"] = bool(payload["done"])
    if not updates:
        return jsonify({"error": "nothing to update"}), 400
    update_task(task_id, user["id"], **updates)
    return jsonify({"status": "ok"})


@app.route("/register", methods=["GET", "POST"])
def register():
    if get_current_user():
        return redirect(url_for("index"))
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            error = "Въведете потребителско име и парола."
        else:
            try:
                create_user(username, password)
                user = get_user_by_username(username)
                session["user_id"] = user["id"]
                return redirect(url_for("index"))
            except sqlite3.IntegrityError:
                error = "Това име вече е заето."
    return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    if get_current_user():
        return redirect(url_for("index"))
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = verify_user(username, password)
        if not user:
            error = "Невалидни идентификационни данни."
        else:
            session["user_id"] = user["id"]
            return redirect(url_for("index"))
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
