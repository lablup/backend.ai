import enum
import uuid
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema


class BgtaskStatus(enum.StrEnum):
    STARTED = "bgtask_started"
    UPDATED = "bgtask_updated"
    DONE = "bgtask_done"
    CANCELLED = "bgtask_cancelled"
    FAILED = "bgtask_failed"
    PARTIAL_SUCCESS = "bgtask_partial_success"

    def finished(self) -> bool:
        return self in {self.DONE, self.CANCELLED, self.FAILED, self.PARTIAL_SUCCESS}


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

    @classmethod
    def all_types(cls) -> set["ServerType"]:
        return {type_ for type_ in cls}


@dataclass
class ServerComponentID:
    server_id: str
    server_type: ServerType


class BackgroundTaskMetadata(BaseModel):
    task_id: TaskID
    task_name: str
    body: Mapping[str, Any]
    server_id: str
    server_types: Collection[ServerType]

    @classmethod
    def create(
        cls,
        task_id: uuid.UUID,
        task_name: str,
        body: Mapping[str, Any],
        server_id: ServerComponentID,
        allow_any_server: bool = False,
    ) -> "BackgroundTaskMetadata":
        server_types = ServerType.all_types() if allow_any_server else {server_id.server_type}
        return cls(
            task_id=TaskID(task_id),
            task_name=task_name,
            body=body,
            server_id=server_id.server_id,
            server_types=server_types,
        )

    def to_json(self) -> str:
        data = self.model_dump_json()
        return data

    @classmethod
    def from_json(cls, data: str | bytes) -> "BackgroundTaskMetadata":
        """Create from Redis hash data"""
        return cls.model_validate_json(data)


@dataclass
class BackgroundTaskMetadataTTL:
    metadata: BackgroundTaskMetadata
    ttl_seconds: int
