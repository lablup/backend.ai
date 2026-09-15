from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from ai.backend.common.metrics.types import (
    CONTAINER_UTILIZATION_METRIC_LABEL_NAME,
    CONTAINER_UTILIZATION_METRIC_NAME,
)
from ai.backend.common.types import KernelId
from ai.backend.manager.clients.prometheus.metric_types import (
    DIFF_METRICS,
    RATE_METRICS,
    ContainerLiveStatQueries,
    ContainerMetricOptionalLabel,
    MetricType,
    resolve_container_metric_unit_hint,
)
from ai.backend.manager.clients.prometheus.preset import LabelMatcher, MetricPreset, regex_union
from ai.backend.manager.clients.prometheus.querier import ContainerMetricQuerier
from ai.backend.manager.clients.prometheus.types import ValueType

_GAUGE_TEMPLATE: Final[str] = (
    "sum by (${{group_by}})(" + CONTAINER_UTILIZATION_METRIC_NAME + "{${{labels}}})"
)
_RATE_TEMPLATE: Final[str] = (
    "sum by (${{group_by}})(rate("
    + CONTAINER_UTILIZATION_METRIC_NAME
    + "{${{labels}}}[${{window}}]))"
)
_DIFF_TEMPLATE: Final[str] = (
    "sum by (${{group_by}})(rate("
    + CONTAINER_UTILIZATION_METRIC_NAME
    + "{${{labels}}}[${{window}}]))"
)
# pct = current / capacity * 100. The `> 0` on capacity drops the series
# instead of dividing by zero.
_PCT_CURRENT_SELECTOR: Final[str] = (
    CONTAINER_UTILIZATION_METRIC_NAME + '{${{labels}},value_type="current"}'
)
_PCT_CAPACITY_SELECTOR: Final[str] = (
    CONTAINER_UTILIZATION_METRIC_NAME + '{${{labels}},value_type="capacity"}'
)
# `current` is a gauge already in the unit of capacity (percent, bytes).
_PCT_TEMPLATE: Final[str] = (
    "label_replace("
    "sum by (${{group_by}})(" + _PCT_CURRENT_SELECTOR + ")"
    " / (sum by (${{group_by}})(" + _PCT_CAPACITY_SELECTOR + ") > 0)"
    ' * 100, "value_type", "pct", "", "")'
)
# `current` is a cumulative counter (CPU msec); rate() makes it per second,
# the unit capacity is reported in.
_PCT_RATE_TEMPLATE: Final[str] = (
    "label_replace("
    "sum by (${{group_by}})(rate(" + _PCT_CURRENT_SELECTOR + "[${{window}}]))"
    " / (sum by (${{group_by}})(" + _PCT_CAPACITY_SELECTOR + ") > 0)"
    ' * 100, "value_type", "pct", "", "")'
)
# Unit hints served as a per-second rate of a cumulative counter (CPU time).
_COUNTER_UNIT_HINTS: Final[frozenset[str]] = frozenset({"msec/s"})
_SERIES_TEMPLATES: Final[Mapping[MetricType, str]] = {
    MetricType.GAUGE: _GAUGE_TEMPLATE,
    MetricType.RATE: _RATE_TEMPLATE,
    MetricType.DIFF: _DIFF_TEMPLATE,
}
_LIVE_STAT_MAX_TEMPLATE: Final[str] = "max_over_time((" + _GAUGE_TEMPLATE + ")[${{window}}:])"
_LIVE_STAT_AVG_TEMPLATE: Final[str] = "avg_over_time((" + _GAUGE_TEMPLATE + ")[${{window}}:])"
_LIVE_STAT_RATE_MAX_TEMPLATE: Final[str] = "max_over_time((" + _RATE_TEMPLATE + ")[${{window}}:])"
_LIVE_STAT_RATE_AVG_TEMPLATE: Final[str] = "avg_over_time((" + _RATE_TEMPLATE + ")[${{window}}:])"
_INSTANT_GROUP_BY: Final[frozenset[str]] = frozenset({
    "kernel_id",
    "container_metric_name",
    "value_type",
})
_AGGREGATED_GROUP_BY: Final[frozenset[str]] = frozenset({
    "kernel_id",
    "container_metric_name",
})


@dataclass(frozen=True)
class LabelValuesQuery:
    label_name: str
    metric_match: str


def _value_type_regex(value_types: Sequence[ValueType]) -> str:
    return regex_union([value_type.value for value_type in value_types])


_LIVE_STAT_RATE_METRIC_REGEX: Final[str] = regex_union(sorted(RATE_METRICS | DIFF_METRICS))
_INSTANT_VALUE_TYPE_REGEX: Final[str] = _value_type_regex([
    ValueType.CURRENT,
    ValueType.CAPACITY,
])


