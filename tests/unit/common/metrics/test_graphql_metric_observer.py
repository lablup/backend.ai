from __future__ import annotations

from ai.backend.common.metrics.metric import GraphQLMetricObserver


class TestGraphQLMetricObserverLabels:
    """Regression tests for BA-6802.

    ``operation_name`` is the client-supplied GraphQL operation name. Using it as a
    Prometheus label lets a client create unbounded time-series cardinality, so it must
    not appear in the label set of the GraphQL request metrics.
    """

    def test_operation_name_not_in_request_count_labels(self) -> None:
        observer = GraphQLMetricObserver.instance()
        assert "operation_name" not in observer._request_count._labelnames

    def test_operation_name_not_in_request_duration_labels(self) -> None:
        observer = GraphQLMetricObserver.instance()
        assert "operation_name" not in observer._request_duration_sec._labelnames

    def test_expected_label_set(self) -> None:
        observer = GraphQLMetricObserver.instance()
        expected = {
            "operation_type",
            "field_name",
            "parent_type",
            "domain",
            "operation",
            "error_detail",
            "success",
        }
        assert set(observer._request_count._labelnames) == expected
        assert set(observer._request_duration_sec._labelnames) == expected
