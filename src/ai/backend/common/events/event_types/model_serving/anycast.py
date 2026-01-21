import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.events.types import AbstractAnycastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent

from . import ModelServiceStatusEventArgs


class ModelServiceStatusAnycastEvent(ModelServiceStatusEventArgs, AbstractAnycastEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "model_service_status_updated"


@dataclass
class RouteCreationEvent(AbstractAnycastEvent):
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


class RouteCreatedAnycastEvent(RouteCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "route_created"


class RouteTerminatingEvent(RouteCreationEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "route_terminating"


@dataclass
class EndpointRouteListUpdatedEvent(AbstractAnycastEvent):
    endpoint_id: uuid.UUID

    def serialize(self) -> tuple:
        return (str(self.endpoint_id),)

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(uuid.UUID(value[0]))

    @classmethod
    @override
    def event_name(cls) -> str:
        return "endpoint_route_list_updated"

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.MODEL_ROUTE

    @override
    def domain_id(self) -> Optional[str]:
        return str(self.endpoint_id)

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None
