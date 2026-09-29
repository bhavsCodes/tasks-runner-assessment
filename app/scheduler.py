import json
import random
import threading
import time
import os

from app.database import get_connection
from app.models import TaskStatus

from datetime import datetime,timezone


MAX_CONCURRENT_TASKS = int(
    os.getenv("MAX_CONCURRENT_TASKS", "2")
)

_running_tasks = 0
_lock = threading.Lock()


def get_waiting_tasks():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM tasks
        WHERE status = ?
        ORDER BY rowid
        """,
        (TaskStatus.WAITING.value,),
    )

    rows = cursor.fetchall()
    connection.close()

    return rows


def dependencies_succeeded(dependency_ids):
    if not dependency_ids:
        return True

    connection = get_connection()
    cursor = connection.cursor()

    for dependency_id in dependency_ids:
        cursor.execute(
            "SELECT status FROM tasks WHERE id = ?",
            (dependency_id,),
        )

        row = cursor.fetchone()

        if row is None or row["status"] != TaskStatus.SUCCEEDED.value:
            connection.close()
            return False

    connection.close()
    return True


def has_failed_dependency(dependency_ids):
    if not dependency_ids:
        return False

    connection = get_connection()
    cursor = connection.cursor()

    for dependency_id in dependency_ids:
        cursor.execute(
            "SELECT status FROM tasks WHERE id = ?",
            (dependency_id,),
        )

        row = cursor.fetchone()

        if row and row["status"] == TaskStatus.FAILED.value:
            connection.close()
            return True

    connection.close()
    return False

def update_task_status(task_id, status, error=None):
    connection = get_connection()
    cursor = connection.cursor()

    completed_at = None

    if status in [
        TaskStatus.SUCCEEDED.value,
        TaskStatus.FAILED.value,
        TaskStatus.BLOCKED.value,
        TaskStatus.CANCELLED.value,
    ]:
        completed_at = datetime.now(timezone.utc).isoformat()

    cursor.execute(
        """
        UPDATE tasks
        SET status = ?, error = ?, completed_at = ?
        WHERE id = ?
        """,
        (
            status,
            error,
            completed_at,
            task_id,
        ),
    )

    connection.commit()
    connection.close()

def is_task_cancelled(task_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT status FROM tasks WHERE id = ?",
        (task_id,),
    )

    row = cursor.fetchone()
    connection.close()

    return (
        row is not None
        and row["status"] == TaskStatus.CANCELLED.value
    )


def execute_task(task):
    global _running_tasks

    try:
        max_attempts = task["max_retries"] + 1

        for attempt_number in range(1, max_attempts + 1):
            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE tasks
                SET status = ?, attempts = ?, error = ?,started_at = ?
                WHERE id = ?
                """,
                (
                    TaskStatus.RUNNING.value,
                    attempt_number,
                    None,
                    datetime.now(timezone.utc).isoformat(),
                    task["id"],
                ),
            )

            connection.commit()
            connection.close()

            time.sleep(random.uniform(1,3))

            if is_task_cancelled(task["id"]):
                return

            if random.random() >= task["failure_chance"]:
                update_task_status(
                    task["id"],
                    TaskStatus.SUCCEEDED.value,
                )
                return

            if attempt_number < max_attempts:
                delay = attempt_number * 2

                update_task_status(
                    task["id"],
                    TaskStatus.RUNNING.value,
                    f"Attempt {attempt_number} failed. Retrying in {delay} seconds.",
                )

                time.sleep(delay)

            else:
                update_task_status(
                    task["id"],
                    TaskStatus.FAILED.value,
                    "Task failed after all retry attempts",
                )

    finally:
        with _lock:
            _running_tasks -= 1


def scheduler_loop():
    global _running_tasks

    while True:
        waiting_tasks = get_waiting_tasks()

        for task in waiting_tasks:
            with _lock:
                if _running_tasks >= MAX_CONCURRENT_TASKS:
                    break

            dependencies = json.loads(task["dependencies"])

            if has_failed_dependency(dependencies):
                update_task_status(
                    task["id"],
                    TaskStatus.BLOCKED.value,
                    "Blocked because a dependency failed",
                )
                continue

            if not dependencies_succeeded(dependencies):
                continue

            with _lock:
                _running_tasks += 1

            thread = threading.Thread(
                target=execute_task,
                args=(task,),
                daemon=True,
            )
            thread.start()

        time.sleep(1)




def start_scheduler():
    thread = threading.Thread(
        target=scheduler_loop,
        daemon=True,
    )
    thread.start()