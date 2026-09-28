# Task Runner Service

A small task execution service built with FastAPI and SQLite.

The service allows users to create tasks, define dependencies between tasks, retry failed tasks, cancel tasks, and query task status.

## Features

- Create tasks through a REST API
- Store tasks in SQLite
- Support task dependencies
- Retry failed tasks
- Block tasks when a dependency fails
- Limit the number of concurrently running tasks
- Cancel waiting tasks
- Query task status
- Simulate task success/failure using `failure_chance`
- Automated tests using Pytest

## Tech Stack

- Python
- FastAPI
- SQLite
- Pydantic
- Pytest
- Uvicorn

## Project Structure

```text
task-runner-assessment/
│
├── app/
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   ├── dependencies.py
│   └── scheduler.py
│
├── tests/
│   └── test_api.py
│
├── requirements.txt
├── README.md
└── .gitignore # Task Runner Service

A small task execution service built with FastAPI and SQLite.

The service allows users to create tasks, define dependencies between tasks, retry failed tasks, cancel tasks, and query task status.

## Features

- Create tasks through a REST API
- Store tasks in SQLite
- Support task dependencies
- Retry failed tasks
- Block tasks when a dependency fails
- Limit the number of concurrently running tasks
- Cancel waiting tasks
- Query task status
- Simulate task success/failure using `failure_chance`
- Automated tests using Pytest

## Tech Stack

- Python
- FastAPI
- SQLite
- Pydantic
- Pytest
- Uvicorn

## Project Structure

```text
task-runner-assessment/
│
├── app/
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   ├── dependencies.py
│   └── scheduler.py
│
├── tests/
│   └── test_api.py
│
├── requirements.txt
├── README.md
└── .gitignore

Task Lifecycle
A task can move through the following states:
waiting
running
succeeded
failed
blocked
cancelled

Typical flow:
waiting -> running -> succeeded

If execution fails:
waiting -> running -> waiting -> running -> failed

The task is placed back into waiting while it waits for another retry.
If one of its dependencies fails:
waiting -> blocked

If a waiting task is cancelled:
waiting -> cancelled

Task Dependencies
A task may depend on one or more previously created tasks.
A dependent task will not run until all of its dependencies have succeeded.
Example:
Task A
  |
  v
Task B

Task B remains in the waiting state until Task A succeeds.
If Task A fails, Task B becomes blocked.
Unknown dependency IDs are rejected when the task is created.
Retry Behaviour
Each task accepts a max_retries value.
The total number of execution attempts is:
1 initial attempt + max_retries

For example:
max_retries = 2

allows up to three attempts.
Retries use a small increasing delay:
Attempt 1 fails -> wait 2 seconds
Attempt 2 fails -> wait 4 seconds
Attempt 3 fails -> task becomes failed

Failure Simulation
The failure_chance field is used to simulate execution failures.
Examples:
0.0 = always succeeds
1.0 = always fails
0.5 = approximately 50% chance of failure

This makes it possible to test retry and failure behaviour without requiring a real external job.
Concurrency
The scheduler limits the number of simultaneously running tasks.
Currently:
MAX_CONCURRENT_TASKS = 2

Additional tasks remain in the waiting state until a running slot becomes available.
Cancellation
A task may be cancelled using:
POST /tasks/{task_id}/cancel

Cancellation is allowed only when the task is in a cancellable state.
Completed tasks such as succeeded, failed, or blocked are not cancelled.
API Endpoints
Create a task
POST /tasks

Example request:
{
  "name": "generate_report",
  "dependencies": [],
  "max_retries": 2,
  "failure_chance": 0.0
}

Get a task
GET /tasks/{task_id}

Cancel a task
POST /tasks/{task_id}/cancel

Running the Project
Create and activate a virtual environment.
On Windows:
python -m venv venv
venv\Scripts\activate

Install dependencies:
pip install -r requirements.txt

Start the API:
uvicorn app.main:app --reload

Open Swagger UI:
http://127.0.0.1:8000/docs

Running Tests
Run:
python -m pytest

The test suite covers the main task-runner behaviour, including task creation, dependencies, cancellation, and retry handling.
Design Decisions
SQLite
SQLite was chosen because this is a small take-home service and does not require external database setup.
Background Scheduler
A lightweight scheduler thread periodically checks waiting tasks and starts eligible tasks.
This keeps the implementation simple while still demonstrating:
- dependency handling
- retries
- task state transitions
- concurrency control
Thread-Based Execution
Tasks are executed using background threads.
For a larger production system, I would consider a dedicated queue and worker system such as Celery, RQ, or a message broker.
Simulated Work
Task execution currently uses a short delay and configurable failure probability.
This keeps the service focused on orchestration rather than implementing a specific business workload.
Assumptions
- Dependencies must already exist when a task is created.
- A task runs only after all dependencies succeed.
- Failed dependencies block dependent tasks.
- Tasks are persisted in SQLite.
- The scheduler starts automatically with the FastAPI application.
- This project is intended as a small local service rather than a distributed production scheduler.
Possible Improvements
With more time, I would consider adding:
- cycle detection for task dependencies
- timestamps for task creation/start/completion
- structured logging
- pagination/list-task endpoint
- database migrations
- FastAPI lifespan events instead of deprecated startup events
- more deterministic scheduler tests
- Docker support
- distributed workers
- authentication and authorization
- configurable retry/backoff policies