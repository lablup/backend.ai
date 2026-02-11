from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from ai.backend.common.exception import (
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
    InvalidAPIParameters,
)
from ai.backend.manager.api.gql_legacy.schema import GQLMetricMiddleware


def _make_info(*, operation_name: str | None = "TestOp") -> MagicMock:
    info = MagicMock(spec_set=["context", "operation", "field_name", "parent_type"])
    info.field_name = "testField"
    info.parent_type.name = "Query"
    info.operation.operation = "query"
    if operation_name is not None:
        info.operation.name.value = operation_name
    else:
        info.operation.name = None
    info.context = SimpleNamespace(metric_observer=MagicMock())
    return info


class TestGQLMetricMiddleware:
    def test_observe_on_success(self) -> None:
        middleware = GQLMetricMiddleware()
        info = _make_info()
        sentinel = object()
        next_fn = MagicMock(return_value=sentinel)

        result = middleware.resolve(next_fn, None, info)

        assert result is sentinel
        next_fn.assert_called_once_with(None, info)
        info.context.metric_observer.observe_request.assert_called_once()
        call_kwargs: dict[str, Any] = info.context.metric_observer.observe_request.call_args.kwargs
        assert call_kwargs["operation_type"] == "query"
        assert call_kwargs["field_name"] == "testField"
        assert call_kwargs["parent_type"] == "Query"
        assert call_kwargs["operation_name"] == "TestOp"
        assert call_kwargs["error_code"] is None
        assert call_kwargs["success"] is True
        assert isinstance(call_kwargs["duration"], float)
        assert call_kwargs["duration"] >= 0

    def test_observe_on_backend_ai_error(self) -> None:
        middleware = GQLMetricMiddleware()
        info = _make_info()
        err = InvalidAPIParameters("bad param")
        next_fn = MagicMock(side_effect=err)

        with pytest.raises(InvalidAPIParameters) as exc_info:
            middleware.resolve(next_fn, None, info)

        assert exc_info.value is err
        info.context.metric_observer.observe_request.assert_called_once()
        call_kwargs: dict[str, Any] = info.context.metric_observer.observe_request.call_args.kwargs
        assert call_kwargs["error_code"] == ErrorCode(
            domain=ErrorDomain.API,
            operation=ErrorOperation.PARSING,
            error_detail=ErrorDetail.INVALID_PARAMETERS,
        )
        assert call_kwargs["success"] is False

    def test_observe_on_unexpected_exception(self) -> None:
        middleware = GQLMetricMiddleware()
        info = _make_info()
        err = RuntimeError("unexpected")
        next_fn = MagicMock(side_effect=err)

        with pytest.raises(RuntimeError) as exc_info:
            middleware.resolve(next_fn, None, info)

        assert exc_info.value is err
        info.context.metric_observer.observe_request.assert_called_once()
        call_kwargs: dict[str, Any] = info.context.metric_observer.observe_request.call_args.kwargs
        assert call_kwargs["error_code"] == ErrorCode.default()
        assert call_kwargs["success"] is False

    def test_anonymous_operation_name(self) -> None:
        middleware = GQLMetricMiddleware()
        info = _make_info(operation_name=None)
        next_fn = MagicMock(return_value=None)

        middleware.resolve(next_fn, None, info)

        call_kwargs: dict[str, Any] = info.context.metric_observer.observe_request.call_args.kwargs
        assert call_kwargs["operation_name"] == "anonymous"
