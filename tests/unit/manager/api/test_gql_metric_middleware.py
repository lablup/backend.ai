"""Tests for GQLMetricMiddleware _observe helper and async resolver timing fix."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock

import pytest
from graphql import OperationType

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
