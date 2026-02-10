"""
Tests for ContainerUtilizationMetricService with PrometheusClient.
"""

from typing import Any
from unittest.mock import AsyncMock, Mock
from uuid import UUID

import pytest

from ai.backend.common.clients.prometheus.client import PrometheusClient
from ai.backend.common.dto.clients.prometheus.request import QueryTimeRange
from ai.backend.common.dto.clients.prometheus.response import (
    LabelValueResponse,
    MetricResponse,
    MetricResponseInfo,
    PrometheusQueryData,
    PrometheusQueryRangeResponse,
)
from ai.backend.common.exception import FailedToGetMetric, PrometheusConnectionError
from ai.backend.manager.services.metric.actions.container import (
    ContainerMetricAction,
    ContainerMetricActionResult,
    ContainerMetricMetadataAction,
)
from ai.backend.manager.services.metric.container_metric import (
    ContainerUtilizationMetricService,
)
from ai.backend.manager.services.metric.types import (
    ContainerMetricOptionalLabel,
    ContainerMetricResponseInfo,
    UtilizationMetricType,
    ValueType,
)


def _make_query_range_response(
    metric_data: list[dict[str, Any]],
) -> PrometheusQueryRangeResponse:
    """Helper to build PrometheusQueryRangeResponse from raw metric dicts."""
    return PrometheusQueryRangeResponse(
        status="success",
        data=PrometheusQueryData(
            result_type="matrix",
            result=[
                MetricResponse(
                    metric=MetricResponseInfo(**d["metric"]),
                    values=d["values"],
                )
                for d in metric_data
            ],
        ),
    )


