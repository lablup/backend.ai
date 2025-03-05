from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Generic, Optional, TypeVar


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

    @abstractmethod
    def request_id(self) -> str:
        raise NotImplementedError


class BaseActionResult(ABC):
    @abstractmethod
    def entity_id(self) -> Optional[str]:
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
