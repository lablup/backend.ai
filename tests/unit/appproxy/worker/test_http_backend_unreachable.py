from __future__ import annotations

import asyncio
import importlib.resources
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import aiohttp
import aiohttp_jinja2
import jinja2
import pytest
import pytest_mock
from aiohttp import web
from aiohttp.test_utils import make_mocked_request

from ai.backend.appproxy.common.errors import WorkerNotAvailable
from ai.backend.appproxy.common.types import AppMode, FrontendMode, ProxyProtocol, RouteInfo
from ai.backend.appproxy.worker.proxy.backend.http import HTTPBackend
from ai.backend.appproxy.worker.proxy.frontend.http.port import PortFrontend
from ai.backend.appproxy.worker.types import Circuit, InteractiveAppInfo, PortFrontendInfo

SESSION_ID = UUID("f5cd34ba-ae53-4537-a813-09f38496443d")
KERNEL_HOST = "10.20.30.40"
KERNEL_PORT = 30123


def _create_circuit(app: str = "jupyter", open_to_public: bool = False) -> Circuit:
    user_id = UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4")
    return Circuit(
        id=UUID("d0e6f60c-f375-4454-b4d3-e8ee202fa372"),
        app=app,
        protocol=ProxyProtocol.HTTP,
        worker=UUID("00000000-0000-0000-0000-000000000000"),
        app_mode=AppMode.INTERACTIVE,
        frontend_mode=FrontendMode.PORT,
        frontend=PortFrontendInfo(10200),
        port=10200,
        app_info=InteractiveAppInfo(user_id=user_id),
        subdomain=None,
        runtime_variant=None,
        envs={},
        arguments=None,
        open_to_public=open_to_public,
        allowed_client_ips=None,
        user_id=user_id,
        access_key="AKIAIOSFODNN7EXAMPLE",
        endpoint_id=None,
        route_info=[
            RouteInfo(
                route_id=UUID("4eeb260b-6cc5-4362-baf3-ea978388becd"),
                session_id=SESSION_ID,
                session_name=None,
                kernel_host=KERNEL_HOST,
                kernel_port=KERNEL_PORT,
                protocol=ProxyProtocol.HTTP,
                traffic_ratio=1.0,
            )
        ],
        session_ids=[SESSION_ID],
        created_at=datetime(2024, 7, 16, 5, 45, 45, 982446, tzinfo=UTC),
        updated_at=datetime(2024, 7, 16, 5, 45, 45, 982452, tzinfo=UTC),
    )


