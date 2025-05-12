import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Generic, Optional, TypeVar

from ai.backend.common.exception import ErrorCode
from ai.backend.manager.actions.types import OperationStatus


class BaseAction(ABC):
    @abstractmethod
    def entity_id(self) -> Optional[str]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def entity_type(cls) -> str:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def operation_type(cls) -> str:
        raise NotImplementedError

    @classmethod
    def type(cls) -> str:
        return f"{cls.entity_type()}:{cls.operation_type()}"


@dataclass
class BaseActionTriggerMeta:
    action_id: uuid.UUID
    started_at: datetime


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


class BaseActionResult(ABC):
    @abstractmethod
    def entity_id(self) -> Optional[str]:
        raise NotImplementedError


class BaseBatchActionResult(ABC):
    @abstractmethod
    def entity_ids(self) -> list[str]:
        raise NotImplementedError


@dataclass
class BaseActionResultMeta:
    action_id: uuid.UUID
    status: OperationStatus
    description: str
    started_at: datetime
    ended_at: datetime
    duration: timedelta
    error_code: Optional[ErrorCode]


TAction = TypeVar("TAction", bound=BaseAction)
TActionResult = TypeVar("TActionResult", bound=BaseActionResult)


@dataclass
class ProcessResult(Generic[TActionResult]):
    meta: BaseActionResultMeta
    result: Optional[TActionResult]
