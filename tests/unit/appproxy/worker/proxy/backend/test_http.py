from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass
from typing import cast
from unittest.mock import MagicMock
from uuid import UUID

import pytest
import pytest_mock
from aiohttp.test_utils import make_mocked_request

from ai.backend.appproxy.common.types import ProxyProtocol, RouteInfo
from ai.backend.appproxy.worker.proxy.backend.http import HTTPBackend

_FORGED_HEADERS = {
    "Forwarded": "host=forged.example.com;proto=https",
    "X-Forwarded-For": "192.0.2.1",
    "X-Forwarded-Host": "forged.example.com",
    "X-Forwarded-Port": "1",
    "X-Forwarded-Proto": "https",
    "X-RStudio-Proto": "https",
    "X-RStudio-Request": "https://forged.example.com/",
}


class _BackendRequestCaptured(Exception):
    pass


@dataclass(frozen=True)
class _ForwardedHeaders:
    forwarded: str | None
    x_forwarded_for: str | None
    x_forwarded_host: str | None
    x_forwarded_port: str | None
    x_forwarded_proto: str | None
    x_rstudio_proto: str | None
    x_rstudio_request: str | None


@dataclass(frozen=True)
class _ForwardedHeadersCase:
    trusted_proxies: list[str]
    tls_advertised: bool
    app: str
    request_headers: Mapping[str, str]
    expected_headers: _ForwardedHeaders


