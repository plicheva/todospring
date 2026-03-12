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

    models.create_task("Полиране на масата", alice_id)
    models.create_task("Организиране на шкаф", bob_id)

    alice_tasks = models.get_tasks(alice_id)
    bob_tasks = models.get_tasks(bob_id)

    assert len(alice_tasks) == 1
    assert alice_tasks[0]["title"] == "Полиране на масата"
    assert bob_tasks[0]["title"] == "Организиране на шкаф"


def test_task_updates_and_deletes(temp_db):
    user_id = models.create_user("carol", "pass123")
    task_id = models.create_task("Подреждане на дрехи", user_id)

    models.update_task(task_id, user_id, title="Подреждане на дрехи и обувки", status=models.STATUS_DONE)
    task = models.get_task(task_id, user_id)

    assert task["title"] == "Подреждане на дрехи и обувки"
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
    task_id = models.create_task("Почистване", user_id)

    models.update_task(task_id, user_id, status=models.STATUS_IN_PROGRESS)
    assert models.get_task(task_id, user_id)["status"] == models.STATUS_IN_PROGRESS

    models.update_task(task_id, user_id, status=models.STATUS_IN_REVIEW)
    assert models.get_task(task_id, user_id)["status"] == models.STATUS_IN_REVIEW
