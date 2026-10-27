from __future__ import annotations

from typing import override

from ai.backend.common.events.types import AbstractAnycastEvent, AbstractBroadcastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent

from .types import RouteInfo
from .types import SerializableCircuit as Circuit


class AppProxyCircuitEvent(AbstractBroadcastEvent):
    target_worker_authority: str
    circuits: list[Circuit]

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


class AppProxyCircuitRouteUpdatedEvent(AbstractBroadcastEvent):
    target_worker_authority: str
    circuit: Circuit
    routes: list[RouteInfo]

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


class GenericWorkerEvent(AbstractAnycastEvent):
    worker_id: str
    reason: str

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


class DoCheckWorkerLostEvent(AbstractAnycastEvent):
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


class DoCheckUnusedPortEvent(AbstractAnycastEvent):
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


class DoReconcileTraefikRoutesEvent(AbstractAnycastEvent):
    """Periodic trigger emitted by the coordinator leader cron to reconcile
    every active inference circuit's routing config against the live Circuit
    DB state. Acts as a safety net against missed propagation events so that
    the etcd-based Traefik provider eventually converges on the DB-backed
    source of truth.
    """

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
