import enum
import uuid
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, NewType, Optional, Self

from pydantic import BaseModel, Field
from pydantic_core import ValidationError

from .exception import InvalidTaskMetadataError


class BgtaskStatus(enum.StrEnum):
    STARTED = "bgtask_started"
    UPDATED = "bgtask_updated"
    DONE = "bgtask_done"
    CANCELLED = "bgtask_cancelled"
    FAILED = "bgtask_failed"
    PARTIAL_SUCCESS = "bgtask_partial_success"

    def finished(self) -> bool:
        return self in {self.DONE, self.CANCELLED, self.FAILED, self.PARTIAL_SUCCESS}


class TaskName(enum.StrEnum):
    CLONE_VFOLDER = "clone_vfolder"
    DELETE_VFOLDER = "delete_vfolder"

    PUSH_IMAGE = "push_image"


TaskID = NewType("TaskID", uuid.UUID)


@dataclass
class TaskDetailIdentifier(BaseModel):
    task_id: TaskID
    task_key: str

    def to_storage_key(self) -> str:
        """Convert to storage key format for Redis sets."""
        return f"{self.task_id.hex}:{self.task_key}"

    @classmethod
    def from_storage_key(cls, storage_key: str) -> Self:
        """Create TaskDetailIdentifier from storage key format."""
        if ":" in storage_key:
            task_id_hex, task_key = storage_key.split(":", 1)
            task_id = TaskID(uuid.UUID(hex=task_id_hex))
            return cls(task_id=task_id, task_key=task_key)
        else:
            # Fallback for old format (task_id only)
            task_id = TaskID(uuid.UUID(hex=storage_key))
            return cls(task_id=task_id, task_key="")


class BackgroundTaskStatusMetadata(BaseModel):
    success_count: int = Field(0, description="Number of successfully completed tasks")
    failure_count: int = Field(0, description="Number of failed tasks")
    pending_count: int = Field(0, description="Number of pending tasks")

    keys: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of keys to identify tasks within the batch",
    )
    created_at: str = Field(
        description="Timestamp when the batch task was created",
    )

    def to_json(self) -> str:
        data = self.model_dump_json()
        return data


class BackgroundTaskDetailMetadata(BaseModel):
    task_key: str
    task_id: TaskID
    task_name: TaskName
    body: Mapping[str, Any]
    server_id: str = Field(description="Server ID where the task is running")
    tags: set[str] = Field(default_factory=set, description="Optional tags to group tasks")

    @classmethod
    def create(
        cls,
        task_key: str,
        task_id: TaskID,
        task_name: TaskName,
        body: Mapping[str, Any],
        server_id: str,
        tags: Optional[Iterable[str]] = None,
    ) -> Self:
        return cls(
            task_key=task_key,
            task_id=task_id,
            task_name=task_name,
            body=body,
            server_id=server_id,
            tags=set(tags) if tags is not None else set(),
        )

    def to_json(self) -> str:
        data = self.model_dump_json()
        return data

    @classmethod
    def from_json(cls, data: str | bytes) -> Self:
        """Create from Redis hash data"""
        try:
            return cls.model_validate_json(data)
        except ValidationError as e:
            raise InvalidTaskMetadataError from e

    @property
    def task_detail_identifier(self) -> TaskDetailIdentifier:
        return TaskDetailIdentifier(task_id=self.task_id, task_key=self.task_key)
