import pytest

import models


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    db_file = tmp_path / "spring_todo.db"
    monkeypatch.setenv("TASKBOARD_DB", str(db_file))
    models.init_db()
    return db_file


def test_user_task_isolation(temp_db):
    alice_id = models.create_user("alice", "pass123")
    bob_id = models.create_user("bob", "secret")

<<<<<<< HEAD
    models.create_task("Polish the table", alice_id)
    models.create_task("Organize the cabinet", bob_id)
=======
    models.create_task("Полиране на масата", alice_id)
    models.create_task("Организиране на шкаф", bob_id)
>>>>>>> b87e5fea71cf0c2459026bbed66920225ab85046

    alice_tasks = models.get_tasks(alice_id)
    bob_tasks = models.get_tasks(bob_id)

    assert len(alice_tasks) == 1
<<<<<<< HEAD
    assert alice_tasks[0]["title"] == "Polish the table"
    assert bob_tasks[0]["title"] == "Organize the cabinet"
=======
    assert alice_tasks[0]["title"] == "Полиране на масата"
    assert bob_tasks[0]["title"] == "Организиране на шкаф"
>>>>>>> b87e5fea71cf0c2459026bbed66920225ab85046


def test_task_updates_and_deletes(temp_db):
    user_id = models.create_user("carol", "pass123")
<<<<<<< HEAD
    task_id = models.create_task("Sort clothes", user_id)

    models.update_task(task_id, user_id, title="Sort clothes and shoes", status=models.STATUS_DONE)
    task = models.get_task(task_id, user_id)

    assert task["title"] == "Sort clothes and shoes"
=======
    task_id = models.create_task("Подреждане на дрехи", user_id)

    models.update_task(task_id, user_id, title="Подреждане на дрехи и обувки", status=models.STATUS_DONE)
    task = models.get_task(task_id, user_id)

    assert task["title"] == "Подреждане на дрехи и обувки"
>>>>>>> b87e5fea71cf0c2459026bbed66920225ab85046
    assert task["status"] == models.STATUS_DONE

    models.delete_task(task_id, user_id)
    assert models.get_task(task_id, user_id) is None


def test_auth_helpers(temp_db):
    user_id = models.create_user("delta", "strong")
    assert models.verify_user("delta", "strong")
    assert not models.verify_user("delta", "wrong")
    assert not models.verify_user("missing", "pass")

    user = models.get_user(user_id)
    assert user["username"] == "delta"


def test_status_transitions(temp_db):
    user_id = models.create_user("echo", "pw")
<<<<<<< HEAD
    task_id = models.create_task("Cleaning", user_id)
=======
    task_id = models.create_task("Почистване", user_id)
>>>>>>> b87e5fea71cf0c2459026bbed66920225ab85046

    models.update_task(task_id, user_id, status=models.STATUS_IN_PROGRESS)
    assert models.get_task(task_id, user_id)["status"] == models.STATUS_IN_PROGRESS

    models.update_task(task_id, user_id, status=models.STATUS_IN_REVIEW)
    assert models.get_task(task_id, user_id)["status"] == models.STATUS_IN_REVIEW
<<<<<<< HEAD


def test_legacy_done_column_migrates_to_status(tmp_path, monkeypatch):
    db_file = tmp_path / "legacy_todo.db"
    monkeypatch.setenv("TASKBOARD_DB", str(db_file))

    with models.connection() as conn:
        conn.executescript(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                done INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            INSERT INTO users (username, password_hash) VALUES ('legacy', 'hash');
            INSERT INTO tasks (title, user_id, done) VALUES ('Old done task', 1, 1);
            INSERT INTO tasks (title, user_id, done) VALUES ('Old todo task', 1, 0);
            """
        )
        conn.commit()

    models.init_db()

    tasks = models.get_tasks(1)
    assert tasks[0]["status"] == models.STATUS_DONE
    assert tasks[1]["status"] == models.STATUS_TODO

    models.update_task(tasks[1]["id"], 1, status=models.STATUS_IN_PROGRESS)
    assert models.get_task(tasks[1]["id"], 1)["status"] == models.STATUS_IN_PROGRESS
=======
>>>>>>> b87e5fea71cf0c2459026bbed66920225ab85046
