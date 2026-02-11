"""Tests for GQLMetricMiddleware _observe helper."""

from __future__ import annotations

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
