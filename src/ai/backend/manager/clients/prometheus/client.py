from collections.abc import Mapping, Sequence
from http import HTTPMethod
from typing import Any, cast

import aiohttp

from ai.backend.common.clients.http_client.client_pool import (
    ClientKey,
    ClientPool,
)
from ai.backend.common.clients.prometheus.preset import LabelMatcher, MetricPreset
from ai.backend.common.dto.clients.prometheus.request import QueryTimeRange
from ai.backend.common.dto.clients.prometheus.response import (
    LabelValueResponse,
    PrometheusResponse,
)
from ai.backend.common.exception import (
    FailedToGetMetric,
    PrometheusConnectionError,
)
from ai.backend.common.types import KernelId
from ai.backend.manager.clients.prometheus.fixed_query_builder import (
    ContainerLiveStatQueryBuilder,
    ContainerMetricQueryBuilder,
)
from ai.backend.manager.clients.prometheus.metric_types import (
    ContainerMetricOptionalLabel,
    ContainerMetricResponseInfo,
    ContainerMetricResult,
    KernelLiveStatBatchResult,
    MetricResultValue,
)

DEFAULT_TIMEOUT_SECONDS: float = 30.0


class PrometheusClient:
    """Client for querying Prometheus metrics."""

    _client_pool: ClientPool
    _client_key: ClientKey
    _timeout: aiohttp.ClientTimeout
    _container_metric_query_builder: ContainerMetricQueryBuilder
    _container_live_stat_query_builder: ContainerLiveStatQueryBuilder

    def __init__(
        self,
        endpoint: str,
        client_pool: ClientPool,
        *,
        container_metric_query_builder: ContainerMetricQueryBuilder,
        container_live_stat_query_builder: ContainerLiveStatQueryBuilder,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._client_pool = client_pool
        self._client_key = ClientKey(endpoint=endpoint, domain="prometheus")
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._container_metric_query_builder = container_metric_query_builder
        self._container_live_stat_query_builder = container_live_stat_query_builder

    async def fetch_available_container_metric_names(self) -> list[str]:
        query = self._container_metric_query_builder.get_container_metric_metadata_query()
        result = await self._query_label_values(
            label_name=query.label_name,
            metric_match=query.metric_match,
        )
        return result.data

    async def fetch_container_metric(
        self,
        metric_name: str,
        label: ContainerMetricOptionalLabel,
        time_range: QueryTimeRange,
    ) -> list[ContainerMetricResult]:
        query = self._container_metric_query_builder.get_container_metric_query(metric_name, label)
        response = await self._query_range(query, time_range)
        return [
            ContainerMetricResult(
                metric=ContainerMetricResponseInfo.from_metric_response_info(m.metric),
                values=[MetricResultValue(*value) for value in m.values],
            )
            for m in response.data.result
        ]

    async def fetch_container_live_stats(
        self,
        kernel_ids: Sequence[KernelId],
    ) -> KernelLiveStatBatchResult:
        queries = self._container_live_stat_query_builder.get_container_live_stat_queries(
            kernel_ids
        )

        # max/rate_max and avg/rate_avg are split: gauge metrics can be aggregated
        # directly, but cumulative counters (cpu_util/net_rx/net_tx) need rate() first.
        instant_res = await self._query_instant(queries.instant)
        rate_current_res = await self._query_instant(queries.rate_current)
        max_res = await self._query_instant(queries.max)
        rate_max_res = await self._query_instant(queries.rate_max)
        avg_res = await self._query_instant(queries.avg)
        rate_avg_res = await self._query_instant(queries.rate_avg)

        return KernelLiveStatBatchResult.from_responses(
            instant=instant_res,
            rate_current=rate_current_res,
            max=max_res,
            rate_max=rate_max_res,
            avg=avg_res,
            rate_avg=rate_avg_res,
        )

    async def execute_preset(
        self,
        *,
        query_template: str,
        filter_labels: Mapping[str, str],
        group_labels: Sequence[str],
        time_window: str,
        time_range: QueryTimeRange | None,
    ) -> PrometheusResponse:
        metric_preset = MetricPreset(
            template=query_template,
            labels={
                label_name: LabelMatcher.exact(label_value)
                for label_name, label_value in filter_labels.items()
            },
            group_by=set(group_labels),
            window=time_window,
        )
        if time_range is None:
            return await self._query_instant(preset=metric_preset)
        return await self._query_range(
            preset=metric_preset,
            time_range=time_range,
        )

    async def preview_query_template(
        self,
        query_template: str,
        default_window: str,
    ) -> PrometheusResponse:
        metric_preset = MetricPreset(
            template=query_template,
            labels={},
            group_by=frozenset(),
            window=default_window,
        )
        return await self._query_instant(preset=metric_preset)

    async def _query_range(
        self,
        preset: MetricPreset,
        time_range: QueryTimeRange,
    ) -> PrometheusResponse:
        """Execute a range query against Prometheus.

        Args:
            preset: The metric preset containing query template and values.
            time_range: The time range for the query.

        Returns:
            PrometheusResponse with query results.
        """
        query = preset.render()
        form_data = aiohttp.FormData({
            "query": query,
            "start": time_range.start,
            "end": time_range.end,
            "step": time_range.step,
        })
        result = await self._execute_request(HTTPMethod.POST, "query_range", data=form_data)
        return PrometheusResponse.model_validate(result)

    async def _query_instant(
        self,
        preset: MetricPreset,
        *,
        time: str | None = None,
    ) -> PrometheusResponse:
        """Execute an instant query against Prometheus.

        Args:
            preset: The metric preset containing query template and values.
            time: Optional evaluation timestamp (RFC3339 or Unix timestamp).

        Returns:
            PrometheusResponse with query results.
        """
        query = preset.render()
        form_fields: dict[str, str] = {"query": query}
        if time is not None:
            form_fields["time"] = time
        form_data = aiohttp.FormData(form_fields)
        result = await self._execute_request(HTTPMethod.POST, "query", data=form_data)
        return PrometheusResponse.model_validate(result)

    async def _query_label_values(
        self,
        label_name: str,
        metric_match: str,
    ) -> LabelValueResponse:
        """Query label values from Prometheus.

        Args:
            label_name: The label name to query values for.
            metric_match: The metric name to match (e.g., "backendai_container_utilization").

        Returns:
            LabelValueResponse containing the list of label values.
        """
        form_data = aiohttp.FormData({"match[]": metric_match})
        result = await self._execute_request(
            HTTPMethod.GET, f"label/{label_name}/values", data=form_data
        )
        return LabelValueResponse.model_validate(result)

    def _get_session(self) -> aiohttp.ClientSession:
        return self._client_pool.load_client_session(self._client_key)

    async def _execute_request(
        self,
        method: HTTPMethod,
        path: str,
        data: aiohttp.FormData | None = None,
    ) -> dict[str, Any]:
        session = self._get_session()
        request_fn = session.get if method == HTTPMethod.GET else session.post
        try:
            async with request_fn(path, data=data, timeout=self._timeout) as response:
                result = cast(dict[str, Any], await response.json())
                if response.ok:
                    return result
                error_msg = result.get("error", f"HTTP {response.status}")
                raise FailedToGetMetric(f"{error_msg} (status={response.status}, path={path})")
        except aiohttp.ClientError as e:
            raise PrometheusConnectionError(str(e)) from e
