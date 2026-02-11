import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TypeVar, override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.common.exception import ErrorCode
from ai.backend.manager.actions.types import ActionOperationType, ActionSpec, OperationStatus


class BaseAction(ABC):
    def entity_id(self) -> str | None:
        """
        Return the ID of the entity this action operates on.
        This returns `None` by default because subclasses may not always need to specify an entity ID.
        """
        return None

    @classmethod
    @abstractmethod
    def entity_type(cls) -> EntityType:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def operation_type(cls) -> ActionOperationType:
        raise NotImplementedError

    @classmethod
    def spec(cls) -> ActionSpec:
        return ActionSpec(
            entity_type=cls.entity_type(),
            operation_type=cls.operation_type(),
        )


@dataclass
class BaseActionTriggerMeta:
    action_id: uuid.UUID
    started_at: datetime


class BaseActionResult(ABC):
    @abstractmethod
    def entity_id(self) -> str | None:
        raise NotImplementedError


@dataclass
class SearchActionResult[T](BaseActionResult):
    items: list[T]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class BaseActionResultMeta:
    action_id: uuid.UUID
    entity_id: str | None
    status: OperationStatus
    description: str
    started_at: datetime
    ended_at: datetime
    duration: timedelta
    error_code: ErrorCode | None


TAction = TypeVar("TAction", bound=BaseAction)
TActionResult = TypeVar("TActionResult", bound=BaseActionResult)


@dataclass
class ProcessResult:
    meta: BaseActionResultMeta
