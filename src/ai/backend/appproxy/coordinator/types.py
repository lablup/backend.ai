import asyncio
import itertools
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import (
    Annotated,
    Any,
    AsyncContextManager,
    Callable,
    Optional,
    Protocol,
    Self,
    Sequence,
    TypeAlias,
)
from uuid import UUID

import aiohttp_cors
import attrs
from prometheus_client import generate_latest
from pydantic import AliasChoices, BaseModel, Field, TypeAdapter

from ai.backend.appproxy.common.etcd import TraefikEtcd, convert_to_etcd_dict
from ai.backend.appproxy.common.events import (
    AppProxyCircuitCreatedEvent,
    AppProxyCircuitRemovedEvent,
    AppProxyCircuitRouteUpdatedEvent,
    AppProxyWorkerCircuitAddedEvent,
)
from ai.backend.appproxy.common.exceptions import ServerMisconfiguredError, ServiceUnavailable
from ai.backend.appproxy.common.types import ProxyProtocol, RouteInfo, SerializableCircuit
from ai.backend.appproxy.coordinator.health_checker import HealthCheckEngine
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.lock import AbstractDistributedLock
from ai.backend.common.metrics.metric import (
    APIMetricObserver,
    EventMetricObserver,
    SystemMetricObserver,
)
from ai.backend.common.types import AgentId, RedisConnectionInfo
from ai.backend.logging import BraceStyleAdapter

from .config import ServerConfig
from .defs import LockID
from .models import Circuit
from .models.utils import ExtendedAsyncSAEngine

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class CoordinatorMetricRegistry:
    _instance: Optional[Self] = None

    api: APIMetricObserver
    event: EventMetricObserver
    system: SystemMetricObserver

    def __init__(self) -> None:
        self.api = APIMetricObserver.instance()
        self.event = EventMetricObserver.instance()
        self.system = SystemMetricObserver.instance()

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def to_prometheus(self) -> str:
        self.system.observe()
        return generate_latest().decode("utf-8")


class DistributedLockFactory(Protocol):
    def __call__(self, lock_id: LockID, lifetime_hint: float) -> AbstractDistributedLock: ...


