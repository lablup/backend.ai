"""Tests for GQLMetricMiddleware metrics and OpenTelemetry span instrumentation."""

from __future__ import annotations

import asyncio
from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock

import pytest
from graphql import OperationType
from graphql.type import GraphQLNonNull, GraphQLObjectType, GraphQLString
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode

from ai.backend.common.exception import (
    ErrorCode,
    InvalidAPIParameters,
)
from ai.backend.manager.api.gql_legacy.schema import GQLMetricMiddleware


@pytest.fixture
def metric_observer() -> MagicMock:
    observer = MagicMock()
    observer.observe_request = MagicMock()
    return observer


@pytest.fixture
def resolve_info(metric_observer: MagicMock) -> MagicMock:
    info = MagicMock()
    info.context.metric_observer = metric_observer
    info.operation.operation = OperationType.QUERY
    info.operation.name.value = "TestQuery"
    info.field_name = "test_field"
    info.parent_type.name = "Query"
    return info


@pytest.fixture
def middleware() -> GQLMetricMiddleware:
    return GQLMetricMiddleware()


class TestGQLMetricMiddlewareSyncResolver:
    """Tests for sync resolver timing in GQLMetricMiddleware."""

    def test_sync_resolver_records_timing(
        self,
        middleware: GQLMetricMiddleware,
        resolve_info: MagicMock,
        metric_observer: MagicMock,
    ) -> None:
        def sync_resolver(root: Any, info: Any, **kwargs: Any) -> str:
            return "sync_result"

        result = middleware.resolve(sync_resolver, None, resolve_info)

        assert result == "sync_result"
        metric_observer.observe_request.assert_called_once()
        call_kwargs = metric_observer.observe_request.call_args.kwargs
        assert call_kwargs["success"] is True
        assert call_kwargs["error_code"] is None
        assert call_kwargs["duration"] >= 0
        assert call_kwargs["field_name"] == "test_field"
        assert call_kwargs["parent_type"] == "Query"
        assert call_kwargs["operation_name"] == "TestQuery"

    def test_sync_resolver_backend_ai_error(
        self,
        middleware: GQLMetricMiddleware,
        resolve_info: MagicMock,
        metric_observer: MagicMock,
    ) -> None:
        error = InvalidAPIParameters("test error")

        def sync_resolver(root: Any, info: Any, **kwargs: Any) -> str:
            raise error

        with pytest.raises(InvalidAPIParameters):
            middleware.resolve(sync_resolver, None, resolve_info)

        metric_observer.observe_request.assert_called_once()
        call_kwargs = metric_observer.observe_request.call_args.kwargs
        assert call_kwargs["success"] is False
        assert call_kwargs["error_code"] == error.error_code()

    def test_sync_resolver_generic_exception(
        self,
        middleware: GQLMetricMiddleware,
        resolve_info: MagicMock,
        metric_observer: MagicMock,
    ) -> None:
        def sync_resolver(root: Any, info: Any, **kwargs: Any) -> str:
            raise RuntimeError("unexpected")

        with pytest.raises(RuntimeError):
            middleware.resolve(sync_resolver, None, resolve_info)

        metric_observer.observe_request.assert_called_once()
        call_kwargs = metric_observer.observe_request.call_args.kwargs
        assert call_kwargs["success"] is False
        assert call_kwargs["error_code"] == ErrorCode.default()

    def test_sync_resolver_anonymous_operation(
        self,
        middleware: GQLMetricMiddleware,
        resolve_info: MagicMock,
        metric_observer: MagicMock,
    ) -> None:
        resolve_info.operation.name = None

        def sync_resolver(root: Any, info: Any, **kwargs: Any) -> str:
            return "result"

        middleware.resolve(sync_resolver, None, resolve_info)

        call_kwargs = metric_observer.observe_request.call_args.kwargs
        assert call_kwargs["operation_name"] == "anonymous"


class TestGQLMetricMiddlewareAsyncAnonymousOperation:
    """Tests for anonymous operation handling with async resolvers."""

    async def test_async_resolver_anonymous_operation(
        self,
        middleware: GQLMetricMiddleware,
        resolve_info: MagicMock,
        metric_observer: MagicMock,
    ) -> None:
        resolve_info.operation.name = None

        async def async_resolver(root: Any, info: Any, **kwargs: Any) -> str:
            return "result"

        await middleware.resolve(async_resolver, None, resolve_info)

        call_kwargs = metric_observer.observe_request.call_args.kwargs
        assert call_kwargs["operation_name"] == "anonymous"


