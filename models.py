import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Generator, List, Optional

from werkzeug.security import check_password_hash, generate_password_hash

DB_PATH = Path(__file__).resolve().parent / "db.sqlite"

SPRING_TASK_SUGGESTIONS = [
<<<<<<< HEAD
    "Review home safety: replace detector batteries and check emergency plans.",
    "Declutter work and sleep areas, discard extras, and organize daily essentials.",
    "Clean and disinfect high-touch surfaces, then refresh the air preventively.",
    "Freshen textiles: wash curtains, rotate clothing, and change bedding.",
    "Check the refrigerator and pantry, discard expired food, and plan a weekly menu.",
    "Do a digital cleanup: archive important files, remove duplicate photos, and update passwords.",
=======
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
>>>>>>> b87e5fea71cf0c2459026bbed66920225ab85046
]


def get_db_path(override: Optional[str] = None) -> Path:
    if override:
        return Path(override)
    env = os.environ.get("TASKBOARD_DB")
    return Path(env) if env else DB_PATH


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def get_connection(path: Optional[str] = None) -> sqlite3.Connection:
    target = get_db_path(path)
    ensure_parent(target)
    conn = sqlite3.connect(target)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def connection(path: Optional[str] = None) -> Generator[sqlite3.Connection, None, None]:
    conn = get_connection(path)
    try:
        yield conn
    finally:
        conn.close()


STATUS_TODO = "todo"
STATUS_IN_PROGRESS = "in_progress"
STATUS_IN_REVIEW = "in_review"
STATUS_DONE = "done"

STATUS_OPTIONS = [STATUS_TODO, STATUS_IN_PROGRESS, STATUS_IN_REVIEW, STATUS_DONE]

STATUS_LABELS = {
<<<<<<< HEAD
    STATUS_TODO: "To Do",
    STATUS_IN_PROGRESS: "In Progress",
    STATUS_IN_REVIEW: "In Review",
    STATUS_DONE: "Done",
=======
    STATUS_TODO: "Чакащи",
    STATUS_IN_PROGRESS: "Работа",
    STATUS_IN_REVIEW: "На преглед",
    STATUS_DONE: "Готови",
>>>>>>> b87e5fea71cf0c2459026bbed66920225ab85046
}


def _recreate_task_table(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS tasks")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            status TEXT NOT NULL DEFAULT 'todo',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )


<<<<<<< HEAD
def _ensure_task_columns(conn: sqlite3.Connection, columns: set[str]) -> None:
    if "status" not in columns:
        conn.execute(
            "ALTER TABLE tasks ADD COLUMN status TEXT NOT NULL DEFAULT 'todo'"
        )
        columns.add("status")
        if "done" in columns:
            conn.execute(
                "UPDATE tasks SET status=? WHERE done=1",
                (STATUS_DONE,),
            )
    if "created_at" not in columns:
        conn.execute("ALTER TABLE tasks ADD COLUMN created_at TEXT")
        conn.execute(
            "UPDATE tasks SET created_at=CURRENT_TIMESTAMP "
            "WHERE created_at IS NULL OR created_at=''"
        )


=======
>>>>>>> b87e5fea71cf0c2459026bbed66920225ab85046
def init_db(path: Optional[str] = None) -> None:
    with connection(path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        task_info = conn.execute("PRAGMA table_info(tasks)").fetchall()
        columns = {row["name"] for row in task_info}
<<<<<<< HEAD
        if not columns:
            _recreate_task_table(conn)
        elif "user_id" not in columns:
            _recreate_task_table(conn)
        else:
            _ensure_task_columns(conn, columns)
=======
        if not columns or "user_id" not in columns:
            _recreate_task_table(conn)
>>>>>>> b87e5fea71cf0c2459026bbed66920225ab85046
        conn.commit()


def row_to_dict(row: sqlite3.Row) -> Dict:
    data = dict(row)
    data["status"] = data.get("status", STATUS_TODO)
    return data


def create_user(username: str, password: str, path: Optional[str] = None) -> int:
    password_hash = generate_password_hash(password)
    with connection(path) as conn:
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash),
        )
        conn.commit()
        return cursor.lastrowid


def get_user(user_id: int, path: Optional[str] = None) -> Optional[Dict]:
    with connection(path) as conn:
        row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if not row:
            return None
        return dict(row)


def get_user_by_username(username: str, path: Optional[str] = None) -> Optional[Dict]:
    with connection(path) as conn:
        row = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if not row:
            return None
        return dict(row)


def verify_user(username: str, password: str, path: Optional[str] = None) -> Optional[Dict]:
    user = get_user_by_username(username, path=path)
    if not user:
        return None
    if not check_password_hash(user["password_hash"], password):
        return None
    return user


def get_tasks(user_id: int, path: Optional[str] = None) -> List[Dict]:
    with connection(path) as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE user_id=? ORDER BY created_at", (user_id,)
        ).fetchall()
        return [row_to_dict(row) for row in rows]


def create_task(title: str, user_id: int, path: Optional[str] = None) -> int:
    with connection(path) as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title, user_id) VALUES (?, ?)",
            (title, user_id),
        )
        conn.commit()
        return cursor.lastrowid


def get_task(task_id: int, user_id: int, path: Optional[str] = None) -> Optional[Dict]:
    with connection(path) as conn:
        row = conn.execute(
            "SELECT * FROM tasks WHERE id=? AND user_id=?",
            (task_id, user_id),
        ).fetchone()
        return row_to_dict(row) if row else None


def update_task(
    task_id: int,
    user_id: int,
    title: Optional[str] = None,
    status: Optional[str] = None,
    path: Optional[str] = None,
) -> None:
    fields: List[str] = []
    params: List = []
    if title is not None:
        fields.append("title = ?")
        params.append(title)
    if status is not None:
        fields.append("status = ?")
        params.append(status)
    if not fields:
        return
    params.extend([task_id, user_id])
    query = f"UPDATE tasks SET {', '.join(fields)} WHERE id=? AND user_id=?"
    with connection(path) as conn:
        conn.execute(query, params)
        conn.commit()


def delete_task(task_id: int, user_id: int, path: Optional[str] = None) -> None:
    with connection(path) as conn:
        conn.execute(
            "DELETE FROM tasks WHERE id=? AND user_id=?", (task_id, user_id)
        )
        conn.commit()
