from collections.abc import Iterator

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request
from opentelemetry import trace
from opentelemetry.instrumentation.aiohttp_server import AioHttpServerInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from ai.backend.logging.otel import build_otel_server_middleware


async def _ok(request: web.Request) -> web.StreamResponse:
    return web.Response(text="ok")


class TestBuildOtelServerMiddleware:
    @pytest.fixture
    def span_exporter(self, monkeypatch: pytest.MonkeyPatch) -> Iterator[InMemorySpanExporter]:
        exporter = InMemorySpanExporter()
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        monkeypatch.setattr(trace, "get_tracer_provider", lambda: provider)
        instrumentor = AioHttpServerInstrumentor()
        instrumentor.instrument(tracer_provider=provider)
        yield exporter
        instrumentor.uninstrument()
        provider.shutdown()

    async def test_traces_request_with_provider_set_before_build(
        self, span_exporter: InMemorySpanExporter
    ) -> None:
        middleware = build_otel_server_middleware()

        response = await middleware(make_mocked_request("GET", "/"), _ok)

        assert response.status == 200
        spans = span_exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].kind == trace.SpanKind.SERVER
