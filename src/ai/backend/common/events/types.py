import enum
from abc import ABC, abstractmethod
from typing import Optional, Self

from .user_event.user_event import UserEvent

__all__ = (
    "EventDomain",
    "AbstractEvent",
)


class EventDomain(enum.StrEnum):
    BGTASK = "bgtask"
    IMAGE = "image"
    KERNEL = "kernel"
    MODEL_SERVING = "model_serving"
    MODEL_ROUTE = "model_route"
    SCHEDULE = "schedule"
    IDLE_CHECK = "idle_check"
    SESSION = "session"
    AGENT = "agent"
    VFOLDER = "vfolder"
    VOLUME = "volume"
    LOG = "log"


class AbstractEvent(ABC):
    @abstractmethod
    def serialize(self) -> tuple[bytes, ...]:
        """
        Return a msgpack-serializable tuple.
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def deserialize(cls, value: tuple[bytes, ...]) -> Self:
        """
        Construct the event args from a tuple deserialized from msgpack.
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def event_domain(self) -> EventDomain:
        """
        Return the event domain.
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def event_name(cls) -> str:
        """
        Return the event name.
        """
        raise NotImplementedError

    @abstractmethod
    def domain_id(self) -> Optional[str]:
        """
        Return the domain ID.
        It's used to identify the event domain in the event hub.
        """
        raise NotImplementedError

    @abstractmethod
    def user_event(self) -> Optional[UserEvent]:
        """
        Return the event as a UserEvent.
        If user event is not supported, return None.
        """
        raise NotImplementedError
