from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from ipaddress import ip_network
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
import pytest_mock

from ai.backend.appproxy.common.types import AppMode, FrontendMode, ProxyProtocol, RouteInfo
from ai.backend.appproxy.worker.ingress.factory import IngressState
from ai.backend.appproxy.worker.ingress.in_memory import InMemoryIngressState
from ai.backend.appproxy.worker.ingress.layered import LayeredIngressState
from ai.backend.appproxy.worker.proxy.frontend.tcp import TCPFrontend
from ai.backend.appproxy.worker.types import Circuit, InteractiveAppInfo, PortFrontendInfo
from ai.backend.common.dto.appproxy.v2.ingress.types import IngressAuthority

_AUTHORITY = IngressAuthority("worker-1")
_PORT = 10200


@dataclass(frozen=True)
class _TCPConnectionCase:
    name: str
    ingress_held: bool = True
    allowed_client_ips: list[str] = field(default_factory=list)
    peer_ip: str = "10.0.0.1"


@dataclass(frozen=True)
class _TCPConnectionSituation:
    frontend: TCPFrontend
    reader: MagicMock
    writer: MagicMock
    backend: MagicMock


@pytest.fixture
async def tcp_connection_situation(
    mocker: pytest_mock.MockerFixture, case: _TCPConnectionCase
) -> _TCPConnectionSituation:
    user_id = UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4")
    session_id = UUID("f5cd34ba-ae53-4537-a813-09f38496443d")
    circuit = Circuit(
        id=UUID("d0e6f60c-f375-4454-b4d3-e8ee202fa372"),
        app="ssh",
        protocol=ProxyProtocol.TCP,
        worker=UUID("00000000-0000-0000-0000-000000000000"),
        app_mode=AppMode.INTERACTIVE,
        frontend_mode=FrontendMode.PORT,
        frontend=PortFrontendInfo(_PORT),
        port=_PORT,
        app_info=InteractiveAppInfo(user_id=user_id),
        subdomain=None,
        runtime_variant=None,
        envs={},
        arguments=None,
        open_to_public=True,
        allowed_client_ips=None,
        user_id=user_id,
        access_key="AKIAIOSFODNN7EXAMPLE",
        endpoint_id=None,
        route_info=[
            RouteInfo(
                route_id=UUID("4eeb260b-6cc5-4362-baf3-ea978388becd"),
                session_id=session_id,
                session_name=None,
                kernel_host="127.0.0.1",
                kernel_port=2200,
                protocol=ProxyProtocol.TCP,
                traffic_ratio=1.0,
            )
        ],
        session_ids=[session_id],
        created_at=datetime(2024, 7, 16, 5, 45, 45, tzinfo=UTC),
        updated_at=datetime(2024, 7, 16, 5, 45, 45, tzinfo=UTC),
    )
    circuit_ingress = circuit.to_ingress(_AUTHORITY)
    ingress = circuit_ingress.model_copy(
        update={
            "access": circuit_ingress.access.model_copy(
                update={
                    "allowed_client_ips": [ip_network(cidr) for cidr in case.allowed_client_ips]
                }
            )
        }
    )
    in_memory = InMemoryIngressState()
    if case.ingress_held:
        await in_memory.apply([ingress])
    root_context = mocker.MagicMock()
    root_context.ingress_state = IngressState(
        reader=LayeredIngressState([in_memory], in_memory=in_memory), writer=None
    )
    frontend = TCPFrontend(root_context)
    backend = mocker.MagicMock(circuit=circuit, bind=AsyncMock())
    frontend.backends[_PORT] = backend
    writer = mocker.MagicMock(wait_closed=AsyncMock())
    writer.get_extra_info.return_value = (case.peer_ip, 54321)
    return _TCPConnectionSituation(
        frontend=frontend, reader=mocker.MagicMock(), writer=writer, backend=backend
    )


class TestTCPFrontendPipe:
    @pytest.mark.parametrize(
        "case",
        [
            _TCPConnectionCase(name="ingress-never-held", ingress_held=False),
            _TCPConnectionCase(
                name="peer-outside-the-allowlist",
                allowed_client_ips=["192.168.0.0/24"],
                peer_ip="10.0.0.1",
            ),
        ],
        ids=lambda case: case.name,
    )
    async def test_connection_is_closed_without_reaching_the_backend(
        self, case: _TCPConnectionCase, tcp_connection_situation: _TCPConnectionSituation
    ) -> None:
        situation = tcp_connection_situation
        await situation.frontend.pipe(_PORT, situation.reader, situation.writer)
        situation.backend.bind.assert_not_awaited()
        situation.writer.close.assert_called_once()

    @pytest.mark.parametrize(
        "case",
        [
            _TCPConnectionCase(name="open-allowlist"),
            _TCPConnectionCase(
                name="peer-inside-the-allowlist",
                allowed_client_ips=["10.0.0.0/8"],
                peer_ip="10.0.0.1",
            ),
        ],
        ids=lambda case: case.name,
    )
    async def test_allowed_connection_is_bound_to_the_backend(
        self, case: _TCPConnectionCase, tcp_connection_situation: _TCPConnectionSituation
    ) -> None:
        situation = tcp_connection_situation
        await situation.frontend.pipe(_PORT, situation.reader, situation.writer)
        situation.backend.bind.assert_awaited_once_with(situation.reader, situation.writer)