class TestGQLMetricMiddlewareAsyncResolver:
    """Tests for async resolver timing in GQLMetricMiddleware."""

    async def test_async_resolver_records_actual_execution_time(
        self,
        middleware: GQLMetricMiddleware,
        resolve_info: MagicMock,
        metric_observer: MagicMock,
    ) -> None:
        sleep_duration = 0.05

        async def async_resolver(root: Any, info: Any, **kwargs: Any) -> str:
            await asyncio.sleep(sleep_duration)
            return "async_result"

        result_coro = middleware.resolve(async_resolver, None, resolve_info)

        # observe_request should NOT have been called yet (before await)
        metric_observer.observe_request.assert_not_called()

        assert asyncio.iscoroutine(result_coro)
        result = await result_coro

        assert result == "async_result"
        metric_observer.observe_request.assert_called_once()
        call_kwargs = metric_observer.observe_request.call_args.kwargs
        assert call_kwargs["success"] is True
        assert call_kwargs["error_code"] is None
        assert call_kwargs["duration"] >= sleep_duration * 0.8

    async def test_async_resolver_backend_ai_error(
        self,
        middleware: GQLMetricMiddleware,
        resolve_info: MagicMock,
        metric_observer: MagicMock,
    ) -> None:
        error = InvalidAPIParameters("async test error")

        async def async_resolver(root: Any, info: Any, **kwargs: Any) -> str:
            raise error

        result_coro = middleware.resolve(async_resolver, None, resolve_info)
        assert asyncio.iscoroutine(result_coro)

        with pytest.raises(InvalidAPIParameters):
            await result_coro

        metric_observer.observe_request.assert_called_once()
        call_kwargs = metric_observer.observe_request.call_args.kwargs
        assert call_kwargs["success"] is False
        assert call_kwargs["error_code"] == error.error_code()
        assert call_kwargs["duration"] >= 0

    async def test_async_resolver_generic_exception(
        self,
        middleware: GQLMetricMiddleware,
        resolve_info: MagicMock,
        metric_observer: MagicMock,
    ) -> None:
        async def async_resolver(root: Any, info: Any, **kwargs: Any) -> str:
            raise RuntimeError("async failure")

        result_coro = middleware.resolve(async_resolver, None, resolve_info)
        assert asyncio.iscoroutine(result_coro)

        with pytest.raises(RuntimeError):
            await result_coro

        metric_observer.observe_request.assert_called_once()
        call_kwargs = metric_observer.observe_request.call_args.kwargs
        assert call_kwargs["success"] is False
        assert call_kwargs["error_code"] == ErrorCode.default()


class TestGQLMetricMiddlewareDataLoaderBatching:
    """Tests that DataLoader batching is preserved with the async wrapper."""

    async def test_sibling_resolvers_can_batch(
        self,
        middleware: GQLMetricMiddleware,
        resolve_info: MagicMock,
        metric_observer: MagicMock,
    ) -> None:
        call_order: list[str] = []

        async def resolver_a(root: Any, info: Any, **kwargs: Any) -> str:
            call_order.append("a_start")
            await asyncio.sleep(0.01)
            call_order.append("a_end")
            return "a"

        async def resolver_b(root: Any, info: Any, **kwargs: Any) -> str:
            call_order.append("b_start")
            await asyncio.sleep(0.01)
            call_order.append("b_end")
            return "b"

        coro_a = middleware.resolve(resolver_a, None, resolve_info)
        coro_b = middleware.resolve(resolver_b, None, resolve_info)

        assert asyncio.iscoroutine(coro_a)
        assert asyncio.iscoroutine(coro_b)

        results = await asyncio.gather(coro_a, coro_b)

        assert list(results) == ["a", "b"]
        assert call_order.index("a_start") < call_order.index("a_end")
        assert call_order.index("b_start") < call_order.index("b_end")
        assert metric_observer.observe_request.call_count == 2


_otel_exporter = InMemorySpanExporter()
_otel_provider = TracerProvider()
_otel_provider.add_span_processor(SimpleSpanProcessor(_otel_exporter))
trace.set_tracer_provider(_otel_provider)


@pytest.fixture
def span_exporter() -> Generator[InMemorySpanExporter, None, None]:
    _otel_exporter.clear()
    yield _otel_exporter


