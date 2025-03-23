from typing import (
    TypedDict,
    cast,
)

import aiohttp
import yarl

from .actions.container import (
    ContainerMetricAction,
    ContainerMetricActionResult,
    ContainerMetricLabelValuesAction,
    ContainerMetricLabelValuesActionResult,
)
from .types import (
    ContainerMetricOptionalLabel,
    ContainerMetricResponseInfo,
    ContainerMetricResult,
    MetricResultValue,
    ServiceInitParameter,
)


class _LabelValueResponse(TypedDict):
    status: str
    data: list[str]


class MetricResponseInfo(TypedDict):
    __name__: str  # "backendai_container_utilization"
    agent_id: str
    container_metric_name: str
    instance: str
    job: str
    kernel_id: str
    owner_project_id: str
    owner_user_id: str
    session_id: str
    value_type: str


def to_response_info(val: MetricResponseInfo) -> ContainerMetricResponseInfo:
    return ContainerMetricResponseInfo(
        agent_id=val["agent_id"],
        container_metric_name=val["container_metric_name"],
        instance=val["instance"],
        job=val["job"],
        kernel_id=val["kernel_id"],
        owner_project_id=val["owner_project_id"],
        owner_user_id=val["owner_user_id"],
        session_id=val["session_id"],
        value_type=val["value_type"],
    )


type MetricResponseValue = tuple[float, str]  # (timestamp, value)


class MetricResponse(TypedDict):
    metric: MetricResponseInfo
    values: list[MetricResponseValue]


class MetricService:
    _metric_query_endpoint: yarl.URL

    def __init__(self, param: ServiceInitParameter) -> None:
        self._metric_query_endpoint = yarl.URL(f"http://{param.metric_query_addr}/api/v1")

    async def query_label_values(
        self,
        action: ContainerMetricLabelValuesAction,
    ) -> ContainerMetricLabelValuesActionResult:
        endpoint = self._metric_query_endpoint / "label" / action.label / "values"
        form_data = aiohttp.FormData({"match[]": "backendai_container_utilization"})
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, data=form_data) as response:
                response.raise_for_status()
                result = cast(_LabelValueResponse, await response.json())
        return ContainerMetricLabelValuesActionResult(result["status"], result["data"])

    def _get_query_string(
        self,
        metric_name: str,
        value_type: str,
        label: ContainerMetricOptionalLabel,
    ) -> str:
        label_values: list[str] = [
            f'container_metric_name="{metric_name}"',
            f'value_type="{value_type}"',
        ]
        if label.agent_id is not None:
            label_values.append(f'agent_id="{label.agent_id}"')
        if label.kernel_id is not None:
            label_values.append(f'kernel_id="{label.kernel_id}"')
        if label.session_id is not None:
            label_values.append(f'session_id="{label.session_id}"')
        if label.user_id is not None:
            label_values.append(f'owner_user_id="{label.user_id}"')
        if label.project_id is not None:
            label_values.append(f'owner_project_id="{label.project_id}"')
        labels = ",".join(label_values)
        return f"backendai_container_utilization{{{labels}}}"

    async def query_metric(
        self,
        action: ContainerMetricAction,
    ) -> ContainerMetricActionResult:
        endpoint = self._metric_query_endpoint / "query_range"
        query = self._get_query_string(action.metric_name, action.value_type, action.labels)
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
