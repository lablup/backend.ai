"""
Simple tests for Container Metric Service functionality.
Tests the core container metric service actions to verify metric collection and querying capabilities.
"""

from typing import Tuple
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import UUID

import aiohttp
import pytest

from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.services.metric.actions.container import (
    ContainerMetricAction,
    ContainerMetricActionResult,
    ContainerMetricMetadataAction,
    ContainerMetricMetadataActionResult,
)
from ai.backend.manager.services.metric.container_metric import (
    ContainerUtilizationMetricService,
)
from ai.backend.manager.services.metric.exceptions import FailedToGetMetric
from ai.backend.manager.services.metric.types import (
    ContainerMetricOptionalLabel,
    ContainerMetricResponseInfo,
    UtilizationMetricType,
    ValueType,
)


def create_mock_aiohttp_session() -> Tuple[Mock, AsyncMock]:
    """Create a properly configured mock session that supports async context manager protocol."""
    mock_session = Mock()

    # Create mock response
    mock_response = AsyncMock()
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)

    # Configure session methods to return the mock response
    mock_get = Mock()
    mock_get.return_value = mock_response
    mock_session.get = mock_get

    mock_post = Mock()
    mock_post.return_value = mock_response
    mock_session.post = mock_post

    # Make session itself an async context manager
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    return mock_session, mock_response


