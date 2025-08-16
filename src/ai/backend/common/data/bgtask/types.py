import enum
import uuid
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from typing import Any, Optional

from pydantic import BaseModel, Field, GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema


class BgTaskProgressData(BaseModel):
    current: int = Field(
        default=0,
        description="Current progress of the scan operation, expressed as a percentage.",
        examples=[0, 50, 100],
    )
    total: int = Field(
        default=0,
        description="Total number of items to be scanned, used to calculate progress.",
        examples=[100, 200, 0],
    )


class TaskID(uuid.UUID):
    """
    TaskID is a UUID subclass used to represent background task IDs.
    It provides a custom string representation for better readability.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def encode(self) -> bytes:
        return self.bytes

    @classmethod
    def from_encoded(cls, data: bytes) -> "TaskID":
        return cls(bytes=data)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls, handler(uuid.UUID))


class ServerType(enum.StrEnum):
    MANAGER = "manager"
    AGENT = "agent"
    STORAGE_PROXY = "storage_proxy"


@dataclass
class ServerComponentID:
    server_id: str
    server_type: ServerType


class BackgroundTaskMetadata(BaseModel):
    task_id: TaskID
    task_name: str
    body: Mapping[str, Any]
    server_id: str = Field(description="Server ID where the task is running")
    server_types: Collection[ServerType] = Field(description="Server types that can run this task")

    @classmethod
    def create(
        cls,
        task_id: uuid.UUID,
        task_name: str,
        body: Mapping[str, Any],
        server_id: ServerComponentID,
        allowed_server_types: Optional[Collection[ServerType]] = None,
    ) -> "BackgroundTaskMetadata":
        server_types = allowed_server_types or set()
        return cls(
            task_id=TaskID(task_id),
            task_name=task_name,
            body=body,
            server_id=server_id.server_id,
            server_types={*server_types, server_id.server_type},
        )

    def to_json(self) -> str:
        data = self.model_dump_json()
        return data

    @classmethod
    def from_json(cls, data: str | bytes) -> "BackgroundTaskMetadata":
        """Create from Redis hash data"""
        return cls.model_validate_json(data)


type TTL_SECOND = int
