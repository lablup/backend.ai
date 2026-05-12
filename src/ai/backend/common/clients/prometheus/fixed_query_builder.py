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


def _regex_union(values: Sequence[str]) -> str:
    return "|".join(re.escape(value) for value in values)


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
            gauge=self._get_container_live_stat_query(
                kernel_ids,
                metric_type=MetricType.GAUGE,
            ),
            diff=self._get_container_live_stat_query(
                kernel_ids,
                metric_type=MetricType.DIFF,
                metric_name_filter=DIFF_METRICS,
                value_type_filter=ValueType.CURRENT,
            ),
            rate=self._get_container_live_stat_query(
                kernel_ids,
                metric_type=MetricType.RATE,
                metric_name_filter=RATE_METRICS,
                value_type_filter=ValueType.CURRENT,
            ),
        )

    def _get_container_live_stat_query(
        self,
        kernel_ids: Sequence[KernelId],
        *,
        metric_type: MetricType,
        metric_name_filter: frozenset[str] | None = None,
        value_type_filter: ValueType | None = None,
    ) -> MetricPreset:
        labels: dict[str, LabelMatcher] = {
            "kernel_id": LabelMatcher.regex(_regex_union([str(kid) for kid in kernel_ids]))
        }
        if metric_name_filter is not None:
            labels["container_metric_name"] = LabelMatcher.regex(
                _regex_union(sorted(metric_name_filter))
            )
        if value_type_filter is not None:
            labels["value_type"] = LabelMatcher.exact(value_type_filter.value)

        return MetricPreset(
            template=self._get_template(metric_type),
            labels=labels,
            group_by=_LIVE_STAT_GROUP_BY,
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
