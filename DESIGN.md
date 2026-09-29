# Design

## Overview

This project is a small task runner service built using FastAPI and SQLite.

Tasks can:

- run independently
- depend on other tasks
- retry after failure
- be cancelled
- become blocked when a required dependency fails or is cancelled
- survive application restarts through database persistence

The scheduler runs in the background and starts tasks when they are ready.

---

## Real-World Scenario

I chose a document-processing pipeline as the example scenario.

For example, when a document is uploaded, the system could create tasks such as:

1. `validate_document`
2. `extract_text`
3. `generate_summary`
4. `store_results`

The dependency flow could look like:

`validate_document -> extract_text -> generate_summary -> store_results`

`extract_text` must not run until `validate_document` succeeds.

Similarly, `generate_summary` must wait for `extract_text`.

For this assessment, the real work is simulated instead of actually processing documents.

Each task:

- sleeps for a random duration between 1 and 3 seconds
- has a configurable `failure_chance`

This keeps the focus on scheduling and task management.

---

## Main Components

### API

`app/main.py`

The FastAPI application provides endpoints for:

- submitting tasks
- checking task status
- cancelling tasks
- viewing scheduler statistics

Main endpoints:

- `POST /tasks`
- `GET /tasks/{task_id}`
- `POST /tasks/{task_id}/cancel`
- `GET /stats`

---

## Persistence

`app/database.py`

SQLite is used to persist tasks.

The database stores information including:

- task id
- task name
- status
- dependencies
- attempts
- maximum retries
- failure chance
- error information
- created timestamp
- started timestamp
- completed timestamp

Because task state is stored in SQLite, completed work is not forgotten when the application restarts.

---

## Task States

The service supports:

- `waiting`
- `running`
- `succeeded`
- `failed`
- `blocked`
- `cancelled`

A successful task normally follows:

`waiting -> running -> succeeded`

A task that needs a retry may follow:

`waiting -> running -> running -> succeeded`

A permanently failing task ends in:

`failed`

A task whose dependency fails or is cancelled becomes:

`blocked`

---

## Dependencies

A task runs only when all of its dependencies have succeeded.

Before starting a waiting task, the scheduler checks its dependency statuses.

If a dependency is still waiting or running, the task remains waiting.

If a dependency permanently fails or is cancelled, the dependent task becomes blocked.

Circular dependencies are checked using graph traversal logic in:

`app/dependencies.py`

A cycle is rejected rather than allowing tasks to wait forever.

---

## Retry Behaviour

Each task has a configurable `max_retries`.

The maximum number of attempts is:

`max_retries + 1`

When an attempt fails and retries remain, the service waits before trying again.

The delay increases with the attempt number.

For example:

- after attempt 1: 2-second delay
- after attempt 2: 4-second delay

If all attempts fail, the task is marked `failed`.

---

## Concurrency

The maximum number of tasks that may run at once is configurable using:

`MAX_CONCURRENT_TASKS`

For example:

```text
MAX_CONCURRENT_TASKS=4