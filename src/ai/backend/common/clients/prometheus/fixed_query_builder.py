import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from ai.backend.common.clients.prometheus.metric_types import (
    DIFF_METRICS,
    RATE_METRICS,
    STATS_AVG_GAUGE_METRIC_PATTERNS,
    STATS_AVG_GAUGE_METRICS,
    STATS_AVG_OVER_RATE_METRICS,
    STATS_MAX_GAUGE_METRIC_PATTERNS,
    STATS_MAX_GAUGE_METRICS,
    STATS_MAX_OVER_RATE_METRICS,
    STATS_RATE_COUNTER_METRICS,
    STATS_RATE_GAUGE_METRICS,
    ContainerLiveStatQueries,
    ContainerMetricOptionalLabel,
    MetricType,
)
from ai.backend.common.clients.prometheus.preset import LabelMatcher, MetricPreset
from ai.backend.common.clients.prometheus.querier import ContainerMetricQuerier
from ai.backend.common.clients.prometheus.types import ValueType
from ai.backend.common.metrics.types import (
    CONTAINER_UTILIZATION_METRIC_LABEL_NAME,
    CONTAINER_UTILIZATION_METRIC_NAME,
    UTILIZATION_METRIC_INTERVAL,
)
from ai.backend.common.types import KernelId

_LIVE_STAT_GROUP_BY: Final[frozenset[str]] = frozenset({
    "kernel_id",
    "container_metric_name",
    "value_type",
})

_GAUGE_TEMPLATE: Final[str] = (
    f"sum by ({{group_by}})({CONTAINER_UTILIZATION_METRIC_NAME}{{{{{{labels}}}}}})"
)
_RATE_TEMPLATE: Final[str] = (
    "sum by ({group_by})(rate("
    f"{CONTAINER_UTILIZATION_METRIC_NAME}{{{{{{labels}}}}}}[{{window}}]))"
    f" / {UTILIZATION_METRIC_INTERVAL}"
)
_DIFF_TEMPLATE: Final[str] = (
    "sum by ({group_by})(rate("
    f"{CONTAINER_UTILIZATION_METRIC_NAME}{{{{{{labels}}}}}}[{{window}}]))"
)


@dataclass(frozen=True)
class LabelValuesQuery:
    label_name: str
    metric_match: str


@dataclass(frozen=True)
class _LiveStatQuerySpec:
    template: str
    metric_name_filter: frozenset[str] | None = None
    value_type_filter: ValueType | None = None


@dataclass(frozen=True)
class _StatsBucket:
    """Window-stats bucket spec (gauge metrics + rate metrics for a single stat)."""

    value_type: ValueType
    gauge_metrics: frozenset[str]
    rate_metrics: frozenset[str]
    gauge_metric_patterns: frozenset[str] = frozenset()


def _regex_union(values: Sequence[str]) -> str:
    return "|".join(re.escape(value).replace(r"\-", "-") for value in values)


def _metric_name_regex(
    metric_names: frozenset[str],
    metric_patterns: frozenset[str] = frozenset(),
) -> str:
    exact_parts = [re.escape(value) for value in sorted(metric_names)]
    return "|".join([*exact_parts, *sorted(metric_patterns)])


_GAUGE_LIVE_STAT_SPEC: Final[_LiveStatQuerySpec] = _LiveStatQuerySpec(
    template=_GAUGE_TEMPLATE,
)
_DIFF_LIVE_STAT_SPEC: Final[_LiveStatQuerySpec] = _LiveStatQuerySpec(
    template=_DIFF_TEMPLATE,
    metric_name_filter=DIFF_METRICS,
    value_type_filter=ValueType.CURRENT,
)
_RATE_LIVE_STAT_SPEC: Final[_LiveStatQuerySpec] = _LiveStatQuerySpec(
    template=_RATE_TEMPLATE,
    metric_name_filter=RATE_METRICS,
    value_type_filter=ValueType.CURRENT,
)

_MAX_STATS_BUCKET: Final[_StatsBucket] = _StatsBucket(
    value_type=ValueType.MAX,
    gauge_metrics=STATS_MAX_GAUGE_METRICS,
    rate_metrics=STATS_MAX_OVER_RATE_METRICS,
    gauge_metric_patterns=STATS_MAX_GAUGE_METRIC_PATTERNS,
)
_AVG_STATS_BUCKET: Final[_StatsBucket] = _StatsBucket(
    value_type=ValueType.AVG,
    gauge_metrics=STATS_AVG_GAUGE_METRICS,
    rate_metrics=STATS_AVG_OVER_RATE_METRICS,
    gauge_metric_patterns=STATS_AVG_GAUGE_METRIC_PATTERNS,
)


