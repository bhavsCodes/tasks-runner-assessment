import time
import uuid

from app.database import get_connection
from app.models import TaskStatus
from app.main import startup_event

from app.dependencies import has_cycle

from app.scheduler import start_scheduler
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Task Runner Service is running"
    }


def test_create_task():
    response = client.post(
        "/tasks",
        json={
            "name": "test_task",
            "dependencies": [],
            "max_retries": 2,
            "failure_chance": 0.0
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "test_task"
    assert data["status"] == "waiting"
    assert data["dependencies"] == []
    assert data["max_retries"] == 2
    assert data["attempts"] == 0


def test_get_task():
    create_response = client.post(
        "/tasks",
        json={
            "name": "get_task_test",
            "dependencies": [],
            "max_retries": 2,
            "failure_chance": 0.0
        }
    )

    assert create_response.status_code == 200

    task_id = create_response.json()["id"]

    get_response = client.get(f"/tasks/{task_id}")

    assert get_response.status_code == 200

    data = get_response.json()

    assert data["id"] == task_id
    assert data["name"] == "get_task_test"


def test_cancel_task():
    create_response = client.post(
        "/tasks",
        json={
            "name": "cancel_test_task",
            "dependencies": [],
            "max_retries": 20,
            "failure_chance": 0.0
        }
    )

    assert create_response.status_code == 200

    task_id = create_response.json()["id"]

    cancel_response = client.post(f"/tasks/{task_id}/cancel")

    assert cancel_response.status_code == 200

    data = cancel_response.json()

    assert data["id"] == task_id
    assert data["status"] == "cancelled"
    assert data["error"] == "Task cancelled by user"


def test_task_with_dependency():
    first_response = client.post(
        "/tasks",
        json={
            "name": "first_task",
            "dependencies": [],
            "max_retries": 2,
            "failure_chance": 0.0
        }
    )

    assert first_response.status_code == 200

    first_task_id = first_response.json()["id"]

    second_response = client.post(
        "/tasks",
        json={
            "name": "second_task",
            "dependencies": [first_task_id],
            "max_retries": 2,
            "failure_chance": 0.0
        }
    )

    assert second_response.status_code == 200

    data = second_response.json()

    assert data["name"] == "second_task"
    assert data["dependencies"] == [first_task_id]


def test_unknown_dependency():
    response = client.post(
        "/tasks",
        json={
            "name": "invalid_dependency_task",
            "dependencies": ["does-not-exist"],
            "max_retries": 2,
            "failure_chance": 0.0
        }
    )

    assert response.status_code == 400

    data = response.json()

    assert "Unknown dependencies" in data["detail"]


def test_task_retries_and_fails():
    start_scheduler()

    response = client.post(
        "/tasks",
        json={
            "name": "retry_test_task",
            "dependencies": [],
            "max_retries": 2,
            "failure_chance": 1.0
        }
    )

    assert response.status_code == 200

    task_id = response.json()["id"]

    final_data = None

    for _ in range(60):
        response = client.get(f"/tasks/{task_id}")

        assert response.status_code == 200

        data = response.json()

        print(
            "status:",
            data["status"],
            "attempts:",
            data["attempts"]
        )

        if data["status"] in ["failed", "succeeded"]:
            final_data = data
            break

        time.sleep(1)

    assert final_data is not None
    assert final_data["status"] == "failed"
    assert final_data["attempts"] == 3


def test_stats_endpoint():
    response = client.get("/stats")

    assert response.status_code == 200

    data = response.json()

    assert "running" in data
    assert "waiting" in data

    assert isinstance(data["running"], int)
    assert isinstance(data["waiting"], int)


def test_restart_recovers_running_tasks():
    connection = get_connection()
    cursor = connection.cursor()

    task_id = str(uuid.uuid4())

    cursor.execute(
        """
        INSERT INTO tasks (
            id,
            name,
            status,
            dependencies,
            attempts,
            max_retries,
            failure_chance,
            error
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            task_id,
            "restart_test_task",
            TaskStatus.RUNNING.value,
            "[]",
            1,
            2,
            0.0,
            None,
        ),
    )

    connection.commit()
    connection.close()

    startup_event()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT status, error FROM tasks WHERE id = ?",
        (task_id,),
    )

    row = cursor.fetchone()
    connection.close()

    assert row["status"] == TaskStatus.WAITING.value
    assert row["error"] == "Recovered after service restart"


def test_cycle_detection():
    graph = {
        "task_a": ["task_b"],
        "task_b": ["task_c"],
        "task_c": ["task_a"],
    }

    assert has_cycle(graph) is True


def test_no_cycle_detection():
    graph = {
        "task_a": ["task_b"],
        "task_b": ["task_c"],
        "task_c": [],
    }

    assert has_cycle(graph) is False