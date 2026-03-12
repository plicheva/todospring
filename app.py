import os

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from models import (
    create_task,
    delete_task,
    get_task,
    get_tasks,
    init_db,
    update_task,
)

SPRING_TASK_SUGGESTIONS = [
    "Освободете една лавица или чекмедже от излишни вещи",
    "Изтъркайте дръжки и ключове на светлините",
    "Подредете канцеларските материали и изхвърлете счупените",
    "Изчистете хладилника и премахнете изтекли продукти",
    "Освежете текстилите: възглавници, завеси, покривки",
    "Прегледайте обувки и дрехи за дарение",
    "Почистете килимите и постелките",
    "Измийте прозорците, за да влезе повече светлина",
    "Подредете кабелите и предпазните ленти",
    "Планирайте кратка дигитална очистка (имейли, файлове)",
]

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("TASKBOARD_SECRET", "spring-list-key")

init_db()


@app.route("/")
def index():
    tasks = get_tasks()
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
def add_task():
    title = request.form.get("title", "").strip()
    if title:
        create_task(title)
    return redirect(url_for("index"))


@app.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
def edit_task(task_id):
    task = get_task(task_id)
    if not task:
        return redirect(url_for("index"))
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        done = request.form.get("done") == "on"
        if title:
            update_task(task_id, title=title, done=done)
        return redirect(url_for("index"))
    return render_template("edit_task.html", task=task)


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
def delete_task_route(task_id):
    delete_task(task_id)
    return redirect(url_for("index"))


@app.route("/api/tasks/<int:task_id>", methods=["PATCH"])
def api_update_task(task_id):
    payload = request.get_json(silent=True) or {}
    task = get_task(task_id)
    if not task:
        return jsonify({"error": "task not found"}), 404
    updates = {}
    if "title" in payload and isinstance(payload["title"], str):
        updates["title"] = payload["title"].strip()
    if "done" in payload:
        updates["done"] = bool(payload["done"])
    if not updates:
        return jsonify({"error": "nothing to update"}), 400
    update_task(task_id, **updates)
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True)
