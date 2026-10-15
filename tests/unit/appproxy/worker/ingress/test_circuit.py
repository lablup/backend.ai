from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from ipaddress import ip_network
from uuid import UUID

import pytest

from ai.backend.appproxy.common.types import (
    AppMode,
    FrontendMode,
    ProxyProtocol,
    RouteInfo,
    SerializableCircuit,
)
from ai.backend.appproxy.worker.ingress.circuit import LegacyCircuitIngressSync
from ai.backend.appproxy.worker.ingress.in_memory import InMemoryIngressState
from ai.backend.appproxy.worker.types import Circuit
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    Ingress,
    IngressAccess,
    IngressAccessMode,
    IngressAuthority,
    IngressBackend,
    IngressBackendID,
    IngressFrontend,
    IngressFrontendKey,
    IngressFrontendKind,
    IngressID,
    IngressProtocol,
    IngressTarget,
    IngressTargetGroup,
    IngressTargetGroupID,
    IngressTargetID,
    PortFrontend,
)

AUTHORITY = IngressAuthority("worker-1")
CIRCUIT_ID = UUID("11111111-1111-1111-1111-111111111111")
WORKER_ID = UUID("22222222-2222-2222-2222-222222222222")
USER_ID = UUID("33333333-3333-3333-3333-333333333333")
ENDPOINT_ID = UUID("44444444-4444-4444-4444-444444444444")
ROUTE_ID = UUID("55555555-5555-5555-5555-555555555555")
SESSION_ID = UUID("66666666-6666-6666-6666-666666666666")
PORT_KEY = IngressFrontendKey("10205")
CREATED_AT = datetime(2026, 1, 1, tzinfo=UTC)


@dataclass(frozen=True)
class _AccessCase:
    app_mode: AppMode
    protocol: ProxyProtocol
    open_to_public: bool
    access_mode: IngressAccessMode


@dataclass(frozen=True)
class _FrontendCase:
    frontend_mode: FrontendMode
    port: int | None
    subdomain: str | None
    frontend_key: IngressFrontendKey
    kind: IngressFrontendKind


@pytest.fixture
def memory() -> InMemoryIngressState:
    return InMemoryIngressState()


@pytest.fixture
def sync(memory: InMemoryIngressState) -> LegacyCircuitIngressSync:
    return LegacyCircuitIngressSync(memory, AUTHORITY)


@pytest.fixture
def route() -> RouteInfo:
    return RouteInfo(
        route_id=ROUTE_ID,
        session_id=SESSION_ID,
        session_name=None,
        kernel_host="10.0.0.5",
        kernel_port=8000,
        protocol=ProxyProtocol.HTTP,
        traffic_ratio=0.7,
    )


@pytest.fixture
def moved_route(route: RouteInfo) -> RouteInfo:
    return route.model_copy(update={"kernel_host": "10.0.0.6"})


@pytest.fixture
def serialized_circuit(route: RouteInfo) -> SerializableCircuit:
    return SerializableCircuit(
        id=CIRCUIT_ID,
        app="jupyter",
        protocol=ProxyProtocol.HTTP,
        worker=WORKER_ID,
        app_mode=AppMode.INTERACTIVE,
        frontend_mode=FrontendMode.PORT,
        envs={},
        arguments=None,
        open_to_public=False,
        allowed_client_ips="10.0.0.0/8, 192.168.0.1",
        port=10205,
        subdomain=None,
        user_id=USER_ID,
        endpoint_id=ENDPOINT_ID,
        runtime_variant=None,
        route_info=[route],
        session_ids=[SESSION_ID],
        created_at=CREATED_AT,
        updated_at=CREATED_AT,
    )


@pytest.fixture
def circuit(serialized_circuit: SerializableCircuit) -> Circuit:
    return Circuit.from_serialized_circuit(serialized_circuit)


@pytest.fixture
def routeless_circuit(serialized_circuit: SerializableCircuit) -> Circuit:
    return Circuit.from_serialized_circuit(
        serialized_circuit.model_copy(
            update={"id": UUID(int=1), "port": 10206, "route_info": [], "session_ids": []}
        )
    )


@pytest.fixture
def access_case_circuit(
    access_case: _AccessCase, serialized_circuit: SerializableCircuit
) -> Circuit:
    return Circuit.from_serialized_circuit(
        serialized_circuit.model_copy(
            update={
                "app_mode": access_case.app_mode,
                "protocol": access_case.protocol,
                "open_to_public": access_case.open_to_public,
            }
        )
    )


@pytest.fixture
def frontend_case_circuit(
    frontend_case: _FrontendCase, serialized_circuit: SerializableCircuit
) -> Circuit:
    return Circuit.from_serialized_circuit(
        serialized_circuit.model_copy(
            update={
                "frontend_mode": frontend_case.frontend_mode,
                "port": frontend_case.port,
                "subdomain": frontend_case.subdomain,
            }
        )
    )


@pytest.fixture
async def ingress_in_memory(memory: InMemoryIngressState) -> None:
    await memory.apply([
        Ingress(
            id=IngressID(str(CIRCUIT_ID)),
            authority=AUTHORITY,
            revision=0,
            frontend=IngressFrontend(
                kind=IngressFrontendKind.PORT,
                protocol=IngressProtocol.HTTP,
                port=PortFrontend(number=10205),
            ),
            access=IngressAccess(mode=IngressAccessMode.PUBLIC, allowed_client_ips=[]),
            backend=IngressBackend(
                id=IngressBackendID(str(CIRCUIT_ID)),
                target_groups=[
                    IngressTargetGroup(id=IngressTargetGroupID("group-1"), weight=1, targets=[])
                ],
            ),
        )
    ])