class TestContainerMetricServiceCompatibility:
    """Test compatibility of container metric service with various metric query scenarios."""

    @pytest.fixture
    def mock_config_provider(self) -> MagicMock:
        """Create mocked configuration provider."""
        config_provider = MagicMock(spec=ManagerConfigProvider)
        config_provider.config.metric.address.to_legacy.return_value = "localhost:9090"
        config_provider.config.metric.timewindow = "1m"
        return config_provider

    @pytest.fixture
    def metric_service(self, mock_config_provider: MagicMock) -> ContainerUtilizationMetricService:
        """Create ContainerUtilizationMetricService instance with mocked dependencies."""
        return ContainerUtilizationMetricService(mock_config_provider)

    @pytest.mark.asyncio
    async def test_query_metadata_returns_all_metrics(
        self, metric_service: ContainerUtilizationMetricService
    ) -> None:
        """Test querying metadata returns list of all available metrics."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session, mock_response = create_mock_aiohttp_session()
            mock_session_class.return_value = mock_session

            # Configure response
            mock_response.status = 200
            mock_response.raise_for_status = AsyncMock()
            mock_response.json = AsyncMock(
                return_value={
                    "status": "success",
                    "data": [
                        "container_cpu_percent",
                        "container_memory_used_bytes",
                        "container_network_rx_bytes",
                        "container_network_tx_bytes",
                    ],
                }
            )

            action = ContainerMetricMetadataAction()
            result = await metric_service.query_metadata(action)

            assert isinstance(result, ContainerMetricMetadataActionResult)
            assert len(result.metric_names) == 4
            assert "container_cpu_percent" in result.metric_names
            mock_session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_metadata_handles_empty_metrics(
        self, metric_service: ContainerUtilizationMetricService
    ) -> None:
        """Test querying metadata handles empty metric list gracefully."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session, mock_response = create_mock_aiohttp_session()
            mock_session_class.return_value = mock_session

            # Configure response
            mock_response.status = 200
            mock_response.raise_for_status = AsyncMock()
            mock_response.json = AsyncMock(return_value={"status": "success", "data": []})

            action = ContainerMetricMetadataAction()
            result = await metric_service.query_metadata(action)

            assert isinstance(result, ContainerMetricMetadataActionResult)
            assert len(result.metric_names) == 0

    @pytest.mark.asyncio
    async def test_query_metadata_connection_failure(
        self, metric_service: ContainerUtilizationMetricService
    ) -> None:
        """Test metadata query handles Prometheus connection failures."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session, _ = create_mock_aiohttp_session()
            mock_session_class.return_value = mock_session

            mock_session.get.side_effect = aiohttp.ClientError("Connection failed")

            with pytest.raises(aiohttp.ClientError):
                await metric_service.query_metadata(ContainerMetricMetadataAction())

    @pytest.mark.asyncio
    async def test_query_cpu_utilization(
        self, metric_service: ContainerUtilizationMetricService
    ) -> None:
        """Test querying CPU utilization metrics for a specific kernel."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session, mock_response = create_mock_aiohttp_session()
            mock_session_class.return_value = mock_session

            # Configure response
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={
                    "status": "success",
                    "data": {
                        "result": [
                            {
                                "metric": {
                                    "value_type": "current",
                                    "__name__": "backendai_container_utilization",
                                    "container_metric_name": "cpu_util",
                                    "kernel_id": "12345678-1234-5678-1234-567812345678",
                                },
                                "values": [
                                    [1704067200.0, "10.5"],
                                    [1704067260.0, "12.3"],
                                    [1704067320.0, "15.7"],
                                ],
                            }
                        ]
                    },
                }
            )

            action = ContainerMetricAction(
                metric_name="container_cpu_percent",
                start="2024-01-01T00:00:00",
                end="2024-01-01T01:00:00",
                step="60s",
                labels=ContainerMetricOptionalLabel(
                    value_type=ValueType.CURRENT,
                    kernel_id=UUID("12345678-1234-5678-1234-567812345678"),
                ),
            )

            result = await metric_service.query_metric(action)

            assert isinstance(result, ContainerMetricActionResult)
            assert len(result.result) == 1
            assert result.result[0].metric.container_metric_name == "cpu_util"
            assert len(result.result[0].values) == 3
            assert float(result.result[0].values[0].value) == 10.5

    @pytest.mark.asyncio
    async def test_query_memory_usage_rate(
        self, metric_service: ContainerUtilizationMetricService
    ) -> None:
        """Test querying memory usage with RATE calculation."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session, mock_response = create_mock_aiohttp_session()
            mock_session_class.return_value = mock_session

            # Configure response
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={
                    "status": "success",
                    "data": {
                        "result": [
                            {
                                "metric": {
                                    "value_type": "current",
                                    "__name__": "backendai_container_utilization",
                                    "container_metric_name": "container_memory_used_bytes",
                                },
                                "values": [
                                    [1704067200.0, "1048576"],
                                    [1704067260.0, "2097152"],
                                ],
                            }
                        ]
                    },
                }
            )

            action = ContainerMetricAction(
                metric_name="container_memory_used_bytes",
                start="2024-01-01T00:00:00",
                end="2024-01-01T00:05:00",
                step="60s",
                labels=ContainerMetricOptionalLabel(
                    value_type=ValueType.CURRENT,
                ),
            )

            result = await metric_service.query_metric(action)

            assert isinstance(result, ContainerMetricActionResult)
            assert len(result.result) == 1
            assert result.result[0].metric.container_metric_name == "container_memory_used_bytes"

    @pytest.mark.asyncio
    async def test_query_network_transmission_by_agent(
        self, metric_service: ContainerUtilizationMetricService
    ) -> None:
        """Test querying network transmission metrics filtered by agent."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session, mock_response = create_mock_aiohttp_session()
            mock_session_class.return_value = mock_session

            # Configure response
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={
                    "status": "success",
                    "data": {
                        "result": [
                            {
                                "metric": {
                                    "value_type": "current",
                                    "__name__": "backendai_container_utilization",
                                    "container_metric_name": "container_network_tx_bytes",
                                    "agent_id": "agent-1",
                                },
                                "values": [
                                    [1704067200.0, "1024000"],
                                    [1704067500.0, "2048000"],
                                ],
                            }
                        ]
                    },
                }
            )

            action = ContainerMetricAction(
                metric_name="container_network_tx_bytes",
                start="2024-01-01T00:00:00",
                end="2024-01-01T00:15:00",
                step="300",
                labels=ContainerMetricOptionalLabel(
                    value_type=ValueType.CURRENT,
                    agent_id="agent-1",
                ),
            )

            result = await metric_service.query_metric(action)

            assert isinstance(result, ContainerMetricActionResult)
            assert result.result[0].metric.agent_id == "agent-1"

    @pytest.mark.asyncio
    async def test_query_metrics_by_project(
        self, metric_service: ContainerUtilizationMetricService
    ) -> None:
        """Test aggregating metrics by project."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session, mock_response = create_mock_aiohttp_session()
            mock_session_class.return_value = mock_session

            # Configure response
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={
                    "status": "success",
                    "data": {
                        "result": [
                            {
                                "metric": {
                                    "value_type": "current",
                                    "__name__": "backendai_container_utilization",
                                    "container_metric_name": "container_cpu_percent",
                                    "owner_project_id": "87654321-4321-8765-4321-876543218765",
                                },
                                "values": [[1704067200.0, "45.2"]],
                            }
                        ]
                    },
                }
            )

            action = ContainerMetricAction(
                metric_name="container_cpu_percent",
                start="2024-01-01T00:00:00",
                end="2024-01-01T01:00:00",
                step="60",
                labels=ContainerMetricOptionalLabel(
                    value_type=ValueType.CURRENT,
                    project_id=UUID("87654321-4321-8765-4321-876543218765"),
                ),
            )

            result = await metric_service.query_metric(action)

            assert isinstance(result, ContainerMetricActionResult)
            assert (
                result.result[0].metric.owner_project_id == "87654321-4321-8765-4321-876543218765"
            )

    @pytest.mark.asyncio
    async def test_query_gpu_utilization_by_user(
        self, metric_service: ContainerUtilizationMetricService
    ) -> None:
        """Test querying GPU utilization metrics filtered by user."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session, mock_response = create_mock_aiohttp_session()
            mock_session_class.return_value = mock_session

            # Configure response
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={
                    "status": "success",
                    "data": {
                        "result": [
                            {
                                "metric": {
                                    "value_type": "current",
                                    "__name__": "backendai_container_utilization",
                                    "container_metric_name": "container_gpu_percent",
                                    "owner_user_id": "11223344-5566-7788-99aa-bbccddeeff00",
                                },
                                "values": [[1704067200.0, "80.5"]],
                            }
                        ]
                    },
                }
            )

            action = ContainerMetricAction(
                metric_name="container_gpu_percent",
                start="2024-01-01T00:00:00",
                end="2024-01-01T01:00:00",
                step="60",
                labels=ContainerMetricOptionalLabel(
                    value_type=ValueType.CURRENT,
                    user_id=UUID("11223344-5566-7788-99aa-bbccddeeff00"),
                ),
            )

            result = await metric_service.query_metric(action)

            assert isinstance(result, ContainerMetricActionResult)
            assert result.result[0].metric.owner_user_id == "11223344-5566-7788-99aa-bbccddeeff00"

    @pytest.mark.asyncio
    async def test_query_with_multiple_label_filters(
        self, metric_service: ContainerUtilizationMetricService
    ) -> None:
        """Test querying metrics with multiple label filters."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session, mock_response = create_mock_aiohttp_session()
            mock_session_class.return_value = mock_session

            # Configure response
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={
                    "status": "success",
                    "data": {
                        "result": [
                            {
                                "metric": {
                                    "value_type": "current",
                                    "__name__": "backendai_container_utilization",
                                    "container_metric_name": "container_cpu_percent",
                                    "agent_id": "agent-1",
                                    "kernel_id": "aabbccdd-eeff-0011-2233-445566778899",
                                },
                                "values": [[1704067200.0, "25.3"]],
                            }
                        ]
                    },
                }
            )

            action = ContainerMetricAction(
                metric_name="container_cpu_percent",
                start="2024-01-01T00:00:00",
                end="2024-01-01T01:00:00",
                step="60",
                labels=ContainerMetricOptionalLabel(
                    value_type=ValueType.CURRENT,
                    agent_id="agent-1",
                    kernel_id=UUID("aabbccdd-eeff-0011-2233-445566778899"),
                ),
            )

            result = await metric_service.query_metric(action)

            assert isinstance(result, ContainerMetricActionResult)
            assert result.result[0].metric.agent_id == "agent-1"
            assert result.result[0].metric.kernel_id == "aabbccdd-eeff-0011-2233-445566778899"

    @pytest.mark.asyncio
    async def test_query_capacity_metrics(
        self, metric_service: ContainerUtilizationMetricService
    ) -> None:
        """Test querying capacity type metrics."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session, mock_response = create_mock_aiohttp_session()
            mock_session_class.return_value = mock_session

            # Configure response
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={
                    "status": "success",
                    "data": {
                        "result": [
                            {
                                "metric": {
                                    "value_type": "capacity",
                                    "__name__": "backendai_container_utilization",
                                    "container_metric_name": "mem",
                                },
                                "values": [[1704067200.0, "8589934592"]],
                            }
                        ]
                    },
                }
            )

            action = ContainerMetricAction(
                metric_name="container_memory_capacity_bytes",
                start="2024-01-01T00:00:00",
                end="2024-01-01T01:00:00",
                step="60s",
                labels=ContainerMetricOptionalLabel(
                    value_type=ValueType.CAPACITY,
                ),
            )

            result = await metric_service.query_metric(action)

            assert isinstance(result, ContainerMetricActionResult)
            assert result.result[0].metric.value_type == "capacity"

    @pytest.mark.asyncio
    async def test_query_invalid_metric_returns_empty(
        self, metric_service: ContainerUtilizationMetricService
    ) -> None:
        """Test querying invalid metric name returns empty result."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session, mock_response = create_mock_aiohttp_session()
            mock_session_class.return_value = mock_session

            # Configure response
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={"status": "success", "data": {"result": []}}
            )

            action = ContainerMetricAction(
                metric_name="invalid_metric_name",
                start="2024-01-01T00:00:00",
                end="2024-01-01T01:00:00",
                step="60",
                labels=ContainerMetricOptionalLabel(
                    value_type=ValueType.CURRENT,
                ),
            )

            result = await metric_service.query_metric(action)

            assert isinstance(result, ContainerMetricActionResult)
            assert len(result.result) == 0

    @pytest.mark.asyncio
    async def test_query_prometheus_error_handling(
        self, metric_service: ContainerUtilizationMetricService
    ) -> None:
        """Test handling Prometheus query errors."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session, mock_response = create_mock_aiohttp_session()
            mock_session_class.return_value = mock_session

            # Configure error response
            mock_response.status = 400
            mock_response.json = AsyncMock(
                return_value={"status": "error", "error": "Bad Request: Invalid query"}
            )

            action = ContainerMetricAction(
                metric_name="container_cpu_percent",
                start="2024-01-01T00:00:00",
                end="2024-01-01T01:00:00",
                step="60",
                labels=ContainerMetricOptionalLabel(
                    value_type=ValueType.CURRENT,
                ),
            )

            with pytest.raises(FailedToGetMetric, match="Bad Request: Invalid query"):
                await metric_service.query_metric(action)

    @pytest.mark.asyncio
    async def test_query_server_error_handling(
        self, metric_service: ContainerUtilizationMetricService
    ) -> None:
        """Test handling server errors from Prometheus."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session, mock_response = create_mock_aiohttp_session()
            mock_session_class.return_value = mock_session

            # Configure server error response
            mock_response.status = 500

            action = ContainerMetricAction(
                metric_name="container_cpu_percent",
                start="2024-01-01T00:00:00",
                end="2024-01-01T01:00:00",
                step="60",
                labels=ContainerMetricOptionalLabel(
                    value_type=ValueType.CURRENT,
                ),
            )

            with pytest.raises(FailedToGetMetric):
                await metric_service.query_metric(action)


class TestMetricTypeDetection:
    """Test metric type detection logic."""

    @pytest.fixture
    def metric_service(self) -> ContainerUtilizationMetricService:
        """Create metric service instance."""
        config_provider = MagicMock(spec=ManagerConfigProvider)
        config_provider.config.metric.address.to_legacy.return_value = "localhost:9090"
        config_provider.config.metric.timewindow = "1m"
        return ContainerUtilizationMetricService(config_provider)

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


class TestQueryStringGeneration:
    """Test Prometheus query string generation."""

    @pytest.fixture
    def metric_service(self) -> ContainerUtilizationMetricService:
        """Create metric service instance."""
        config_provider = MagicMock(spec=ManagerConfigProvider)
        config_provider.config.metric.address.to_legacy.return_value = "localhost:9090"
        config_provider.config.metric.timewindow = "1m"
        return ContainerUtilizationMetricService(config_provider)

    @pytest.mark.asyncio
    async def test_gauge_query_string_generation(
        self, metric_service: ContainerUtilizationMetricService
    ) -> None:
        """Test gauge metric query string generation with labels."""
        query = await metric_service._get_query_string(
            "container_memory_used_bytes",
            ContainerMetricOptionalLabel(
                kernel_id=UUID("12345678-1234-5678-1234-567812345678"), value_type=ValueType.CURRENT
            ),
        )

        assert "sum by (value_type,kernel_id)" in query
        assert 'container_metric_name="container_memory_used_bytes"' in query
        assert 'kernel_id="12345678-1234-5678-1234-567812345678"' in query
        assert 'value_type="current"' in query

    @pytest.mark.asyncio
    async def test_rate_query_string_generation(
        self, metric_service: ContainerUtilizationMetricService
    ) -> None:
        """Test rate metric query string generation."""
        query = await metric_service._get_query_string(
            "net_rx",
            ContainerMetricOptionalLabel(value_type=ValueType.CURRENT, agent_id="agent-1"),
        )

        assert "rate(" in query
        assert "[1m]" in query  # timewindow
        assert 'container_metric_name="net_rx"' in query
        assert 'agent_id="agent-1"' in query

    @pytest.mark.asyncio
    async def test_diff_query_string_generation(
        self, metric_service: ContainerUtilizationMetricService
    ) -> None:
        """Test diff metric query string generation with session filter."""
        query = await metric_service._get_query_string(
            "cpu_util",
            ContainerMetricOptionalLabel(
                value_type=ValueType.CURRENT,
                session_id=UUID("99887766-5544-3322-1100-ffeeddccbbaa"),
            ),
        )

        assert "rate(" in query
        assert "[1m]" in query
        assert 'value_type="current"' in query
        assert 'session_id="99887766-5544-3322-1100-ffeeddccbbaa"' in query


class TestComplexScenarios:
    """Test complex usage scenarios."""

    @pytest.fixture
    def metric_service(self) -> ContainerUtilizationMetricService:
        """Create metric service instance."""
        config_provider = MagicMock(spec=ManagerConfigProvider)
        config_provider.config.metric.address.to_legacy.return_value = "localhost:9090"
        config_provider.config.metric.timewindow = "1m"
        return ContainerUtilizationMetricService(config_provider)

    @pytest.mark.asyncio
    async def test_multi_kernel_session_monitoring(
        self, metric_service: ContainerUtilizationMetricService
    ) -> None:
        """Test monitoring multiple kernels in a cluster session."""
        kernel_ids = ["kernel-1", "kernel-2", "kernel-3"]
        kernel_uuids = [UUID(f"12345678-1234-5678-1234-56781234567{i}") for i in range(3)]

        with patch("aiohttp.ClientSession") as mock_session_class:
            results = []
            for i, kernel_id in enumerate(kernel_ids):
                mock_session, mock_response = create_mock_aiohttp_session()
                mock_session_class.return_value = mock_session

                # Configure response
                mock_response.status = 200
                mock_response.json = AsyncMock(
                    return_value={
                        "status": "success",
                        "data": {
                            "result": [
                                {
                                    "metric": {
                                        "value_type": "current",
                                        "__name__": "backendai_container_utilization",
                                        "container_metric_name": "container_cpu_percent",
                                        "kernel_id": kernel_id,
                                    },
                                    "values": [[1704067200.0, "10.5"]],
                                }
                            ]
                        },
                    }
                )

                action = ContainerMetricAction(
                    metric_name="container_cpu_percent",
                    start="2024-01-01T00:00:00",
                    end="2024-01-01T01:00:00",
                    step="60",
                    labels=ContainerMetricOptionalLabel(
                        value_type=ValueType.CURRENT,
                        kernel_id=kernel_uuids[i],
                    ),
                )

                result = await metric_service.query_metric(action)
                results.append(result)

            # Verify we got results for all kernels
            assert len(results) == 3
            for i, result in enumerate(results):
                assert result.result[0].metric.kernel_id == kernel_ids[i]

    @pytest.mark.asyncio
    async def test_resource_usage_trend_analysis(
        self, metric_service: ContainerUtilizationMetricService
    ) -> None:
        """Test retrieving 24-hour resource usage trends."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session, mock_response = create_mock_aiohttp_session()
            mock_session_class.return_value = mock_session

            # Configure response
            mock_response.status = 200

            # Generate hourly data points
            hourly_values = []
            base_timestamp = 1704067200.0  # 2024-01-01 00:00:00
            for i in range(24):
                hourly_values.append([base_timestamp + (i * 3600), str(10 + i * 2)])

            mock_response.json = AsyncMock(
                return_value={
                    "status": "success",
                    "data": {
                        "result": [
                            {
                                "metric": {
                                    "value_type": "current",
                                    "__name__": "backendai_container_utilization",
                                    "container_metric_name": "container_cpu_percent",
                                },
                                "values": hourly_values,
                            }
                        ]
                    },
                }
            )

            action = ContainerMetricAction(
                metric_name="container_cpu_percent",
                start="2024-01-01T00:00:00",
                end="2024-01-02T00:00:00",
                step="3600",  # 1 hour intervals
                labels=ContainerMetricOptionalLabel(
                    value_type=ValueType.CURRENT,
                ),
            )

            result = await metric_service.query_metric(action)

            # Verify trend data
            assert len(result.result[0].values) == 24
            # Check if values show increasing trend (simulated peak usage)
            first_value = float(result.result[0].values[0].value)
            last_value = float(result.result[0].values[-1].value)
            assert last_value > first_value  # Usage increased over time

    def test_container_metric_action_fields(self) -> None:
        """Test that ContainerMetricAction has all expected fields."""
        action = ContainerMetricAction(
            metric_name="container_cpu_percent",
            start="2024-01-01T00:00:00",
            end="2024-01-01T01:00:00",
            step="60s",
            labels=ContainerMetricOptionalLabel(
                value_type=ValueType.CURRENT,
                agent_id="agent-1",
                kernel_id=UUID("12345678-1234-5678-1234-567812345678"),
                session_id=UUID("87654321-4321-8765-4321-876543218765"),
                user_id=UUID("11223344-5566-7788-99aa-bbccddeeff00"),
                project_id=UUID("aabbccdd-eeff-0011-2233-445566778899"),
            ),
        )

        assert action.metric_name == "container_cpu_percent"
        assert action.start == "2024-01-01T00:00:00"
        assert action.end == "2024-01-01T01:00:00"
        assert action.step == "60s"
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
