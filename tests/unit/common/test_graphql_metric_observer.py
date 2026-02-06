import pytest
from prometheus_client import CollectorRegistry, Counter, Histogram

from ai.backend.common.metrics.metric import GraphQLMetricObserver

_LABEL_NAMES = [
    "operation_type",
    "field_name",
    "parent_type",
    "operation_name",
    "client_operation",
    "domain",
    "operation",
    "error_detail",
    "success",
]


@pytest.fixture
def registry() -> CollectorRegistry:
    return CollectorRegistry()


@pytest.fixture
def observer(registry: CollectorRegistry) -> GraphQLMetricObserver:
    obs = GraphQLMetricObserver.__new__(GraphQLMetricObserver)
    obs._request_count = Counter(
        name="test_graphql_request_count",
        documentation="Test counter",
        labelnames=_LABEL_NAMES,
        registry=registry,
    )
    obs._request_duration_sec = Histogram(
        name="test_graphql_request_duration_sec",
        documentation="Test histogram",
        labelnames=_LABEL_NAMES,
        buckets=[0.001, 0.01, 0.1, 0.5, 1, 2, 5, 10, 30],
        registry=registry,
    )
    return obs


def test_observe_request_with_client_operation(
    observer: GraphQLMetricObserver, registry: CollectorRegistry
) -> None:
    observer.observe_request(
        operation_type="query",
        field_name="compute_sessions",
        parent_type="Query",
        operation_name="ListSessions",
        client_operation="list_sessions",
        error_code=None,
        success=True,
        duration=0.05,
    )
    sample = registry.get_sample_value(
        "test_graphql_request_count_total",
        labels={
            "operation_type": "query",
            "field_name": "compute_sessions",
            "parent_type": "Query",
            "operation_name": "ListSessions",
            "client_operation": "list_sessions",
            "domain": "",
            "operation": "",
            "error_detail": "",
            "success": "True",
        },
    )
    assert sample == 1.0


def test_observe_request_without_client_operation(
    observer: GraphQLMetricObserver, registry: CollectorRegistry
) -> None:
    observer.observe_request(
        operation_type="query",
        field_name="compute_sessions",
        parent_type="Query",
        operation_name="ListSessions",
        error_code=None,
        success=True,
        duration=0.05,
    )
    sample = registry.get_sample_value(
        "test_graphql_request_count_total",
        labels={
            "operation_type": "query",
            "field_name": "compute_sessions",
            "parent_type": "Query",
            "operation_name": "ListSessions",
            "client_operation": "",
            "domain": "",
            "operation": "",
            "error_detail": "",
            "success": "True",
        },
    )
    assert sample == 1.0


def test_observe_request_default_parameter_backward_compat(
    observer: GraphQLMetricObserver,
) -> None:
    observer.observe_request(
        operation_type="query",
        field_name="agents",
        parent_type="Query",
        operation_name="ListAgents",
        error_code=None,
        success=True,
        duration=0.01,
    )
