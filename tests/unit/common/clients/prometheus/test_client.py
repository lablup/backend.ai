from typing import Any
from unittest.mock import AsyncMock, Mock

import aiohttp
import pytest

from ai.backend.common.clients.prometheus import (
    MetricPreset,
    PrometheusClient,
)
from ai.backend.common.dto.clients.prometheus import (
    LabelValueResponse,
    PrometheusQueryRangeResponse,
    QueryTimeRange,
)
from ai.backend.common.exception import FailedToGetMetric, PrometheusConnectionError


def create_mock_response(
    status: int,
    json_data: dict[str, Any] | None = None,
    *,
    connection_error: bool = False,
) -> AsyncMock:
    """Create a mock response with async context manager support."""
    mock_response = AsyncMock()
    mock_response.__aexit__ = AsyncMock(return_value=None)
    mock_response.status = status
    mock_response.ok = 200 <= status < 300

    if connection_error:
        mock_response.__aenter__ = AsyncMock(side_effect=aiohttp.ClientError("Connection refused"))
    else:
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)

    if json_data is not None:
        mock_response.json = AsyncMock(return_value=json_data)

    return mock_response


@pytest.fixture
def mock_session() -> Mock:
    return Mock(spec=aiohttp.ClientSession)


@pytest.fixture
def mock_pool(mock_session: Mock) -> Mock:
    pool = Mock()
    pool.load_client_session.return_value = mock_session
    return pool


@pytest.fixture
def prometheus_client(mock_pool: Mock) -> PrometheusClient:
    return PrometheusClient(
        endpoint="http://localhost:9090/api/v1",
        client_pool=mock_pool,
    )


class TestQueryRange:
    """Tests for PrometheusClient.query_range() method."""

    @pytest.fixture
    def sample_preset(self) -> MetricPreset:
        return MetricPreset(
            template="sum(my_metric{{{labels}}}) by ({group_by})",
            labels={"container_metric_name": "mem", "value_type": "current"},
            group_by=frozenset({"value_type"}),
            window="5m",
        )

    @pytest.fixture
    def sample_time_range(self) -> QueryTimeRange:
        return QueryTimeRange(
            start="2024-01-01T00:00:00Z",
            end="2024-01-01T01:00:00Z",
            step="60s",
        )

    @pytest.fixture
    def success_response(self, mock_session: Mock) -> AsyncMock:
        response = create_mock_response(
            status=200,
            json_data={
                "status": "success",
                "data": {
                    "resultType": "matrix",
                    "result": [
                        {
                            "metric": {"value_type": "current"},
                            "values": [[1704067200.0, "10.5"]],
                        }
                    ],
                },
            },
        )
        mock_session.post.return_value = response
        return response

    async def test_success_returns_parsed_response(
        self,
        prometheus_client: PrometheusClient,
        sample_preset: MetricPreset,
        sample_time_range: QueryTimeRange,
        success_response: AsyncMock,
    ) -> None:
        result = await prometheus_client.query_range(sample_preset, sample_time_range)

        assert isinstance(result, PrometheusQueryRangeResponse)
        assert result.status == "success"
        assert result.data.result_type == "matrix"
        assert len(result.data.result) == 1

    @pytest.fixture
    def error_4xx_response(self, mock_session: Mock) -> AsyncMock:
        response = create_mock_response(
            status=400,
            json_data={"status": "error", "error": "Bad Request: Invalid query"},
        )
        mock_session.post.return_value = response
        return response

    async def test_http_4xx_raises_failed_to_get_metric(
        self,
        prometheus_client: PrometheusClient,
        sample_preset: MetricPreset,
        sample_time_range: QueryTimeRange,
        error_4xx_response: AsyncMock,
    ) -> None:
        with pytest.raises(FailedToGetMetric, match="Bad Request: Invalid query"):
            await prometheus_client.query_range(sample_preset, sample_time_range)

    @pytest.fixture
    def error_5xx_response(self, mock_session: Mock) -> AsyncMock:
        response = create_mock_response(
            status=500,
            json_data={"status": "error", "error": "Internal Server Error"},
        )
        mock_session.post.return_value = response
        return response

    async def test_http_5xx_raises_failed_to_get_metric(
        self,
        prometheus_client: PrometheusClient,
        sample_preset: MetricPreset,
        sample_time_range: QueryTimeRange,
        error_5xx_response: AsyncMock,
    ) -> None:
        with pytest.raises(FailedToGetMetric):
            await prometheus_client.query_range(sample_preset, sample_time_range)

    @pytest.fixture
    def connection_error_response(self, mock_session: Mock) -> AsyncMock:
        response = create_mock_response(status=200, connection_error=True)
        mock_session.post.return_value = response
        return response

    async def test_connection_error_raises_prometheus_connection_error(
        self,
        prometheus_client: PrometheusClient,
        sample_preset: MetricPreset,
        sample_time_range: QueryTimeRange,
        connection_error_response: AsyncMock,
    ) -> None:
        with pytest.raises(PrometheusConnectionError):
            await prometheus_client.query_range(sample_preset, sample_time_range)