class ContainerMetricQueryBuilder:
    """Builds PromQL queries for individual container-metric retrieval
    (`fetch_available_container_metric_names` / `fetch_container_metric`)."""

    _timewindow: str

    def __init__(self, timewindow: str) -> None:
        self._timewindow = timewindow

    def get_container_metric_metadata_query(self) -> LabelValuesQuery:
        return LabelValuesQuery(
            label_name=CONTAINER_UTILIZATION_METRIC_LABEL_NAME,
            metric_match=CONTAINER_UTILIZATION_METRIC_NAME,
        )

    def get_container_metric_type(
        self,
        metric_name: str,
        label: ContainerMetricOptionalLabel,
    ) -> MetricType:
        if metric_name in DIFF_METRICS and label.value_type == ValueType.CURRENT:
            return MetricType.DIFF
        if metric_name in RATE_METRICS:
            return MetricType.RATE
        return MetricType.GAUGE

    def get_container_metric_query(
        self,
        metric_name: str,
        label: ContainerMetricOptionalLabel,
    ) -> MetricPreset:
        querier = ContainerMetricQuerier(
            metric_name=metric_name,
            value_type=ValueType(label.value_type.value),
            kernel_id=label.kernel_id,
            session_id=label.session_id,
            agent_id=label.agent_id,
            user_id=label.user_id,
            project_id=label.project_id,
        )
        return MetricPreset(
            template=self._get_template(metric_name, label),
            labels=querier.labels(),
            group_by=querier.group_by_labels(),
            window=self._timewindow,
        )

    def _get_template(self, metric_name: str, label: ContainerMetricOptionalLabel) -> str:
        match label.value_type:
            case ValueType.CURRENT | ValueType.CAPACITY:
                return _SERIES_TEMPLATES[self.get_container_metric_type(metric_name, label)]
            case ValueType.PCT:
                return self._get_pct_template(metric_name)

    def _get_pct_template(self, metric_name: str) -> str:
        if resolve_container_metric_unit_hint(metric_name) in _COUNTER_UNIT_HINTS:
            return _PCT_RATE_TEMPLATE
        return _PCT_TEMPLATE


class ContainerLiveStatQueryBuilder:
    """Builds the per-query PromQL batch backing the legacy `live_stat`
    payload (`fetch_container_live_stats`)."""

    _timewindow: str

    def __init__(self, timewindow: str) -> None:
        self._timewindow = timewindow

    def get_container_live_stat_queries(
        self,
        kernel_ids: Sequence[KernelId],
    ) -> ContainerLiveStatQueries:
        kernel_id_regex = regex_union([str(kid) for kid in kernel_ids])

        instant_labels = {
            "kernel_id": LabelMatcher.regex(kernel_id_regex),
            "value_type": LabelMatcher.regex(_INSTANT_VALUE_TYPE_REGEX),
        }
        current_labels = {
            "kernel_id": LabelMatcher.regex(kernel_id_regex),
            "value_type": LabelMatcher.exact(ValueType.CURRENT.value),
        }
        rate_labels = {
            "kernel_id": LabelMatcher.regex(kernel_id_regex),
            "container_metric_name": LabelMatcher.regex(_LIVE_STAT_RATE_METRIC_REGEX),
            "value_type": LabelMatcher.exact(ValueType.CURRENT.value),
        }

        return ContainerLiveStatQueries(
            instant=MetricPreset(
                template=_GAUGE_TEMPLATE,
                labels=instant_labels,
                group_by=_INSTANT_GROUP_BY,
            ),
            rate_current=MetricPreset(
                template=_RATE_TEMPLATE,
                labels=rate_labels,
                group_by=_AGGREGATED_GROUP_BY,
                window=self._timewindow,
            ),
            max=MetricPreset(
                template=_LIVE_STAT_MAX_TEMPLATE,
                labels=current_labels,
                group_by=_AGGREGATED_GROUP_BY,
                window=self._timewindow,
            ),
            rate_max=MetricPreset(
                template=_LIVE_STAT_RATE_MAX_TEMPLATE,
                labels=rate_labels,
                group_by=_AGGREGATED_GROUP_BY,
                window=self._timewindow,
            ),
            avg=MetricPreset(
                template=_LIVE_STAT_AVG_TEMPLATE,
                labels=current_labels,
                group_by=_AGGREGATED_GROUP_BY,
                window=self._timewindow,
            ),
            rate_avg=MetricPreset(
                template=_LIVE_STAT_RATE_AVG_TEMPLATE,
                labels=rate_labels,
                group_by=_AGGREGATED_GROUP_BY,
                window=self._timewindow,
            ),
        )
