# Tradeoffs

## SQLite instead of a production database

SQLite was chosen because this is a small take-home service and it keeps setup simple.

Advantages:
- no separate database server is required
- easy to run locally
- supports persistence across restarts

Tradeoff:
- SQLite is not ideal for high concurrency or distributed deployments

For a production system, PostgreSQL or another managed database would be a better choice.

## Background threads instead of a distributed worker system

The scheduler uses Python background threads to execute tasks.

Advantages:
- simple to understand
- no additional infrastructure is required
- suitable for a small local service

Tradeoff:
- tasks only run inside one application process
- this design does not scale across multiple service instances
- a process crash can interrupt running work

For a larger system, a queue and worker system such as Celery, RQ, or a cloud queue service would be more appropriate.

## Polling scheduler

The scheduler checks the database periodically for waiting tasks.

Advantages:
- straightforward implementation
- easy to debug
- works well for this assignment

Tradeoff:
- polling adds unnecessary database queries when there is no work
- tasks may wait briefly until the next polling cycle

A production system could use an event-driven queue instead.

## Retry strategy

Retries use a simple increasing delay based on the attempt number.

Advantages:
- easy to understand
- prevents immediate repeated retries

Tradeoff:
- this is not a full exponential backoff strategy
- there is no jitter

A production system could use exponential backoff with jitter.

## Dependency handling

Task dependencies are stored as JSON inside the task row.

Advantages:
- simple schema
- easy to retrieve with the task

Tradeoff:
- dependency queries are less efficient than using a separate relational table
- more complex dependency graphs would be harder to query directly in SQL

For a larger system, dependencies could be stored in a separate task_dependencies table.

## Restart recovery

Tasks that were running when the service stopped are moved back to waiting during startup.

Advantages:
- prevents tasks from remaining permanently stuck in running state
- simple recovery behaviour

Tradeoff:
- the service cannot know whether the original work actually completed just before the crash
- this can result in a task being executed again

Real production systems would need idempotent task execution or stronger delivery guarantees.

## Cancellation

Cancellation changes the persisted task status.

Tradeoff:
- the current implementation cannot forcibly terminate arbitrary Python work that is already executing
- the worker checks task state and stops when cancellation is detected

For long-running real tasks, cooperative cancellation would need to be built into the task implementation.

## Concurrency

The concurrency limit is configurable using the `MAX_CONCURRENT_TASKS` environment variable.

Tradeoff:
- the limit is only enforced within one process
- multiple application instances would each have their own independent limit

A distributed implementation would require a shared concurrency mechanism.

## Additional improvement

Task lifecycle timestamps were added:

- `created_at`
- `started_at`
- `completed_at`

This makes the service easier to operate and debug with minimal additional complexity.