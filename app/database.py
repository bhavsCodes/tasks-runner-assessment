import sqlite3
from pathlib import Path


DB_PATH = Path("tasks.db")


def get_connection():
    connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            dependencies TEXT NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            max_retries INTEGER NOT NULL DEFAULT 2,
            failure_chance REAL NOT NULL DEFAULT 0.0,
            error TEXT,
            create_at TEXT,
            started_at TEXT,
            completed_at TEXT
        )
        """
    )


    cursor.execute("PRAGMA table_info(tasks)")

    existing_columns = {
        row["name"] for row in cursor.fetchall()
    }

    if "created_at" not in existing_columns:
        cursor.execute(
            "ALTER TABLE tasks ADD COLUMN created_at TEXT"
        )

    if "started_at" not in existing_columns:
        cursor.execute(
            "ALTER TABLE tasks ADD COLUMN started_at TEXT"
        )

    if "completed_at" not in existing_columns:
        cursor.execute(
            "ALTER TABLE tasks ADD COLUMN completed_at TEXT"
        )


    
    connection.commit()
    connection.close()