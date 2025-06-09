import logging
from typing import (
    Any,
    Optional,
)

import aiohttp
import yarl
from pydantic import BaseModel, ConfigDict, Field

from ai.backend.common.metrics.types import (
    CONTAINER_UTILIZATION_METRIC_LABEL_NAME,
    UTILIZATION_METRIC_INTERVAL,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.config.provider import ManagerConfigProvider

from .actions.container import (
    ContainerMetricAction,
    ContainerMetricActionResult,
    ContainerMetricMetadataAction,
    ContainerMetricMetadataActionResult,
)
from .exceptions import FailedToGetMetric
from .types import (
    ContainerMetricOptionalLabel,
    ContainerMetricResponseInfo,
    ContainerMetricResult,
    MetricResultValue,
    MetricSpecForQuery,
    UtilizationMetricType,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class LabelValueResponse(BaseModel):
    status: str
    data: list[str]


class MetricResponseInfo(BaseModel):
    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)

    value_type: str
    name: Optional[str] = Field(
        default=None, validation_alias="__name__"
    )  # "backendai_container_utilization"
    agent_id: Optional[str] = Field(default=None)
    container_metric_name: Optional[str] = Field(default=None)
    instance: Optional[str] = Field(default=None)
    job: Optional[str] = Field(default=None)
    kernel_id: Optional[str] = Field(default=None)
    owner_project_id: Optional[str] = Field(default=None)
    owner_user_id: Optional[str] = Field(default=None)
    session_id: Optional[str] = Field(default=None)

    def to_response_info(self) -> ContainerMetricResponseInfo:
        return ContainerMetricResponseInfo(
            value_type=self.value_type,
            agent_id=self.agent_id,
            container_metric_name=self.container_metric_name,
            instance=self.instance,
            job=self.job,
            kernel_id=self.kernel_id,
            owner_project_id=self.owner_project_id,
            owner_user_id=self.owner_user_id,
            session_id=self.session_id,
        )


type MetricResponseValue = tuple[float, str]  # (timestamp, value)


class MetricResponse(BaseModel):
    metric: MetricResponseInfo
    values: list[MetricResponseValue]


class ContainerUtilizationMetricService:
    _config_provider: ManagerConfigProvider

    def __init__(self, config_provider: ManagerConfigProvider) -> None:
        self._config_provider = config_provider

    @property
    def _metric_query_endpoint(self) -> yarl.URL:
        metric_query_addr = self._config_provider.config.metric.address.to_legacy()
        return yarl.URL(f"http://{metric_query_addr}/api/v1")

    @property
    def _range_vector_timewindow(self) -> str:
        # 1m by default
        return self._config_provider.config.metric.timewindow

    async def _query_label_values(self, label_name: str) -> LabelValueResponse:
        endpoint = self._metric_query_endpoint / "label" / label_name / "values"
        form_data = aiohttp.FormData({"match[]": "backendai_container_utilization"})
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, data=form_data) as response:
                response.raise_for_status()
                data = await response.json()
        return LabelValueResponse(**data)

    async def query_metadata(
        self,
        action: ContainerMetricMetadataAction,
    ) -> ContainerMetricMetadataActionResult:
        result = await self._query_label_values(CONTAINER_UTILIZATION_METRIC_LABEL_NAME)
        return ContainerMetricMetadataActionResult(result.data)

    def _get_label_values_for_query(
        self, label: ContainerMetricOptionalLabel, metric_name: str
    ) -> list[str]:
        label_values: list[str] = [
            f'container_metric_name="{metric_name}"',
        ]

        def _append_if_not_none(value: Any, name: str) -> None:
            if value is not None:
                label_values.append(f'{name}="{value}"')

        _append_if_not_none(label.value_type, "value_type")
        _append_if_not_none(label.agent_id, "agent_id")
        _append_if_not_none(label.kernel_id, "kernel_id")
        _append_if_not_none(label.session_id, "session_id")
        _append_if_not_none(label.user_id, "user_id")
        _append_if_not_none(label.project_id, "project_id")
        return label_values

    def _get_sum_by_for_query(self, label: ContainerMetricOptionalLabel) -> list[str]:
        sum_by_values = ["value_type"]

        def _append_if_not_none(value: Any, name: str) -> None:
            if value is not None:
                sum_by_values.append(name)

        _append_if_not_none(label.agent_id, "agent_id")
        _append_if_not_none(label.kernel_id, "kernel_id")
        _append_if_not_none(label.session_id, "session_id")
        _append_if_not_none(label.user_id, "user_id")
        _append_if_not_none(label.project_id, "project_id")
        return sum_by_values

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

    def _parse_query_string_by_metric_spec(
        self,
        param: MetricSpecForQuery,
    ) -> str:
        match param.metric_type:
            case UtilizationMetricType.GAUGE:
                return f"{param.str_sum_by()}(backendai_container_utilization{param.str_labels()})"
            case UtilizationMetricType.RATE:
                return (
                    f"{param.str_sum_by()}(rate(backendai_container_utilization{param.str_labels()}[{param.timewindow}])) "
                    f"/ {UTILIZATION_METRIC_INTERVAL}"
                )
            case UtilizationMetricType.DIFF:
                return f"{param.str_sum_by()}(rate(backendai_container_utilization{param.str_labels()}[{param.timewindow}]))"

    async def _get_query_string(
        self,
        metric_name: str,
        label: ContainerMetricOptionalLabel,
    ) -> str:
        metric_type = self._get_metric_type(metric_name, label)
        label_values = self._get_label_values_for_query(label, metric_name)
        sum_by_values = self._get_sum_by_for_query(label)
        return self._parse_query_string_by_metric_spec(
            MetricSpecForQuery(
                metric_name=metric_name,
                metric_type=metric_type,
                timewindow=self._range_vector_timewindow,
                sum_by=sum_by_values,
                labels=label_values,
            )
        )

    async def query_metric(
        self,
        action: ContainerMetricAction,
    ) -> ContainerMetricActionResult:
        endpoint = self._metric_query_endpoint / "query_range"
        query = await self._get_query_string(action.metric_name, action.labels)
        form_data = aiohttp.FormData({
            "query": query,
            "start": action.start,
            "end": action.end,
            "step": action.step,
        })
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, data=form_data) as response:
                match response.status // 100:
                    case 2:
                        result = await response.json()
                    case 4:
                        result = await response.json()
                        msg = result.get("error", "Unknown error")
                        log.exception(f"Failed to get metric: {msg}")
                        raise FailedToGetMetric(msg)
                    case _:
                        log.exception(f"Failed to get metric. code: {response.status}")
                        raise FailedToGetMetric

        metrics: list[MetricResponse] = [
            MetricResponse(**data) for data in result["data"]["result"]
        ]
        return ContainerMetricActionResult(
            result=[
                ContainerMetricResult(
                    metric=m.metric.to_response_info(),
                    values=[MetricResultValue(*value) for value in m.values],
                )
                for m in metrics
            ]
        )
