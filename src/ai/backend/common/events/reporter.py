from abc import ABC, abstractmethod
from typing import Optional, Protocol

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


class AbstractEventReporter(ABC):
    @abstractmethod
    async def on_consumer_start(
        self,
        event: EventProtocol,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def on_consumer_complete(
        self,
        event: EventProtocol,
        duration: Optional[float] = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def on_subscriber_start(
        self,
        event: EventProtocol,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def on_subscriber_complete(
        self,
        event: EventProtocol,
        duration: Optional[float] = None,
    ) -> None:
        raise NotImplementedError
