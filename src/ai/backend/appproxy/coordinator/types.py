from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import AsyncIterator, Callable, Sequence
from contextlib import AbstractAsyncContextManager
from contextlib import asynccontextmanager as actxmgr
from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Protocol,
    Self,
)
from uuid import UUID

import aiohttp_cors
import attrs
from pydantic import AliasChoices, BaseModel, Field, TypeAdapter

from ai.backend.appproxy.common.errors import ServerMisconfiguredError, ServiceUnavailable
from ai.backend.appproxy.common.etcd import TraefikEtcd, convert_to_etcd_dict
from ai.backend.appproxy.common.events import (
    AppProxyCircuitCreatedEvent,
    AppProxyCircuitRemovedEvent,
    AppProxyCircuitRouteUpdatedEvent,
    AppProxyWorkerCircuitAddedEvent,
)
from ai.backend.appproxy.common.types import ProxyProtocol, RouteInfo, SerializableCircuit
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.health_checker.probe import HealthProbe
from ai.backend.common.leader import ValkeyLeaderElection
from ai.backend.common.lock import AbstractDistributedLock
from ai.backend.common.metrics.metric import (
    APIMetricObserver,
    EventMetricObserver,
    SystemMetricObserver,
)
from ai.backend.common.metrics.multiprocess import generate_latest_multiprocess
from ai.backend.common.types import AgentId, RedisConnectionInfo
from ai.backend.logging import BraceStyleAdapter

from .config import ServerConfig
from .defs import LockID
from .models import Circuit
from .models.utils import ExtendedAsyncSAEngine
from .models.worker import Worker

if TYPE_CHECKING:
    from .services.endpoint import EndpointService

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class CoordinatorMetricRegistry:
    _instance: Self | None = None

    api: APIMetricObserver
    event: EventMetricObserver
    system: SystemMetricObserver

    def __init__(self) -> None:
        self.api = APIMetricObserver.instance()
        self.event = EventMetricObserver.instance()
        self.system = SystemMetricObserver.instance()

    @classmethod
    def instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def to_prometheus(self) -> str:
        self.system.observe()
        return generate_latest_multiprocess().decode("utf-8")


class DistributedLockFactory(Protocol):
    def __call__(self, lock_id: LockID, lifetime_hint: float) -> AbstractDistributedLock: ...


