from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass
from typing import Any, Optional

from pydantic import BaseModel

from .defs import (
    DEFAULT_HEARTBEAT_INTERVAL,
    DEFAULT_HEARTBEAT_THRESHOLD,
    DEFAULT_MAX_RETRIES,
)


class ServerType(enum.StrEnum):
    """Server component types that can process background tasks"""

    MANAGER = "manager"
    AGENT = "agent"
    STORAGE_PROXY = "storage-proxy"


@dataclass
class ServerComponentID:
    """Unique identifier for a server component"""

    server_id: str
    server_type: ServerType

    def __str__(self) -> str:
        return f"{self.server_type}:{self.server_id}"

    def __hash__(self) -> int:
        return hash((self.server_id, self.server_type))


class BgtaskStatus(enum.StrEnum):
    STARTED = "bgtask_started"
    UPDATED = "bgtask_updated"
    DONE = "bgtask_done"
    CANCELLED = "bgtask_cancelled"
    FAILED = "bgtask_failed"
    PARTIAL_SUCCESS = "bgtask_partial_success"

    def finished(self) -> bool:
        return self in {self.DONE, self.CANCELLED, self.FAILED, self.PARTIAL_SUCCESS}


class BackgroundTaskMetadata(BaseModel):
    task_id: uuid.UUID
    task_name: str
    body: dict[str, Any]  # Original request data for retry
    created_at: float
    retried_at: Optional[float]
    server_id: str
    server_type: ServerType
    allow_any_server: bool = False  # If True, task can be processed by any server
    retry_count: int = 0
    max_retries: int = DEFAULT_MAX_RETRIES
    checkpoint: Optional[dict[str, Any]] = None  # For resumable tasks
    error_message: Optional[str] = None

    @classmethod
    def create(
        cls,
        task_id: uuid.UUID,
        task_name: str,
        body: dict[str, Any],
        server_id: ServerComponentID,
        allow_any_server: bool = False,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> BackgroundTaskMetadata:
        now = time.time()
        return cls(
            task_id=task_id,
            task_name=task_name,
            body=body,
            created_at=now,
            retried_at=None,
            server_id=server_id.server_id,
            server_type=server_id.server_type,
            allow_any_server=allow_any_server,
            max_retries=max_retries,
        )

    def to_json(self) -> str:
        data = self.model_dump_json()
        return data

    @classmethod
    def from_json(cls, data: str | bytes) -> BackgroundTaskMetadata:
        """Create from Redis hash data"""
        return cls.model_validate_json(data)

    def update_for_retry(self) -> None:
        """Update metadata for retry attempt"""
        self.retry_count += 1
        self.status = BgtaskStatus.STARTED
        self.retried_at = time.time()
        self.error_message = None


@dataclass
class BackgroundTaskRetryArgs:
    body: dict[str, Any]
    allow_any_server: bool = False  # If True, task can be retried by any server
    max_retries: int = DEFAULT_MAX_RETRIES


@dataclass
class BackgroundTaskHeartbeat:
    """Track task liveness"""

    task_id: uuid.UUID
    server_id: str
    last_heartbeat: float
    heartbeat_interval: float = DEFAULT_HEARTBEAT_INTERVAL

    def is_alive(self, threshold: float = DEFAULT_HEARTBEAT_THRESHOLD) -> bool:
        """Check if task is still alive"""
        return (time.time() - self.last_heartbeat) < threshold
