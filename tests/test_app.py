import re

import pytest

import models


def _csrf_from(response):
    html = response.get_data(as_text=True)
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    if match:
        return match.group(1)
    match = re.search(r'name="csrf-token" content="([^"]+)"', html)
    assert match, "CSRF token not found in response"
    return match.group(1)


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "app_flow.db"
    monkeypatch.setenv("TASKBOARD_DB", str(db_file))
    monkeypatch.setenv("TASKBOARD_SECRET", "test-secret")

    import app as app_module

    app_module.init_db()
    app_module.app.config.update(TESTING=True, SECRET_KEY="test-secret")
    with app_module.app.test_client() as test_client:
        yield test_client


def test_post_without_csrf_is_rejected(client):
    response = client.post(
        "/register",
        data={"username": "blocked", "password": "secret1"},
    )
    assert response.status_code == 400


def test_auth_task_and_logs_flow(client):
    token = _csrf_from(client.get("/register"))
    response = client.post(
        "/register",
        data={"username": "flow", "password": "secret1", "csrf_token": token},
        follow_redirects=False,
    )
    assert response.status_code == 302

    with client.session_transaction() as session:
        user_id = session["user_id"]

    response = client.get("/")
    token = _csrf_from(response)
    assert response.status_code == 200
    assert "Spring Cleaning Board" in response.get_data(as_text=True)

    response = client.post(
        "/tasks",
        data={"title": "Flow task", "csrf_token": token},
        follow_redirects=False,
    )
    assert response.status_code == 302

    task = models.get_tasks(user_id)[0]
    response = client.get(f"/tasks/{task['id']}/edit")
    token = _csrf_from(response)
    assert response.status_code == 200

    response = client.post(
        f"/tasks/{task['id']}/edit",
        data={
            "title": "Updated flow task",
            "status": models.STATUS_IN_PROGRESS,
            "csrf_token": token,
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert models.get_task(task["id"], user_id)["status"] == models.STATUS_IN_PROGRESS

    response = client.patch(
        f"/api/tasks/{task['id']}",
        json={"status": models.STATUS_DONE},
        headers={"X-CSRF-Token": token},
    )
    assert response.status_code == 200
    assert models.get_task(task["id"], user_id)["status"] == models.STATUS_DONE

    response = client.post(
        f"/tasks/{task['id']}/delete",
        data={"csrf_token": token},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert models.get_task(task["id"], user_id) is None

    response = client.get("/logs")
    assert response.status_code == 200
    assert "Application Logs" in response.get_data(as_text=True)

    response = client.get("/logout", follow_redirects=False)
    assert response.status_code == 302
