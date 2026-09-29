# Task Runner Service

A small task execution service built with FastAPI and SQLite.

The service allows users to create tasks, define dependencies between tasks, retry failed tasks, cancel tasks, query task status, and view basic scheduler statistics.

## Features

- Create tasks through a REST API
- Store task state in SQLite
- Support task dependencies
- Reject unknown dependencies
- Detect circular dependencies
- Retry failed tasks with increasing delay
- Block tasks when a dependency fails or is cancelled
- Limit the number of concurrently running tasks
- Configure concurrency using an environment variable
- Cancel tasks
- Query task status and attempt count
- View running and waiting task counts
- Recover interrupted running tasks after restart
- Simulate task execution using random duration and configurable `failure_chance`
- Track task lifecycle using `created_at`, `started_at`, and `completed_at`
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
├── DESIGN.md
├── TRADEOFFS.md
├── requirements.txt
├── README.md
└── .gitignore

Real-World Scenario
This project uses a document-processing pipeline as an example scenario.
A task flow could be:
validate_document
        |
        v
extract_text
        |
        v
generate_summary
        |
        v
store_results

A dependent task runs only after all of its required dependencies have succeeded.
The actual task work is simulated using a random sleep duration and a configurable chance of failure.
Task Lifecycle
A task can move through the following states:
- waiting
- running
- succeeded
- failed
- blocked
- cancelled
Typical successful flow:
waiting -> running -> succeeded

A task that requires retries may run multiple times before succeeding or failing permanently.
A permanently failing task ends as:
failed

If a dependency fails or is cancelled:
waiting -> blocked

If a task is cancelled:
waiting/running -> cancelled

Task Dependencies
A task may depend on one or more previously created tasks.
A dependent task does not run until every dependency has succeeded.
Example:
Task A
  |
  v
Task B

Task B remains in the waiting state until Task A succeeds.
If Task A fails permanently or is cancelled, Task B becomes blocked.
Unknown dependency IDs are rejected when a task is submitted.
Circular dependencies are also detected and rejected.
Retry Behaviour
Each task accepts a max_retries value.
The total number of execution attempts is:
1 initial attempt + max_retries

For example:
max_retries = 2

allows up to three execution attempts.
Retry delays increase with the attempt number.
Example:
Attempt 1 fails -> wait 2 seconds
Attempt 2 fails -> wait 4 seconds
Attempt 3 fails -> task becomes failed

Failure Simulation
The failure_chance field controls simulated execution failure.
Examples:
0.0 = always succeeds
1.0 = always fails
0.5 = approximately 50% chance of failure

Task execution also sleeps for a random duration between 1 and 3 seconds.
This keeps the project focused on orchestration rather than implementing real business work.
Concurrency
The maximum number of simultaneously running tasks is configurable using the environment variable:
MAX_CONCURRENT_TASKS

If it is not provided, the default value is:
2

Example on Windows PowerShell:
$env:MAX_CONCURRENT_TASKS="4"
uvicorn app.main:app --reload

Additional tasks remain in the waiting state until a running slot becomes available.
Cancellation
A task can be cancelled using:
POST /tasks/{task_id}/cancel

Tasks that are already completed, failed, blocked, or cancelled are not cancelled again.
If another task depends on a cancelled task, the dependent task becomes blocked.
This prevents dependent tasks from remaining in the waiting state forever when a required prerequisite can no longer succeed.
Restart Recovery
Task state is persisted in SQLite.
If the service stops while a task is in the running state, the in-memory worker is lost.
When the service starts again, tasks that were left as running are moved back to waiting.
The scheduler can then execute them again.
This provides automatic recovery, although duplicate execution is possible in some crash scenarios.
More detail is available in DESIGN.md.
Statistics
The service provides:
GET /stats

This returns the number of:
- running tasks
- waiting tasks
API Endpoints
Create a task
POST /tasks

Example request:
{
  "name": "extract_text",
  "dependencies": [],
  "max_retries": 2,
  "failure_chance": 0.2
}

Create a dependent task
{
  "name": "generate_summary",
  "dependencies": [
    "TASK_ID_HERE"
  ],
  "max_retries": 2,
  "failure_chance": 0.1
}

Get task status
GET /tasks/{task_id}

Cancel a task
POST /tasks/{task_id}/cancel

Get scheduler statistics
GET /stats

Running the Project
Clone the repository:
git clone https://github.com/bhavsCodes/tasks-runner-assessment.git
cd tasks-runner-assessment

Create a virtual environment:
python -m venv venv

Activate it on Windows:
venv\Scripts\activate

Install dependencies:
pip install -r requirements.txt

Start the FastAPI application:
uvicorn app.main:app --reload

Open Swagger UI in your browser:
http://127.0.0.1:8000/docs

Running Tests
Run:
python -m pytest

The test suite covers important task-runner behaviour including:
- task creation
- task status
- dependency handling
- circular dependency detection
- retry behaviour
- failed dependency handling
- cancelled dependency handling
- cancellation
- restart recovery
Design Decisions
SQLite
SQLite was chosen because this is a small take-home project and it does not require separate database setup.
It also provides persistence across application restarts.
Background Scheduler
A lightweight scheduler thread periodically checks waiting tasks and starts eligible tasks.
This keeps the implementation simple while demonstrating:
- dependency handling
- retries
- state transitions
- concurrency control
Thread-Based Execution
Tasks are executed using Python background threads.
For a larger production system, a dedicated distributed worker system such as Celery, RQ, or a message queue could be considered.
Simulated Work
Task execution uses:
- random duration between 1 and 3 seconds
- configurable failure probability
This keeps the focus on task orchestration.
Additional Improvement
Task lifecycle timestamps were added:
- created_at
- started_at
- completed_at
These fields make it easier to understand when tasks are created, started, and completed.
Assumptions
- Dependencies must already exist when a task is submitted.
- A task runs only after all dependencies succeed.
- Failed or cancelled dependencies block dependent tasks.
- Tasks are persisted in SQLite.
- The scheduler starts automatically with the FastAPI application.
- The scheduler uses first-submitted-first-considered ordering.
- The project is designed as a small local service rather than a distributed production scheduler.
Documentation
See:
- DESIGN.md for architecture, scenario, restart behaviour, scheduling decisions, and required design questions
- TRADEOFFS.md for implementation tradeoffs
Possible Future Improvements
With more time, I would consider adding:
- structured logging
- pagination and a list-tasks endpoint
- a formal database migration tool
- FastAPI lifespan events instead of deprecated startup events
- Docker support
- distributed workers
- authentication and authorization
- configurable retry/backoff strategies with jitter
- task priorities

After pasting it:

```text
Ctrl + S

Then run:
python -m pytest

You should still get:
12 passed