class TestTimeout:
    """Tests for PrometheusClient timeout behavior."""

    @pytest.fixture
    def mock_session(self) -> Mock:
        return Mock(spec=aiohttp.ClientSession)

    @pytest.fixture
    def mock_pool(self, mock_session: Mock) -> Mock:
        pool = Mock()
        pool.load_client_session.return_value = mock_session
        return pool

    @pytest.fixture
    def client_with_custom_timeout(self, mock_pool: Mock) -> PrometheusClient:
        return PrometheusClient(
            endpoint="http://localhost:9090/api/v1",
            client_pool=mock_pool,
            timeout=5.0,
        )

    @pytest.fixture
    def sample_preset(self) -> MetricPreset:
        return MetricPreset(
            template="sum(my_metric{{{labels}}})",
            labels={},
            group_by=frozenset(),
        )

    @pytest.fixture
    def sample_time_range(self) -> QueryTimeRange:
        return QueryTimeRange(
            start="2024-01-01T00:00:00Z",
            end="2024-01-01T01:00:00Z",
            step="60s",
        )

    @pytest.fixture
    def timeout_response(self, mock_session: Mock) -> AsyncMock:
        """Create a response that simulates a timeout error."""
        mock_response = AsyncMock()
        mock_response.__aenter__ = AsyncMock(
            side_effect=aiohttp.ServerTimeoutError("Connection timeout")
        )
        mock_response.__aexit__ = AsyncMock(return_value=None)
        mock_session.post.return_value = mock_response
        return mock_response

    async def test_timeout_raises_prometheus_connection_error(
        self,
        client_with_custom_timeout: PrometheusClient,
        sample_preset: MetricPreset,
        sample_time_range: QueryTimeRange,
        timeout_response: AsyncMock,
    ) -> None:
        with pytest.raises(PrometheusConnectionError):
            await client_with_custom_timeout.query_range(sample_preset, sample_time_range)


class TestQueryLabelValues:
    """Tests for PrometheusClient.query_label_values() method."""

    @pytest.fixture
    def success_response(self, mock_session: Mock) -> AsyncMock:
        response = create_mock_response(
            status=200,
            json_data={
                "status": "success",
                "data": ["cpu_util", "mem_used", "net_rx", "net_tx"],
            },
        )
        mock_session.get.return_value = response
        return response

    async def test_success_returns_label_list(
        self,
        prometheus_client: PrometheusClient,
        success_response: AsyncMock,
    ) -> None:
        result = await prometheus_client.query_label_values(
            label_name="container_metric_name",
            metric_match="backendai_container_utilization",
        )

        assert isinstance(result, LabelValueResponse)
        assert result.status == "success"
        assert result.data == ["cpu_util", "mem_used", "net_rx", "net_tx"]

    @pytest.fixture
    def error_4xx_response(self, mock_session: Mock) -> AsyncMock:
        response = create_mock_response(
            status=400,
            json_data={"status": "error", "error": "Bad Request"},
        )
        mock_session.get.return_value = response
        return response

    async def test_http_error_raises_failed_to_get_metric(
        self,
        prometheus_client: PrometheusClient,
        error_4xx_response: AsyncMock,
    ) -> None:
        with pytest.raises(FailedToGetMetric):
            await prometheus_client.query_label_values(
                label_name="container_metric_name",
                metric_match="backendai_container_utilization",
            )

    @pytest.fixture
    def connection_error_response(self, mock_session: Mock) -> AsyncMock:
        response = create_mock_response(status=200, connection_error=True)
        mock_session.get.return_value = response
        return response

    async def test_connection_error_raises_prometheus_connection_error(
        self,
        prometheus_client: PrometheusClient,
        connection_error_response: AsyncMock,
    ) -> None:
        with pytest.raises(PrometheusConnectionError):
            await prometheus_client.query_label_values(
                label_name="container_metric_name",
                metric_match="backendai_container_utilization",
            )
