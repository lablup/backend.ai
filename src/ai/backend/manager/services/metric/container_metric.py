from typing import (
    Optional,
    TypedDict,
)

import aiohttp
import yarl

from ai.backend.common.metrics.types import (
    CONTAINER_UTILIZATION_METRIC_LABEL_NAME,
    UTILIZATION_METRIC_INTERVAL,
)
from ai.backend.common.types import HostPortPair

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
)


class LabelValueResponse(TypedDict):
    status: str
    data: list[str]


class MetricResponseInfo(TypedDict):
    value_type: str
    __name__: Optional[str]  # "backendai_container_utilization"
    agent_id: Optional[str]
    container_metric_name: Optional[str]
    instance: Optional[str]
    job: Optional[str]
    kernel_id: Optional[str]
    owner_project_id: Optional[str]
    owner_user_id: Optional[str]
    session_id: Optional[str]


def to_response_info(val: MetricResponseInfo) -> ContainerMetricResponseInfo:
    return ContainerMetricResponseInfo(
        value_type=val["value_type"],
        agent_id=val.get("agent_id"),
        container_metric_name=val.get("container_metric_name"),
        instance=val.get("instance"),
        job=val.get("job"),
        kernel_id=val.get("kernel_id"),
        owner_project_id=val.get("owner_project_id"),
        owner_user_id=val.get("owner_user_id"),
        session_id=val.get("session_id"),
    )


type MetricResponseValue = tuple[float, str]  # (timestamp, value)


class MetricResponse(TypedDict):
    metric: MetricResponseInfo
    values: list[MetricResponseValue]


class MetricService:
    _metric_query_endpoint: yarl.URL

    def __init__(self, metric_query_addr: HostPortPair) -> None:
        self._metric_query_endpoint = yarl.URL(f"http://{metric_query_addr}/api/v1")

    async def _query_label_values(self, label_name: str) -> LabelValueResponse:
        endpoint = self._metric_query_endpoint / "label" / label_name / "values"
        form_data = aiohttp.FormData({"match[]": "backendai_container_utilization"})
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, data=form_data) as response:
                response.raise_for_status()
                return await response.json()

    async def query_metadata(
        self,
        action: ContainerMetricMetadataAction,
    ) -> ContainerMetricMetadataActionResult:
        result = await self._query_label_values(CONTAINER_UTILIZATION_METRIC_LABEL_NAME)
        return ContainerMetricMetadataActionResult(result["data"])

    def _parse_query_string_by_metric_spec(
        self,
        metric_name: str,
        sum_by: str,
        labels: str,
    ) -> str:
        match metric_name:
            case "cpu_util":
                return f"sum by ({sum_by}) (rate(backendai_container_utilization{{{labels}}}[1m]))"
            case "net_rx" | "net_tx":
                return f"sum by ({sum_by}) (rate(backendai_container_utilization{{{labels}}}[1m])) / {UTILIZATION_METRIC_INTERVAL}"
            case _:
                return f"sum by ({sum_by}) (backendai_container_utilization{{{labels}}})"

    def _get_query_string(
        self,
        metric_name: str,
        label: ContainerMetricOptionalLabel,
    ) -> str:
        label_values = label.get_label_values_for_query(metric_name)
        sum_by_values = label.get_sum_by_for_query()
        labels = ",".join(label_values)
        sum_by = ",".join(sum_by_values)
        return self._parse_query_string_by_metric_spec(metric_name, sum_by, labels)

    async def query_metric(
        self,
        action: ContainerMetricAction,
    ) -> ContainerMetricActionResult:
        endpoint = self._metric_query_endpoint / "query_range"
        query = self._get_query_string(action.metric_name, action.labels)
        form_data = aiohttp.FormData({
            "query": query,
            "start": action.start,
            "end": action.end,
            "step": action.step,
        })
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, data=form_data) as response:
                response.raise_for_status()
                result = await response.json()

        metrics: list[MetricResponse] = result["data"]["result"]
        return ContainerMetricActionResult(
            result=[
                ContainerMetricResult(
                    metric=to_response_info(m["metric"]),
                    values=[MetricResultValue(*value) for value in m["values"]],
                )
                for m in metrics
            ]
        )
