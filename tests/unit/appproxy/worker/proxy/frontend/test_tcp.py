from __future__ import annotations

from dataclasses import dataclass, field
from ipaddress import ip_network
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
import pytest_mock

from ai.backend.appproxy.worker.errors.ingress import IngressNotRegisteredError
from ai.backend.appproxy.worker.proxy.frontend.tcp import TCPFrontend
from ai.backend.common.dto.appproxy.v2.ingress.types import IngressAccess, IngressAccessMode

_PORT = 10200


@dataclass(frozen=True)
class _TCPConnectionCase:
    name: str
    ingress_registered: bool = True
    allowed_client_ips: list[str] = field(default_factory=list)
    peer_ip: str = "10.0.0.1"


@dataclass(frozen=True)
class _TCPConnectionSituation:
    frontend: TCPFrontend
    reader: MagicMock
    writer: MagicMock
    backend: MagicMock


@pytest.fixture
def tcp_connection_situation(
    mocker: pytest_mock.MockerFixture, case: _TCPConnectionCase
) -> _TCPConnectionSituation:
    root_context = mocker.MagicMock()
    if case.ingress_registered:
        access = IngressAccess(
            mode=IngressAccessMode.PUBLIC,
            allowed_client_ips=[ip_network(cidr) for cidr in case.allowed_client_ips],
        )
        root_context.ingress_state.reader.get = AsyncMock(
            return_value=mocker.MagicMock(access=access)
        )
    else:
        root_context.ingress_state.reader.get = AsyncMock(
            side_effect=IngressNotRegisteredError("no layer holds the frontend")
        )
    frontend = TCPFrontend(root_context)
    backend = mocker.MagicMock(
        circuit=mocker.MagicMock(id=UUID("d0e6f60c-f375-4454-b4d3-e8ee202fa372")),
        bind=AsyncMock(),
    )
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
            _TCPConnectionCase(name="no-ingress", ingress_registered=False),
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
