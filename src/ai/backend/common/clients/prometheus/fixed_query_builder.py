import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from ai.backend.common.clients.prometheus.metric_types import (
    DIFF_METRICS,
    RATE_METRICS,
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
)
from ai.backend.common.types import KernelId

_GAUGE_TEMPLATE: Final[str] = (
    f"sum by ({{group_by}})({CONTAINER_UTILIZATION_METRIC_NAME}{{{{{{labels}}}}}})"
)
_RATE_TEMPLATE: Final[str] = (
    "sum by ({group_by})(rate("
    f"{CONTAINER_UTILIZATION_METRIC_NAME}{{{{{{labels}}}}}}[{{window}}]))"
)
_DIFF_TEMPLATE: Final[str] = (
    "sum by ({group_by})(rate("
    f"{CONTAINER_UTILIZATION_METRIC_NAME}{{{{{{labels}}}}}}[{{window}}]))"
)
_LIVE_STAT_MAX_TEMPLATE: Final[str] = f"max_over_time(({_GAUGE_TEMPLATE})[{{window}}:])"
_LIVE_STAT_AVG_TEMPLATE: Final[str] = f"avg_over_time(({_GAUGE_TEMPLATE})[{{window}}:])"
_LIVE_STAT_RATE_MAX_TEMPLATE: Final[str] = f"max_over_time(({_RATE_TEMPLATE})[{{window}}:])"
_LIVE_STAT_RATE_AVG_TEMPLATE: Final[str] = f"avg_over_time(({_RATE_TEMPLATE})[{{window}}:])"

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


def _regex_union(values: Sequence[str]) -> str:
    return "|".join(re.escape(value).replace(r"\-", "-") for value in values)


def _value_type_regex(value_types: Sequence[ValueType]) -> str:
    return _regex_union([value_type.value for value_type in value_types])


_LIVE_STAT_RATE_METRIC_REGEX: Final[str] = _regex_union(sorted(RATE_METRICS | DIFF_METRICS))
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

    def _get_template(self, metric_type: MetricType) -> str:
        match metric_type:
            case MetricType.GAUGE:
                return _GAUGE_TEMPLATE
            case MetricType.RATE:
                return _RATE_TEMPLATE
            case MetricType.DIFF:
                return _DIFF_TEMPLATE


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
        kernel_id_regex = _regex_union([str(kid) for kid in kernel_ids])

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