@dataclass
class CircuitManager:
    event_dispatcher: EventDispatcher
    event_producer: EventProducer
    traefik_etcd: TraefikEtcd | None
    local_config: ServerConfig

    async def initialize_circuits(self, circuits: Sequence[Circuit]) -> None:
        if self.local_config.proxy_coordinator.enable_traefik:
            await self.initialize_traefik_circuits(circuits)
        else:
            for circuit in circuits:
                await self.initialize_legacy_circuit(circuit)

    async def initialize_traefik_circuits(self, circuits: Sequence[Circuit]) -> None:
        log.debug("initialize_traefik_circuits(): start")
        if not self.traefik_etcd:
            raise ServerMisconfiguredError("proxy-coordinator.traefik")

        for circuit_chunk in itertools.batched(circuits, 5):
            total_map: defaultdict[str, Any] = defaultdict(
                lambda: defaultdict(lambda: {"services": {}, "routers": {}, "middlewares": {}})
            )
            for circuit in circuit_chunk:
                worker_authority = circuit.worker_row.authority

                routers = circuit.traefik_routers
                middlewares = circuit.get_traefik_middlewares(self.local_config)
                services = circuit.traefik_services

                total_map[f"worker_{worker_authority}"][circuit.protocol.value.lower()][
                    "services"
                ].update(services)
                total_map[f"worker_{worker_authority}"][circuit.protocol.value.lower()][
                    "routers"
                ].update(routers)
                if middlewares:
                    total_map[f"worker_{worker_authority}"][circuit.protocol.value.lower()][
                        "middlewares"
                    ].update(middlewares)

            log.debug("traefik_etcd put_prefix {}", convert_to_etcd_dict(total_map))
            await self.traefik_etcd.put_prefix("", convert_to_etcd_dict(total_map))
            log.debug("initialize_traefik_circuits(): end")

    async def initialize_legacy_circuit(self, circuit: Circuit) -> None:
        worker_ready_evt = asyncio.Event()
        authority = circuit.worker_row.authority

        async def _event_handler(
            context: CircuitManager,
            agent_id: AgentId,
            event: AppProxyWorkerCircuitAddedEvent,
        ) -> None:
            if circuit.id in [c.id for c in event.circuits]:
                worker_ready_evt.set()

        worker_ready_event_handler = self.event_dispatcher.subscribe(
            AppProxyWorkerCircuitAddedEvent,
            self,
            _event_handler,
        )
        evt = AppProxyCircuitCreatedEvent(
            authority,
            [SerializableCircuit(**circuit.dump_model())],
        )
        await self.event_producer.broadcast_event(evt)
        try:
            async with asyncio.timeout(15.0):
                await worker_ready_evt.wait()
        except asyncio.TimeoutError:
            raise ServiceUnavailable(
                "E10001: Proxy worker not responding", extra_data={"worker": authority}
            )

        self.event_dispatcher.unsubscribe(worker_ready_event_handler)

    async def update_circuit_routes(self, circuit: Circuit, old_routes: list[RouteInfo]) -> None:
        if self.local_config.proxy_coordinator.enable_traefik:
            await self.update_traefik_circuit_routes(circuit, old_routes)
        else:
            await self.update_legacy_circuit_routes(circuit, old_routes)

    async def update_traefik_circuit_routes(
        self, circuit: Circuit, old_routes: list[RouteInfo]
    ) -> None:
        log.debug("update_traefik_circuit_routes(): start")
        if not self.traefik_etcd:
            raise ServerMisconfiguredError("proxy-coordinator.traefik")

        worker_authority = circuit.worker_row.authority
        etcd_prefix = f"worker_{worker_authority}/{circuit.protocol.value.lower()}"

        # Use health-aware services configuration
        new_route_keys = {
            f"bai_session_{r.session_id}_{circuit.id}" for r in circuit.healthy_routes
        }
        new_services = circuit.traefik_services
        new_services = {
            f"bai_service_{circuit.id}": new_services[f"bai_service_{circuit.id}"],
            **{k: v for k, v in new_services.items() if k in new_route_keys},
        }

        # clear old routes
        for route in old_routes:
            log.debug(
                "traefik_etcd.delete_prefix {}",
                f"{etcd_prefix}/services/bai_session_{route.session_id}_{circuit.id}",
            )
            await self.traefik_etcd.delete_prefix(
                f"{etcd_prefix}/services/bai_session_{route.session_id}_{circuit.id}"
            )
        log.debug(
            "traefik_etcd.delete_prefix {}", f"{etcd_prefix}/services/bai_service_{circuit.id}"
        )
        await self.traefik_etcd.delete_prefix(f"{etcd_prefix}/services/bai_service_{circuit.id}")

        log.debug(
            "traefik_etcd.put_prefix {} {}",
            f"{etcd_prefix}/services",
            convert_to_etcd_dict(new_services),
        )
        await self.traefik_etcd.put_prefix(
            f"{etcd_prefix}/services",
            convert_to_etcd_dict(new_services),
        )
        log.debug("update_traefik_circuit_routes(): end")

    async def update_legacy_circuit_routes(
        self, circuit: Circuit, old_routes: list[RouteInfo]
    ) -> None:
        # Get healthy routes for the circuit
        healthy_routes = circuit.healthy_routes

        event = AppProxyCircuitRouteUpdatedEvent(
            target_worker_authority=circuit.worker_row.authority,
            circuit=SerializableCircuit(**circuit.dump_model()),
            routes=healthy_routes,
        )
        await self.event_producer.broadcast_event(event)

    async def unload_circuits(self, circuits: Sequence[Circuit]) -> None:
        if self.local_config.proxy_coordinator.enable_traefik:
            for circuit in circuits:
                await self.unload_traefik_circuit(circuit)
        else:
            await self.unload_legacy_circuits(circuits)

    async def unload_traefik_circuit(self, circuit: Circuit) -> None:
        log.debug("unload_traefik_circuit(): start")
        if not self.traefik_etcd:
            raise ServerMisconfiguredError("proxy-coordinator.traefik")

        worker_authority = circuit.worker_row.authority
        etcd_prefix = f"worker_{worker_authority}/{circuit.protocol.value.lower()}"

        prefixes_to_remove = [
            f"{etcd_prefix}/routers/bai_router_{circuit.id}",
            f"{etcd_prefix}/services/bai_service_{circuit.id}",
        ] + [
            f"{etcd_prefix}/services/bai_session_{r.session_id}_{circuit.id}"
            for r in circuit.route_info
        ]
        if circuit.protocol == ProxyProtocol.HTTP:
            prefixes_to_remove.append(
                f"{etcd_prefix}/middlewares/bai_appproxy_plugin_{circuit.id}",
            )
            prefixes_to_remove.append(
                f"{etcd_prefix}/middlewares/appproxy/plugin/bai_appproxy_plugin_{circuit.id}",
            )

        for prefix in prefixes_to_remove:
            log.debug("traefik_etcd.delete_prefix {}", prefix)
            await self.traefik_etcd.delete_prefix(prefix)
        log.debug("unload_traefik_circuit(): end")

    async def unload_legacy_circuits(self, circuits: Sequence[Circuit]) -> None:
        circuits_by_worker: defaultdict[str, list[Circuit]] = defaultdict(lambda: [])
        for circuit in circuits:
            circuits_by_worker[circuit.worker_row.authority].append(circuit)

        for authority, circuits in circuits_by_worker.items():
            event = AppProxyCircuitRemovedEvent(
                target_worker_authority=authority,
                circuits=[SerializableCircuit(**c.dump_model()) for c in circuits],
            )
            await self.event_producer.broadcast_event(event)