class TestContainerMetricServiceWithPrometheusClient:
    """Characterization tests: verify public interface behavior with PrometheusClient."""

    @pytest.fixture
    def mock_prometheus_client(self) -> Mock:
        return Mock(spec=PrometheusClient)

    @pytest.fixture
    def metric_service(self, mock_prometheus_client: Mock) -> ContainerUtilizationMetricService:
        return ContainerUtilizationMetricService(mock_prometheus_client, timewindow="1m")

    # -- query_metadata --

    @pytest.fixture
    def mock_label_values_with_metrics(self, mock_prometheus_client: Mock) -> Mock:
        mock_prometheus_client.query_label_values = AsyncMock(
            return_value=LabelValueResponse(
                status="success",
                data=[
                    "container_cpu_percent",
                    "container_memory_used_bytes",
                    "container_network_rx_bytes",
                    "container_network_tx_bytes",
                ],
            )
        )
        return mock_prometheus_client

    @pytest.mark.asyncio
    async def test_query_metadata_returns_metric_names(
        self,
        metric_service: ContainerUtilizationMetricService,
        mock_label_values_with_metrics: Mock,
    ) -> None:
        result = await metric_service.query_metadata(ContainerMetricMetadataAction())

        assert isinstance(result.metric_names, list)
        assert len(result.metric_names) == 4
        assert "container_cpu_percent" in result.metric_names

    @pytest.fixture
    def mock_label_values_empty(self, mock_prometheus_client: Mock) -> Mock:
        mock_prometheus_client.query_label_values = AsyncMock(
            return_value=LabelValueResponse(status="success", data=[])
        )
        return mock_prometheus_client

    @pytest.mark.asyncio
    async def test_query_metadata_empty_result(
        self,
        metric_service: ContainerUtilizationMetricService,
        mock_label_values_empty: Mock,
    ) -> None:
        result = await metric_service.query_metadata(ContainerMetricMetadataAction())

        assert len(result.metric_names) == 0

    @pytest.fixture
    def mock_label_values_connection_error(self, mock_prometheus_client: Mock) -> Mock:
        mock_prometheus_client.query_label_values = AsyncMock(
            side_effect=PrometheusConnectionError("Connection failed")
        )
        return mock_prometheus_client

    @pytest.mark.asyncio
    async def test_query_metadata_propagates_connection_error(
        self,
        metric_service: ContainerUtilizationMetricService,
        mock_label_values_connection_error: Mock,
    ) -> None:
        with pytest.raises(PrometheusConnectionError):
            await metric_service.query_metadata(ContainerMetricMetadataAction())

    # -- query_metric: GAUGE (memory) --

    @pytest.fixture
    def mock_query_range_gauge_memory(self, mock_prometheus_client: Mock) -> Mock:
        mock_prometheus_client.query_range = AsyncMock(
            return_value=_make_query_range_response([
                {
                    "metric": {
                        "value_type": "current",
                        "__name__": "backendai_container_utilization",
                        "container_metric_name": "container_memory_used_bytes",
                    },
                    "values": [(1704067200.0, "1048576"), (1704067260.0, "2097152")],
                }
            ])
        )
        return mock_prometheus_client

    @pytest.mark.asyncio
    async def test_query_metric_gauge_returns_correct_result(
        self,
        metric_service: ContainerUtilizationMetricService,
        mock_query_range_gauge_memory: Mock,
    ) -> None:
        action = ContainerMetricAction(
            metric_name="container_memory_used_bytes",
            labels=ContainerMetricOptionalLabel(value_type=ValueType.CURRENT),
            time_range=QueryTimeRange(
                start="2024-01-01T00:00:00", end="2024-01-01T00:05:00", step="60s"
            ),
        )
        result = await metric_service.query_metric(action)

        assert isinstance(result, ContainerMetricActionResult)
        assert len(result.result) == 1
        assert result.result[0].metric.container_metric_name == "container_memory_used_bytes"
        assert result.result[0].metric.value_type == "current"
        assert len(result.result[0].values) == 2

    # -- query_metric: RATE (network tx by agent) --

    @pytest.fixture
    def mock_query_range_rate_net_tx(self, mock_prometheus_client: Mock) -> Mock:
        mock_prometheus_client.query_range = AsyncMock(
            return_value=_make_query_range_response([
                {
                    "metric": {
                        "value_type": "current",
                        "__name__": "backendai_container_utilization",
                        "container_metric_name": "container_network_tx_bytes",
                        "agent_id": "agent-1",
                    },
                    "values": [(1704067200.0, "1024000"), (1704067500.0, "2048000")],
                }
            ])
        )
        return mock_prometheus_client

    @pytest.mark.asyncio
    async def test_query_metric_rate_returns_correct_result(
        self,
        metric_service: ContainerUtilizationMetricService,
        mock_query_range_rate_net_tx: Mock,
    ) -> None:
        action = ContainerMetricAction(
            metric_name="net_tx",
            labels=ContainerMetricOptionalLabel(
                value_type=ValueType.CURRENT,
                agent_id="agent-1",
            ),
            time_range=QueryTimeRange(
                start="2024-01-01T00:00:00", end="2024-01-01T00:15:00", step="300"
            ),
        )
        result = await metric_service.query_metric(action)

        assert isinstance(result, ContainerMetricActionResult)
        assert result.result[0].metric.agent_id == "agent-1"

    # -- query_metric: DIFF (cpu_util by kernel) --

    @pytest.fixture
    def mock_query_range_diff_cpu_util(self, mock_prometheus_client: Mock) -> Mock:
        mock_prometheus_client.query_range = AsyncMock(
            return_value=_make_query_range_response([
                {
                    "metric": {
                        "value_type": "current",
                        "__name__": "backendai_container_utilization",
                        "container_metric_name": "cpu_util",
                        "kernel_id": "12345678-1234-5678-1234-567812345678",
                    },
                    "values": [
                        (1704067200.0, "10.5"),
                        (1704067260.0, "12.3"),
                        (1704067320.0, "15.7"),
                    ],
                }
            ])
        )
        return mock_prometheus_client

    @pytest.mark.asyncio
    async def test_query_metric_diff_returns_correct_result(
        self,
        metric_service: ContainerUtilizationMetricService,
        mock_query_range_diff_cpu_util: Mock,
    ) -> None:
        action = ContainerMetricAction(
            metric_name="cpu_util",
            labels=ContainerMetricOptionalLabel(
                value_type=ValueType.CURRENT,
                kernel_id=UUID("12345678-1234-5678-1234-567812345678"),
            ),
            time_range=QueryTimeRange(
                start="2024-01-01T00:00:00", end="2024-01-01T01:00:00", step="60s"
            ),
        )
        result = await metric_service.query_metric(action)

        assert isinstance(result, ContainerMetricActionResult)
        assert len(result.result) == 1
        assert result.result[0].metric.container_metric_name == "cpu_util"
        assert len(result.result[0].values) == 3
        assert float(result.result[0].values[0].value) == 10.5

    # -- query_metric: by project --

    @pytest.fixture
    def mock_query_range_by_project(self, mock_prometheus_client: Mock) -> Mock:
        mock_prometheus_client.query_range = AsyncMock(
            return_value=_make_query_range_response([
                {
                    "metric": {
                        "value_type": "current",
                        "__name__": "backendai_container_utilization",
                        "container_metric_name": "container_cpu_percent",
                        "owner_project_id": "87654321-4321-8765-4321-876543218765",
                    },
                    "values": [(1704067200.0, "45.2")],
                }
            ])
        )
        return mock_prometheus_client

    @pytest.mark.asyncio
    async def test_query_metric_by_project(
        self,
        metric_service: ContainerUtilizationMetricService,
        mock_query_range_by_project: Mock,
    ) -> None:
        action = ContainerMetricAction(
            metric_name="container_cpu_percent",
            labels=ContainerMetricOptionalLabel(
                value_type=ValueType.CURRENT,
                project_id=UUID("87654321-4321-8765-4321-876543218765"),
            ),
            time_range=QueryTimeRange(
                start="2024-01-01T00:00:00", end="2024-01-01T01:00:00", step="60"
            ),
        )
        result = await metric_service.query_metric(action)

        assert isinstance(result, ContainerMetricActionResult)
        assert result.result[0].metric.owner_project_id == "87654321-4321-8765-4321-876543218765"

    # -- query_metric: by user --

    @pytest.fixture
    def mock_query_range_by_user(self, mock_prometheus_client: Mock) -> Mock:
        mock_prometheus_client.query_range = AsyncMock(
            return_value=_make_query_range_response([
                {
                    "metric": {
                        "value_type": "current",
                        "__name__": "backendai_container_utilization",
                        "container_metric_name": "container_gpu_percent",
                        "owner_user_id": "11223344-5566-7788-99aa-bbccddeeff00",
                    },
                    "values": [(1704067200.0, "80.5")],
                }
            ])
        )
        return mock_prometheus_client

    @pytest.mark.asyncio
    async def test_query_metric_by_user(
        self,
        metric_service: ContainerUtilizationMetricService,
        mock_query_range_by_user: Mock,
    ) -> None:
        action = ContainerMetricAction(
            metric_name="container_gpu_percent",
            labels=ContainerMetricOptionalLabel(
                value_type=ValueType.CURRENT,
                user_id=UUID("11223344-5566-7788-99aa-bbccddeeff00"),
            ),
            time_range=QueryTimeRange(
                start="2024-01-01T00:00:00", end="2024-01-01T01:00:00", step="60"
            ),
        )
        result = await metric_service.query_metric(action)

        assert isinstance(result, ContainerMetricActionResult)
        assert result.result[0].metric.owner_user_id == "11223344-5566-7788-99aa-bbccddeeff00"

    # -- query_metric: multiple labels --

    @pytest.fixture
    def mock_query_range_multiple_labels(self, mock_prometheus_client: Mock) -> Mock:
        mock_prometheus_client.query_range = AsyncMock(
            return_value=_make_query_range_response([
                {
                    "metric": {
                        "value_type": "current",
                        "__name__": "backendai_container_utilization",
                        "container_metric_name": "container_cpu_percent",
                        "agent_id": "agent-1",
                        "kernel_id": "aabbccdd-eeff-0011-2233-445566778899",
                    },
                    "values": [(1704067200.0, "25.3")],
                }
            ])
        )
        return mock_prometheus_client

    @pytest.mark.asyncio
    async def test_query_metric_with_multiple_labels(
        self,
        metric_service: ContainerUtilizationMetricService,
        mock_query_range_multiple_labels: Mock,
    ) -> None:
        action = ContainerMetricAction(
            metric_name="container_cpu_percent",
            labels=ContainerMetricOptionalLabel(
                value_type=ValueType.CURRENT,
                agent_id="agent-1",
                kernel_id=UUID("aabbccdd-eeff-0011-2233-445566778899"),
            ),
            time_range=QueryTimeRange(
                start="2024-01-01T00:00:00", end="2024-01-01T01:00:00", step="60"
            ),
        )
        result = await metric_service.query_metric(action)

        assert isinstance(result, ContainerMetricActionResult)
        assert result.result[0].metric.agent_id == "agent-1"
        assert result.result[0].metric.kernel_id == "aabbccdd-eeff-0011-2233-445566778899"

    # -- query_metric: empty result --

    @pytest.fixture
    def mock_query_range_empty(self, mock_prometheus_client: Mock) -> Mock:
        mock_prometheus_client.query_range = AsyncMock(return_value=_make_query_range_response([]))
        return mock_prometheus_client

    @pytest.mark.asyncio
    async def test_query_metric_empty_result(
        self,
        metric_service: ContainerUtilizationMetricService,
        mock_query_range_empty: Mock,
    ) -> None:
        action = ContainerMetricAction(
            metric_name="invalid_metric_name",
            labels=ContainerMetricOptionalLabel(value_type=ValueType.CURRENT),
            time_range=QueryTimeRange(
                start="2024-01-01T00:00:00", end="2024-01-01T01:00:00", step="60"
            ),
        )
        result = await metric_service.query_metric(action)

        assert isinstance(result, ContainerMetricActionResult)
        assert len(result.result) == 0

    # -- query_metric: error propagation --

    @pytest.fixture
    def mock_query_range_failed_to_get_metric(self, mock_prometheus_client: Mock) -> Mock:
        mock_prometheus_client.query_range = AsyncMock(
            side_effect=FailedToGetMetric("Bad Request: Invalid query")
        )
        return mock_prometheus_client

    @pytest.mark.asyncio
    async def test_query_metric_propagates_failed_to_get_metric(
        self,
        metric_service: ContainerUtilizationMetricService,
        mock_query_range_failed_to_get_metric: Mock,
    ) -> None:
        action = ContainerMetricAction(
            metric_name="container_cpu_percent",
            labels=ContainerMetricOptionalLabel(value_type=ValueType.CURRENT),
            time_range=QueryTimeRange(
                start="2024-01-01T00:00:00", end="2024-01-01T01:00:00", step="60"
            ),
        )
        with pytest.raises(FailedToGetMetric):
            await metric_service.query_metric(action)

    @pytest.fixture
    def mock_query_range_connection_error(self, mock_prometheus_client: Mock) -> Mock:
        mock_prometheus_client.query_range = AsyncMock(
            side_effect=PrometheusConnectionError("Connection refused")
        )
        return mock_prometheus_client

    @pytest.mark.asyncio
    async def test_query_metric_propagates_connection_error(
        self,
        metric_service: ContainerUtilizationMetricService,
        mock_query_range_connection_error: Mock,
    ) -> None:
        action = ContainerMetricAction(
            metric_name="container_cpu_percent",
            labels=ContainerMetricOptionalLabel(value_type=ValueType.CURRENT),
            time_range=QueryTimeRange(
                start="2024-01-01T00:00:00", end="2024-01-01T01:00:00", step="60"
            ),
        )
        with pytest.raises(PrometheusConnectionError):
            await metric_service.query_metric(action)

    # -- query_metric: capacity value type --

    @pytest.fixture
    def mock_query_range_capacity(self, mock_prometheus_client: Mock) -> Mock:
        mock_prometheus_client.query_range = AsyncMock(
            return_value=_make_query_range_response([
                {
                    "metric": {
                        "value_type": "capacity",
                        "__name__": "backendai_container_utilization",
                        "container_metric_name": "mem",
                    },
                    "values": [(1704067200.0, "8589934592")],
                }
            ])
        )
        return mock_prometheus_client

    @pytest.mark.asyncio
    async def test_query_metric_capacity_value_type(
        self,
        metric_service: ContainerUtilizationMetricService,
        mock_query_range_capacity: Mock,
    ) -> None:
        action = ContainerMetricAction(
            metric_name="container_memory_capacity_bytes",
            labels=ContainerMetricOptionalLabel(value_type=ValueType.CAPACITY),
            time_range=QueryTimeRange(
                start="2024-01-01T00:00:00", end="2024-01-01T01:00:00", step="60s"
            ),
        )
        result = await metric_service.query_metric(action)

        assert result.result[0].metric.value_type == "capacity"