class TestLegacyCircuitIngressSync:
    @pytest.mark.parametrize(
        "access_case",
        [
            _AccessCase(
                app_mode=AppMode.INTERACTIVE,
                protocol=ProxyProtocol.HTTP,
                open_to_public=False,
                access_mode=IngressAccessMode.USER,
            ),
            _AccessCase(
                app_mode=AppMode.INFERENCE,
                protocol=ProxyProtocol.HTTP,
                open_to_public=False,
                access_mode=IngressAccessMode.TOKEN,
            ),
            _AccessCase(
                app_mode=AppMode.INTERACTIVE,
                protocol=ProxyProtocol.HTTP,
                open_to_public=True,
                access_mode=IngressAccessMode.PUBLIC,
            ),
            _AccessCase(
                app_mode=AppMode.INFERENCE,
                protocol=ProxyProtocol.TCP,
                open_to_public=False,
                access_mode=IngressAccessMode.PUBLIC,
            ),
        ],
        ids=lambda case: f"{case.app_mode}-{case.protocol}-public-{case.open_to_public}",
    )
    async def test_apply_maps_the_circuit_access(
        self,
        sync: LegacyCircuitIngressSync,
        memory: InMemoryIngressState,
        access_case: _AccessCase,
        access_case_circuit: Circuit,
    ) -> None:
        await sync.apply(access_case_circuit, access_case_circuit.route_info)
        stored_ingress = await memory.get(PORT_KEY)
        assert stored_ingress is not None
        assert stored_ingress.access.mode == access_case.access_mode

    @pytest.mark.parametrize(
        "frontend_case",
        [
            _FrontendCase(
                frontend_mode=FrontendMode.PORT,
                port=10205,
                subdomain=None,
                frontend_key=IngressFrontendKey("10205"),
                kind=IngressFrontendKind.PORT,
            ),
            _FrontendCase(
                frontend_mode=FrontendMode.WILDCARD_DOMAIN,
                port=None,
                subdomain="notebook",
                frontend_key=IngressFrontendKey("notebook"),
                kind=IngressFrontendKind.WILDCARD,
            ),
        ],
        ids=lambda case: case.frontend_mode.value,
    )
    async def test_apply_keys_the_ingress_by_the_circuit_frontend(
        self,
        sync: LegacyCircuitIngressSync,
        memory: InMemoryIngressState,
        frontend_case: _FrontendCase,
        frontend_case_circuit: Circuit,
    ) -> None:
        await sync.apply(frontend_case_circuit, frontend_case_circuit.route_info)
        stored_ingress = await memory.get(frontend_case.frontend_key)
        assert stored_ingress is not None
        assert stored_ingress.frontend.kind == frontend_case.kind

    async def test_apply_keeps_the_circuit_id_users_and_allowed_networks(
        self, sync: LegacyCircuitIngressSync, memory: InMemoryIngressState, circuit: Circuit
    ) -> None:
        await sync.apply(circuit, circuit.route_info)
        stored_ingress = await memory.get(PORT_KEY)
        assert stored_ingress is not None
        assert stored_ingress.id == str(CIRCUIT_ID)
        assert stored_ingress.access.users is not None
        assert stored_ingress.access.users.allowed_user_ids == [USER_ID]
        assert stored_ingress.access.allowed_client_ips == [
            ip_network("10.0.0.0/8"),
            ip_network("192.168.0.1/32"),
        ]

    async def test_apply_carries_each_route_as_a_weighted_target_group(
        self, sync: LegacyCircuitIngressSync, memory: InMemoryIngressState, circuit: Circuit
    ) -> None:
        await sync.apply(circuit, circuit.route_info)
        stored_ingress = await memory.get(PORT_KEY)
        assert stored_ingress is not None
        assert stored_ingress.backend.target_groups == [
            IngressTargetGroup(
                id=IngressTargetGroupID(str(ROUTE_ID)),
                weight=70,
                targets=[
                    IngressTarget(id=IngressTargetID(str(ROUTE_ID)), host="10.0.0.5", port=8000)
                ],
            )
        ]

    async def test_a_later_event_for_the_circuit_is_stored_over_an_earlier_one(
        self,
        sync: LegacyCircuitIngressSync,
        memory: InMemoryIngressState,
        circuit: Circuit,
        moved_route: RouteInfo,
    ) -> None:
        await sync.apply(circuit, circuit.route_info)
        await sync.apply(circuit, [moved_route])
        stored_ingress = await memory.get(PORT_KEY)
        assert stored_ingress is not None
        assert [
            target.host
            for group in stored_ingress.backend.target_groups
            for target in group.targets
        ] == ["10.0.0.6"]

    @pytest.mark.usefixtures("ingress_in_memory")
    async def test_apply_without_routes_removes_the_ingress(
        self, sync: LegacyCircuitIngressSync, memory: InMemoryIngressState, circuit: Circuit
    ) -> None:
        await sync.apply(circuit, [])
        assert await memory.get(PORT_KEY) is None

    @pytest.mark.usefixtures("ingress_in_memory")
    async def test_remove_drops_the_ingress_of_the_circuit(
        self, sync: LegacyCircuitIngressSync, memory: InMemoryIngressState, circuit: Circuit
    ) -> None:
        await sync.remove([circuit])
        assert await memory.get(PORT_KEY) is None

    async def test_replace_all_holds_only_the_circuits_with_routes(
        self,
        sync: LegacyCircuitIngressSync,
        memory: InMemoryIngressState,
        circuit: Circuit,
        routeless_circuit: Circuit,
    ) -> None:
        await sync.replace_all([circuit, routeless_circuit])
        assert [ingress.id for ingress in await memory.get_all()] == [str(CIRCUIT_ID)]
