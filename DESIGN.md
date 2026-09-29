# Design

## Overview

This project is a small task runner service built with FastAPI and SQLite.

A task can:
- run independently
- depend on other tasks
- retry after failure
- be cancelled
- become blocked if a dependency fails

The scheduler runs in the background and picks up tasks that are ready to execute.

## Main Components

### FastAPI API Layer

`app/main.py` contains the HTTP endpoints used to create tasks, get task status, cancel tasks, and view scheduler statistics.

Main endpoints:

- `POST /tasks`
- `GET /tasks/{task_id}`
- `POST /tasks/{task_id}/cancel`
- `GET /stats`

### SQLite Persistence

`app/database.py` manages the SQLite database.

Task state is persisted so tasks are not lost when the service restarts.

The database stores:

- task id
- name
- status
- dependencies
- retry information
- failure chance
- error message
- timestamps

### Scheduler

`app/scheduler.py` contains the background scheduler.

The scheduler:

1. Finds tasks in `waiting` state.
2. Checks dependency status.
3. Blocks tasks whose dependencies failed.
4. Starts tasks only when all dependencies succeeded.
5. Limits concurrent execution.
6. Handles retries.
7. Updates task state after execution.

### Dependency Validation

`app/dependencies.py` validates task dependencies.

It checks that referenced tasks exist and contains cycle detection logic to reject circular dependency graphs.

## Task States

The service uses the following states:

- `waiting`
- `running`
- `succeeded`
- `failed`
- `blocked`
- `cancelled`

A normal task typically follows:

`waiting -> running -> succeeded`

A failing task may follow:

`waiting -> running -> waiting -> running -> failed`

A task with a failed dependency becomes:

`waiting -> blocked`

A cancelled task becomes:

`waiting/running -> cancelled`

## Retry Behaviour

Each task has a configurable `max_retries`.

The total number of attempts is:

`max_retries + 1`

After a failed attempt, the task returns to `waiting` and waits before retrying.

The retry delay increases with the attempt number.

## Concurrency

The scheduler uses a configurable concurrency limit.

The environment variable is:

`MAX_CONCURRENT_TASKS`

If it is not provided, the default value is `2`.

## Restart Behaviour

If the service stops while a task is in `running` state, the task would otherwise remain stuck.

During application startup, tasks left in `running` state are moved back to `waiting`.

This allows the scheduler to recover them after restart.

## Cancellation

Tasks can be cancelled through:

`POST /tasks/{task_id}/cancel`

Completed, failed, blocked, or already-cancelled tasks cannot be cancelled again.

## Statistics

`GET /stats` returns the current number of:

- running tasks
- waiting tasks

## Additional Improvement

Timestamps were added as an additional operational improvement:

- `created_at`
- `started_at`
- `completed_at`

These make it easier to understand task lifecycle and execution timing.