class TestMetricTypeDetection:
    """Test metric type detection logic."""

    @pytest.fixture
    def metric_service(self) -> ContainerUtilizationMetricService:
        """Create metric service instance."""
        mock_client = Mock(spec=PrometheusClient)
        return ContainerUtilizationMetricService(mock_client, timewindow="1m")

    def test_cpu_util_detected_as_diff_type(
        self, metric_service: ContainerUtilizationMetricService
    ) -> None:
        """Test CPU utilization metric is detected as DIFF type."""
        metric_type = metric_service._get_metric_type(
            "cpu_util", ContainerMetricOptionalLabel(value_type=ValueType.CURRENT)
        )
        assert metric_type == UtilizationMetricType.DIFF

    def test_network_metrics_detected_as_rate_type(
        self, metric_service: ContainerUtilizationMetricService
    ) -> None:
        """Test network metrics are detected as RATE type."""
        for metric_name in ["net_rx", "net_tx"]:
            metric_type = metric_service._get_metric_type(
                metric_name, ContainerMetricOptionalLabel(value_type=ValueType.CURRENT)
            )
            assert metric_type == UtilizationMetricType.RATE

    def test_memory_metrics_detected_as_gauge_type(
        self, metric_service: ContainerUtilizationMetricService
    ) -> None:
        """Test memory and GPU metrics are detected as GAUGE type."""
        for metric_name in ["container_memory_used_bytes", "container_gpu_percent"]:
            metric_type = metric_service._get_metric_type(
                metric_name, ContainerMetricOptionalLabel(value_type=ValueType.CURRENT)
            )
            assert metric_type == UtilizationMetricType.GAUGE


