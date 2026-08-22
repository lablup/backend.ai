import enum
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Self, final, override

from pydantic import BaseModel, ConfigDict, ValidationError
from pydantic_core import PydanticSerializationError

from ai.backend.common.exception import BackendAIError
from ai.backend.common.message_queue.payload import BroadcastMessagePayload
from ai.backend.common.message_queue.types import MessageName

from .exceptions import EventPayloadDecodingError, EventPayloadEncodingError
from .message import EventMessage
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


class AbstractEvent(BaseModel, ABC):
    """
    The base of every event.

    An event is a Pydantic model, so its own fields are the message body: the
    conversion to and from `EventMessage` below is the same for every event, is
    written once here, and is final — no event may redefine how its body is
    rendered.

    Unknown fields are ignored rather than rejected, which is what lets a producer
    add a field without breaking a consumer running an older version — the whole
    reason the body is named fields instead of a positional tuple.
    """

    model_config = ConfigDict(extra="ignore")

    @final
    def to_message(self) -> EventMessage:
        """
        Render this event as the message it is handed to the queue as.

        Raises:
            EventPayloadEncodingError: If a field of this event is not JSON-representable
        """
        name = MessageName(self.event_name())
        try:
            payload = self.model_dump_json()
        except PydanticSerializationError as e:
            raise EventPayloadEncodingError(extra_msg=f"{name}: {e}") from e
        return EventMessage(name=name, payload=payload)

    @final
    @classmethod
    def from_message(cls, message: EventMessage) -> Self:
        """
        Reconstruct the event from the message it was rendered as.

        Raises:
            EventPayloadDecodingError: If the body does not validate against this event
        """
        try:
            return cls.model_validate_json(message.payload)
        except (ValidationError, BackendAIError) as e:
            # An event deriving `BackendAISchema` maps `ValidationError` to a
            # `BackendAIError` of its own choosing, so both forms arrive here.
            raise EventPayloadDecodingError(extra_msg=f"{message.name}: {e}") from e

    @classmethod
    @abstractmethod
    def delivery_pattern(cls) -> DeliveryPattern:
        """
        Return the delivery pattern of the event.
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


class AbstractAnycastEvent(AbstractEvent):
    """
    An event that should be sent to a single recipient.
    """

    @classmethod
    @override
    def delivery_pattern(cls) -> DeliveryPattern:
        return DeliveryPattern.ANYCAST


class AbstractBroadcastEvent(AbstractEvent):
    """
    An event that should be broadcasted to all subscribers.
    """

    _register_dict: ClassVar[dict[str, type["AbstractBroadcastEvent"]]] = {}

    @override
    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        try:
            name = cls.event_name()
            if name in cls._register_dict:
                raise RuntimeError(f"Event {name} is already registered")
            cls._register_dict[name] = cls
        except NotImplementedError:
            # If the event name is not implemented, we cannot register it.
            return

    @classmethod
    def from_broadcast_payload(cls, payload: BroadcastMessagePayload) -> "AbstractBroadcastEvent":
        """
        Reconstruct the event a broadcast payload carries.

        A payload names its event but does not carry its class, so this is where the
        name is resolved against the registry — the one place a subscriber that holds
        only a payload can get back to a typed event.
        """
        event_class = cls._register_dict.get(payload.name)
        if not event_class:
            raise ValueError(f"Event class for name {payload.name} not found")
        return event_class.from_message(EventMessage(name=payload.name, payload=payload.payload))

    @classmethod
    @override
    def delivery_pattern(cls) -> DeliveryPattern:
        return DeliveryPattern.BROADCAST

    def generate_events(self) -> list["AbstractBroadcastEvent"]:
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


class BatchBroadcastEvent(AbstractBroadcastEvent):
    """
    An event that generates multiple individual events for propagation.
    Subclasses should override generate_events() to create individual events.
    """

    @override
    @abstractmethod
    def generate_events(self) -> list[AbstractBroadcastEvent]:
        """
        Generate individual events to be propagated through EventHub.
        Each generated event will be broadcast separately.
        Must be overridden by subclasses to generate multiple events.
        """
        raise NotImplementedError
