import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import aiohttp
import pytest
from aiohttp import web
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import SpanKind, StatusCode

from ai.backend.logging.otel import build_otel_server_middleware

type ClientFactory = Callable[[web.Application], Awaitable[Any]]


async def _ok(_request: web.Request) -> web.Response:
    return web.Response(text="ok")


async def _fail(_request: web.Request) -> web.Response:
    raise web.HTTPServiceUnavailable()


async def _static(_request: web.Request) -> web.Response:
    return web.Response(text="asset")


@pytest.fixture
def app() -> web.Application:
    app = web.Application(middlewares=[build_otel_server_middleware(untraced_handlers={_static})])
    app.router.add_get("/health", _ok)
    app.router.add_get("/health/readyz", _ok)
    app.router.add_get("/metrics", _ok)
    app.router.add_get("/domains/{name}", _ok)
    app.router.add_get("/broken", _fail)
    app.router.add_get("/{path:.*$}", _static)
    return app


class TestOtelServerMiddleware:
    async def test_request_span_uses_route_and_status(
        self,
        app: web.Application,
        aiohttp_client: ClientFactory,
        span_exporter: InMemorySpanExporter,
    ) -> None:
        client = await aiohttp_client(app)
        response = await client.get("/domains/default")
        assert response.status == 200

        (span,) = span_exporter.get_finished_spans()
        assert span.name == "GET /domains/{name}"
        assert span.kind == SpanKind.SERVER
        assert span.attributes is not None
        assert span.attributes["http.response.status_code"] == 200
        assert span.attributes["url.path"] == "/domains/default"
        assert span.status.status_code == StatusCode.UNSET

    async def test_server_error_marks_span_error(
        self,
        app: web.Application,
        aiohttp_client: ClientFactory,
        span_exporter: InMemorySpanExporter,
    ) -> None:
        client = await aiohttp_client(app)
        response = await client.get("/broken")
        assert response.status == 503

        (span,) = span_exporter.get_finished_spans()
        assert span.attributes is not None
        assert span.attributes["http.response.status_code"] == 503
        assert span.status.status_code == StatusCode.ERROR

    async def test_incoming_traceparent_becomes_parent(
        self,
        app: web.Application,
        aiohttp_client: ClientFactory,
        span_exporter: InMemorySpanExporter,
    ) -> None:
        trace_id = "0af7651916cd43dd8448eb211c80319c"
        parent_span_id = "b7ad6b7169203331"
        client = await aiohttp_client(app)
        await client.get(
            "/domains/default",
            headers={"traceparent": f"00-{trace_id}-{parent_span_id}-01"},
        )

        (span,) = span_exporter.get_finished_spans()
        assert format(span.context.trace_id, "032x") == trace_id
        assert span.parent is not None
        assert format(span.parent.span_id, "016x") == parent_span_id

    @pytest.mark.parametrize("path", ["/health", "/health/readyz", "/metrics", "/assets/main.js"])
    async def test_untraced_paths_create_no_span(
        self,
        app: web.Application,
        aiohttp_client: ClientFactory,
        span_exporter: InMemorySpanExporter,
        path: str,
    ) -> None:
        client = await aiohttp_client(app)
        response = await client.get(path)
        assert response.status == 200

        assert span_exporter.get_finished_spans() == ()


class TestParentRequiredPrefixes:
    @pytest.fixture
    def internal_app(self) -> web.Application:
        app = web.Application(
            middlewares=[build_otel_server_middleware(parent_required_prefixes=("/api/",))]
        )
        app.router.add_patch("/api/worker/{worker_id}", _ok)
        app.router.add_get("/v2/proxy/auth", _ok)
        return app

    async def test_request_without_parent_creates_no_span(
        self,
        internal_app: web.Application,
        aiohttp_client: ClientFactory,
        span_exporter: InMemorySpanExporter,
    ) -> None:
        client = await aiohttp_client(internal_app)
        await client.patch("/api/worker/w-1")

        assert span_exporter.get_finished_spans() == ()

    async def test_request_with_parent_is_traced(
        self,
        internal_app: web.Application,
        aiohttp_client: ClientFactory,
        span_exporter: InMemorySpanExporter,
    ) -> None:
        client = await aiohttp_client(internal_app)
        await client.patch(
            "/api/worker/w-1",
            headers={"traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"},
        )

        (span,) = span_exporter.get_finished_spans()
        assert span.name == "PATCH /api/worker/{worker_id}"

    async def test_other_paths_are_traced_without_parent(
        self,
        internal_app: web.Application,
        aiohttp_client: ClientFactory,
        span_exporter: InMemorySpanExporter,
    ) -> None:
        client = await aiohttp_client(internal_app)
        await client.get("/v2/proxy/auth")

        (span,) = span_exporter.get_finished_spans()
        assert span.name == "GET /v2/proxy/auth"


async def _crash(_request: web.Request) -> web.Response:
    raise RuntimeError("crash")


async def _cancelled(_request: web.Request) -> web.Response:
    raise asyncio.CancelledError()


class TestFailedRequests:
    @pytest.fixture
    def failing_app(self) -> web.Application:
        app = web.Application(middlewares=[build_otel_server_middleware()])
        app.router.add_get("/crash", _crash)
        app.router.add_get("/cancelled", _cancelled)
        return app

    async def test_unmatched_route_has_a_fixed_span_name(
        self,
        failing_app: web.Application,
        aiohttp_client: ClientFactory,
        span_exporter: InMemorySpanExporter,
    ) -> None:
        client = await aiohttp_client(failing_app)
        response = await client.get("/scanner/probe-123")
        assert response.status == 404

        (span,) = span_exporter.get_finished_spans()
        assert span.name == "GET <unmatched>"
        assert span.attributes is not None
        assert span.attributes["http.response.status_code"] == 404

    async def test_unhandled_exception_is_a_server_error(
        self,
        failing_app: web.Application,
        aiohttp_client: ClientFactory,
        span_exporter: InMemorySpanExporter,
    ) -> None:
        client = await aiohttp_client(failing_app)
        response = await client.get("/crash")
        assert response.status == 500

        (span,) = span_exporter.get_finished_spans()
        assert span.status.status_code == StatusCode.ERROR
        assert span.attributes is not None
        assert span.attributes["http.response.status_code"] == 500
        assert [event.name for event in span.events] == ["exception"]

    async def test_cancelled_request_records_no_status(
        self,
        failing_app: web.Application,
        aiohttp_client: ClientFactory,
        span_exporter: InMemorySpanExporter,
    ) -> None:
        client = await aiohttp_client(failing_app)
        with pytest.raises(aiohttp.ClientError):
            await client.get("/cancelled")

        (span,) = span_exporter.get_finished_spans()
        assert span.status.status_code == StatusCode.UNSET
        assert span.attributes is not None
        assert "http.response.status_code" not in span.attributes
        assert span.events == ()
