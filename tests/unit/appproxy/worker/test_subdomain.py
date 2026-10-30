from __future__ import annotations

import gzip
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

import aiohttp
import pytest
import pytest_mock
from aiohttp import web

from ai.backend.appproxy.common.types import (
    AppMode,
    FrontendMode,
    ProxyProtocol,
    RouteInfo,
)
from ai.backend.appproxy.worker.ingress.factory import IngressState
from ai.backend.appproxy.worker.ingress.in_memory import InMemoryIngressState
from ai.backend.appproxy.worker.ingress.layered import LayeredIngressState
from ai.backend.appproxy.worker.proxy.frontend.http.subdomain import SubdomainFrontend
from ai.backend.appproxy.worker.types import Circuit, InferenceAppInfo, SubdomainFrontendInfo
from ai.backend.common.dto.appproxy.v2.ingress.types import IngressAuthority
from ai.backend.common.types import RuntimeVariant

_AUTHORITY = IngressAuthority("worker-1")
_WILDCARD_DOMAIN = ".apps.example.com"
_SUBDOMAIN = "echo"
_GZIP_REQUEST_BODY = gzip.compress(b'{"data": "' + b"a" * 1000 + b'"}')


@dataclass(frozen=True)
class _ServingSubdomainFrontend:
    port: int
    bodies_received_by_backend: list[bytes]


@pytest.fixture
async def serving_subdomain_frontend(
    mocker: pytest_mock.MockerFixture,
    unused_tcp_port: int,
) -> AsyncIterator[_ServingSubdomainFrontend]:
    root_context = mocker.MagicMock()
    proxy_worker_config = root_context.local_config.proxy_worker
    proxy_worker_config.tls_listen = False
    proxy_worker_config.trusted_proxies = []
    proxy_worker_config.max_header_field_size = 8190
    proxy_worker_config.wildcard_domain.bind_addr.host = "127.0.0.1"
    proxy_worker_config.wildcard_domain.bind_addr.port = unused_tcp_port
    proxy_worker_config.wildcard_domain.domain = _WILDCARD_DOMAIN
    bodies_received_by_backend: list[bytes] = []

    async def record_request_body(request: web.Request) -> web.Response:
        bodies_received_by_backend.append(await request.read())
        return web.Response()

    circuit = Circuit(
        id=UUID("d0e6f60c-f375-4454-b4d3-e8ee202fa372"),
        app="vllm",
        protocol=ProxyProtocol.HTTP,
        worker=UUID("00000000-0000-0000-0000-000000000000"),
        app_mode=AppMode.INTERACTIVE,
        frontend_mode=FrontendMode.WILDCARD_DOMAIN,
        frontend=SubdomainFrontendInfo(_SUBDOMAIN),
        port=None,
        app_info=InferenceAppInfo(
            endpoint_id=UUID("b9567a3b-3ca1-4d8f-b8eb-a9567073808d"),
            runtime_variant=RuntimeVariant("vllm"),
        ),
        subdomain=_SUBDOMAIN,
        runtime_variant=RuntimeVariant("vllm"),
        envs={},
        arguments=None,
        open_to_public=True,
        allowed_client_ips=None,
        user_id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
        access_key="AKIAIOSFODNN7EXAMPLE",
        endpoint_id=None,
        route_info=[
            RouteInfo(
                route_id=UUID("4eeb260b-6cc5-4362-baf3-ea978388becd"),
                session_id=UUID("f5cd34ba-ae53-4537-a813-09f38496443d"),
                session_name=None,
                kernel_host="127.0.0.1",
                kernel_port=30729,
                protocol=ProxyProtocol.HTTP,
                traffic_ratio=1.0,
            )
        ],
        session_ids=[UUID("f5cd34ba-ae53-4537-a813-09f38496443d")],
        created_at=datetime(2024, 7, 16, 5, 45, 45, 982446, tzinfo=UTC),
        updated_at=datetime(2024, 7, 16, 5, 45, 45, 982452, tzinfo=UTC),
    )
    in_memory = InMemoryIngressState()
    await in_memory.apply([circuit.to_ingress(_AUTHORITY)])
    root_context.ingress_state = IngressState(
        reader=LayeredIngressState([in_memory], in_memory=in_memory), writer=None
    )
    frontend = SubdomainFrontend(root_context=root_context)
    frontend.backends = {
        _SUBDOMAIN: mocker.MagicMock(proxy_http=record_request_body, circuit=circuit)
    }
    await frontend.start()
    yield _ServingSubdomainFrontend(
        port=unused_tcp_port,
        bodies_received_by_backend=bodies_received_by_backend,
    )
    await frontend.stop()


class TestSubdomainFrontend:
    async def test_proxy_passes_compressed_request_body_as_received(
        self,
        serving_subdomain_frontend: _ServingSubdomainFrontend,
    ) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://127.0.0.1:{serving_subdomain_frontend.port}/",
                data=_GZIP_REQUEST_BODY,
                headers={
                    "Host": f"{_SUBDOMAIN}{_WILDCARD_DOMAIN}:{serving_subdomain_frontend.port}",
                    "Content-Encoding": "gzip",
                },
            ) as response:
                assert response.status == 200

        assert serving_subdomain_frontend.bodies_received_by_backend == [_GZIP_REQUEST_BODY]
