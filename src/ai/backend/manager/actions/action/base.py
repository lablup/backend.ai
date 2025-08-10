import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, TypeVar

from ai.backend.common.exception import ErrorCode
from ai.backend.manager.actions.types import OperationStatus

from ..types import ActionSpec


class BaseAction(ABC):
    # TODO: Migrate to One of BaseSingleEntityAction, BaseMultiEntityAction, or BaseScopeAction

    @classmethod
    def spec(cls) -> ActionSpec:
        return ActionSpec(
            entity_type=cls.entity_type(),
            operation_type=cls.operation_type(),
        )

    @classmethod
    @abstractmethod
    def entity_type(cls) -> str:
        """Return the entity type this action operates on."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def operation_type(cls) -> str:
        """Return the operation type of this action."""
        raise NotImplementedError

    @abstractmethod
    def entity_id(self) -> Optional[str]:
        """Return the ID of the entity this action operates on."""
        raise NotImplementedError


class BaseActionResult(ABC):
    @abstractmethod
    def entity_id(self) -> Optional[str]:
        raise NotImplementedError


class BaseBatchAction(ABC):
    @abstractmethod
    def entity_ids(self) -> list[str]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def entity_type(cls) -> str:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def operation_type(cls) -> str:
        raise NotImplementedError


class BaseBatchActionResult(ABC):
    @abstractmethod
    def entity_ids(self) -> list[str]:
        raise NotImplementedError


@dataclass
class BaseActionResultMeta:
    action_id: uuid.UUID
    entity_id: Optional[str]
    status: OperationStatus
    description: str
    started_at: datetime
    ended_at: datetime
    duration: timedelta
    error_code: Optional[ErrorCode]


TAction = TypeVar("TAction", bound=BaseAction)
TActionResult = TypeVar("TActionResult", bound=BaseActionResult)