@attrs.define(slots=True, auto_attribs=True, init=False)
class RootContext:
    pidx: int
    db: ExtendedAsyncSAEngine
    distributed_lock_factory: DistributedLockFactory
    event_dispatcher: EventDispatcher
    event_producer: EventProducer
    core_event_dispatcher: EventDispatcher
    core_event_producer: EventProducer

    valkey_live: ValkeyLiveClient
    redis_lock: RedisConnectionInfo
    core_valkey_live: ValkeyLiveClient
    valkey_schedule: ValkeyScheduleClient
    local_config: ServerConfig
    cors_options: dict[str, aiohttp_cors.ResourceOptions]
    traefik_etcd: TraefikEtcd | None

    circuit_manager: CircuitManager
    health_engine: HealthCheckEngine

    metrics: CoordinatorMetricRegistry


CleanupContext: TypeAlias = Callable[["RootContext"], AsyncContextManager[None]]


class InferenceAppConfig(BaseModel):
    session_id: Annotated[
        UUID,
        Field(
            ...,
            description="ID of the session associated with the inference app.",
            validation_alias=AliasChoices("session-id", "session_id"),
            serialization_alias="session-id",
        ),
    ]
    route_id: Annotated[
        Optional[UUID],
        Field(
            default=None,
            description="ID of the route. This is optional and may not be present for older routes.",
            validation_alias=AliasChoices("route-id", "route_id"),
            serialization_alias="route-id",
        ),
    ]
    kernel_host: Annotated[
        Optional[str],
        Field(
            ...,
            description="Host/IP address of the kernel. This is the address that the proxy will use to connect to the kernel.",
            validation_alias=AliasChoices("kernel-host", "kernel_host"),
            serialization_alias="kernel-host",
        ),
    ]
    kernel_port: Annotated[
        int,
        Field(
            ...,
            ge=1,
            le=65535,
            description="Port number of the kernel. This is the port that the proxy will use to connect to the kernel.",
            validation_alias=AliasChoices("kernel-port", "kernel_port"),
            serialization_alias="kernel-port",
        ),
    ]
    protocol: Annotated[
        ProxyProtocol,
        Field(
            default=ProxyProtocol.HTTP,
            description="Protocol used to connect to the kernel. Supported protocols are HTTP and WebSocket.",
            validation_alias=AliasChoices("protocol"),
            serialization_alias="protocol",
        ),
    ]
    traffic_ratio: Annotated[
        float,
        Field(
            ge=0.0,
            le=1.0,
            default=1.0,
            description="Traffic ratio for the inference app. This is used for load balancing between multiple apps.",
            validation_alias=AliasChoices("traffic-ratio", "traffic_ratio"),
            serialization_alias="traffic-ratio",
        ),
    ]


InferenceAppConfigDict = TypeAdapter(dict[str, list[InferenceAppConfig]])
