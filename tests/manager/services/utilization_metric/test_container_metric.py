"""
Simple tests for Container Metric Service functionality.
Tests the core container metric service actions to verify metric collection and querying capabilities.
"""

from unittest.mock import AsyncMock, Mock
from uuid import UUID

import pytest

from ai.backend.common.clients.prometheus.container_util.client import ContainerUtilizationReader
from ai.backend.common.clients.prometheus.container_util.data.response import (
    ContainerUtilizationQueryResult,
)
from ai.backend.common.clients.prometheus.data.response import (
    LabelValueQueryResponseData,
    ResultMetric,
    ResultValue,
)
from ai.backend.manager.services.metric.actions.container import (
    ContainerCurrentMetricAction,
    ContainerCurrentMetricActionResult,
    ContainerMetricAction,
    ContainerMetricActionResult,
    ContainerMetricMetadataAction,
    ContainerMetricMetadataActionResult,
)
from ai.backend.manager.services.metric.container_metric import ContainerUtilizationMetricService
from ai.backend.manager.services.metric.types import (
    ContainerMetricOptionalLabel,
    UtilizationMetricType,
    ValueType,
)


class TestContainerMetricServiceCompatibility:
    """Test compatibility of container metric service with various metric query scenarios."""

    @pytest.fixture
    def mock_utilization_reader(self) -> Mock:
        """Create mocked ContainerUtilizationReader."""
        return AsyncMock(spec=ContainerUtilizationReader)

    @pytest.fixture
    def metric_service(self, mock_utilization_reader: Mock) -> ContainerUtilizationMetricService:
        """Create ContainerUtilizationMetricService instance with mocked dependencies."""
        return ContainerUtilizationMetricService(mock_utilization_reader)

    @pytest.mark.asyncio
    async def test_query_metadata_returns_all_metrics(
        self,
        metric_service: ContainerUtilizationMetricService,
        mock_utilization_reader: Mock,
    ) -> None:
        """Test querying metadata returns list of all available metrics."""
        # Configure mock response
        mock_utilization_reader.get_label_values.return_value = LabelValueQueryResponseData(
            status="success",
            data=[
                "cpu_util",
                "mem",
                "net_rx",
                "net_tx",
                "io_read",
                "io_write",
            ],
        )

        action = ContainerMetricMetadataAction()
        result = await metric_service.query_metadata(action)

        assert isinstance(result, ContainerMetricMetadataActionResult)
        assert len(result.metric_names) == 6
        assert "cpu_util" in result.metric_names
        assert "mem" in result.metric_names
        mock_utilization_reader.get_label_values.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_metadata_handles_empty_metrics(
        self,
        metric_service: ContainerUtilizationMetricService,
        mock_utilization_reader: Mock,
    ) -> None:
        """Test querying metadata handles empty metric list gracefully."""
        # Configure mock response
        mock_utilization_reader.get_label_values.return_value = LabelValueQueryResponseData(
            status="success",
            data=[],
        )

        action = ContainerMetricMetadataAction()
        result = await metric_service.query_metadata(action)

        assert isinstance(result, ContainerMetricMetadataActionResult)
        assert len(result.metric_names) == 0

    @pytest.mark.asyncio
    async def test_query_cpu_utilization(
        self,
        metric_service: ContainerUtilizationMetricService,
        mock_utilization_reader: Mock,
    ) -> None:
        """Test querying CPU utilization metrics for a specific kernel."""
        # Configure mock response
        mock_result = ContainerUtilizationQueryResult(
            metric=ResultMetric(
                value_type="current",
                name="backendai_container_utilization",
                container_metric_name="cpu_util",
                kernel_id="12345678-1234-5678-1234-567812345678",
            ),
            values=[
                ResultValue(timestamp=1704067200.0, value="10.5"),
                ResultValue(timestamp=1704067260.0, value="12.3"),
                ResultValue(timestamp=1704067320.0, value="15.7"),
            ],
        )
        mock_utilization_reader.get_container_utilization_diff.return_value = [mock_result]

        action = ContainerMetricAction(
            metric_name="cpu_util",
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
        mock_utilization_reader.get_container_utilization_diff.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_memory_usage_gauge(
        self,
        metric_service: ContainerUtilizationMetricService,
        mock_utilization_reader: Mock,
    ) -> None:
        """Test querying memory usage with GAUGE type."""
        # Configure mock response
        mock_result = ContainerUtilizationQueryResult(
            metric=ResultMetric(
                value_type="current",
                name="backendai_container_utilization",
                container_metric_name="mem",
            ),
            values=[
                ResultValue(timestamp=1704067200.0, value="1048576"),
                ResultValue(timestamp=1704067260.0, value="2097152"),
            ],
        )
        mock_utilization_reader.get_container_utilization_gauge.return_value = [mock_result]

        action = ContainerMetricAction(
            metric_name="mem",
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
        assert result.result[0].metric.container_metric_name == "mem"
        mock_utilization_reader.get_container_utilization_gauge.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_network_transmission_rate(
        self,
        metric_service: ContainerUtilizationMetricService,
        mock_utilization_reader: Mock,
    ) -> None:
        """Test querying network transmission metrics with RATE type."""
        # Configure mock response
        mock_result = ContainerUtilizationQueryResult(
            metric=ResultMetric(
                value_type="current",
                name="backendai_container_utilization",
                container_metric_name="net_tx",
                agent_id="agent-1",
            ),
            values=[
                ResultValue(timestamp=1704067200.0, value="1024.5"),
                ResultValue(timestamp=1704067500.0, value="2048.7"),
            ],
        )
        mock_utilization_reader.get_container_utilization_rate.return_value = [mock_result]

        action = ContainerMetricAction(
            metric_name="net_tx",
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
        mock_utilization_reader.get_container_utilization_rate.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_metrics_by_project(
        self,
        metric_service: ContainerUtilizationMetricService,
        mock_utilization_reader: Mock,
    ) -> None:
        """Test aggregating metrics by project."""
        # Configure mock response
        mock_result = ContainerUtilizationQueryResult(
            metric=ResultMetric(
                value_type="current",
                name="backendai_container_utilization",
                container_metric_name="cpu_util",
                owner_project_id="87654321-4321-8765-4321-876543218765",
            ),
            values=[ResultValue(timestamp=1704067200.0, value="45.2")],
        )
        mock_utilization_reader.get_container_utilization_diff.return_value = [mock_result]

        action = ContainerMetricAction(
            metric_name="cpu_util",
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
        assert result.result[0].metric.owner_project_id == "87654321-4321-8765-4321-876543218765"

    @pytest.mark.asyncio
    async def test_query_capacity_metrics(
        self,
        metric_service: ContainerUtilizationMetricService,
        mock_utilization_reader: Mock,
    ) -> None:
        """Test querying capacity type metrics."""
        # Configure mock response
        mock_result = ContainerUtilizationQueryResult(
            metric=ResultMetric(
                value_type="capacity",
                name="backendai_container_utilization",
                container_metric_name="mem",
            ),
            values=[ResultValue(timestamp=1704067200.0, value="8589934592")],
        )
        mock_utilization_reader.get_container_utilization_gauge.return_value = [mock_result]

        action = ContainerMetricAction(
            metric_name="mem",
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
    async def test_query_current_metric(
        self,
        metric_service: ContainerUtilizationMetricService,
        mock_utilization_reader: Mock,
    ) -> None:
        """Test querying current metric values."""
        # Configure mock response
        mock_result = ContainerUtilizationQueryResult(
            metric=ResultMetric(
                value_type="current",
                name="backendai_container_utilization",
                container_metric_name="cpu_util",
                kernel_id="12345678-1234-5678-1234-567812345678",
            ),
            values=[ResultValue(timestamp=1704067200.0, value="25.5")],
        )
        mock_utilization_reader.get_container_utilization.return_value = [mock_result]

        action = ContainerCurrentMetricAction(
            labels=ContainerMetricOptionalLabel(
                value_type=ValueType.CURRENT,
                kernel_id=UUID("12345678-1234-5678-1234-567812345678"),
            ),
        )

        result = await metric_service.query_current_metric(action)

        assert isinstance(result, ContainerCurrentMetricActionResult)
        assert len(result.result) == 1
        assert result.result[0].metric.kernel_id == "12345678-1234-5678-1234-567812345678"
        assert float(result.result[0].values[0].value) == 25.5
        mock_utilization_reader.get_container_utilization.assert_called_once()


class TestMetricTypeDetection:
    """Test metric type detection logic."""

    @pytest.fixture
    def metric_service(self) -> ContainerUtilizationMetricService:
        """Create metric service instance."""
        mock_reader = AsyncMock(spec=ContainerUtilizationReader)
        return ContainerUtilizationMetricService(mock_reader)

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
        """Test memory and other metrics are detected as GAUGE type."""
        for metric_name in ["mem", "io_read", "io_write", "unknown_metric"]:
            metric_type = metric_service._get_metric_type(
                metric_name, ContainerMetricOptionalLabel(value_type=ValueType.CURRENT)
            )
            assert metric_type == UtilizationMetricType.GAUGE


class TestComplexScenarios:
    """Test complex usage scenarios."""

    @pytest.fixture
    def mock_utilization_reader(self) -> Mock:
        """Create mocked ContainerUtilizationReader."""
        return AsyncMock(spec=ContainerUtilizationReader)

    @pytest.fixture
    def metric_service(self, mock_utilization_reader: Mock) -> ContainerUtilizationMetricService:
        """Create metric service instance."""
        return ContainerUtilizationMetricService(mock_utilization_reader)

    @pytest.mark.asyncio
    async def test_multi_kernel_session_monitoring(
        self,
        metric_service: ContainerUtilizationMetricService,
        mock_utilization_reader: Mock,
    ) -> None:
        """Test monitoring multiple kernels in a cluster session."""
        kernel_ids = ["kernel-1", "kernel-2", "kernel-3"]
        kernel_uuids = [UUID(f"12345678-1234-5678-1234-56781234567{i}") for i in range(3)]

        results = []
        for i, kernel_id in enumerate(kernel_ids):
            # Configure mock response for each kernel
            mock_result = ContainerUtilizationQueryResult(
                metric=ResultMetric(
                    value_type="current",
                    name="backendai_container_utilization",
                    container_metric_name="cpu_util",
                    kernel_id=str(kernel_uuids[i]),
                ),
                values=[ResultValue(timestamp=1704067200.0, value="10.5")],
            )
            mock_utilization_reader.get_container_utilization_diff.return_value = [mock_result]

            action = ContainerMetricAction(
                metric_name="cpu_util",
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
            assert result.result[0].metric.kernel_id == str(kernel_uuids[i])

    @pytest.mark.asyncio
    async def test_resource_usage_trend_analysis(
        self,
        metric_service: ContainerUtilizationMetricService,
        mock_utilization_reader: Mock,
    ) -> None:
        """Test retrieving 24-hour resource usage trends."""
        # Generate hourly data points
        hourly_values = []
        base_timestamp = 1704067200.0  # 2024-01-01 00:00:00
        for i in range(24):
            hourly_values.append(
                ResultValue(
                    timestamp=base_timestamp + (i * 3600),
                    value=str(10 + i * 2),
                )
            )

        mock_result = ContainerUtilizationQueryResult(
            metric=ResultMetric(
                value_type="current",
                name="backendai_container_utilization",
                container_metric_name="cpu_util",
            ),
            values=hourly_values,
        )
        mock_utilization_reader.get_container_utilization_diff.return_value = [mock_result]

        action = ContainerMetricAction(
            metric_name="cpu_util",
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
            metric_name="cpu_util",
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

        assert action.metric_name == "cpu_util"
        assert action.start == "2024-01-01T00:00:00"
        assert action.end == "2024-01-01T01:00:00"
        assert action.step == "60s"
        assert action.labels.value_type == ValueType.CURRENT
        assert action.labels.agent_id == "agent-1"
        assert isinstance(action.labels.kernel_id, UUID)
        assert isinstance(action.labels.session_id, UUID)
        assert isinstance(action.labels.user_id, UUID)
        assert isinstance(action.labels.project_id, UUID)
