from __future__ import annotations

import asyncio
import itertools
import logging
from collections import defaultdict
from collections.abc import AsyncIterator, Callable, Sequence
from contextlib import AbstractAsyncContextManager, AsyncExitStack
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
from pydantic import AliasChoices, Field, TypeAdapter

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
from ai.backend.common.types import AgentId, BackendAISchema, RedisConnectionInfo
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
class CircuitRouteUpdateItem:
    """One circuit's route-table change pending propagation to workers.

    ``old_routes`` is kept alongside ``circuit`` so the legacy and
    Traefik propagation paths share a single entry shape: legacy
    propagation does not consult ``old_routes``, but Traefik's per-
    session cleanup historically did, and pre-bundling them keeps the
    bulk method's caller from re-reading state per circuit.
    """

    circuit: Circuit
    old_routes: list[RouteInfo]


@dataclass
class CircuitManager:
    event_dispatcher: EventDispatcher
    event_producer: EventProducer
    traefik_etcd: TraefikEtcd | None
    local_config: ServerConfig
    _circuit_locks: dict[UUID, asyncio.Lock] = field(default_factory=dict)

    def _get_lock(self, circuit_id: UUID) -> asyncio.Lock:
        if circuit_id not in self._circuit_locks:
            self._circuit_locks[circuit_id] = asyncio.Lock()
        return self._circuit_locks[circuit_id]

    def _release_circuit_lock(self, circuit_id: UUID) -> None:
        self._circuit_locks.pop(circuit_id, None)

    @actxmgr
    async def circuit_lock(self, circuit_id: UUID) -> AsyncIterator[None]:
        async with self._get_lock(circuit_id):
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

        # Publish each circuit's router / service / middleware subtrees via the same
        # atomic per-subtree replace used by the route-update path, keeping both etcd
        # write paths consistent. Each top-level traefik object (one router, one
        # service, each middleware) maps to its own ``.../{kind}/{name}`` subtree so a
        # re-publish only rewrites that object and never disturbs sibling circuits.
        for circuit_chunk in itertools.batched(circuits, 5):
            replacements: dict[str, Any] = {}
            for circuit in circuit_chunk:
                worker_authority = circuit.worker_row.authority
                etcd_prefix = f"worker_{worker_authority}/{circuit.protocol.value.lower()}"
                for name, body in circuit.traefik_routers.items():
                    replacements[f"{etcd_prefix}/routers/{name}"] = convert_to_etcd_dict(body)
                for name, body in circuit.traefik_services.items():
                    replacements[f"{etcd_prefix}/services/{name}"] = convert_to_etcd_dict(body)
                for name, body in circuit.get_traefik_middlewares(self.local_config).items():
                    replacements[f"{etcd_prefix}/middlewares/{name}"] = convert_to_etcd_dict(body)

            log.debug("traefik_etcd atomic_replace_prefixes {}", replacements)
            await self.traefik_etcd.atomic_replace_prefixes(replacements)
            log.debug("initialize_traefik_circuits(): end")

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
        finally:
            self.event_dispatcher.unsubscribe(worker_ready_event_handler)

    async def update_circuit_routes(self, circuit: Circuit, old_routes: list[RouteInfo]) -> None:
        # Single-circuit entry point still exists for callers that don't
        # batch (delete cleanups etc.). It just degenerates to the bulk
        # path with one item so propagation logic lives in one place.
        await self.update_circuit_routes_bulk([
            CircuitRouteUpdateItem(circuit=circuit, old_routes=old_routes)
        ])

    async def update_circuit_routes_bulk(self, items: Sequence[CircuitRouteUpdateItem]) -> None:
        """Apply many circuits' route-table changes under their per-circuit locks.

        Locks are acquired in deterministic id order to avoid a deadlock
        if two callers happen to bulk-update overlapping circuit sets.
        Worker propagation is then issued in one batched call (Traefik:
        one combined ``put_prefix``; legacy: one broadcast event per
        worker authority) so the AppProxy side does not pay per-circuit
        DB connection / etcd round-trip cost.
        """
        if not items:
            return
        ordered = sorted(items, key=lambda it: it.circuit.id)
        async with AsyncExitStack() as stack:
            for item in ordered:
                await stack.enter_async_context(self.circuit_lock(item.circuit.id))
            if self.local_config.proxy_coordinator.enable_traefik:
                await self._update_traefik_circuit_routes_bulk(ordered)
            else:
                await self._update_legacy_circuit_routes_bulk(ordered)

    async def _update_traefik_circuit_routes_bulk(
        self, items: Sequence[CircuitRouteUpdateItem]
    ) -> None:
        if not self.traefik_etcd:
            raise ServerMisconfiguredError("proxy-coordinator.traefik")

        # Replace each circuit's ``bai_service_{id}`` subtree in a single etcd
        # transaction so Traefik never observes a revision where the service was
        # deleted but the new one not yet published (which would briefly leave the
        # router pointing at a missing backend and drop requests). A circuit whose
        # service shrinks (fewer routes) has its stale ``servers/N`` keys removed
        # by the diff; a circuit with no routes yields an empty subtree that is
        # fully removed, matching the previous delete-then-empty-put behaviour.
        replacements: dict[str, Any] = {}
        for item in items:
            worker_authority = item.circuit.worker_row.authority
            etcd_prefix = f"worker_{worker_authority}/{item.circuit.protocol.value.lower()}"
            service_prefix = f"{etcd_prefix}/services/bai_service_{item.circuit.id}"
            service_body = item.circuit.traefik_services.get(f"bai_service_{item.circuit.id}", {})
            replacements[service_prefix] = convert_to_etcd_dict(service_body)
        await self.traefik_etcd.atomic_replace_prefixes(replacements)

    async def _update_legacy_circuit_routes_bulk(
        self, items: Sequence[CircuitRouteUpdateItem]
    ) -> None:
        # Legacy mode broadcasts one event per circuit because each
        # event carries a single SerializableCircuit payload that the
        # worker's RoutePool consumes. Batching them into a multi-
        # circuit event would require a new wire shape on the worker
        # side, which is out of scope for this change. Healthy-route
        # filtering remains worker-side.
        for item in items:
            event = AppProxyCircuitRouteUpdatedEvent(
                target_worker_authority=item.circuit.worker_row.authority,
                circuit=SerializableCircuit(**item.circuit.dump_model()),
                routes=item.circuit.route_info,
            )
            await self.event_producer.broadcast_event(event)

    async def unload_circuits(self, circuits: Sequence[Circuit]) -> None:
        for circuit in circuits:
            try:
                async with self.circuit_lock(circuit.id):
                    if self.local_config.proxy_coordinator.enable_traefik:
                        await self.unload_traefik_circuit(circuit)
                    else:
                        await self.unload_legacy_circuit(circuit)
            except Exception:
                log.exception("Failed to unload circuit {}", circuit.id)
            finally:
                self._release_circuit_lock(circuit.id)

    async def unload_traefik_circuit(self, circuit: Circuit) -> None:
        log.debug("unload_traefik_circuit(): start")
        if not self.traefik_etcd:
            raise ServerMisconfiguredError("proxy-coordinator.traefik")

        worker_authority = circuit.worker_row.authority
        etcd_prefix = f"worker_{worker_authority}/{circuit.protocol.value.lower()}"

        # Circuit.traefik_services now emits a single bai_service_{circuit.id}
        # prefix per circuit (no per-session sub-keys), so cleanup only needs
        # to drop router / service / middleware prefixes scoped to the circuit id.
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
            # Removed even when the circuit had no allowlist.
            prefixes_to_remove.append(
                f"{etcd_prefix}/middlewares/bai_ipallowlist_{circuit.id}",
            )

        for prefix in prefixes_to_remove:
            log.debug("traefik_etcd.delete_prefix {}", prefix)
            await self.traefik_etcd.delete_prefix(prefix)
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
                        # Removed even when the stale circuit had no allowlist.
                        prefixes_to_remove.append(
                            f"{etcd_prefix}/middlewares/bai_ipallowlist_{stale_id}"
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


class InferenceAppConfig(BackendAISchema):
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
