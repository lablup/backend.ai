from __future__ import annotations

import enum
import uuid
from collections.abc import Mapping
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
    UNKNOWN = "bgtask_unknown"

    def finished(self) -> bool:
        return self in {self.DONE, self.CANCELLED, self.FAILED, self.PARTIAL_SUCCESS}


class TaskName(enum.StrEnum):
    CLONE_VFOLDER = "clone_vfolder"
    DELETE_VFOLDER = "delete_vfolder"

    PUSH_IMAGE = "push_image"


BgTaskKey = NewType("BgTaskKey", str)

TaskID = NewType("TaskID", uuid.UUID)


class TaskType(enum.StrEnum):
    SINGLE = "single"
    MULTI = "multi"


class BackgroundTaskMetadata(BaseModel):
    task_id: TaskID
    task_name: TaskName
    body: Mapping[str, Any]

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


class TaskStatusInfo(BaseModel):
    """
    Status information for a background task.
    """

    task_id: TaskID = Field(description="Unique identifier for the task")
    task_type: TaskType = Field(description="Type of the task: single or multi")
    pending_count: int = Field(default=0, description="Number of pending sub-tasks")
    success_count: int = Field(default=0, description="Number of successful sub-tasks")
    failure_count: int = Field(default=0, description="Number of failed sub-tasks")
    status: BgtaskStatus = Field(description="Current status of the task")


class TaskKeyStatusInfo(BaseModel):
    """
    Status information for a specific task key.
    """

    task_id: TaskID = Field(description="Unique identifier for the task")
    key: BgTaskKey = Field(description="Key representing the task or sub-task")
    status: BgtaskStatus = Field(description="Current status of the task")
    last_message: Optional[str] = Field(
        default=None, description="Last message or error associated with the task"
    )
