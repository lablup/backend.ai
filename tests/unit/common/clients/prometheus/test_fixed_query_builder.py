"""
Tests for FixedQueryBuilder: query building, metric type classification,
and live stat query construction.
"""

import re
from uuid import UUID

import pytest

from ai.backend.common.clients.prometheus import (
    FixedQueryBuilder,
)
from ai.backend.common.clients.prometheus.fixed_query_builder import _regex_union
from ai.backend.common.clients.prometheus.metric_types import (
    ContainerMetricOptionalLabel,
    MetricType,
)
from ai.backend.common.clients.prometheus.preset import LabelMatcher, LabelOperator, MetricPreset
from ai.backend.common.clients.prometheus.types import ValueType
from ai.backend.common.types import KernelId


class TestGetContainerMetricType:
    @pytest.fixture
    def builder(self) -> FixedQueryBuilder:
        return FixedQueryBuilder("1m")

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
        builder: FixedQueryBuilder,
        metric_name: str,
        value_type: ValueType,
        expected: MetricType,
    ) -> None:
        label = ContainerMetricOptionalLabel(value_type=value_type)
        assert builder.get_container_metric_type(metric_name, label) == expected


class TestGetContainerMetricQuery:
    @pytest.fixture
    def builder(self) -> FixedQueryBuilder:
        return FixedQueryBuilder("5m")

    def test_gauge_query_preset(self, builder: FixedQueryBuilder) -> None:
        label = ContainerMetricOptionalLabel(value_type=ValueType.CURRENT)

        result = builder.get_container_metric_query("mem", label)

        assert isinstance(result, MetricPreset)
        assert result.window == "5m"
        assert result.labels["container_metric_name"] == LabelMatcher.exact("mem")
        assert result.labels["value_type"] == LabelMatcher.exact("current")
        assert "value_type" in result.group_by

    @pytest.mark.parametrize("metric_name", ["net_rx", "cpu_util"])
    def test_rate_based_query_uses_rate_function(
        self, builder: FixedQueryBuilder, metric_name: str
    ) -> None:
        label = ContainerMetricOptionalLabel(value_type=ValueType.CURRENT)

        rendered = builder.get_container_metric_query(metric_name, label).render()

        assert "rate(" in rendered
        assert "[5m]" in rendered

    def test_query_with_optional_labels(self, builder: FixedQueryBuilder) -> None:
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
        builder = FixedQueryBuilder("1m")
        kid1 = KernelId(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
        kid2 = KernelId(UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"))

        result = builder.get_container_live_stat_queries([kid1, kid2])

        matcher = result.gauge.labels["kernel_id"]
        assert matcher.operator == LabelOperator.REGEX
        pattern = re.compile(matcher.value)
        assert pattern.fullmatch(str(kid1))
        assert pattern.fullmatch(str(kid2))
        assert not pattern.fullmatch("cccccccc-cccc-cccc-cccc-cccccccccccc")

    @pytest.mark.parametrize(
        ("preset_attr", "expected_metrics"),
        [
            ("diff", ["cpu_util"]),
            ("rate", ["net_rx", "net_tx"]),
        ],
    )
    def test_preset_filters_by_metric_name_and_value_type(
        self, preset_attr: str, expected_metrics: list[str]
    ) -> None:
        builder = FixedQueryBuilder("1m")
        kid = KernelId(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))

        result = builder.get_container_live_stat_queries([kid])
        labels = getattr(result, preset_attr).labels

        assert labels["container_metric_name"].operator == LabelOperator.REGEX
        for metric in expected_metrics:
            assert metric in labels["container_metric_name"].value
        assert labels["value_type"] == LabelMatcher.exact("current")

    def test_gauge_has_no_metric_name_filter(self) -> None:
        builder = FixedQueryBuilder("1m")
        kid = KernelId(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))

        result = builder.get_container_live_stat_queries([kid])

        assert "container_metric_name" not in result.gauge.labels


class TestRegexUnion:
    def test_escapes_special_chars(self) -> None:
        result = _regex_union(["a.b", "c+d"])
        assert r"a\.b" in result
        assert r"c\+d" in result
        assert "|" in result
