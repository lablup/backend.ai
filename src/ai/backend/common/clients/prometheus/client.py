from typing import Any, Literal, cast

import aiohttp

from ai.backend.common.clients.http_client.client_pool import (
    ClientKey,
    ClientPool,
)
from ai.backend.common.dto.clients.prometheus.request import QueryTimeRange
from ai.backend.common.dto.clients.prometheus.response import (
    LabelValueResponse,
    PrometheusQueryRangeResponse,
)
from ai.backend.common.exception import FailedToGetMetric, PrometheusConnectionError

from .preset import MetricPreset

DEFAULT_TIMEOUT_SECONDS: float = 30.0


class PrometheusClient:
    """Client for querying Prometheus metrics."""

    _client_pool: ClientPool
    _client_key: ClientKey
    _timeout: aiohttp.ClientTimeout

    def __init__(
        self,
        endpoint: str,
        client_pool: ClientPool,
        *,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._client_pool = client_pool
        self._client_key = ClientKey(endpoint=endpoint, domain="prometheus")
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    async def query_range(
        self,
        preset: MetricPreset,
        time_range: QueryTimeRange,
    ) -> PrometheusQueryRangeResponse:
        """Execute a range query against Prometheus.

        Args:
            preset: The metric preset containing query template and values.
            time_range: The time range for the query.

        Returns:
            PrometheusQueryRangeResponse with query results.
        """
        query = preset.render()
        form_data = aiohttp.FormData({
            "query": query,
            "start": time_range.start,
            "end": time_range.end,
            "step": time_range.step,
        })
        result = await self._execute_request("post", "/query_range", data=form_data)
        return PrometheusQueryRangeResponse.model_validate(result)

    async def query_label_values(
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
        result = await self._execute_request("get", f"/label/{label_name}/values", data=form_data)
        return LabelValueResponse.model_validate(result)

    def _get_session(self) -> aiohttp.ClientSession:
        return self._client_pool.load_client_session(self._client_key)

    async def _execute_request(
        self,
        method: Literal["get", "post"],
        path: str,
        data: aiohttp.FormData | None = None,
    ) -> dict[str, Any]:
        session = self._get_session()
        request_fn = session.get if method == "get" else session.post
        try:
            async with request_fn(path, data=data, timeout=self._timeout) as response:
                result = cast(dict[str, Any], await response.json())
                if response.ok:
                    return result
                error_msg = result.get("error", f"HTTP {response.status}")
                raise FailedToGetMetric(f"{error_msg} (status={response.status}, path={path})")
        except aiohttp.ClientError as e:
            raise PrometheusConnectionError(str(e)) from e
