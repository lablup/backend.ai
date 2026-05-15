"""
Tests for the container-metric and live-stat query builders:
query building, metric type classification, and live stat query construction.
"""

from uuid import UUID

import pytest

from ai.backend.common.clients.prometheus import (
    ContainerLiveStatQueryBuilder,
    ContainerMetricQueryBuilder,
)
from ai.backend.common.clients.prometheus.fixed_query_builder import _regex_union
from ai.backend.common.clients.prometheus.metric_types import (
    ContainerMetricOptionalLabel,
    MetricType,
)
from ai.backend.common.clients.prometheus.preset import LabelMatcher, MetricPreset
from ai.backend.common.clients.prometheus.types import ValueType
from ai.backend.common.types import KernelId


class TestGetContainerMetricType:
    @pytest.fixture
    def builder(self) -> ContainerMetricQueryBuilder:
        return ContainerMetricQueryBuilder("1m")

    @pytest.mark.parametrize(
        ("metric_name", "value_type", "expected"),
        [
            ("mem", ValueType.CURRENT, MetricType.GAUGE),
            ("cpu_util", ValueType.CAPACITY, MetricType.GAUGE),
            ("net_rx", ValueType.CURRENT, MetricType.RATE),
            ("net_tx", ValueType.CURRENT, MetricType.RATE),
            ("net_rx", ValueType.CAPACITY, MetricType.RATE),
            ("cpu_util", ValueType.CURRENT, MetricType.DIFF),
        ],
        ids=[
            "gauge-unknown-metric",
            "gauge-capacity-overrides-diff",
            "rate-net_rx",
            "rate-net_tx",
            "rate-precedence-over-value_type",
            "diff-cpu_util-current",
        ],
    )
    def test_metric_type_classification(
        self,
        builder: ContainerMetricQueryBuilder,
        metric_name: str,
        value_type: ValueType,
        expected: MetricType,
    ) -> None:
        label = ContainerMetricOptionalLabel(value_type=value_type)
        assert builder.get_container_metric_type(metric_name, label) == expected


class TestGetContainerMetricQuery:
    @pytest.fixture
    def builder(self) -> ContainerMetricQueryBuilder:
        return ContainerMetricQueryBuilder("5m")

    def test_gauge_query_preset(self, builder: ContainerMetricQueryBuilder) -> None:
        label = ContainerMetricOptionalLabel(value_type=ValueType.CURRENT)

        result = builder.get_container_metric_query("mem", label)

        assert isinstance(result, MetricPreset)
        assert result.window == "5m"
        assert result.labels["container_metric_name"] == LabelMatcher.exact("mem")
        assert result.labels["value_type"] == LabelMatcher.exact("current")
        assert "value_type" in result.group_by

    @pytest.mark.parametrize("metric_name", ["net_rx", "cpu_util"])
    def test_rate_based_query_uses_rate_function(
        self, builder: ContainerMetricQueryBuilder, metric_name: str
    ) -> None:
        label = ContainerMetricOptionalLabel(value_type=ValueType.CURRENT)

        rendered = builder.get_container_metric_query(metric_name, label).render()

        assert "rate(" in rendered
        assert "[5m]" in rendered

    def test_query_with_optional_labels(self, builder: ContainerMetricQueryBuilder) -> None:
        kid = UUID("12345678-1234-5678-1234-567812345678")
        label = ContainerMetricOptionalLabel(
            value_type=ValueType.CURRENT,
            kernel_id=kid,
        )

        result = builder.get_container_metric_query("mem", label)

        assert result.labels["kernel_id"] == LabelMatcher.exact(str(kid))
        assert "kernel_id" in result.group_by


class TestGetContainerLiveStatQueries:
    def test_kernel_id_regex_filter(self) -> None:
        builder = ContainerLiveStatQueryBuilder("1m")
        kid1 = KernelId(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
        kid2 = KernelId(UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"))

        result = builder.get_container_live_stat_queries([kid1, kid2])
        rendered = "\n".join(
            query.render()
            for query in (
                result.instant,
                result.rate_current,
                result.max,
                result.rate_max,
                result.avg,
                result.rate_avg,
            )
        )

        assert str(kid1) in rendered
        assert str(kid2) in rendered
        assert "cccccccc-cccc-cccc-cccc-cccccccccccc" not in rendered

    def test_window_queries_read_current_series(self) -> None:
        builder = ContainerLiveStatQueryBuilder("1m")
        kid = KernelId(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))

        result = builder.get_container_live_stat_queries([kid])

        assert "sum by (container_metric_name,kernel_id)" in result.max.render()
        assert "sum by (container_metric_name,kernel_id)" in result.avg.render()
        assert 'value_type="current"' in result.max.render()
        assert 'value_type="current"' in result.avg.render()
        assert "rate(" not in result.max.render()
        assert "rate(" not in result.avg.render()

    def test_rate_window_queries_read_rate_series(self) -> None:
        builder = ContainerLiveStatQueryBuilder("1m")
        kid = KernelId(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))

        result = builder.get_container_live_stat_queries([kid])

        assert (
            "max_over_time((sum by (container_metric_name,kernel_id)(rate("
            in result.rate_max.render()
        )
        assert (
            "avg_over_time((sum by (container_metric_name,kernel_id)(rate("
            in result.rate_avg.render()
        )
        assert 'container_metric_name=~"cpu_util|net_rx|net_tx"' in result.rate_max.render()
        assert 'container_metric_name=~"cpu_util|net_rx|net_tx"' in result.rate_avg.render()
        assert 'value_type="current"' in result.rate_max.render()
        assert 'value_type="current"' in result.rate_avg.render()


class TestRegexUnion:
    def test_escapes_special_chars(self) -> None:
        result = _regex_union(["a.b", "c+d"])
        assert r"a\.b" in result
        assert r"c\+d" in result
        assert "|" in result