class TestGQLMetricMiddlewareSyncSpans:
    """Tests for sync resolver OTel span behavior."""

    def test_successful_sync_resolver_produces_ok_span(
        self,
        middleware: GQLMetricMiddleware,
        resolve_info: MagicMock,
        span_exporter: InMemorySpanExporter,
    ) -> None:
        def sync_resolver(root: Any, info: Any, **kwargs: Any) -> str:
            return "sync_result"

        result = middleware.resolve(sync_resolver, None, resolve_info)

        assert result == "sync_result"
        spans = span_exporter.get_finished_spans()
        assert len(spans) == 1
        span = spans[0]
        assert span.name == "gql.TestQuery.test_field"
        assert span.attributes is not None
        assert span.attributes["graphql.operation_name"] == "TestQuery"
        assert span.attributes["graphql.field_name"] == "test_field"
        assert span.attributes["graphql.parent_type"] == "Query"
        assert span.status.status_code == StatusCode.OK

    def test_sync_exception_produces_error_span(
        self,
        middleware: GQLMetricMiddleware,
        resolve_info: MagicMock,
        span_exporter: InMemorySpanExporter,
    ) -> None:
        def sync_resolver(root: Any, info: Any, **kwargs: Any) -> str:
            raise RuntimeError("test sync error")

        with pytest.raises(RuntimeError, match="test sync error"):
            middleware.resolve(sync_resolver, None, resolve_info)

        spans = span_exporter.get_finished_spans()
        assert len(spans) == 1
        span = spans[0]
        assert span.status.status_code == StatusCode.ERROR
        assert span.status.description == "test sync error"
        assert any(event.name == "exception" for event in span.events)

    def test_anonymous_operation_span_name(
        self,
        middleware: GQLMetricMiddleware,
        resolve_info: MagicMock,
        span_exporter: InMemorySpanExporter,
    ) -> None:
        resolve_info.operation.name = None

        def sync_resolver(root: Any, info: Any, **kwargs: Any) -> str:
            return "result"

        middleware.resolve(sync_resolver, None, resolve_info)

        spans = span_exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].name == "gql.anonymous.test_field"
        assert spans[0].attributes is not None
        assert spans[0].attributes["graphql.operation_name"] == "anonymous"

    def test_sync_resolver_span_is_child_of_current_context(
        self,
        middleware: GQLMetricMiddleware,
        resolve_info: MagicMock,
        span_exporter: InMemorySpanExporter,
    ) -> None:
        def sync_resolver(root: Any, info: Any, **kwargs: Any) -> str:
            return "child_result"

        tracer = trace.get_tracer("test")

        with tracer.start_as_current_span("parent_http_span"):
            result = middleware.resolve(sync_resolver, None, resolve_info)

        assert result == "child_result"
        spans = span_exporter.get_finished_spans()
        assert len(spans) == 2
        parent = next(s for s in spans if s.name == "parent_http_span")
        child = next(s for s in spans if s.name == "gql.TestQuery.test_field")
        assert child.parent is not None
        assert child.parent.span_id == parent.context.span_id
        assert child.parent.trace_id == parent.context.trace_id

    def test_sync_resolver_span_is_active_during_execution(
        self,
        middleware: GQLMetricMiddleware,
        resolve_info: MagicMock,
        span_exporter: InMemorySpanExporter,
    ) -> None:
        captured_span_context: list[trace.Span] = []

        def sync_resolver(root: Any, info: Any, **kwargs: Any) -> str:
            captured_span_context.append(trace.get_current_span())
            return "result"

        middleware.resolve(sync_resolver, None, resolve_info)

        spans = span_exporter.get_finished_spans()
        assert len(spans) == 1
        assert captured_span_context[0].get_span_context() == spans[0].context


