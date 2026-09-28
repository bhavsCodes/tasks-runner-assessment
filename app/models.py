from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    WAITING = "waiting"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskCreate(BaseModel):
    name: str
    dependencies: List[str] = Field(default_factory=list)
    max_retries: int = 2
    failure_chance: float = 0.0


class TaskResponse(BaseModel):
    id: str
    name: str
    status: TaskStatus
    dependencies: List[str]
    attempts: int
    max_retries: int
    error: Optional[str] = None