from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Self, override

from pydantic import TypeAdapter

from ai.backend.common.events.payload import AnycastEventPayload, BroadcastEventPayload
from ai.backend.common.events.types import AbstractAnycastEvent, AbstractBroadcastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent

from .types import RouteInfo
from .types import SerializableCircuit as Circuit


class AppProxyCircuitEventPayload(BroadcastEventPayload):
    target_worker_authority: str
    circuits: list[Circuit]


class AppProxyCircuitRouteUpdatedEventPayload(BroadcastEventPayload):
    target_worker_authority: str
    circuit: Circuit
    routes: list[RouteInfo]


class GenericWorkerEventPayload(AnycastEventPayload):
    worker_id: str
    reason: str


class CheckWorkerLostEventPayload(AnycastEventPayload):
    """The worker-lost check carries no arguments."""


class CheckUnusedPortEventPayload(AnycastEventPayload):
    """The unused-port check carries no arguments."""


class ReconcileTraefikRoutesEventPayload(AnycastEventPayload):
    """The traefik reconcile trigger carries no arguments."""


@dataclass
class AppProxyCircuitEvent(AbstractBroadcastEvent[AppProxyCircuitEventPayload]):
    target_worker_authority: str
    circuits: list[Circuit]

    @override
    def to_payload(self) -> AppProxyCircuitEventPayload:
        return AppProxyCircuitEventPayload(
            target_worker_authority=self.target_worker_authority,
            circuits=self.circuits,
        )

    @classmethod
    @override
    def from_payload(cls, payload: AppProxyCircuitEventPayload) -> Self:
        return cls(
            target_worker_authority=payload.target_worker_authority,
            circuits=payload.circuits,
        )

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (
            self.target_worker_authority,
            TypeAdapter(list[Circuit]).dump_json(self.circuits).decode("utf-8"),
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(
            target_worker_authority=value[0],
            circuits=[Circuit(**r) for r in json.loads(value[1])],
        )

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.MODEL_ROUTE

    @override
    def domain_id(self) -> str | None:
        return ",".join([str(c.id) for c in self.circuits])

    @override
    def user_event(self) -> UserEvent | None:
        return None


@dataclass
class AppProxyCircuitRouteUpdatedEvent(
    AbstractBroadcastEvent[AppProxyCircuitRouteUpdatedEventPayload]
):
    target_worker_authority: str
    circuit: Circuit
    routes: list[RouteInfo]

    @override
    def to_payload(self) -> AppProxyCircuitRouteUpdatedEventPayload:
        return AppProxyCircuitRouteUpdatedEventPayload(
            target_worker_authority=self.target_worker_authority,
            circuit=self.circuit,
            routes=self.routes,
        )

    @classmethod
    @override
    def from_payload(cls, payload: AppProxyCircuitRouteUpdatedEventPayload) -> Self:
        return cls(
            target_worker_authority=payload.target_worker_authority,
            circuit=payload.circuit,
            routes=payload.routes,
        )

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (
            self.target_worker_authority,
            self.circuit.model_dump_json(),
            TypeAdapter(list[RouteInfo]).dump_json(self.routes).decode("utf-8"),
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
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
    def domain_id(self) -> str | None:
        return str(self.circuit.id)

    @override
    def user_event(self) -> UserEvent | None:
        return None


@dataclass
class GenericWorkerEvent(AbstractAnycastEvent[GenericWorkerEventPayload]):
    worker_id: str
    reason: str

    @override
    def to_payload(self) -> GenericWorkerEventPayload:
        return GenericWorkerEventPayload(
            worker_id=self.worker_id,
            reason=self.reason,
        )

    @classmethod
    @override
    def from_payload(cls, payload: GenericWorkerEventPayload) -> Self:
        return cls(
            worker_id=payload.worker_id,
            reason=payload.reason,
        )

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (
            self.worker_id,
            self.reason,
        )

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(value[0], value[1])

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.MODEL_ROUTE

    @override
    def domain_id(self) -> str | None:
        return self.worker_id

    @override
    def user_event(self) -> UserEvent | None:
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


class DoCheckWorkerLostEvent(AbstractAnycastEvent[CheckWorkerLostEventPayload]):
    @override
    def to_payload(self) -> CheckWorkerLostEventPayload:
        return CheckWorkerLostEventPayload()

    @classmethod
    @override
    def from_payload(cls, payload: CheckWorkerLostEventPayload) -> Self:
        return cls()

    @override
    def serialize(self) -> tuple[Any, ...]:
        return tuple()

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
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
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None


class DoCheckUnusedPortEvent(AbstractAnycastEvent[CheckUnusedPortEventPayload]):
    @override
    def to_payload(self) -> CheckUnusedPortEventPayload:
        return CheckUnusedPortEventPayload()

    @classmethod
    @override
    def from_payload(cls, payload: CheckUnusedPortEventPayload) -> Self:
        return cls()

    @override
    def serialize(self) -> tuple[Any, ...]:
        return tuple()

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
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
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None


class DoReconcileTraefikRoutesEvent(AbstractAnycastEvent[ReconcileTraefikRoutesEventPayload]):
    """Periodic trigger emitted by the coordinator leader cron to reconcile
    every active inference circuit's routing config against the live Circuit
    DB state. Acts as a safety net against missed propagation events so that
    the etcd-based Traefik provider eventually converges on the DB-backed
    source of truth.
    """

    @override
    def to_payload(self) -> ReconcileTraefikRoutesEventPayload:
        return ReconcileTraefikRoutesEventPayload()

    @classmethod
    @override
    def from_payload(cls, payload: ReconcileTraefikRoutesEventPayload) -> Self:
        return cls()

    @override
    def serialize(self) -> tuple[Any, ...]:
        return tuple()

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls()

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_reconcile_traefik_routes"

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.MODEL_ROUTE

    @override
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None
