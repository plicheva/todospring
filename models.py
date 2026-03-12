import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Generator, List, Optional

DB_PATH = Path(__file__).resolve().parent / "db.sqlite"


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


def init_db(path: Optional[str] = None) -> None:
    schema = """
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        done INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """
    with connection(path) as conn:
        existing = conn.execute("PRAGMA table_info(tasks)").fetchall()
        column_names = [row["name"] for row in existing]
        if "notes" in column_names or "list_id" in column_names or "board_id" in column_names:
            conn.execute("DROP TABLE IF EXISTS tasks")
        conn.executescript(schema)
        conn.commit()


def row_to_dict(row: sqlite3.Row) -> Dict:
    data = dict(row)
    data["done"] = bool(data["done"])
    return data


def get_tasks(path: Optional[str] = None) -> List[Dict]:
    with connection(path) as conn:
        rows = conn.execute("SELECT * FROM tasks ORDER BY created_at").fetchall()
        return [row_to_dict(row) for row in rows]


def create_task(title: str, path: Optional[str] = None) -> int:
    with connection(path) as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title) VALUES (?)",
            (title,),
        )
        conn.commit()
        return cursor.lastrowid


def update_task(
    task_id: int,
    title: Optional[str] = None,
    notes: Optional[str] = None,
    done: Optional[bool] = None,
    path: Optional[str] = None,
) -> None:
    fields: List[str] = []
    params: List = []
    if title is not None:
        fields.append("title = ?")
        params.append(title)
    if done is not None:
        fields.append("done = ?")
        params.append(int(done))
    if not fields:
        return
    params.append(task_id)
    query = f"UPDATE tasks SET {', '.join(fields)} WHERE id=?"
    with connection(path) as conn:
        conn.execute(query, params)
        conn.commit()


def delete_task(task_id: int, path: Optional[str] = None) -> None:
    with connection(path) as conn:
        conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        conn.commit()


def get_task(task_id: int, path: Optional[str] = None) -> Optional[Dict]:
    with connection(path) as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        return row_to_dict(row) if row else None
