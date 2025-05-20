import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.events.types import AbstractEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import KernelId, ModelServiceStatus, SessionId


@dataclass
class ModelServiceStatusEventArgs(AbstractEvent):
    kernel_id: KernelId
    session_id: SessionId
    model_name: str
    new_status: ModelServiceStatus

    def serialize(self) -> tuple:
        return (
            str(self.kernel_id),
            str(self.session_id),
            self.model_name,
            self.new_status.value,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            kernel_id=KernelId(uuid.UUID(value[0])),
            session_id=SessionId(uuid.UUID(value[1])),
            model_name=value[2],
            new_status=ModelServiceStatus(value[3]),
        )

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.MODEL_SERVING

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


class ModelServiceStatusEvent(ModelServiceStatusEventArgs):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "model_service_status_updated"


@dataclass
class RouteCreationEvent(AbstractEvent):
    route_id: uuid.UUID

    def serialize(self) -> tuple:
        return (str(self.route_id),)

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(uuid.UUID(value[0]))

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.MODEL_ROUTE

    @override
    def domain_id(self) -> Optional[str]:
        return str(self.route_id)

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


class RouteCreatedEvent(RouteCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "route_created"
