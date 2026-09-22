"""
Tests for the container-metric and live-stat query builders:
query building, metric type classification, and live stat query construction.
"""

from dataclasses import dataclass
from uuid import UUID

import pytest

from ai.backend.common.types import KernelId
from ai.backend.manager.clients.prometheus import (
    ContainerLiveStatQueryBuilder,
    ContainerMetricQueryBuilder,
)
from ai.backend.manager.clients.prometheus.metric_types import (
    ContainerMetricOptionalLabel,
    MetricType,
)
from ai.backend.manager.clients.prometheus.preset import (
    LabelMatcher,
    MetricPreset,
    PromQLTemplateRenderer,
    regex_union,
)
from ai.backend.manager.clients.prometheus.types import ValueType

_USER_ID = UUID("32345678-1234-5678-1234-567812345678")


@dataclass(frozen=True)
class _PctQueryCase:
    metric_name: str
    expected_query: str


@pytest.fixture
def renderer() -> PromQLTemplateRenderer:
    return PromQLTemplateRenderer()


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
        self,
        builder: ContainerMetricQueryBuilder,
        renderer: PromQLTemplateRenderer,
        metric_name: str,
    ) -> None:
        label = ContainerMetricOptionalLabel(value_type=ValueType.CURRENT)

        rendered = renderer.render(builder.get_container_metric_query(metric_name, label))

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

    @pytest.mark.parametrize(
        "case",
        [
            _PctQueryCase(
                metric_name="cpu_util",
                expected_query=(
                    "label_replace("
                    "sum by (user_id)(rate(backendai_container_utilization"
                    f'{{container_metric_name="cpu_util",user_id="{_USER_ID}",value_type="current"}}[5m]))'
                    ' / 1000 * 100, "value_type", "pct", "", "")'
                ),
            ),
            _PctQueryCase(
                metric_name="net_rx",
                expected_query=(
                    "label_replace("
                    "sum by (user_id)(backendai_container_utilization"
                    f'{{container_metric_name="net_rx",user_id="{_USER_ID}",value_type="current"}})'
                    " / (sum by (user_id)(backendai_container_utilization"
                    f'{{container_metric_name="net_rx",user_id="{_USER_ID}",value_type="capacity"}}) > 0)'
                    ' * 100, "value_type", "pct", "", "")'
                ),
            ),
            _PctQueryCase(
                metric_name="cuda_util",
                expected_query=(
                    "label_replace("
                    "sum by (user_id)(backendai_container_utilization"
                    f'{{container_metric_name="cuda_util",user_id="{_USER_ID}",value_type="current"}})'
                    " / (sum by (user_id)(backendai_container_utilization"
                    f'{{container_metric_name="cuda_util",user_id="{_USER_ID}",value_type="capacity"}}) > 0)'
                    ' * 100, "value_type", "pct", "", "")'
                ),
            ),
        ],
        ids=lambda case: case.metric_name,
    )
    def test_pct_query_divides_current_by_capacity(
        self,
        builder: ContainerMetricQueryBuilder,
        renderer: PromQLTemplateRenderer,
        case: _PctQueryCase,
    ) -> None:
        label = ContainerMetricOptionalLabel(value_type=ValueType.PCT, user_id=_USER_ID)

        rendered = renderer.render(builder.get_container_metric_query(case.metric_name, label))

        assert rendered == case.expected_query


class TestGetContainerLiveStatQueries:
    def test_kernel_id_regex_filter(self, renderer: PromQLTemplateRenderer) -> None:
        builder = ContainerLiveStatQueryBuilder("1m")
        kid1 = KernelId(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
        kid2 = KernelId(UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"))

        result = builder.get_container_live_stat_queries([kid1, kid2])
        rendered = "\n".join(
            renderer.render(query)
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

    def test_window_queries_read_current_series(self, renderer: PromQLTemplateRenderer) -> None:
        builder = ContainerLiveStatQueryBuilder("1m")
        kid = KernelId(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))

        result = builder.get_container_live_stat_queries([kid])

        assert "sum by (container_metric_name,kernel_id)" in renderer.render(result.max)
        assert "sum by (container_metric_name,kernel_id)" in renderer.render(result.avg)
        assert 'value_type="current"' in renderer.render(result.max)
        assert 'value_type="current"' in renderer.render(result.avg)
        assert "rate(" not in renderer.render(result.max)
        assert "rate(" not in renderer.render(result.avg)

    def test_rate_window_queries_read_rate_series(self, renderer: PromQLTemplateRenderer) -> None:
        builder = ContainerLiveStatQueryBuilder("1m")
        kid = KernelId(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))

        result = builder.get_container_live_stat_queries([kid])

        assert "max_over_time((sum by (container_metric_name,kernel_id)(rate(" in renderer.render(
            result.rate_max
        )
        assert "avg_over_time((sum by (container_metric_name,kernel_id)(rate(" in renderer.render(
            result.rate_avg
        )
        assert 'container_metric_name=~"cpu_util|net_rx|net_tx"' in renderer.render(result.rate_max)
        assert 'container_metric_name=~"cpu_util|net_rx|net_tx"' in renderer.render(result.rate_avg)
        assert 'value_type="current"' in renderer.render(result.rate_max)
        assert 'value_type="current"' in renderer.render(result.rate_avg)


class TestRegexUnion:
    def test_escapes_special_chars(self) -> None:
        result = regex_union(["a.b", "c+d"])
        assert r"a\.b" in result
        assert r"c\+d" in result
        assert "|" in result
