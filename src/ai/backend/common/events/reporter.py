from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Protocol, Self

from .types import EventDomain


class EventProtocol(Protocol):
    @classmethod
    def event_domain(self) -> EventDomain:
        pass

    @classmethod
    def event_name(cls) -> str:
        pass

    def domain_id(self) -> Optional[str]:
        pass


@dataclass
class EventReportArgs:
    duration: Optional[float] = None

    @classmethod
    def nop(cls) -> Self:
        return cls()


class AbstractEventReporter(ABC):
    @abstractmethod
    async def report(
        self,
        event: EventProtocol,
        arg: EventReportArgs = EventReportArgs.nop(),
    ) -> None:
        raise NotImplementedError
