import json
import uuid

from fastapi import FastAPI, HTTPException

from datetime import datetime,timezone

from app.database import get_connection, initialize_database
from app.dependencies import validate_dependencies,has_cycle
from app.models import TaskCreate, TaskResponse, TaskStatus
from app.scheduler import start_scheduler


app = FastAPI(title="Task Runner Service")


@app.on_event("startup")
def startup_event():
    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE tasks
        SET status = ?, error = ?
        WHERE status = ?
        """,
        (
            TaskStatus.WAITING.value,
            "Recovered after service restart",
            TaskStatus.RUNNING.value,
        ),
    )

    connection.commit()
    connection.close()

    start_scheduler()


@app.get("/")
def root():
    return {"message": "Task Runner Service is running"}


import json
import uuid

from fastapi import FastAPI, HTTPException

from app.database import get_connection, initialize_database
from app.dependencies import validate_dependencies,has_cycle
from app.models import TaskCreate, TaskResponse, TaskStatus
from app.scheduler import start_scheduler


app = FastAPI(title="Task Runner Service")


@app.on_event("startup")
def startup_event():
    initialize_database()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE tasks
        SET status = ?, error = ?
        WHERE status = ?
        """,
        (
            TaskStatus.WAITING.value,
            "Recovered after service restart",
            TaskStatus.RUNNING.value,
        ),
    )

    connection.commit()
    connection.close()

    start_scheduler()


@app.get("/")
def root():
    return {"message": "Task Runner Service is running"}


@app.post("/tasks", response_model=TaskResponse)
def create_task(task: TaskCreate):
    missing_dependencies = validate_dependencies(task.dependencies)

    if missing_dependencies:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown dependencies: {missing_dependencies}",
        )
    
    task_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    connection = get_connection()
    cursor = connection.cursor()

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
            error,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?,?)
        """,
        (
            task_id,
            task.name,
            TaskStatus.WAITING.value,
            json.dumps(task.dependencies),
            0,
            task.max_retries,
            task.failure_chance,
            None,
            created_at,
        ),
    )

    connection.commit()
    connection.close()

    return TaskResponse(
        id=task_id,
        name=task.name,
        status=TaskStatus.WAITING,
        dependencies=task.dependencies,
        attempts=0,
        max_retries=task.max_retries,
        error=None,

        created_at=created_at,
        started_at=None,
        completed_at=None,
    )


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: str):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,),
    )

    row = cursor.fetchone()
    connection.close()

    if row is None:
        return {"error": "Task not found"}

    return TaskResponse(
        id=row["id"],
        name=row["name"],
        status=TaskStatus(row["status"]),
        dependencies=json.loads(row["dependencies"]),
        attempts=row["attempts"],
        max_retries=row["max_retries"],
        error=row["error"],

        created_at=row["created_at"],
        started_at=row["started_at"],
        completed_at=row["completed_at"],
    )



@app.post("/tasks/{task_id}/cancel", response_model=TaskResponse)
def cancel_task(task_id: str):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,),
    )

    row = cursor.fetchone()

    if row is None:
        connection.close()
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    if row["status"] in [
        TaskStatus.SUCCEEDED.value,
        TaskStatus.FAILED.value,
        TaskStatus.BLOCKED.value,
        TaskStatus.CANCELLED.value,
    ]:
        connection.close()
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel task in status {row['status']}"
        )

    cursor.execute(
        """
        UPDATE tasks
        SET status = ?, error = ?
        WHERE id = ?
        """,
        (
            TaskStatus.CANCELLED.value,
            "Task cancelled by user",
            task_id,
        ),
    )

    connection.commit()

    cursor.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,),
    )

    updated_row = cursor.fetchone()
    connection.close()

    return TaskResponse(
        id=updated_row["id"],
        name=updated_row["name"],
        status=TaskStatus(updated_row["status"]),
        dependencies=json.loads(updated_row["dependencies"]),
        attempts=updated_row["attempts"],
        max_retries=updated_row["max_retries"],
        error=updated_row["error"],
    )



@app.get("/stats")
def get_stats():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT COUNT(*) AS count FROM tasks WHERE status = ?",
        (TaskStatus.RUNNING.value,),
    )
    running_count = cursor.fetchone()["count"]

    cursor.execute(
        "SELECT COUNT(*) AS count FROM tasks WHERE status = ?",
        (TaskStatus.WAITING.value,),
    )
    waiting_count = cursor.fetchone()["count"]

    connection.close()

    return {
        "running": running_count,
        "waiting": waiting_count,
    }

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
            task.name,
            TaskStatus.WAITING.value,
            json.dumps(task.dependencies),
            0,
            task.max_retries,
            task.failure_chance,
            None,
        ),
    )

    connection.commit()
    connection.close()

    return TaskResponse(
        id=task_id,
        name=task.name,
        status=TaskStatus.WAITING,
        dependencies=task.dependencies,
        attempts=0,
        max_retries=task.max_retries,
        error=None,
    )


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: str):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,),
    )

    row = cursor.fetchone()
    connection.close()

    if row is None:
        return {"error": "Task not found"}

    return TaskResponse(
        id=row["id"],
        name=row["name"],
        status=TaskStatus(row["status"]),
        dependencies=json.loads(row["dependencies"]),
        attempts=row["attempts"],
        max_retries=row["max_retries"],
        error=row["error"],
    )



@app.post("/tasks/{task_id}/cancel", response_model=TaskResponse)
def cancel_task(task_id: str):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,),
    )

    row = cursor.fetchone()

    if row is None:
        connection.close()
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    if row["status"] in [
        TaskStatus.SUCCEEDED.value,
        TaskStatus.FAILED.value,
        TaskStatus.BLOCKED.value,
        TaskStatus.CANCELLED.value,
    ]:
        connection.close()
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel task in status {row['status']}"
        )

    cursor.execute(
        """
        UPDATE tasks
        SET status = ?, error = ?
        WHERE id = ?
        """,
        (
            TaskStatus.CANCELLED.value,
            "Task cancelled by user",
            task_id,
        ),
    )

    connection.commit()

    cursor.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,),
    )

    updated_row = cursor.fetchone()
    connection.close()

    return TaskResponse(
        id=updated_row["id"],
        name=updated_row["name"],
        status=TaskStatus(updated_row["status"]),
        dependencies=json.loads(updated_row["dependencies"]),
        attempts=updated_row["attempts"],
        max_retries=updated_row["max_retries"],
        error=updated_row["error"],
    )



@app.get("/stats")
def get_stats():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT COUNT(*) AS count FROM tasks WHERE status = ?",
        (TaskStatus.RUNNING.value,),
    )
    running_count = cursor.fetchone()["count"]

    cursor.execute(
        "SELECT COUNT(*) AS count FROM tasks WHERE status = ?",
        (TaskStatus.WAITING.value,),
    )
    waiting_count = cursor.fetchone()["count"]

    connection.close()

    return {
        "running": running_count,
        "waiting": waiting_count,
    }