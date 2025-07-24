import enum
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from ai.backend.common.exception import ErrorCode
from ai.backend.manager.data.permission.id import ScopeId


class OperationStatus(enum.StrEnum):
    SUCCESS = "success"
    ERROR = "error"
    UNKNOWN = "unknown"
    RUNNING = "running"


@dataclass
class ActionSpec:
    entity_type: str
    operation_type: str

    def type(self) -> str:
        return f"{self.entity_type}:{self.operation_type}"


class AbstractProcessorPackage(ABC):
    @abstractmethod
    def supported_actions(self) -> list[ActionSpec]:
        """Get the list of action specs that this processors can handle."""
        raise NotImplementedError


class MultiEntityFailureHandlingPolicy(enum.StrEnum):
    ALL_OR_NONE = "all_or_none"
    PARTIAL_SUCCESS = "partial_success"


@dataclass
class ActionTriggerMeta:
    action_id: uuid.UUID
    started_at: datetime


@dataclass
class ActionResultTargetMeta:
    entity_type: str
    entity_ids: Optional[list[str]] = None
    scope: Optional[ScopeId] = None

    @property
    def entity_id(self) -> Optional[str]:
        """Return the first entity ID if available, otherwise None."""
        return self.entity_ids[0] if self.entity_ids else None


@dataclass
class ActionResultMeta:
    action_id: uuid.UUID
    target: ActionResultTargetMeta
    status: OperationStatus
    description: str
    started_at: datetime
    ended_at: datetime
    duration: timedelta
    error_code: Optional[ErrorCode]


@dataclass
class ProcessResult:
    meta: ActionResultMeta