class TestContainerMetricDataTypes:
    """Test data types used in container metric service."""

    def test_container_metric_action_fields(self) -> None:
        """Test that ContainerMetricAction has all expected fields."""
        action = ContainerMetricAction(
            metric_name="container_cpu_percent",
            labels=ContainerMetricOptionalLabel(
                value_type=ValueType.CURRENT,
                agent_id="agent-1",
                kernel_id=UUID("12345678-1234-5678-1234-567812345678"),
                session_id=UUID("87654321-4321-8765-4321-876543218765"),
                user_id=UUID("11223344-5566-7788-99aa-bbccddeeff00"),
                project_id=UUID("aabbccdd-eeff-0011-2233-445566778899"),
            ),
            time_range=QueryTimeRange(
                start="2024-01-01T00:00:00", end="2024-01-01T01:00:00", step="60s"
            ),
        )

        assert action.metric_name == "container_cpu_percent"
        assert action.time_range.start == "2024-01-01T00:00:00"
        assert action.time_range.end == "2024-01-01T01:00:00"
        assert action.time_range.step == "60s"
        assert action.labels.value_type == ValueType.CURRENT
        assert action.labels.agent_id == "agent-1"
        assert isinstance(action.labels.kernel_id, UUID)
        assert isinstance(action.labels.session_id, UUID)
        assert isinstance(action.labels.user_id, UUID)
        assert isinstance(action.labels.project_id, UUID)

    def test_container_metric_response_fields(self) -> None:
        """Test that ContainerMetricResponseInfo supports all expected fields."""
        response_info = ContainerMetricResponseInfo(
            value_type="current",
            container_metric_name="container_cpu_percent",
            agent_id="agent-1",
            instance="instance-1",
            job="job-1",
            kernel_id="12345678-1234-5678-1234-567812345678",
            owner_project_id="87654321-4321-8765-4321-876543218765",
            owner_user_id="11223344-5566-7788-99aa-bbccddeeff00",
            session_id="aabbccdd-eeff-0011-2233-445566778899",
        )

        assert response_info.value_type == "current"
        assert response_info.container_metric_name == "container_cpu_percent"
        assert response_info.agent_id == "agent-1"
        assert response_info.instance == "instance-1"
        assert response_info.job == "job-1"
        assert response_info.kernel_id == "12345678-1234-5678-1234-567812345678"
        assert response_info.owner_project_id == "87654321-4321-8765-4321-876543218765"
        assert response_info.owner_user_id == "11223344-5566-7788-99aa-bbccddeeff00"
        assert response_info.session_id == "aabbccdd-eeff-0011-2233-445566778899"
