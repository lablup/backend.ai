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
from ai.backend.appproxy.worker.errors.circuit import InvalidCircuitDataError
from ai.backend.appproxy.worker.types import Circuit
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    IngressAccessMode,
    IngressAuthority,
    IngressFrontendKey,
    IngressFrontendKind,
    IngressKey,
    IngressTarget,
    IngressTargetGroup,
    IngressTargetGroupID,
    IngressTargetID,
)

AUTHORITY = IngressAuthority("worker-1")
CIRCUIT_ID = UUID("11111111-1111-1111-1111-111111111111")
WORKER_ID = UUID("22222222-2222-2222-2222-222222222222")
USER_ID = UUID("33333333-3333-3333-3333-333333333333")
ENDPOINT_ID = UUID("44444444-4444-4444-4444-444444444444")
ROUTE_ID = UUID("55555555-5555-5555-5555-555555555555")
SESSION_ID = UUID("66666666-6666-6666-6666-666666666666")
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
def route() -> RouteInfo:
    return RouteInfo(
        route_id=ROUTE_ID,
        session_id=SESSION_ID,
        session_name=None,
        kernel_host="10.0.0.5",
        kernel_port=8000,
        protocol=ProxyProtocol.HTTP,
        traffic_ratio=1.0,
    )


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
        serialized_circuit.model_copy(update={"route_info": [], "session_ids": []})
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
def unsupported_protocol_circuit(
    unsupported_protocol: ProxyProtocol, serialized_circuit: SerializableCircuit
) -> Circuit:
    return Circuit.from_serialized_circuit(
        serialized_circuit.model_copy(update={"protocol": unsupported_protocol})
    )


class TestCircuit:
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
    def test_to_ingress_maps_the_circuit_access(
        self, access_case: _AccessCase, access_case_circuit: Circuit
    ) -> None:
        assert access_case_circuit.to_ingress(AUTHORITY).access.mode == access_case.access_mode

    @pytest.mark.parametrize(
        "frontend_case",
        [
            _FrontendCase(
                frontend_mode=FrontendMode.PORT,
                port=10205,
                subdomain=None,
                frontend_key=IngressFrontendKey("port-10205"),
                kind=IngressFrontendKind.PORT,
            ),
            _FrontendCase(
                frontend_mode=FrontendMode.WILDCARD_DOMAIN,
                port=None,
                subdomain="notebook",
                frontend_key=IngressFrontendKey("wildcard-notebook"),
                kind=IngressFrontendKind.WILDCARD,
            ),
            _FrontendCase(
                frontend_mode=FrontendMode.WILDCARD_DOMAIN,
                port=None,
                subdomain="NoteBook",
                frontend_key=IngressFrontendKey("wildcard-notebook"),
                kind=IngressFrontendKind.WILDCARD,
            ),
        ],
        ids=lambda case: f"{case.frontend_mode.value}-{case.port or case.subdomain}",
    )
    def test_to_ingress_frontend_keys_by_the_circuit_frontend(
        self, frontend_case: _FrontendCase, frontend_case_circuit: Circuit
    ) -> None:
        ingress_frontend = frontend_case_circuit.to_ingress_frontend()
        assert ingress_frontend.kind == frontend_case.kind
        assert ingress_frontend.key() == frontend_case.frontend_key

    @pytest.mark.parametrize(
        "unsupported_protocol",
        [ProxyProtocol.PREOPEN, ProxyProtocol.GRPC, ProxyProtocol.VNC, ProxyProtocol.RDP],
        ids=lambda protocol: protocol.value,
    )
    def test_to_ingress_frontend_rejects_a_protocol_a_worker_does_not_serve(
        self, unsupported_protocol_circuit: Circuit
    ) -> None:
        with pytest.raises(InvalidCircuitDataError):
            unsupported_protocol_circuit.to_ingress_frontend()

    def test_to_ingress_keeps_the_circuit_users_and_allowed_networks(
        self, circuit: Circuit
    ) -> None:
        ingress = circuit.to_ingress(AUTHORITY)
        assert ingress.access.users is not None
        assert ingress.access.users.allowed_user_ids == [USER_ID]
        assert ingress.access.allowed_client_ips == [
            ip_network("10.0.0.0/8"),
            ip_network("192.168.0.1/32"),
        ]

    def test_to_ingress_carries_every_route_as_a_target_of_one_group(
        self, circuit: Circuit
    ) -> None:
        assert circuit.to_ingress(AUTHORITY).backend.target_groups == [
            IngressTargetGroup(
                id=IngressTargetGroupID(str(UUID(int=0))),
                weight=1,
                targets=[
                    IngressTarget(id=IngressTargetID(str(UUID(int=0))), host="10.0.0.5", port=8000)
                ],
            )
        ]

    def test_to_ingress_without_routes_holds_a_group_with_no_targets(
        self, routeless_circuit: Circuit
    ) -> None:
        target_groups = routeless_circuit.to_ingress(AUTHORITY).backend.target_groups
        assert [group.targets for group in target_groups] == [[]]

    def test_to_ingress_key_pairs_the_authority_with_the_frontend_key(
        self, circuit: Circuit
    ) -> None:
        assert circuit.to_ingress_key(AUTHORITY) == IngressKey(
            authority=AUTHORITY, frontend_key=IngressFrontendKey("port-10205")
        )
