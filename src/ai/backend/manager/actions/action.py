from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Generic, Mapping, Optional, TypeVar


@dataclass
class BaseAction(ABC):
    @abstractmethod
    def entity_id(self) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def entity_type(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def operation_type(self) -> str:
        raise NotImplementedError


@dataclass
class BaseActionResult(ABC):
    @abstractmethod
    def entity_id(self) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def status(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def description(self) -> Optional[str]:
        raise NotImplementedError


@dataclass
class BaseBatchAction(ABC):
    @abstractmethod
    def entity_ids(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def entity_type(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def operation_type(self) -> str:
        raise NotImplementedError


@dataclass
class BaseBatchActionResult(ABC):
    @abstractmethod
    def entity_ids(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def statuses(self) -> Mapping[str, str]:
        raise NotImplementedError


@dataclass
class BaseActionResultMeta:
    status: str
    description: str
    started_at: datetime
    end_at: datetime
    duration: float


TAction = TypeVar("TAction", bound=BaseAction)
TActionResult = TypeVar("TActionResult", bound=BaseActionResult)


@dataclass
class ProcessResult(Generic[TActionResult]):
    meta: BaseActionResultMeta
    result: TActionResult
