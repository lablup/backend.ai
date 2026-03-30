from __future__ import annotations

import enum
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, NewType, Protocol, Self

from pydantic import BaseModel, Field
from pydantic_core import ValidationError

from ai.backend.common.json import dump_json, load_json

from .exception import InvalidTaskMetadataError


class BgtaskStatus(enum.StrEnum):
    STARTED = "bgtask_started"
    UPDATED = "bgtask_updated"
    DONE = "bgtask_done"
    CANCELLED = "bgtask_cancelled"
    FAILED = "bgtask_failed"
    PARTIAL_SUCCESS = "bgtask_partial_success"
    UNKNOWN = "bgtask_unknown"

    def finished(self) -> bool:
        return self in {self.DONE, self.CANCELLED, self.FAILED, self.PARTIAL_SUCCESS}


class BgtaskNameBase(Protocol):
    """
    Protocol for background task names.

    Each component (storage, manager, agent) should define its own
    background task name enum inheriting from StrEnum and implementing this protocol.
    """

    @property
    def value(self) -> str:
        """Return the string value of the background task name."""
        ...

    @classmethod
    def from_str(cls, value: str) -> Self:
        """Create instance from string value."""
        ...


BgTaskKey = NewType("BgTaskKey", str)

# Special key for single tasks without subtasks (represents the entire task)
WHOLE_TASK_KEY: BgTaskKey = BgTaskKey("__whole__")

TaskID = NewType("TaskID", uuid.UUID)


class TaskType(enum.StrEnum):
    SINGLE = "single"
    BATCH = "batch"
    PARALLEL = "parallel"


@dataclass
class TaskInfo:
    """
    Information about a background task.
    """

    task_id: TaskID
    task_name: str
    task_type: TaskType
    body: Mapping[str, Any]
    ongoing_count: int
    success_count: int = 0
    failure_count: int = 0

    def to_valkey_hash_fields(self) -> dict[str | bytes, str | bytes]:
        body = dump_json(self.body)
        return {
            b"task_id": str(self.task_id),
            b"task_name": self.task_name,
            b"task_type": self.task_type,
            b"body": body,
            b"ongoing_count": str(self.ongoing_count),
            b"success_count": str(self.success_count),
            b"failure_count": str(self.failure_count),
        }

    @classmethod
    def from_valkey_hash_fields(cls, data: dict[bytes, bytes]) -> Self:
        try:
            body = load_json(data[b"body"])
            return cls(
                task_id=TaskID(uuid.UUID(data[b"task_id"].decode())),
                task_name=data[b"task_name"].decode(),
                task_type=TaskType(data[b"task_type"].decode()),
                body=body,
                ongoing_count=int(data[b"ongoing_count"].decode()),
                success_count=int(data[b"success_count"].decode()),
                failure_count=int(data[b"failure_count"].decode()),
            )
        except (KeyError, ValueError, ValidationError) as e:
            raise InvalidTaskMetadataError from e


class TaskStatus(enum.StrEnum):
    ONGOING = "ongoing"
    SUCCESS = "success"
    FAILURE = "failure"


class TaskSubKeyInfo(BaseModel):
    """
    Status information for a specific task key.
    """

    task_id: TaskID = Field(description="Unique identifier for the task")
    key: BgTaskKey = Field(description="Key representing the task or sub-task")
    status: TaskStatus = Field(description="Current status of the task")
    last_message: str = Field(
        description="Last status message or error message related to the task",
    )

    def to_valkey_hash_fields(self) -> dict[str | bytes, str | bytes]:
        return {
            b"task_id": str(self.task_id),
            b"key": str(self.key),
            b"status": self.status,
            b"last_message": self.last_message,
        }

    @classmethod
    def from_valkey_hash_fields(cls, data: dict[bytes, bytes]) -> Self:
        try:
            return cls(
                task_id=TaskID(uuid.UUID(data[b"task_id"].decode())),
                key=BgTaskKey(data[b"key"].decode()),
                status=TaskStatus(data[b"status"].decode()),
                last_message=data[b"last_message"].decode(),
            )
        except (KeyError, ValueError, ValidationError) as e:
            raise InvalidTaskMetadataError from e


@dataclass
class TaskTotalInfo:
    """
    Comprehensive information about a background task, including its status across multiple keys.
    """

    task_info: TaskInfo
    task_key_list: list[TaskSubKeyInfo]

    def subkeys(self) -> list[str | bytes]:
        return [subkey.key for subkey in self.task_key_list]
