import json
import uuid

from fastapi import FastAPI, HTTPException

from app.database import get_connection, initialize_database
from app.dependencies import validate_dependencies
from app.models import TaskCreate, TaskResponse, TaskStatus


app = FastAPI(title="Task Runner Service")


@app.on_event("startup")
def startup_event():
    initialize_database()


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