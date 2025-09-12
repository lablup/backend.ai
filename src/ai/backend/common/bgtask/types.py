import enum
import uuid
from collections.abc import Iterable, Mapping
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


class BackgroundTaskMetadata(BaseModel):
    task_id: TaskID
    task_name: TaskName
    body: Mapping[str, Any]
    server_id: str = Field(description="Server ID where the task is running")
    tags: set[str] = Field(default_factory=set, description="Optional tags to group tasks")

    @classmethod
    def create(
        cls,
        task_id: TaskID,
        task_name: TaskName,
        body: Mapping[str, Any],
        server_id: str,
        tags: Optional[Iterable[str]] = None,
    ) -> Self:
        return cls(
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
