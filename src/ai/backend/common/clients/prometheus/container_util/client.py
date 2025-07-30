from typing import Any

from ..base import PrometheusHTTPClient
from ..data.request import QueryData, QueryStringSpec
from ..data.response import LabelValueQueryResponseData, ResultValue
from ..defs import UTILIZATION_METRIC_INTERVAL
from ..exception import PrometheusException, ResultNotFound
from .data.request import ContainerUtilizationQueryParameter
from .data.response import ContainerUtilizationQueryResult


class ContainerUtilizationReader(PrometheusHTTPClient):
    def _get_label_values_for_query(self, label: ContainerUtilizationQueryParameter) -> list[str]:
        label_values: list[str] = []

        def _append_if_not_none(value: Any, name: str) -> None:
            if value is not None:
                label_values.append(f'{name}="{value}"')

        _append_if_not_none(label.container_metric_name, "container_metric_name")
        _append_if_not_none(label.value_type, "value_type")
        _append_if_not_none(label.agent_id, "agent_id")
        _append_if_not_none(label.kernel_id, "kernel_id")
        _append_if_not_none(label.session_id, "session_id")
        _append_if_not_none(label.user_id, "user_id")
        _append_if_not_none(label.project_id, "project_id")
        return label_values

    def _get_sum_by_for_query(self, label: ContainerUtilizationQueryParameter) -> list[str]:
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

    async def get_container_utilization(
        self, param: ContainerUtilizationQueryParameter
    ) -> list[ContainerUtilizationQueryResult]:
        label_values = self._get_label_values_for_query(param)
        spec = QueryStringSpec(param.container_metric_name, self._timewindow, [], label_values)
        query_string = f"backendai_container_utilization{spec.str_labels()}[{spec.timewindow}]"
        query_data = QueryData(
            query_string,
            start=param.range.start_iso if param.range else None,
            end=param.range.end_iso if param.range else None,
            step=param.range.step if param.range else None,
        )
        query_result = await self._query(query_data)
        return_val: list[ContainerUtilizationQueryResult] = []
        for result in query_result.result:
            if result.metric is None:
                continue
            return_val.append(
                ContainerUtilizationQueryResult(
                    metric=result.metric,
                    values=[
                        ResultValue(timestamp=value.timestamp, value=value.value)
                        for value in result.values
                    ],
                )
            )
        return return_val

    async def get_container_utilization_gauge(
        self, param: ContainerUtilizationQueryParameter
    ) -> list[ContainerUtilizationQueryResult]:
        label_values = self._get_label_values_for_query(param)
        sum_by_values = self._get_sum_by_for_query(param)
        spec = QueryStringSpec(
            param.container_metric_name, self._timewindow, sum_by_values, label_values
        )
        query_string = f"{spec.str_sum_by()}(backendai_container_utilization{spec.str_labels()})"
        query_data = QueryData(
            query_string,
            start=param.range.start_iso if param.range else None,
            end=param.range.end_iso if param.range else None,
            step=param.range.step if param.range else None,
        )
        query_result = await self._query_range(query_data)
        return_val: list[ContainerUtilizationQueryResult] = []
        for result in query_result.result:
            if result.metric is None:
                continue
            return_val.append(
                ContainerUtilizationQueryResult(
                    metric=result.metric,
                    values=[
                        ResultValue(timestamp=value.timestamp, value=value.value)
                        for value in result.values
                    ],
                )
            )
        return return_val

    async def get_container_utilization_rate(
        self,
        param: ContainerUtilizationQueryParameter,
        interval: float = UTILIZATION_METRIC_INTERVAL,
    ) -> list[ContainerUtilizationQueryResult]:
        label_values = self._get_label_values_for_query(param)
        sum_by_values = self._get_sum_by_for_query(param)
        spec = QueryStringSpec(
            param.container_metric_name, self._timewindow, sum_by_values, label_values
        )
        query_string = (
            f"{spec.str_sum_by()}(rate(backendai_container_utilization{spec.str_labels()}[{spec.timewindow}])) "
            f"/ {interval}"
        )
        query_data = QueryData(
            query_string,
            start=param.range.start_iso if param.range else None,
            end=param.range.end_iso if param.range else None,
            step=param.range.step if param.range else None,
        )
        query_result = await self._query_range(query_data)
        return_val: list[ContainerUtilizationQueryResult] = []
        for result in query_result.result:
            if result.metric is None:
                continue
            return_val.append(
                ContainerUtilizationQueryResult(
                    metric=result.metric,
                    values=[
                        ResultValue(timestamp=value.timestamp, value=value.value)
                        for value in result.values
                    ],
                )
            )
        return return_val

    async def get_container_utilization_diff(
        self, param: ContainerUtilizationQueryParameter
    ) -> list[ContainerUtilizationQueryResult]:
        label_values = self._get_label_values_for_query(param)
        sum_by_values = self._get_sum_by_for_query(param)
        spec = QueryStringSpec(
            param.container_metric_name, self._timewindow, sum_by_values, label_values
        )
        query_string = f"{spec.str_sum_by()}(rate(backendai_container_utilization{spec.str_labels()}[{spec.timewindow}]))"
        query_data = QueryData(
            query_string,
            start=param.range.start_iso if param.range else None,
            end=param.range.end_iso if param.range else None,
            step=param.range.step if param.range else None,
        )
        query_result = await self._query_range(query_data)
        return_val: list[ContainerUtilizationQueryResult] = []
        for result in query_result.result:
            if result.metric is None:
                continue
            return_val.append(
                ContainerUtilizationQueryResult(
                    metric=result.metric,
                    values=[
                        ResultValue(timestamp=value.timestamp, value=value.value)
                        for value in result.values
                    ],
                )
            )
        return return_val

    async def get_label_values(self, label_name: str) -> LabelValueQueryResponseData:
        address = self._endpoint / "label" / label_name / "values"
        client = self._load_client(str(address))
        async with client.get(address) as response:
            match response.status // 100:
                case 2:
                    raw_data = await response.json()
                    return LabelValueQueryResponseData(**raw_data)
                case 4:
                    raise ResultNotFound("No label values found")
                case _:
                    raise PrometheusException(f"Failed to get label values: {response.status}")
