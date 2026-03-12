import pytest

import models


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    db_file = tmp_path / "spring_todo.db"
    monkeypatch.setenv("TASKBOARD_DB", str(db_file))
    models.init_db()
    return db_file


def test_create_and_retrieve_task(temp_db):
    task_id = models.create_task("Buy tulips")
    tasks = models.get_tasks()
    assert len(tasks) == 1
    task = tasks[0]
    assert task["id"] == task_id
    assert task["title"] == "Buy tulips"
    assert task["done"] is False


def test_update_done_and_text(temp_db):
    task_id = models.create_task("Spray watered plants")
    models.update_task(task_id, title="Water plants thoroughly", done=True)
    task = models.get_task(task_id)
    assert task["title"] == "Water plants thoroughly"
    assert task["done"] is True


def test_delete_task(temp_db):
    task_id = models.create_task("Recycle bottles")
    models.delete_task(task_id)
    assert models.get_task(task_id) is None
    assert models.get_tasks() == []
