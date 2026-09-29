# Tradeoffs

## 1. SQLite instead of PostgreSQL

### Choice

I used SQLite for persistence.

### Alternative

A production database such as PostgreSQL.

### Why I chose SQLite

SQLite keeps the project simple to run locally and does not require a separate database server.

It is enough for a small take-home assignment and still provides persistence across application restarts.

### Why I did not choose PostgreSQL

PostgreSQL would provide better concurrency and production scalability, but it would add installation and setup overhead that is not necessary for this small service.

---

## 2. Background threads instead of a distributed task queue

### Choice

Tasks are executed using Python background threads inside the FastAPI process.

### Alternative

Use a dedicated worker system such as Celery with Redis or another external queue.

### Why I chose background threads

Threads keep the implementation small and easy to understand.

They allow multiple simulated tasks to run concurrently without requiring additional infrastructure.

### Why I did not choose a distributed queue

A system such as Celery would be more scalable and reliable across multiple machines, but it would make the assignment significantly more complex.

The goal of this project is to demonstrate scheduling, dependencies, retries, and failure handling rather than infrastructure setup.

---

## 3. Polling scheduler instead of event-driven scheduling

### Choice

The scheduler periodically reads waiting tasks from SQLite.

### Alternative

Use an event-driven queue where new tasks immediately notify workers.

### Why I chose polling

Polling is straightforward to implement and debug.

For the small number of tasks expected in this assessment, the extra database checks are acceptable.

### Why I did not choose event-driven scheduling

An event-driven system would reduce unnecessary polling and respond more quickly, but it would require additional coordination or messaging infrastructure.

For this project, that complexity was not necessary.

---

## 4. Requeue interrupted tasks after restart instead of failing them

### Choice

If the service restarts while a task is marked as `running`, the task is changed back to `waiting`.

### Alternative

Mark interrupted tasks as permanently `failed`.

### Why I chose to requeue them

A service interruption does not necessarily mean the task itself failed.

Returning the task to `waiting` allows the scheduler to recover automatically and try the work again.

### Why I did not mark them failed

Marking every interrupted task as failed would require manual recovery even when the task could safely be retried.

The downside of requeueing is that duplicate work is possible if the task completed externally just before the crash.

In a production system, task operations should therefore be idempotent or use stronger delivery guarantees.