class TestHTTPBackendUnreachableUpstream:
    @pytest.fixture
    def root_ctx(self) -> MagicMock:
        root_ctx = MagicMock()
        root_ctx.last_used_time_marker_redis_queue = asyncio.Queue()
        root_ctx.request_counter_redis_queue = asyncio.Queue()
        return root_ctx

    @pytest.fixture
    async def backend(
        self, mocker: pytest_mock.MockerFixture, root_ctx: MagicMock
    ) -> AsyncIterator[HTTPBackend]:
        mocker.patch(
            "ai.backend.appproxy.worker.proxy.backend.http.ClientPool",
            return_value=mocker.MagicMock(close=mocker.AsyncMock()),
        )
        circuit = _create_circuit()
        backend = HTTPBackend(circuit.route_info, root_ctx, circuit)
        try:
            yield backend
        finally:
            await backend.close()

    def _request(self, accept: str | None = None) -> web.Request:
        app = web.Application()
        with importlib.resources.as_file(
            importlib.resources.files("ai.backend.appproxy.common")
        ) as f:
            aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(f / "templates"))
        headers = {"Accept": accept} if accept else {}
        return make_mocked_request(method="GET", path="/", headers=headers, app=app)

    async def _render(
        self, root_ctx: MagicMock, backend: HTTPBackend, request: web.Request
    ) -> web.StreamResponse:
        frontend = PortFrontend(root_ctx)
        return await frontend.exception_safe_handler_wrapper(request, backend.proxy_http)

    @pytest.mark.parametrize(
        "error",
        [
            aiohttp.ClientConnectorError(MagicMock(host=KERNEL_HOST, port=KERNEL_PORT), OSError()),
            aiohttp.ClientOSError(111, "Connection refused"),
            aiohttp.ConnectionTimeoutError("connect timeout"),
            TimeoutError(),
        ],
    )
    async def test_unreachable_upstream_returns_502_page(
        self,
        mocker: pytest_mock.MockerFixture,
        root_ctx: MagicMock,
        backend: HTTPBackend,
        error: Exception,
    ) -> None:
        mocker.patch.object(backend, "request_http", side_effect=error)
        record_failure = mocker.patch.object(backend._pool, "record_failure")

        response = await self._render(root_ctx, backend, self._request())

        assert isinstance(response, web.Response)
        assert response.status == 502
        assert response.content_type == "text/html"
        body = response.text or ""
        assert "jupyter" in body
        assert "not reachable" in body
        assert str(SESSION_ID) in body
        assert KERNEL_HOST not in body
        assert str(KERNEL_PORT) not in body
        record_failure.assert_called_once()

    async def test_json_client_gets_json_502(
        self,
        mocker: pytest_mock.MockerFixture,
        root_ctx: MagicMock,
        backend: HTTPBackend,
    ) -> None:
        mocker.patch.object(
            backend, "request_http", side_effect=aiohttp.ClientOSError(111, "refused")
        )

        response = await self._render(root_ctx, backend, self._request(accept="application/json"))

        assert isinstance(response, web.Response)
        assert response.status == 502
        assert response.headers["Access-Control-Allow-Origin"] == "*"
        text = response.text or ""
        assert "not reachable" in json.loads(text)["msg"]
        assert KERNEL_HOST not in text
        assert str(KERNEL_PORT) not in text

    async def test_no_healthy_route_returns_502(
        self,
        mocker: pytest_mock.MockerFixture,
        root_ctx: MagicMock,
        backend: HTTPBackend,
    ) -> None:
        mocker.patch.object(backend._pool, "select", side_effect=WorkerNotAvailable)

        response = await self._render(root_ctx, backend, self._request())

        assert response.status == 502
        assert "not reachable" in (getattr(response, "text", "") or "")

    async def test_message_omits_session_clause_without_sessions(
        self,
        mocker: pytest_mock.MockerFixture,
        root_ctx: MagicMock,
        backend: HTTPBackend,
    ) -> None:
        backend.circuit = _create_circuit().model_copy(update={"session_ids": []})
        mocker.patch.object(backend._pool, "select", side_effect=WorkerNotAvailable)

        response = await self._render(root_ctx, backend, self._request())

        body = getattr(response, "text", "") or ""
        assert response.status == 502
        assert "not reachable" in body
        assert "of session" not in body
        assert "&#34;jupyter&#34; is not reachable." in body

    @pytest.mark.parametrize("accept", [None, "application/json"])
    async def test_public_circuit_shows_no_session_id(
        self,
        mocker: pytest_mock.MockerFixture,
        root_ctx: MagicMock,
        backend: HTTPBackend,
        accept: str | None,
    ) -> None:
        backend.circuit = _create_circuit(open_to_public=True)
        mocker.patch.object(
            backend, "request_http", side_effect=aiohttp.ClientOSError(111, "refused")
        )

        response = await self._render(root_ctx, backend, self._request(accept=accept))

        body = getattr(response, "text", "") or ""
        assert response.status == 502
        assert "temporarily unreachable" in body
        assert "jupyter" in body
        assert str(SESSION_ID) not in body
        assert KERNEL_HOST not in body
        assert str(KERNEL_PORT) not in body

    async def test_pool_marks_route_unhealthy_then_still_502(
        self,
        mocker: pytest_mock.MockerFixture,
        root_ctx: MagicMock,
        backend: HTTPBackend,
    ) -> None:
        mocker.patch.object(
            backend, "request_http", side_effect=aiohttp.ClientOSError(111, "refused")
        )

        statuses = [
            (await self._render(root_ctx, backend, self._request())).status for _ in range(5)
        ]

        assert statuses == [502] * 5

    async def test_app_name_is_escaped(
        self,
        mocker: pytest_mock.MockerFixture,
        root_ctx: MagicMock,
        backend: HTTPBackend,
    ) -> None:
        backend.circuit = _create_circuit(app="<script>x</script>")
        mocker.patch.object(
            backend, "request_http", side_effect=aiohttp.ClientOSError(111, "refused")
        )

        response = await self._render(root_ctx, backend, self._request())

        body = getattr(response, "text", "") or ""
        assert "<script>" not in body
        assert "&lt;script&gt;" in body

    async def test_failure_after_prepare_is_not_replaced_by_error_page(
        self,
        mocker: pytest_mock.MockerFixture,
        backend: HTTPBackend,
    ) -> None:
        upstream = MagicMock()
        upstream.status = 200
        upstream.reason = "OK"
        upstream.headers = {"Content-Length": "2"}

        async def _chunks() -> AsyncIterator[bytes]:
            yield b"ok"
            raise aiohttp.ClientOSError(104, "reset")

        upstream.content.iter_any = _chunks

        @asynccontextmanager
        async def _request_http(*args: Any, **kwargs: Any) -> AsyncIterator[MagicMock]:
            yield upstream

        mocker.patch.object(backend, "request_http", _request_http)
        mocker.patch.object(web.StreamResponse, "prepare", AsyncMock())
        mocker.patch.object(web.StreamResponse, "write", AsyncMock())
        mocker.patch.object(web.StreamResponse, "write_eof", AsyncMock())
        mocker.patch.object(
            web.StreamResponse, "prepared", new_callable=mocker.PropertyMock, return_value=True
        )

        with pytest.raises(aiohttp.ClientOSError):
            await backend.proxy_http(self._request())

    async def test_successful_proxy_is_unchanged(
        self,
        mocker: pytest_mock.MockerFixture,
        backend: HTTPBackend,
    ) -> None:
        upstream = MagicMock()
        upstream.status = 200
        upstream.reason = "OK"
        upstream.headers = {"Content-Length": "2"}
        upstream.content_length = 2

        async def _chunks() -> AsyncIterator[bytes]:
            yield b"ok"

        upstream.content.iter_any = _chunks

        @asynccontextmanager
        async def _request_http(*args: Any, **kwargs: Any) -> AsyncIterator[MagicMock]:
            yield upstream

        mocker.patch.object(backend, "request_http", _request_http)
        record_failure = mocker.patch.object(backend._pool, "record_failure")
        record_success = mocker.patch.object(backend._pool, "record_success")
        request = self._request()
        mocker.patch.object(web.StreamResponse, "prepare", AsyncMock())
        mocker.patch.object(web.StreamResponse, "write", AsyncMock())
        mocker.patch.object(web.StreamResponse, "write_eof", AsyncMock())

        response = await backend.proxy_http(request)

        assert response.status == 200
        record_success.assert_called_once()
        record_failure.assert_not_called()