class TestProxyHttpForwardedHeaders:
    @pytest.fixture
    async def http_backend(
        self, case: _ForwardedHeadersCase, mocker: pytest_mock.MockerFixture
    ) -> AsyncIterator[HTTPBackend]:
        mocker.patch(
            "ai.backend.appproxy.worker.proxy.backend.http.ClientPool",
            return_value=mocker.MagicMock(close=mocker.AsyncMock()),
        )
        root_context = MagicMock()
        root_context.last_used_time_marker_redis_queue = asyncio.Queue()
        root_context.request_counter_redis_queue = asyncio.Queue()
        worker_config = root_context.local_config.proxy_worker
        worker_config.trusted_proxies = case.trusted_proxies
        worker_config.tls_advertised = case.tls_advertised
        worker_config.tls_listen = False
        route = RouteInfo(
            route_id=UUID("4eeb260b-6cc5-4362-baf3-ea978388becd"),
            session_id=UUID("f5cd34ba-ae53-4537-a813-09f38496443d"),
            session_name=None,
            kernel_host="10.0.0.1",
            kernel_port=8000,
            protocol=ProxyProtocol.HTTP,
            traffic_ratio=1.0,
        )
        backend = HTTPBackend([route], root_context, MagicMock(app=case.app))
        mocker.patch.object(backend, "request_http", side_effect=_BackendRequestCaptured)
        try:
            yield backend
        finally:
            await backend.close()

    @pytest.mark.parametrize(
        "case",
        [
            pytest.param(
                _ForwardedHeadersCase(
                    trusted_proxies=[],
                    tls_advertised=False,
                    app="jupyter",
                    request_headers={"Host": "app.example.com", **_FORGED_HEADERS},
                    expected_headers=_ForwardedHeaders(
                        forwarded="host=app.example.com;proto=http",
                        x_forwarded_for=None,
                        x_forwarded_host="app.example.com",
                        x_forwarded_port=None,
                        x_forwarded_proto="http",
                        x_rstudio_proto=None,
                        x_rstudio_request=None,
                    ),
                ),
                id="without_trusted_proxies_forged_headers_are_replaced",
            ),
            pytest.param(
                _ForwardedHeadersCase(
                    trusted_proxies=[],
                    tls_advertised=False,
                    app="rstudio",
                    request_headers={"Host": "app.example.com", **_FORGED_HEADERS},
                    expected_headers=_ForwardedHeaders(
                        forwarded="host=app.example.com;proto=http",
                        x_forwarded_for=None,
                        x_forwarded_host="app.example.com",
                        x_forwarded_port=None,
                        x_forwarded_proto="http",
                        x_rstudio_proto="http",
                        x_rstudio_request="http://app.example.com/",
                    ),
                ),
                id="without_trusted_proxies_rstudio_headers_use_the_host_header",
            ),
            pytest.param(
                _ForwardedHeadersCase(
                    trusted_proxies=[],
                    tls_advertised=True,
                    app="jupyter",
                    request_headers={"Host": "app.example.com:8443"},
                    expected_headers=_ForwardedHeaders(
                        forwarded="host=app.example.com:8443;proto=https",
                        x_forwarded_for=None,
                        x_forwarded_host="app.example.com:8443",
                        x_forwarded_port="8443",
                        x_forwarded_proto="https",
                        x_rstudio_proto=None,
                        x_rstudio_request=None,
                    ),
                ),
                id="without_trusted_proxies_proto_comes_from_the_tls_config",
            ),
            pytest.param(
                _ForwardedHeadersCase(
                    trusted_proxies=[],
                    tls_advertised=False,
                    app="rstudio",
                    request_headers=_FORGED_HEADERS,
                    expected_headers=_ForwardedHeaders(
                        forwarded=None,
                        x_forwarded_for=None,
                        x_forwarded_host=None,
                        x_forwarded_port=None,
                        x_forwarded_proto="http",
                        x_rstudio_proto="http",
                        x_rstudio_request=None,
                    ),
                ),
                id="without_a_host_header_forged_headers_are_dropped",
            ),
            pytest.param(
                _ForwardedHeadersCase(
                    trusted_proxies=["10.0.0.0/8"],
                    tls_advertised=False,
                    app="jupyter",
                    request_headers={
                        "Host": "worker.internal",
                        "X-Forwarded-Host": "app.example.com",
                        "X-Forwarded-Proto": "https",
                    },
                    expected_headers=_ForwardedHeaders(
                        forwarded="host=app.example.com;proto=https",
                        x_forwarded_for=None,
                        x_forwarded_host="app.example.com",
                        x_forwarded_port=None,
                        x_forwarded_proto="https",
                        x_rstudio_proto=None,
                        x_rstudio_request=None,
                    ),
                ),
                id="with_trusted_proxies_forwarded_values_are_used",
            ),
            pytest.param(
                _ForwardedHeadersCase(
                    trusted_proxies=["10.0.0.0/8"],
                    tls_advertised=True,
                    app="jupyter",
                    request_headers={"Host": "worker.internal"},
                    expected_headers=_ForwardedHeaders(
                        forwarded="host=worker.internal;proto=https",
                        x_forwarded_for=None,
                        x_forwarded_host="worker.internal",
                        x_forwarded_port=None,
                        x_forwarded_proto="https",
                        x_rstudio_proto=None,
                        x_rstudio_request=None,
                    ),
                ),
                id="with_trusted_proxies_missing_values_fall_back",
            ),
        ],
    )
    async def test_headers_sent_to_the_session_app(
        self, case: _ForwardedHeadersCase, http_backend: HTTPBackend
    ) -> None:
        frontend_request = make_mocked_request("GET", "/", headers=case.request_headers)

        with pytest.raises(_BackendRequestCaptured):
            await http_backend.proxy_http(frontend_request)

        request_http = cast(MagicMock, http_backend.request_http)
        sent_headers = request_http.call_args.args[1].headers
        assert (
            _ForwardedHeaders(
                forwarded=sent_headers.get("Forwarded"),
                x_forwarded_for=sent_headers.get("X-Forwarded-For"),
                x_forwarded_host=sent_headers.get("X-Forwarded-Host"),
                x_forwarded_port=sent_headers.get("X-Forwarded-Port"),
                x_forwarded_proto=sent_headers.get("X-Forwarded-Proto"),
                x_rstudio_proto=sent_headers.get("X-RStudio-Proto"),
                x_rstudio_request=sent_headers.get("X-RStudio-Request"),
            )
            == case.expected_headers
        )