@dataclass
class CircuitManager:
    event_dispatcher: EventDispatcher
    event_producer: EventProducer
    traefik_etcd: TraefikEtcd | None
    local_config: ServerConfig
    # Keyed by ``{worker_authority}:{port or subdomain}`` so that two distinct
    # circuits occupying the same worker slot serialize against each other.
    # Keying by circuit.id would let create(B) and unload(A) on the same port
    # race — their etcd writes could then interleave and produce a window
    # where Traefik sees two routers matching the same traffic but pointing
    # at different services.
    _slot_locks: dict[str, asyncio.Lock] = field(default_factory=dict)

    @staticmethod
    def _slot_key(circuit: Circuit) -> str:
        worker_authority = circuit.worker_row.authority
        slot = circuit.port if circuit.port is not None else circuit.subdomain
        return f"{worker_authority}:{slot}"

    def _get_slot_lock(self, slot_key: str) -> asyncio.Lock:
        if slot_key not in self._slot_locks:
            self._slot_locks[slot_key] = asyncio.Lock()
        return self._slot_locks[slot_key]

    @actxmgr
    async def circuit_lock(self, circuit: Circuit) -> AsyncIterator[None]:
        async with self._get_slot_lock(self._slot_key(circuit)):
            yield

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

        # Each circuit is published under its own slot lock so a concurrent
        # unload on the same slot cannot interleave its delete_prefix calls
        # with our put_prefix. Batching across circuits is dropped here — a
        # single worker's startup has one circuit per slot, and per-request
        # create is always a single-element list, so the extra put_prefix
        # calls are negligible in practice.
        for circuit in circuits:
            async with self.circuit_lock(circuit):
                await self._publish_traefik_circuit(circuit)
        log.debug("initialize_traefik_circuits(): end")

    async def _publish_traefik_circuit(self, circuit: Circuit) -> None:
        if not self.traefik_etcd:
            raise ServerMisconfiguredError("proxy-coordinator.traefik")
        worker_authority = circuit.worker_row.authority
        protocol = circuit.protocol.value.lower()

        routers = circuit.traefik_routers
        middlewares = circuit.get_traefik_middlewares(self.local_config)
        services = circuit.traefik_services

        scope: dict[str, dict[str, Any]] = {
            "services": dict(services),
            "routers": dict(routers),
        }
        if middlewares:
            scope["middlewares"] = dict(middlewares)
        total_map: dict[str, Any] = {f"worker_{worker_authority}": {protocol: scope}}

        log.debug("traefik_etcd put_prefix {}", convert_to_etcd_dict(total_map))
        await self.traefik_etcd.put_prefix("", convert_to_etcd_dict(total_map))

    async def initialize_legacy_circuit(self, circuit: Circuit) -> None:
        worker_ready_evt = asyncio.Event()
        authority = circuit.worker_row.authority

        async def _event_handler(
            _context: CircuitManager,
            _agent_id: AgentId,
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
        except TimeoutError as e:
            raise ServiceUnavailable(
                "E10001: Proxy worker not responding", extra_data={"worker": authority}
            ) from e

        self.event_dispatcher.unsubscribe(worker_ready_event_handler)

    async def update_circuit_routes(self, circuit: Circuit, old_routes: list[RouteInfo]) -> None:
        async with self.circuit_lock(circuit):
            await self._update_circuit_routes_unlocked(circuit, old_routes)

    async def _update_circuit_routes_unlocked(
        self, circuit: Circuit, old_routes: list[RouteInfo]
    ) -> None:
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

        # Circuit.traefik_services emits a single bai_service_{circuit.id}
        # loadBalancer (see models/circuit.py). We must atomically replace
        # the subtree: a non-atomic delete+put leaves an empty service
        # visible to Traefik between the two RPCs if the put fails, and
        # requests to this circuit's router then receive 503s.
        del old_routes  # legacy signature; no per-session cleanup needed
        new_services = circuit.traefik_services
        service_prefix = f"{etcd_prefix}/services/bai_service_{circuit.id}"
        service_body = new_services.get(f"bai_service_{circuit.id}", {})

        log.debug(
            "traefik_etcd.replace_prefix {} {}",
            service_prefix,
            convert_to_etcd_dict(service_body),
        )
        await self.traefik_etcd.replace_prefix(
            service_prefix,
            convert_to_etcd_dict(service_body),
        )
        log.debug("update_traefik_circuit_routes(): end")

    async def update_legacy_circuit_routes(
        self, circuit: Circuit, old_routes: list[RouteInfo]
    ) -> None:
        # Propagate the full route list to the worker. Healthy-route filtering
        # is now a worker-side concern: the worker's per-backend route pool
        # tracks TCP reachability and excludes unhealthy upstreams from traffic
        # selection. The coordinator ships the canonical DB state and the
        # worker decides which routes to dispatch traffic to.
        event = AppProxyCircuitRouteUpdatedEvent(
            target_worker_authority=circuit.worker_row.authority,
            circuit=SerializableCircuit(**circuit.dump_model()),
            routes=circuit.route_info,
        )
        await self.event_producer.broadcast_event(event)

    async def unload_circuits(self, circuits: Sequence[Circuit]) -> None:
        for circuit in circuits:
            async with self.circuit_lock(circuit):
                await self._unload_one_with_retry(circuit)

    async def _unload_one_with_retry(self, circuit: Circuit, max_attempts: int = 3) -> None:
        """Unload a single circuit with bounded retry on transient errors.

        A transient etcd hiccup used to leave the circuit's Traefik metadata
        partially deleted because (a) the four delete_prefix calls in
        ``unload_traefik_circuit`` were not atomic and (b) the surrounding
        code silently swallowed the raised exception. The atomic
        ``delete_prefixes`` makes each attempt all-or-nothing; this retry
        loop absorbs short-lived failures so a single blip does not force
        the caller's DB transaction to roll back. After the bounded budget
        is exhausted we re-raise so the DB transaction rolls back —
        preserving the invariant that DB and etcd agree on which circuits
        exist.
        """
        for attempt in range(max_attempts):
            try:
                if self.local_config.proxy_coordinator.enable_traefik:
                    await self.unload_traefik_circuit(circuit)
                else:
                    await self.unload_legacy_circuit(circuit)
                return
            except Exception as e:
                if attempt == max_attempts - 1:
                    log.exception(
                        "unload failed after {} attempts for circuit {}",
                        max_attempts,
                        circuit.id,
                    )
                    raise
                log.warning(
                    "unload attempt {}/{} failed for circuit {}: {}",
                    attempt + 1,
                    max_attempts,
                    circuit.id,
                    e,
                )
                await asyncio.sleep(0.1 * (2**attempt))

    async def unload_traefik_circuit(self, circuit: Circuit) -> None:
        log.debug("unload_traefik_circuit(): start")
        if not self.traefik_etcd:
            raise ServerMisconfiguredError("proxy-coordinator.traefik")

        worker_authority = circuit.worker_row.authority
        etcd_prefix = f"worker_{worker_authority}/{circuit.protocol.value.lower()}"

        # Circuit.traefik_services emits a single bai_service_{circuit.id}
        # prefix per circuit (no per-session sub-keys). The full keyset that
        # must disappear atomically is the router, the service, and — for
        # HTTP — the two middleware prefixes; otherwise a transient failure
        # between individual deletes leaves Traefik with a stale router
        # that can route to a kernel host:port reassigned to a different
        # endpoint.
        prefixes_to_remove = [
            f"{etcd_prefix}/routers/bai_router_{circuit.id}",
            f"{etcd_prefix}/services/bai_service_{circuit.id}",
        ]
        if circuit.protocol == ProxyProtocol.HTTP:
            prefixes_to_remove.append(
                f"{etcd_prefix}/middlewares/bai_appproxy_plugin_{circuit.id}",
            )
            prefixes_to_remove.append(
                f"{etcd_prefix}/middlewares/appproxy/plugin/bai_appproxy_plugin_{circuit.id}",
            )

        log.debug("traefik_etcd.delete_prefixes {}", prefixes_to_remove)
        await self.traefik_etcd.delete_prefixes(prefixes_to_remove)
        log.debug("unload_traefik_circuit(): end")

    async def reconcile_traefik_etcd_state(
        self,
        live_circuits: Sequence[Circuit],
        workers: Sequence[Worker],
    ) -> None:
        """Drop stale circuit keys left behind in etcd by missed unloads.

        For each (worker, protocol) scope, compare the set of circuit ids
        currently in the coordinator DB against the set of ``bai_service_{id}``
        keys present under ``worker_{authority}/{protocol}/services``. Any
        circuit id present in etcd but missing from the DB is an orphan
        (lost unload event, coordinator crash between DB delete and etcd
        cleanup, etc.) and gets the same prefix set removed as
        ``unload_traefik_circuit`` would have.

        The per-circuit put reconcile still runs before this helper, so this
        method is a pure cleanup pass — it never adds keys, only removes them.
        """
        if not self.traefik_etcd:
            raise ServerMisconfiguredError("proxy-coordinator.traefik")

        live_by_scope: dict[tuple[str, str], set[UUID]] = defaultdict(set)
        for circuit in live_circuits:
            scope = (circuit.worker_row.authority, circuit.protocol.value.lower())
            live_by_scope[scope].add(circuit.id)

        dropped = 0
        for worker in workers:
            for protocol in ("http", "tcp"):
                etcd_prefix = f"worker_{worker.authority}/{protocol}"
                services_prefix = f"{etcd_prefix}/services"
                try:
                    existing = await self.traefik_etcd.get_prefix(services_prefix)
                except Exception:
                    log.exception(
                        "reconcile_traefik_etcd_state: failed to list etcd services at {}",
                        services_prefix,
                    )
                    continue

                existing_ids: set[UUID] = set()
                for top_key in existing.keys():
                    if not top_key.startswith("bai_service_"):
                        continue
                    try:
                        existing_ids.add(UUID(top_key.removeprefix("bai_service_")))
                    except ValueError:
                        continue

                live_ids = live_by_scope.get((worker.authority, protocol), set())
                stale_ids = existing_ids - live_ids

                for stale_id in stale_ids:
                    prefixes_to_remove = [
                        f"{etcd_prefix}/routers/bai_router_{stale_id}",
                        f"{etcd_prefix}/services/bai_service_{stale_id}",
                    ]
                    if protocol == "http":
                        prefixes_to_remove.append(
                            f"{etcd_prefix}/middlewares/bai_appproxy_plugin_{stale_id}"
                        )
                        prefixes_to_remove.append(
                            f"{etcd_prefix}/middlewares/appproxy/plugin/bai_appproxy_plugin_{stale_id}"
                        )
                    for prefix in prefixes_to_remove:
                        try:
                            await self.traefik_etcd.delete_prefix(prefix)
                        except Exception:
                            log.exception(
                                "reconcile_traefik_etcd_state: delete_prefix {} failed",
                                prefix,
                            )
                    log.info(
                        "reconcile_traefik_etcd_state: dropped stale circuit {} from worker={} protocol={}",
                        stale_id,
                        worker.authority,
                        protocol,
                    )
                    dropped += 1

        if dropped:
            log.info("reconcile_traefik_etcd_state: dropped {} stale circuit(s)", dropped)

    async def unload_legacy_circuit(self, circuit: Circuit) -> None:
        event = AppProxyCircuitRemovedEvent(
            target_worker_authority=circuit.worker_row.authority,
            circuits=[SerializableCircuit(**circuit.dump_model())],
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
    endpoint_service: EndpointService

    metrics: CoordinatorMetricRegistry
    health_probe: HealthProbe
    leader_election: ValkeyLeaderElection


type CleanupContext = Callable[["RootContext"], AbstractAsyncContextManager[None]]


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
        UUID | None,
        Field(
            default=None,
            description="ID of the route. This is optional and may not be present for older routes.",
            validation_alias=AliasChoices("route-id", "route_id"),
            serialization_alias="route-id",
        ),
    ]
    kernel_host: Annotated[
        str | None,
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
