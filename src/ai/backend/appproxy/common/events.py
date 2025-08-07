import json
from dataclasses import dataclass
from typing import Optional, override

from pydantic import TypeAdapter

from ai.backend.common.events.types import AbstractAnycastEvent, AbstractBroadcastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent

from .types import RouteInfo
from .types import SerializableCircuit as Circuit


@dataclass
class AppProxyCircuitEvent(AbstractBroadcastEvent):
    target_worker_authority: str
    circuits: list[Circuit]

    def serialize(self) -> tuple:
        return (
            self.target_worker_authority,
            TypeAdapter(list[Circuit]).dump_json(self.circuits).decode("utf-8"),
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            target_worker_authority=value[0],
            circuits=[Circuit(**r) for r in json.loads(value[1])],
        )

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.MODEL_ROUTE

    @override
    def domain_id(self) -> Optional[str]:
        return ",".join([str(c.id) for c in self.circuits])

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


@dataclass
class AppProxyCircuitRouteUpdatedEvent(AbstractBroadcastEvent):
    target_worker_authority: str
    circuit: Circuit
    routes: list[RouteInfo]

    def serialize(self) -> tuple:
        return (
            self.target_worker_authority,
            self.circuit.model_dump_json(),
            TypeAdapter(list[RouteInfo]).dump_json(self.routes).decode("utf-8"),
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            target_worker_authority=value[0],
            circuit=Circuit(**json.loads(value[1])),
            routes=[RouteInfo(**r) for r in json.loads(value[2])],
        )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "appproxy_circuit_route_updated_event"

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.MODEL_ROUTE

    @override
    def domain_id(self) -> Optional[str]:
        return str(self.circuit.id)

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


@dataclass
class GenericWorkerEvent(AbstractAnycastEvent):
    worker_id: str
    reason: str

    def serialize(self) -> tuple:
        return (
            self.worker_id,
            self.reason,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(value[0], value[1])

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.MODEL_ROUTE

    @override
    def domain_id(self) -> Optional[str]:
        return self.worker_id

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


class AppProxyCircuitCreatedEvent(AppProxyCircuitEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "appproxy_circuit_created_event"


class AppProxyCircuitRemovedEvent(AppProxyCircuitEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "appproxy_circuit_removed_event"


class AppProxyWorkerCircuitAddedEvent(AppProxyCircuitEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "appproxy_worker_circuit_added_event"


class WorkerLostEvent(GenericWorkerEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "worker_lost"


class WorkerTerminatedEvent(GenericWorkerEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "worker_terminated"


class DoCheckWorkerLostEvent(AbstractAnycastEvent):
    def serialize(self) -> tuple:
        return tuple()

    @classmethod
    def deserialize(cls, value: tuple):
        return cls()

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_check_worker_lost"

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.MODEL_ROUTE

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


class DoCheckUnusedPortEvent(AbstractAnycastEvent):
    def serialize(self) -> tuple:
        return tuple()

    @classmethod
    def deserialize(cls, value: tuple):
        return cls()

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_check_unused_port"

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.MODEL_ROUTE

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


class DoHealthCheckEvent(AbstractAnycastEvent):
    def serialize(self) -> tuple:
        return tuple()

    @classmethod
    def deserialize(cls, value: tuple):
        return cls()

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_health_check"

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.MODEL_ROUTE

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None
