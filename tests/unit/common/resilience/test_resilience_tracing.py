from __future__ import annotations

from opentelemetry import trace
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from ai.backend.common.resilience.policies.retry import RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience


class _Repository:
    call_count: int

    def __init__(self) -> None:
        self.call_count = 0

    @Resilience(policies=[RetryPolicy(RetryArgs(max_retries=3, retry_delay=0.0))]).apply()
    async def fetch(self) -> str:
        self.call_count += 1
        if self.call_count < 3:
            raise ConnectionError("transient")
        return "fetched"


class TestResilienceTracing:
    async def test_no_span_without_parent(self, span_exporter: InMemorySpanExporter) -> None:
        repository = _Repository()

        assert await repository.fetch() == "fetched"

        assert span_exporter.get_finished_spans() == ()

    async def test_child_span_under_parent(self, span_exporter: InMemorySpanExporter) -> None:
        repository = _Repository()

        with trace.get_tracer(__name__).start_as_current_span("parent") as parent:
            assert await repository.fetch() == "fetched"

        spans = {span.name: span for span in span_exporter.get_finished_spans()}
        child = spans["_Repository.fetch"]
        assert child.parent is not None
        assert child.parent.span_id == parent.get_span_context().span_id

    async def test_retries_share_one_span(self, span_exporter: InMemorySpanExporter) -> None:
        repository = _Repository()

        with trace.get_tracer(__name__).start_as_current_span("parent"):
            await repository.fetch()

        names = [span.name for span in span_exporter.get_finished_spans()]
        assert repository.call_count == 3
        assert names.count("_Repository.fetch") == 1
