from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
import pytest_mock

from ai.backend.appproxy.common.types import AppMode, FrontendMode, ProxyProtocol
from ai.backend.appproxy.worker.proxy.frontend.h2.port import PortFrontend
from ai.backend.appproxy.worker.types import Circuit, InteractiveAppInfo, PortFrontendInfo

_LISTEN_PORT = 10200
_API_PORT = 20000
_USER_ID = UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4")


@dataclass(frozen=True)
class _StoredCircuitCase:
    open_to_public: bool
    allowed_client_ips: str | None
    expected_registered_ports: list[int]


@dataclass(frozen=True)
class _ListenAddressCase:
    tls_listen: bool
    expected_frontend_argument: str


@pytest.fixture
def root_context() -> MagicMock:
    root_ctx = MagicMock()
    root_ctx.local_config.proxy_worker.http2.api_port_pool = (_API_PORT, _API_PORT)
    root_ctx.local_config.proxy_worker.port_proxy.bind_host = "192.0.2.1"
    root_ctx.local_config.proxy_worker.port_proxy.bind_port_range = (_LISTEN_PORT, _LISTEN_PORT)
    return root_ctx


class TestRegisterCircuit:
    @pytest.fixture
    def h2_frontend(
        self, root_context: MagicMock, mocker: pytest_mock.MockerFixture
    ) -> PortFrontend:
        mocker.patch(
            "ai.backend.appproxy.worker.proxy.frontend.h2.port.H2Backend.update_config",
            AsyncMock(),
        )
        frontend = PortFrontend(root_context)
        frontend.api_ports = {_LISTEN_PORT: _API_PORT}
        return frontend

    @pytest.fixture
    def stored_circuit(self, case: _StoredCircuitCase) -> Circuit:
        return Circuit(
            id=UUID("d0e6f60c-f375-4454-b4d3-e8ee202fa372"),
            app="grpc-app",
            protocol=ProxyProtocol.HTTP2,
            worker=UUID("00000000-0000-0000-0000-000000000000"),
            app_mode=AppMode.INTERACTIVE,
            frontend_mode=FrontendMode.PORT,
            frontend=PortFrontendInfo(_LISTEN_PORT),
            port=_LISTEN_PORT,
            app_info=InteractiveAppInfo(user_id=_USER_ID),
            subdomain=None,
            runtime_variant=None,
            envs={},
            arguments=None,
            open_to_public=case.open_to_public,
            allowed_client_ips=case.allowed_client_ips,
            user_id=_USER_ID,
            access_key="AKIAIOSFODNN7EXAMPLE",
            endpoint_id=None,
            route_info=[],
            session_ids=[],
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            updated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

    @pytest.mark.parametrize(
        "case",
        [
            pytest.param(
                _StoredCircuitCase(
                    open_to_public=True,
                    allowed_client_ips=None,
                    expected_registered_ports=[_LISTEN_PORT],
                ),
                id="public_without_allowlist_is_registered",
            ),
            pytest.param(
                _StoredCircuitCase(
                    open_to_public=False,
                    allowed_client_ips=None,
                    expected_registered_ports=[],
                ),
                id="private_is_skipped",
            ),
            pytest.param(
                _StoredCircuitCase(
                    open_to_public=True,
                    allowed_client_ips="10.0.0.0/8",
                    expected_registered_ports=[],
                ),
                id="public_with_allowlist_is_skipped",
            ),
        ],
    )
    async def test_registered_ports(
        self, case: _StoredCircuitCase, h2_frontend: PortFrontend, stored_circuit: Circuit
    ) -> None:
        await h2_frontend.register_circuit(stored_circuit, [])

        assert list(h2_frontend.backends) == case.expected_registered_ports


class TestListenAddress:
    @pytest.fixture
    async def started_frontend_exec(
        self,
        case: _ListenAddressCase,
        root_context: MagicMock,
        mocker: pytest_mock.MockerFixture,
    ) -> AsyncIterator[AsyncMock]:
        root_context.local_config.proxy_worker.tls_listen = case.tls_listen
        root_context.local_config.proxy_worker.tls_cert = "/tls/cert.pem"
        root_context.local_config.proxy_worker.tls_privkey = "/tls/key.pem"
        nghttpx_stream = MagicMock(readline=AsyncMock(return_value=b""))
        create_subprocess_exec = mocker.patch(
            "ai.backend.appproxy.worker.proxy.frontend.h2.port.subprocess.create_subprocess_exec",
            AsyncMock(
                return_value=MagicMock(
                    stdout=nghttpx_stream, stderr=nghttpx_stream, wait=AsyncMock()
                )
            ),
        )
        frontend = PortFrontend(root_context)
        frontend.proc_monitor_tasks = []
        frontend.log_monitor_tasks = []
        await frontend.start()
        yield create_subprocess_exec
        await asyncio.gather(*frontend.proc_monitor_tasks, *frontend.log_monitor_tasks)

    @pytest.mark.parametrize(
        "case",
        [
            pytest.param(
                _ListenAddressCase(
                    tls_listen=False,
                    expected_frontend_argument=f"--frontend=192.0.2.1,{_LISTEN_PORT};no-tls",
                ),
                id="without_tls",
            ),
            pytest.param(
                _ListenAddressCase(
                    tls_listen=True,
                    expected_frontend_argument=f"--frontend=192.0.2.1,{_LISTEN_PORT}",
                ),
                id="with_tls",
            ),
        ],
    )
    async def test_nghttpx_listens_on_the_bind_host(
        self, case: _ListenAddressCase, started_frontend_exec: AsyncMock
    ) -> None:
        assert case.expected_frontend_argument in started_frontend_exec.call_args.args
