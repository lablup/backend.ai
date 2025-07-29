import logging
from datetime import datetime

from ai.backend.common.clients.prometheus.container_util.client import ContainerUtilizationReader
from ai.backend.common.clients.prometheus.types import (
    ContainerUtilizationQueryParameter,
    QueryRange,
)
from ai.backend.common.metrics.types import (
    CONTAINER_UTILIZATION_METRIC_LABEL_NAME,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider

from .actions.container import (
    ContainerCurrentMetricAction,
    ContainerCurrentMetricActionResult,
    ContainerMetricAction,
    ContainerMetricActionResult,
    ContainerMetricMetadataAction,
    ContainerMetricMetadataActionResult,
)
from .types import (
    ContainerMetricOptionalLabel,
    ContainerMetricResult,
    UtilizationMetricType,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ContainerUtilizationMetricService:
    _config_provider: ManagerConfigProvider
    _util_reader: ContainerUtilizationReader

    def __init__(self, utilization_reader: ContainerUtilizationReader) -> None:
        self._util_reader = utilization_reader

    def _get_metric_type(
        self,
        metric_name: str,
        label: ContainerMetricOptionalLabel,
    ) -> UtilizationMetricType:
        # TODO: Define device metadata for each metric and use it rather than hardcoding
        match metric_name:
            case "cpu_util" if label.value_type == "current":
                return UtilizationMetricType.DIFF
            case "net_rx" | "net_tx":
                return UtilizationMetricType.RATE
            case _:
                return UtilizationMetricType.GAUGE

    async def query_metadata(
        self,
        action: ContainerMetricMetadataAction,
    ) -> ContainerMetricMetadataActionResult:
        result = await self._util_reader.get_label_values(CONTAINER_UTILIZATION_METRIC_LABEL_NAME)
        return ContainerMetricMetadataActionResult(result.data)

    async def query_metric(
        self,
        action: ContainerMetricAction,
    ) -> ContainerMetricActionResult:
        metric_type = self._get_metric_type(action.metric_name, action.labels)
        param = ContainerUtilizationQueryParameter(
            value_type=action.labels.value_type,
            container_metric_name=action.labels.container_metric_name,
            agent_id=action.labels.agent_id,
            kernel_id=action.labels.kernel_id,
            session_id=action.labels.session_id,
            user_id=action.labels.user_id,
            project_id=action.labels.project_id,
            range=QueryRange(
                action.step,
                datetime.fromisoformat(action.start),
                datetime.fromisoformat(action.end),
            ),
        )
        match metric_type:
            case UtilizationMetricType.GAUGE:
                data = await self._util_reader.get_container_utilization_gauge(param)
            case UtilizationMetricType.RATE:
                data = await self._util_reader.get_container_utilization_rate(param)
            case UtilizationMetricType.DIFF:
                data = await self._util_reader.get_container_utilization_diff(param)
        return ContainerMetricActionResult(
            result=[ContainerMetricResult.from_result(result) for result in data]
        )

    async def query_current_metric(
        self, action: ContainerCurrentMetricAction
    ) -> ContainerCurrentMetricActionResult:
        data = await self._util_reader.get_container_utilization(
            ContainerUtilizationQueryParameter(
                value_type=action.labels.value_type,
                container_metric_name=action.labels.container_metric_name,
                agent_id=action.labels.agent_id,
                kernel_id=action.labels.kernel_id,
                session_id=action.labels.session_id,
                user_id=action.labels.user_id,
                project_id=action.labels.project_id,
            )
        )
        return ContainerCurrentMetricActionResult(
            result=[ContainerMetricResult.from_result(result) for result in data]
        )
