import enum
from abc import ABC, abstractmethod
from typing import Any, Self, final, override

from ai.backend.common.message_queue.payload import BroadcastMessagePayload

from .payload import AnycastEventPayload, BroadcastEventPayload
from .user_event.user_event import UserEvent

__all__ = (
    "AbstractAnycastEvent",
    "AbstractBroadcastEvent",
    "AbstractEvent",
    "BatchBroadcastEvent",
    "DeliveryPattern",
    "EventDomain",
)


class EventDomain(enum.StrEnum):
    BGTASK = "bgtask"
    IMAGE = "image"
    KERNEL = "kernel"
    MODEL_SERVING = "model_serving"
    MODEL_ROUTE = "model_route"
    NOTIFICATION = "notification"
    SCHEDULE = "schedule"
    IDLE_CHECK = "idle_check"
    SESSION = "session"
    AGENT = "agent"
    ARTIFACT = "artifact"
    VFOLDER = "vfolder"
    VOLUME = "volume"
    LOG = "log"
    WORKFLOW = "workflow"
    SERVICE_DISCOVERY = "service_discovery"


class EventCacheDomain(enum.StrEnum):
    """
    Enum for event cache domains.
    This is used to identify the domain of the cached event.
    """

    BGTASK = "bgtask"
    SESSION_SCHEDULER = "session_scheduler"

    def cache_id(self, id: str) -> str:
        """
        Return the cache ID for the event.
        The cache ID is a string that identifies the cached event.
        """
        return f"{self.value}.{id}"


class DeliveryPattern(enum.StrEnum):
    BROADCAST = "broadcast"
    ANYCAST = "anycast"


class AbstractEvent(ABC):
    @classmethod
    @abstractmethod
    def delivery_pattern(cls) -> DeliveryPattern:
        """
        Return the delivery pattern of the event.
        """
        raise NotImplementedError

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
    def event_domain(cls) -> EventDomain:
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
    def domain_id(self) -> str | None:
        """
        Return the ID within the event domain.
        It's used to reverse-look up the event domain in the event hub.
        """
        raise NotImplementedError

    @abstractmethod
    def user_event(self) -> UserEvent | None:
        """
        Return the event as a UserEvent.
        If user event is not supported, return None.
        """
        raise NotImplementedError


class AbstractAnycastEvent[TPayload: AnycastEventPayload](AbstractEvent):
    """
    An event that should be sent to a single recipient.

    The type parameter is the event's own payload model. It has no default, so every
    event is forced to declare the payload it carries. Code that handles events
    whatever their payload annotates this class as `[Any]`.
    """

    @abstractmethod
    def to_payload(self) -> TPayload:
        """
        Return this event's arguments as its payload model.
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def from_payload(cls, payload: TPayload) -> Self:
        """
        Reconstruct the event from its payload model.
        """
        raise NotImplementedError

    @classmethod
    @override
    def delivery_pattern(cls) -> DeliveryPattern:
        return DeliveryPattern.ANYCAST


class AbstractBroadcastEvent[TPayload: BroadcastEventPayload](AbstractEvent):
    """
    An event that should be broadcasted to all subscribers.

    The type parameter is the event's own payload model. It has no default, so every
    event is forced to declare the payload it carries. Code that handles events
    whatever their payload annotates this class as `[Any]`.
    """

    # The registry and the propagation helpers below hold events regardless of their
    # payload type, so they are deliberately annotated with Any.
    _register_dict: dict[str, type["AbstractBroadcastEvent[Any]"]] = {}

    @abstractmethod
    def to_payload(self) -> TPayload:
        """
        Return this event's arguments as its payload model.
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def from_payload(cls, payload: TPayload) -> Self:
        """
        Reconstruct the event from its payload model.
        """
        raise NotImplementedError

    @override
    def __init_subclass__(cls) -> None:
        try:
            name = cls.event_name()
            if name in cls._register_dict:
                raise RuntimeError(f"Event {name} is already registered")
            cls._register_dict[name] = cls
        except NotImplementedError:
            # If the event name is not implemented, we cannot register it.
            return

    @classmethod
    def deserialize_from_wrapper(
        cls, payload: BroadcastMessagePayload
    ) -> "AbstractBroadcastEvent[Any]":
        """
        Deserialize the event from its broadcast payload.
        """
        event_class = cls._register_dict.get(payload.name)
        if not event_class:
            raise ValueError(f"Event class for name {payload.name} not found")
        return event_class.deserialize(payload.decode_args())

    @classmethod
    @override
    def delivery_pattern(cls) -> DeliveryPattern:
        return DeliveryPattern.BROADCAST

    def generate_events(self) -> list["AbstractBroadcastEvent[Any]"]:
        """
        Generate events to be propagated through EventHub.
        Default implementation returns just this event itself.
        Subclasses can override to generate multiple events.
        """
        return [self]

    @classmethod
    def cache_domain(cls) -> EventCacheDomain | None:
        """
        Return the event domain.
        """
        return None

    @final
    def cache_id(self) -> str | None:
        """
        Return the cache ID for this event.
        If None is returned, the event will not be cached.
        Subclasses can override to provide a cache ID.
        """
        cache_domain = self.cache_domain()
        if cache_domain is None:
            return None
        domain_id = self.domain_id()
        if domain_id is None:
            return None
        return cache_domain.cache_id(domain_id)


class BatchBroadcastEvent[TPayload: BroadcastEventPayload](AbstractBroadcastEvent[TPayload]):
    """
    An event that generates multiple individual events for propagation.
    Subclasses should override generate_events() to create individual events.
    """

    @override
    @abstractmethod
    def generate_events(self) -> list[AbstractBroadcastEvent[Any]]:
        """
        Generate individual events to be propagated through EventHub.
        Each generated event will be broadcast separately.
        Must be overridden by subclasses to generate multiple events.
        """
        raise NotImplementedError
