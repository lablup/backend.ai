import logging
from datetime import datetime

from ai.backend.common.clients.prometheus.data.request import QueryRange
from ai.backend.common.clients.prometheus.device_util.client import DeviceUtilizationReader
from ai.backend.common.clients.prometheus.device_util.data.request import (
    DeviceUtilizationQueryParameter,
)
from ai.backend.common.metrics.types import (
    CONTAINER_UTILIZATION_METRIC_LABEL_NAME,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider

from .actions.device import (
    DeviceCurrentMetricAction,
    DeviceCurrentMetricActionResult,
    DeviceMetricAction,
    DeviceMetricActionResult,
    DeviceMetricMetadataAction,
    DeviceMetricMetadataActionResult,
)
from .types import (
    DeviceMetricOptionalLabel,
    DeviceMetricResult,
    UtilizationMetricType,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class DeviceUtilizationMetricService:
    _config_provider: ManagerConfigProvider

    def __init__(self, utilization_reader: DeviceUtilizationReader) -> None:
        self._util_reader = utilization_reader

    def _get_metric_type(
        self,
        metric_name: str,
        label: DeviceMetricOptionalLabel,
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
        action: DeviceMetricMetadataAction,
    ) -> DeviceMetricMetadataActionResult:
        result = await self._util_reader.get_label_values(CONTAINER_UTILIZATION_METRIC_LABEL_NAME)
        return DeviceMetricMetadataActionResult(result.data)

    async def query_metric(
        self,
        action: DeviceMetricAction,
    ) -> DeviceMetricActionResult:
        metric_type = self._get_metric_type(action.metric_name, action.labels)
        param = DeviceUtilizationQueryParameter(
            value_type=action.labels.value_type,
            device_metric_name=action.metric_name,
            agent_id=action.labels.agent_id,
            device_id=action.labels.device_id,
            range=QueryRange(
                action.step,
                datetime.fromisoformat(action.start),
                datetime.fromisoformat(action.end),
            ),
        )
        match metric_type:
            case UtilizationMetricType.GAUGE:
                data = await self._util_reader.get_device_utilization_gauge(param)
            case UtilizationMetricType.RATE:
                data = await self._util_reader.get_device_utilization_rate(param)
            case UtilizationMetricType.DIFF:
                data = await self._util_reader.get_device_utilization_diff(param)
        return DeviceMetricActionResult(
            result=[DeviceMetricResult.from_result(result) for result in data]
        )

    async def query_current_metric(
        self, action: DeviceCurrentMetricAction
    ) -> DeviceCurrentMetricActionResult:
        data = await self._util_reader.get_device_utilization(
            DeviceUtilizationQueryParameter(
                value_type=action.labels.value_type,
                device_metric_name=action.labels.device_metric_name,
                agent_id=action.labels.agent_id,
                device_id=action.labels.device_id,
            )
        )
        return DeviceCurrentMetricActionResult(
            result=[DeviceMetricResult.from_result(result) for result in data]
        )
