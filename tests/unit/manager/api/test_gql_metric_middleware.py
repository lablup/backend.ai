from __future__ import annotations

from unittest.mock import MagicMock

from ai.backend.common.contexts.client_operation import with_client_operation
from ai.backend.manager.api.gql_legacy.schema import GQLMetricMiddleware


def test_gql_metric_middleware_passes_client_operation() -> None:
    mock_observer = MagicMock()
    mock_info = MagicMock()
    mock_info.operation.operation = "query"
    mock_info.field_name = "compute_sessions"
    mock_info.parent_type.name = "Query"
    mock_info.operation.name.value = "ListSessions"
    mock_info.context.metric_observer = mock_observer

    middleware = GQLMetricMiddleware()
    mock_next = MagicMock(return_value="result")

    with with_client_operation("list_sessions"):
        middleware.resolve(mock_next, None, mock_info)

    mock_observer.observe_request.assert_called_once()
    call_kwargs = mock_observer.observe_request.call_args.kwargs
    assert call_kwargs["client_operation"] == "list_sessions"


def test_gql_metric_middleware_empty_client_operation_without_context() -> None:
    mock_observer = MagicMock()
    mock_info = MagicMock()
    mock_info.operation.operation = "query"
    mock_info.field_name = "agents"
    mock_info.parent_type.name = "Query"
    mock_info.operation.name.value = "ListAgents"
    mock_info.context.metric_observer = mock_observer

    middleware = GQLMetricMiddleware()
    mock_next = MagicMock(return_value="result")

    middleware.resolve(mock_next, None, mock_info)

    mock_observer.observe_request.assert_called_once()
    call_kwargs = mock_observer.observe_request.call_args.kwargs
    assert call_kwargs["client_operation"] == ""
