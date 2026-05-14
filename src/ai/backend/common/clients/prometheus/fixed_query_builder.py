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
from ai.backend.common.clients.prometheus.preset import MetricPreset
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

_LIVE_STAT_RATE_METRICS: Final[frozenset[str]] = RATE_METRICS | DIFF_METRICS

_LIVE_STAT_INSTANT_TEMPLATE: Final[str] = (
    f"sum by (kernel_id,container_metric_name,value_type)({CONTAINER_UTILIZATION_METRIC_NAME}"
    '{{kernel_id=~"{kernel_ids}",value_type=~"{value_types}"}})'
)

_LIVE_STAT_RATE_CURRENT_TEMPLATE: Final[str] = (
    f"sum by (kernel_id,container_metric_name)(rate("
    f"{CONTAINER_UTILIZATION_METRIC_NAME}"
    '{{kernel_id=~"{kernel_ids}",container_metric_name=~"{metric_names}",value_type="{value_type}"}}'
    "[{window}]))"
)

_LIVE_STAT_RATE_MAX_TEMPLATE: Final[str] = (
    f"max_over_time(({_LIVE_STAT_RATE_CURRENT_TEMPLATE})[{{window}}:])"
)

_LIVE_STAT_RATE_AVG_TEMPLATE: Final[str] = (
    f"avg_over_time(({_LIVE_STAT_RATE_CURRENT_TEMPLATE})[{{window}}:])"
)

_LIVE_STAT_MAX_TEMPLATE: Final[str] = (
    "max_over_time(("
    f"sum by (kernel_id,container_metric_name)({CONTAINER_UTILIZATION_METRIC_NAME}"
    '{{kernel_id=~"{kernel_ids}",value_type="{value_type}"}}'
    "))[{window}:])"
)

_LIVE_STAT_AVG_TEMPLATE: Final[str] = (
    "avg_over_time(("
    f"sum by (kernel_id,container_metric_name)({CONTAINER_UTILIZATION_METRIC_NAME}"
    '{{kernel_id=~"{kernel_ids}",value_type="{value_type}"}}'
    "))[{window}:])"
)


@dataclass(frozen=True)
class LabelValuesQuery:
    label_name: str
    metric_match: str


def _regex_union(values: Sequence[str]) -> str:
    return "|".join(re.escape(value).replace(r"\-", "-") for value in values)


def _value_type_regex(value_types: Sequence[ValueType]) -> str:
    return _regex_union([value_type.value for value_type in value_types])


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
        kernel_id_regex = _regex_union([str(kid) for kid in kernel_ids])

        instant_query = _LIVE_STAT_INSTANT_TEMPLATE.format(
            kernel_ids=kernel_id_regex,
            value_types=_value_type_regex([
                ValueType.CURRENT,
                ValueType.CAPACITY,
            ]),
        )
        rate_current_query = _LIVE_STAT_RATE_CURRENT_TEMPLATE.format(
            kernel_ids=kernel_id_regex,
            metric_names=_regex_union(sorted(_LIVE_STAT_RATE_METRICS)),
            value_type=ValueType.CURRENT.value,
            window=self._timewindow,
        )
        max_query = _LIVE_STAT_MAX_TEMPLATE.format(
            kernel_ids=kernel_id_regex,
            value_type=ValueType.CURRENT.value,
            window=self._timewindow,
        )
        rate_max_query = _LIVE_STAT_RATE_MAX_TEMPLATE.format(
            kernel_ids=kernel_id_regex,
            metric_names=_regex_union(sorted(_LIVE_STAT_RATE_METRICS)),
            value_type=ValueType.CURRENT.value,
            window=self._timewindow,
        )
        avg_query = _LIVE_STAT_AVG_TEMPLATE.format(
            kernel_ids=kernel_id_regex,
            value_type=ValueType.CURRENT.value,
            window=self._timewindow,
        )
        rate_avg_query = _LIVE_STAT_RATE_AVG_TEMPLATE.format(
            kernel_ids=kernel_id_regex,
            metric_names=_regex_union(sorted(_LIVE_STAT_RATE_METRICS)),
            value_type=ValueType.CURRENT.value,
            window=self._timewindow,
        )

        return ContainerLiveStatQueries(
            instant=MetricPreset(template=instant_query),
            rate_current=MetricPreset(template=rate_current_query),
            max=MetricPreset(template=max_query),
            rate_max=MetricPreset(template=rate_max_query),
            avg=MetricPreset(template=avg_query),
            rate_avg=MetricPreset(template=rate_avg_query),
        )

    def _get_template(self, metric_type: MetricType) -> str:
        match metric_type:
            case MetricType.GAUGE:
                return _GAUGE_TEMPLATE
            case MetricType.RATE:
                return _RATE_TEMPLATE
            case MetricType.DIFF:
                return _DIFF_TEMPLATE