class FixedQueryBuilder:
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
        metric_type = self.get_container_metric_type(metric_name, label)
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
            template=self._get_template(metric_type),
            labels=querier.labels(),
            group_by=querier.group_by_labels(),
            window=self._timewindow,
        )

    def get_container_live_stat_queries(
        self,
        kernel_ids: Sequence[KernelId],
    ) -> ContainerLiveStatQueries:
        return ContainerLiveStatQueries(
            gauge=self._build_filtered_preset(kernel_ids, _GAUGE_LIVE_STAT_SPEC),
            diff=self._build_filtered_preset(kernel_ids, _DIFF_LIVE_STAT_SPEC),
            rate=self._build_filtered_preset(kernel_ids, _RATE_LIVE_STAT_SPEC),
            max=self._build_window_stats_preset(kernel_ids, _MAX_STATS_BUCKET),
            avg=self._build_window_stats_preset(kernel_ids, _AVG_STATS_BUCKET),
            rate_stats=self._build_rate_stats_preset(kernel_ids),
        )

    def _build_rate_stats_preset(
        self,
        kernel_ids: Sequence[KernelId],
    ) -> MetricPreset:
        kernel_id_regex = _regex_union([str(kid) for kid in kernel_ids])
        group_by = ",".join(sorted(_LIVE_STAT_GROUP_BY))
        parts: list[str] = []
        if STATS_RATE_GAUGE_METRICS:
            gauge_regex = _regex_union(sorted(STATS_RATE_GAUGE_METRICS))
            selector = self._utilization_selector(kernel_id_regex, gauge_regex)
            parts.append(self._labelled_sum(selector, group_by, ValueType.RATE))
        if STATS_RATE_COUNTER_METRICS:
            counter_regex = _regex_union(sorted(STATS_RATE_COUNTER_METRICS))
            base = self._utilization_selector(kernel_id_regex, counter_regex)
            selector = f"rate({base}[{self._timewindow}])"
            parts.append(self._labelled_sum(selector, group_by, ValueType.RATE))
        return MetricPreset(template=" or ".join(parts))

    def _labelled_sum(self, selector: str, group_by: str, stat_label: ValueType) -> str:
        return (
            f"label_replace(sum by ({group_by})({selector}),"
            f'"value_type","{stat_label}","value_type",".*")'
        )

    def _build_window_stats_preset(
        self,
        kernel_ids: Sequence[KernelId],
        bucket: _StatsBucket,
    ) -> MetricPreset:
        kernel_id_regex = _regex_union([str(kid) for kid in kernel_ids])
        group_by = ",".join(sorted(_LIVE_STAT_GROUP_BY))
        return MetricPreset(
            template=self._render_stats_query(
                bucket,
                kernel_id_regex=kernel_id_regex,
                group_by=group_by,
            )
        )

    def _build_filtered_preset(
        self,
        kernel_ids: Sequence[KernelId],
        spec: _LiveStatQuerySpec,
    ) -> MetricPreset:
        labels: dict[str, LabelMatcher] = {
            "kernel_id": LabelMatcher.regex(_regex_union([str(kid) for kid in kernel_ids]))
        }
        if spec.metric_name_filter is not None:
            labels["container_metric_name"] = LabelMatcher.regex(
                _regex_union(sorted(spec.metric_name_filter))
            )
        if spec.value_type_filter is not None:
            labels["value_type"] = LabelMatcher.exact(spec.value_type_filter.value)

        return MetricPreset(
            template=spec.template,
            group_by=_LIVE_STAT_GROUP_BY,
            labels=labels,
            window=self._timewindow,
        )

    def _render_stats_query(
        self,
        bucket: _StatsBucket,
        *,
        kernel_id_regex: str,
        group_by: str,
    ) -> str:
        stat_fn = f"{bucket.value_type}_over_time"
        parts: list[str] = []
        if bucket.gauge_metrics or bucket.gauge_metric_patterns:
            gauge_regex = _metric_name_regex(bucket.gauge_metrics, bucket.gauge_metric_patterns)
            selector = self._utilization_selector(kernel_id_regex, gauge_regex)
            parts.append(self._window_stat_subquery(stat_fn, selector, group_by, bucket.value_type))
        if bucket.rate_metrics:
            rate_regex = _regex_union(sorted(bucket.rate_metrics))
            base = self._utilization_selector(kernel_id_regex, rate_regex)
            selector = f"rate({base}[{self._timewindow}])"
            parts.append(self._window_stat_subquery(stat_fn, selector, group_by, bucket.value_type))
        return " or ".join(parts)

    def _utilization_selector(self, kernel_id_regex: str, metric_name_regex: str) -> str:
        labels = self._live_stat_current_labels(
            kernel_id_regex=kernel_id_regex,
            metric_name_regex=metric_name_regex,
        )
        return f"{CONTAINER_UTILIZATION_METRIC_NAME}{{{labels}}}"

    def _window_stat_subquery(
        self,
        stat_fn: str,
        selector: str,
        group_by: str,
        stat_label: ValueType,
    ) -> str:
        return (
            f"label_replace("
            f"{stat_fn}((sum by ({group_by})({selector}))[{self._timewindow}:]),"
            f'"value_type","{stat_label}","value_type",".*")'
        )

    def _live_stat_current_labels(
        self,
        *,
        kernel_id_regex: str,
        metric_name_regex: str,
    ) -> str:
        return (
            f'kernel_id=~"{kernel_id_regex}"'
            f',container_metric_name=~"{metric_name_regex}"'
            f',value_type="{ValueType.CURRENT}"'
        )

    def _get_template(self, metric_type: MetricType) -> str:
        match metric_type:
            case MetricType.GAUGE:
                return _GAUGE_TEMPLATE
            case MetricType.RATE:
                return _RATE_TEMPLATE
            case MetricType.DIFF:
                return _DIFF_TEMPLATE
