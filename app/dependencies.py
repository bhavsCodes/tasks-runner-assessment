from typing import Dict, List, Set

from app.database import get_connection


def validate_dependencies(dependency_ids: List[str]) -> List[str]:
    """
    Check that every dependency ID already exists in the database.

    Returns a list of dependency IDs that were not found.
    """
    if not dependency_ids:
        return []

    connection = get_connection()
    cursor = connection.cursor()

    missing = []

    for dependency_id in dependency_ids:
        cursor.execute(
            "SELECT id FROM tasks WHERE id = ?",
            (dependency_id,),
        )

        if cursor.fetchone() is None:
            missing.append(dependency_id)

    connection.close()

    return missing


def has_cycle(graph: Dict[str, List[str]]) -> bool:
    """
    Return True if the dependency graph contains a circular dependency.
    """

    visiting: Set[str] = set()
    visited: Set[str] = set()

    def visit(task_id: str) -> bool:
        if task_id in visiting:
            return True

        if task_id in visited:
            return False

        visiting.add(task_id)

        for dependency_id in graph.get(task_id, []):
            if visit(dependency_id):
                return True

        visiting.remove(task_id)
        visited.add(task_id)

        return False

    for task_id in graph:
        if visit(task_id):
            return True

    return False