class TestGQLMetricMiddlewareAsyncSpans:
    """Tests for async resolver OTel span behavior."""

    async def test_async_span_not_ended_before_await(
        self,
        middleware: GQLMetricMiddleware,
        resolve_info: MagicMock,
        span_exporter: InMemorySpanExporter,
    ) -> None:
        async def async_resolver(root: Any, info: Any, **kwargs: Any) -> str:
            return "async_result"

        result_coro = middleware.resolve(async_resolver, None, resolve_info)
        assert span_exporter.get_finished_spans() == ()

        result = await result_coro
        assert result == "async_result"

        spans = span_exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].name == "gql.TestQuery.test_field"
        assert spans[0].status.status_code == StatusCode.OK

    async def test_failing_async_resolver_produces_error_span(
        self,
        middleware: GQLMetricMiddleware,
        resolve_info: MagicMock,
        span_exporter: InMemorySpanExporter,
    ) -> None:
        async def failing_resolver(root: Any, info: Any, **kwargs: Any) -> str:
            raise ValueError("async error")

        result_coro = middleware.resolve(failing_resolver, None, resolve_info)

        with pytest.raises(ValueError, match="async error"):
            await result_coro

        spans = span_exporter.get_finished_spans()
        assert len(spans) == 1
        span = spans[0]
        assert span.status.status_code == StatusCode.ERROR
        assert span.status.description == "async error"
        assert any(event.name == "exception" for event in span.events)

    async def test_resolver_span_is_child_of_current_context(
        self,
        middleware: GQLMetricMiddleware,
        resolve_info: MagicMock,
        span_exporter: InMemorySpanExporter,
    ) -> None:
        async def async_resolver(root: Any, info: Any, **kwargs: Any) -> str:
            return "child_result"

        tracer = trace.get_tracer("test")

        with tracer.start_as_current_span("parent_http_span"):
            result_coro = middleware.resolve(async_resolver, None, resolve_info)
            result = await result_coro

        assert result == "child_result"
        spans = span_exporter.get_finished_spans()
        assert len(spans) == 2
        parent = next(s for s in spans if s.name == "parent_http_span")
        child = next(s for s in spans if s.name == "gql.TestQuery.test_field")
        assert child.parent is not None
        assert child.parent.span_id == parent.context.span_id
        assert child.parent.trace_id == parent.context.trace_id


class TestGQLMetricMiddlewareNoTracerProvider:
    """Tests verifying behavior when OTel is not configured (no-op spans)."""

    def test_sync_resolver_works_without_tracer_provider(
        self,
        middleware: GQLMetricMiddleware,
        resolve_info: MagicMock,
    ) -> None:
        def sync_resolver(root: Any, info: Any, **kwargs: Any) -> str:
            return "result"

        result = middleware.resolve(sync_resolver, None, resolve_info)

        assert result == "result"

    async def test_async_resolver_works_without_tracer_provider(
        self,
        middleware: GQLMetricMiddleware,
        resolve_info: MagicMock,
    ) -> None:
        async def async_resolver(root: Any, info: Any, **kwargs: Any) -> str:
            return "async_no_otel"

        result_coro = middleware.resolve(async_resolver, None, resolve_info)
        result = await result_coro

        assert result == "async_no_otel"


class TestGQLMetricMiddlewareLeafTypeBypass:
    """Tests verifying that leaf-type resolvers skip span and metric creation."""

    def test_scalar_return_type_skips_span_and_metrics(
        self,
        middleware: GQLMetricMiddleware,
        resolve_info: MagicMock,
        metric_observer: MagicMock,
        span_exporter: InMemorySpanExporter,
    ) -> None:
        resolve_info.return_type = GraphQLString

        def sync_resolver(root: Any, info: Any, **kwargs: Any) -> str:
            return "scalar_value"

        result = middleware.resolve(sync_resolver, None, resolve_info)

        assert result == "scalar_value"
        assert span_exporter.get_finished_spans() == ()
        metric_observer.observe_request.assert_not_called()

    def test_nonnull_scalar_return_type_skips_span(
        self,
        middleware: GQLMetricMiddleware,
        resolve_info: MagicMock,
        metric_observer: MagicMock,
        span_exporter: InMemorySpanExporter,
    ) -> None:
        resolve_info.return_type = GraphQLNonNull(GraphQLString)

        def sync_resolver(root: Any, info: Any, **kwargs: Any) -> str:
            return "nonnull_scalar"

        result = middleware.resolve(sync_resolver, None, resolve_info)

        assert result == "nonnull_scalar"
        assert span_exporter.get_finished_spans() == ()
        metric_observer.observe_request.assert_not_called()

    def test_object_return_type_creates_span(
        self,
        middleware: GQLMetricMiddleware,
        resolve_info: MagicMock,
        span_exporter: InMemorySpanExporter,
    ) -> None:
        resolve_info.return_type = GraphQLObjectType("User", fields={})

        def sync_resolver(root: Any, info: Any, **kwargs: Any) -> str:
            return "object_value"

        result = middleware.resolve(sync_resolver, None, resolve_info)

        assert result == "object_value"
        spans = span_exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].name == "gql.TestQuery.test_field"
