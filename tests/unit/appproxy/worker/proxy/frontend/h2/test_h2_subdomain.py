from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime
from unittest.mock import AsyncMock, call
from uuid import UUID

import aiohttp
import pytest
import pytest_mock
from yarl import URL

from ai.backend.appproxy.common.types import AppMode, FrontendMode, ProxyProtocol, RouteInfo
from ai.backend.appproxy.worker.proxy.backend.h2 import BackendConfig, H2Backend
from ai.backend.appproxy.worker.proxy.frontend.h2.subdomain import SubdomainFrontend
from ai.backend.appproxy.worker.types import Circuit, InteractiveAppInfo, SubdomainFrontendInfo

_SUBDOMAIN = "notebook"
_KERNEL_HOST = "10.0.0.5"
_KERNEL_PORT = 8080


@dataclass(frozen=True)
class _H2StartCase:
    name: str
    backend_registered: bool = True
    refused_api_requests: int = 0


@dataclass(frozen=True)
class _H2FrontendSituation:
    frontend: SubdomainFrontend
    circuit: Circuit
    update_config: AsyncMock


@pytest.fixture
async def h2_frontend_situation(
    mocker: pytest_mock.MockerFixture, case: _H2StartCase
) -> AsyncIterator[_H2FrontendSituation]:
    root_context = mocker.MagicMock()
    proxy_worker_config = root_context.local_config.proxy_worker
    proxy_worker_config.http2.api_port_pool = (20000, 20000)
    proxy_worker_config.tls_listen = False
    proxy_worker_config.wildcard_domain.bind_addr.host = "127.0.0.1"
    proxy_worker_config.wildcard_domain.bind_addr.port = 10250
    nghttpx_exited = asyncio.Event()
    nghttpx_stdout = asyncio.StreamReader()
    nghttpx_stdout.feed_eof()
    nghttpx_stderr = asyncio.StreamReader()
    nghttpx_stderr.feed_eof()
    nghttpx_process = mocker.MagicMock(
        stdout=nghttpx_stdout,
        stderr=nghttpx_stderr,
        wait=AsyncMock(side_effect=nghttpx_exited.wait),
    )
    mocker.patch(
        "ai.backend.appproxy.worker.proxy.frontend.h2.subdomain.subprocess.create_subprocess_exec",
        AsyncMock(return_value=nghttpx_process),
    )
    update_config = mocker.patch.object(
        H2Backend,
        "update_config",
        new_callable=AsyncMock,
        side_effect=[
            *(
                aiohttp.ClientConnectionError("nghttpx is not listening")
                for _ in range(case.refused_api_requests)
            ),
            None,
        ],
    )
    user_id = UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4")
    session_id = UUID("f5cd34ba-ae53-4537-a813-09f38496443d")
    circuit = Circuit(
        id=UUID("d0e6f60c-f375-4454-b4d3-e8ee202fa372"),
        app="jupyter",
        protocol=ProxyProtocol.HTTP2,
        worker=UUID("00000000-0000-0000-0000-000000000000"),
        app_mode=AppMode.INTERACTIVE,
        frontend_mode=FrontendMode.WILDCARD_DOMAIN,
        frontend=SubdomainFrontendInfo(_SUBDOMAIN),
        port=None,
        app_info=InteractiveAppInfo(user_id=user_id),
        subdomain=_SUBDOMAIN,
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
                kernel_host=_KERNEL_HOST,
                kernel_port=_KERNEL_PORT,
                protocol=ProxyProtocol.HTTP2,
                traffic_ratio=1.0,
            )
        ],
        session_ids=[session_id],
        created_at=datetime(2024, 7, 16, 5, 45, 45, tzinfo=UTC),
        updated_at=datetime(2024, 7, 16, 5, 45, 45, tzinfo=UTC),
    )
    frontend = SubdomainFrontend(root_context)
    if case.backend_registered:
        frontend.backends[_SUBDOMAIN] = H2Backend(
            URL(f"http://localhost:{frontend.api_port}"), root_context, circuit
        )
    yield _H2FrontendSituation(frontend=frontend, circuit=circuit, update_config=update_config)
    if frontend.proc_monitor_task is not None:
        frontend.proc_monitor_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await frontend.proc_monitor_task


class TestH2SubdomainFrontend:
    @pytest.mark.parametrize(
        "case",
        [_H2StartCase(name="nothing-registered", backend_registered=False)],
        ids=lambda case: case.name,
    )
    async def test_registering_a_circuit_before_start_sends_no_routes(
        self, case: _H2StartCase, h2_frontend_situation: _H2FrontendSituation
    ) -> None:
        situation = h2_frontend_situation
        await situation.frontend.register_circuit(situation.circuit, situation.circuit.route_info)
        situation.update_config.assert_not_awaited()

    @pytest.mark.parametrize(
        "case",
        [
            _H2StartCase(name="api-accepting-at-once"),
            _H2StartCase(name="api-refusing-twice", refused_api_requests=2),
        ],
        ids=lambda case: case.name,
    )
    async def test_start_sends_the_routes_of_backends_registered_before_it(
        self, case: _H2StartCase, h2_frontend_situation: _H2FrontendSituation
    ) -> None:
        situation = h2_frontend_situation
        await situation.frontend.start()
        assert situation.update_config.await_args_list[-1] == call([
            BackendConfig(_KERNEL_HOST, _KERNEL_PORT)
        ])
        assert situation.update_config.await_count == case.refused_api_requests + 1
