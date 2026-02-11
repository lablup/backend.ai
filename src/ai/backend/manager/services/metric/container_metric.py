import logging
from typing import Final

from ai.backend.common.clients.prometheus.client import PrometheusClient
from ai.backend.common.clients.prometheus.preset import MetricPreset
from ai.backend.common.clients.prometheus.querier import ContainerMetricQuerier
from ai.backend.common.clients.prometheus.types import ValueType as PrometheusValueType
from ai.backend.common.metrics.types import (
    CONTAINER_UTILIZATION_METRIC_LABEL_NAME,
    UTILIZATION_METRIC_INTERVAL,
)
from ai.backend.logging import BraceStyleAdapter

from .actions.container import (
    ContainerMetricAction,
    ContainerMetricActionResult,
    ContainerMetricMetadataAction,
    ContainerMetricMetadataActionResult,
)
from .types import (
    ContainerMetricOptionalLabel,
    ContainerMetricResponseInfo,
    ContainerMetricResult,
    MetricResultValue,
    UtilizationMetricType,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

CONTAINER_UTILIZATION_METRIC_NAME: Final[str] = "backendai_container_utilization"


class ContainerUtilizationMetricService:
    _client: PrometheusClient
    _timewindow: str

    def __init__(self, client: PrometheusClient, *, timewindow: str) -> None:
        self._client = client
        self._timewindow = timewindow

    async def query_metadata(
        self,
        _action: ContainerMetricMetadataAction,
    ) -> ContainerMetricMetadataActionResult:
        result = await self._client.query_label_values(
            label_name=CONTAINER_UTILIZATION_METRIC_LABEL_NAME,
            metric_match=CONTAINER_UTILIZATION_METRIC_NAME,
        )
        return ContainerMetricMetadataActionResult(result.data)

    def _get_metric_type(
        self,
        metric_name: str,
        label: ContainerMetricOptionalLabel,
    ) -> UtilizationMetricType:
        # TODO: Refactor metric type detection to query metric metadata from the repository layer
        match metric_name:
            case "cpu_util" if label.value_type == "current":
                return UtilizationMetricType.DIFF
            case "net_rx" | "net_tx":
                return UtilizationMetricType.RATE
            case _:
                return UtilizationMetricType.GAUGE

    def _build_preset(
        self,
        metric_name: str,
        label: ContainerMetricOptionalLabel,
    ) -> MetricPreset:
        metric_type = self._get_metric_type(metric_name, label)
        querier = ContainerMetricQuerier(
            metric_name=metric_name,
            value_type=PrometheusValueType(label.value_type.value),
            kernel_id=label.kernel_id,
            session_id=label.session_id,
            agent_id=label.agent_id,
            user_id=label.user_id,
            project_id=label.project_id,
        )
        match metric_type:
            # TODO: Define device metadata for each metric
            # TODO: Refactor metric template retrieval to query metric metadata from the repository layer
            case UtilizationMetricType.GAUGE:
                template = (
                    "sum by ({group_by})(" + CONTAINER_UTILIZATION_METRIC_NAME + "{{{labels}}})"
                )
            case UtilizationMetricType.RATE:
                template = (
                    "sum by ({group_by})(rate("
                    + CONTAINER_UTILIZATION_METRIC_NAME
                    + "{{{labels}}}[{window}]))"
                    " / " + str(UTILIZATION_METRIC_INTERVAL)
                )
            case UtilizationMetricType.DIFF:
                template = (
                    "sum by ({group_by})(rate("
                    + CONTAINER_UTILIZATION_METRIC_NAME
                    + "{{{labels}}}[{window}]))"
                )
            case _:
                raise ValueError(f"Unknown metric type: {metric_type}")
        return MetricPreset(
            template=template,
            labels=querier.labels(),
            group_by=querier.group_by_labels(),
            window=self._timewindow,
        )

    async def query_metric(
        self,
        action: ContainerMetricAction,
    ) -> ContainerMetricActionResult:
        preset = self._build_preset(action.metric_name, action.labels)
        response = await self._client.query_range(preset, action.time_range)
        return ContainerMetricActionResult(
            result=[
                ContainerMetricResult(
                    metric=ContainerMetricResponseInfo.from_metric_response_info(m.metric),
                    values=[MetricResultValue(*value) for value in m.values],
                )
                for m in response.data.result
            ]
        )
