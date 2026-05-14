"""
Tests for container metric queries in MetricRepository.
"""

from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from ai.backend.common.clients.prometheus.client import PrometheusClient
from ai.backend.common.clients.prometheus.fixed_query_builder import FixedQueryBuilder
from ai.backend.common.clients.prometheus.metric_types import (
    ContainerLiveStatQueries,
    ContainerMetricOptionalLabel,
    ContainerMetricResponseInfo,
    KernelLiveStatBatchResult,
    MetricType,
    ValueType,
)
from ai.backend.common.dto.clients.prometheus.request import QueryTimeRange
from ai.backend.common.dto.clients.prometheus.response import (
    LabelValueResponse,
    MetricResponse,
    MetricResponseInfo,
    PrometheusQueryData,
    PrometheusResponse,
)
from ai.backend.common.exception import (
    FailedToGetMetric,
    InvalidAPIParameters,
    PrometheusConnectionError,
)
from ai.backend.common.types import KernelId
from ai.backend.manager.repositories.metric.repository import MetricRepository
from ai.backend.manager.services.metric.actions.container import (
    ContainerMetricAction,
)


def _make_query_range_response(
    metric_data: list[dict[str, Any]],
) -> PrometheusResponse:
    """Helper to build PrometheusResponse from raw metric dicts."""
    return PrometheusResponse(
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


def _make_metric_repository(
    mock_prometheus_client: PrometheusClient,
    *,
    timewindow: str = "1m",
) -> MetricRepository:
    mock_prometheus_client._fixed_query_builder = FixedQueryBuilder(timewindow)
    return MetricRepository(
        db=MagicMock(),
        prometheus_client=mock_prometheus_client,
    )


def _set_query_label_values(mock_prometheus_client: PrometheusClient, mock: Any) -> None:
    setattr(mock_prometheus_client, "_query_label_values", mock)


def _set_query_range(mock_prometheus_client: PrometheusClient, mock: Any) -> None:
    setattr(mock_prometheus_client, "_query_range", mock)


class TestContainerMetricRepositoryQueries:
    """Characterization tests: verify public interface behavior with PrometheusClient."""

    @pytest.fixture
    def mock_prometheus_client(self) -> PrometheusClient:
        return PrometheusClient(
            endpoint="http://localhost:9090/api/v1",
            client_pool=MagicMock(),
            fixed_query_builder=FixedQueryBuilder("1m"),
        )

    @pytest.fixture
    def metric_repository(self, mock_prometheus_client: PrometheusClient) -> MetricRepository:
        return _make_metric_repository(mock_prometheus_client)

    # -- query_container_metric_metadata --

    @pytest.fixture
    def mock_label_values_with_metrics(
        self, mock_prometheus_client: PrometheusClient
    ) -> PrometheusClient:
        _set_query_label_values(
            mock_prometheus_client,
            AsyncMock(
                return_value=LabelValueResponse(
                    status="success",
                    data=[
                        "container_cpu_percent",
                        "container_memory_used_bytes",
                        "container_network_rx_bytes",
                        "container_network_tx_bytes",
                    ],
                )
            ),
        )
        return mock_prometheus_client

    async def test_query_metadata_returns_metric_names(
        self,
        metric_repository: MetricRepository,
        mock_label_values_with_metrics: PrometheusClient,
    ) -> None:
        result = await metric_repository.query_container_metric_metadata()

        assert isinstance(result, list)
        assert len(result) == 4
        assert "container_cpu_percent" in result

    @pytest.fixture
    def mock_label_values_empty(self, mock_prometheus_client: PrometheusClient) -> PrometheusClient:
        _set_query_label_values(
            mock_prometheus_client,
            AsyncMock(return_value=LabelValueResponse(status="success", data=[])),
        )
        return mock_prometheus_client

    async def test_query_metadata_empty_result(
        self,
        metric_repository: MetricRepository,
        mock_label_values_empty: PrometheusClient,
    ) -> None:
        result = await metric_repository.query_container_metric_metadata()

        assert len(result) == 0

    @pytest.fixture
    def mock_label_values_connection_error(
        self, mock_prometheus_client: PrometheusClient
    ) -> PrometheusClient:
        _set_query_label_values(
            mock_prometheus_client,
            AsyncMock(side_effect=PrometheusConnectionError("Connection failed")),
        )
        return mock_prometheus_client

    async def test_query_metadata_propagates_connection_error(
        self,
        metric_repository: MetricRepository,
        mock_label_values_connection_error: PrometheusClient,
    ) -> None:
        with pytest.raises(PrometheusConnectionError):
            await metric_repository.query_container_metric_metadata()

    # -- query_container_metric: GAUGE (memory) --

    @pytest.fixture
    def mock_query_range_gauge_memory(
        self, mock_prometheus_client: PrometheusClient
    ) -> PrometheusClient:
        _set_query_range(
            mock_prometheus_client,
            AsyncMock(
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
            ),
        )
        return mock_prometheus_client

    async def test_query_metric_gauge_returns_correct_result(
        self,
        metric_repository: MetricRepository,
        mock_query_range_gauge_memory: PrometheusClient,
    ) -> None:
        result = await metric_repository.query_container_metric(
            metric_name="container_memory_used_bytes",
            label=ContainerMetricOptionalLabel(value_type=ValueType.CURRENT),
            time_range=QueryTimeRange(
                start="2024-01-01T00:00:00", end="2024-01-01T00:05:00", step="60s"
            ),
        )

        assert len(result) == 1
        assert result[0].metric.container_metric_name == "container_memory_used_bytes"
        assert result[0].metric.value_type == "current"
        assert len(result[0].values) == 2

    # -- query_container_metric: RATE (network tx by agent) --

    @pytest.fixture
    def mock_query_range_rate_net_tx(
        self, mock_prometheus_client: PrometheusClient
    ) -> PrometheusClient:
        _set_query_range(
            mock_prometheus_client,
            AsyncMock(
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
            ),
        )
        return mock_prometheus_client

    async def test_query_metric_rate_returns_correct_result(
        self,
        metric_repository: MetricRepository,
        mock_query_range_rate_net_tx: PrometheusClient,
    ) -> None:
        result = await metric_repository.query_container_metric(
            metric_name="net_tx",
            label=ContainerMetricOptionalLabel(
                value_type=ValueType.CURRENT,
                agent_id="agent-1",
            ),
            time_range=QueryTimeRange(
                start="2024-01-01T00:00:00", end="2024-01-01T00:15:00", step="300"
            ),
        )

        assert result[0].metric.agent_id == "agent-1"

    # -- query_container_metric: DIFF (cpu_util by kernel) --

    @pytest.fixture
    def mock_query_range_diff_cpu_util(
        self, mock_prometheus_client: PrometheusClient
    ) -> PrometheusClient:
        _set_query_range(
            mock_prometheus_client,
            AsyncMock(
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
            ),
        )
        return mock_prometheus_client

    async def test_query_metric_diff_returns_correct_result(
        self,
        metric_repository: MetricRepository,
        mock_query_range_diff_cpu_util: PrometheusClient,
    ) -> None:
        result = await metric_repository.query_container_metric(
            metric_name="cpu_util",
            label=ContainerMetricOptionalLabel(
                value_type=ValueType.CURRENT,
                kernel_id=UUID("12345678-1234-5678-1234-567812345678"),
            ),
            time_range=QueryTimeRange(
                start="2024-01-01T00:00:00", end="2024-01-01T01:00:00", step="60s"
            ),
        )

        assert len(result) == 1
        assert result[0].metric.container_metric_name == "cpu_util"
        assert len(result[0].values) == 3
        assert float(result[0].values[0].value) == 10.5

    # -- query_container_metric: by project --

    @pytest.fixture
    def mock_query_range_by_project(
        self, mock_prometheus_client: PrometheusClient
    ) -> PrometheusClient:
        _set_query_range(
            mock_prometheus_client,
            AsyncMock(
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
            ),
        )
        return mock_prometheus_client

    async def test_query_metric_by_project(
        self,
        metric_repository: MetricRepository,
        mock_query_range_by_project: PrometheusClient,
    ) -> None:
        result = await metric_repository.query_container_metric(
            metric_name="container_cpu_percent",
            label=ContainerMetricOptionalLabel(
                value_type=ValueType.CURRENT,
                project_id=UUID("87654321-4321-8765-4321-876543218765"),
            ),
            time_range=QueryTimeRange(
                start="2024-01-01T00:00:00", end="2024-01-01T01:00:00", step="60"
            ),
        )

        assert result[0].metric.owner_project_id == "87654321-4321-8765-4321-876543218765"

    # -- query_container_metric: by user --

    @pytest.fixture
    def mock_query_range_by_user(
        self, mock_prometheus_client: PrometheusClient
    ) -> PrometheusClient:
        _set_query_range(
            mock_prometheus_client,
            AsyncMock(
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
            ),
        )
        return mock_prometheus_client

    async def test_query_metric_by_user(
        self,
        metric_repository: MetricRepository,
        mock_query_range_by_user: PrometheusClient,
    ) -> None:
        result = await metric_repository.query_container_metric(
            metric_name="container_gpu_percent",
            label=ContainerMetricOptionalLabel(
                value_type=ValueType.CURRENT,
                user_id=UUID("11223344-5566-7788-99aa-bbccddeeff00"),
            ),
            time_range=QueryTimeRange(
                start="2024-01-01T00:00:00", end="2024-01-01T01:00:00", step="60"
            ),
        )

        assert result[0].metric.owner_user_id == "11223344-5566-7788-99aa-bbccddeeff00"

    # -- query_container_metric: multiple labels --

    @pytest.fixture
    def mock_query_range_multiple_labels(
        self, mock_prometheus_client: PrometheusClient
    ) -> PrometheusClient:
        _set_query_range(
            mock_prometheus_client,
            AsyncMock(
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
            ),
        )
        return mock_prometheus_client

    async def test_query_metric_with_multiple_labels(
        self,
        metric_repository: MetricRepository,
        mock_query_range_multiple_labels: PrometheusClient,
    ) -> None:
        result = await metric_repository.query_container_metric(
            metric_name="container_cpu_percent",
            label=ContainerMetricOptionalLabel(
                value_type=ValueType.CURRENT,
                agent_id="agent-1",
                kernel_id=UUID("aabbccdd-eeff-0011-2233-445566778899"),
            ),
            time_range=QueryTimeRange(
                start="2024-01-01T00:00:00", end="2024-01-01T01:00:00", step="60"
            ),
        )

        assert result[0].metric.agent_id == "agent-1"
        assert result[0].metric.kernel_id == "aabbccdd-eeff-0011-2233-445566778899"

    # -- query_container_metric: empty result --

    @pytest.fixture
    def mock_query_range_empty(self, mock_prometheus_client: PrometheusClient) -> PrometheusClient:
        _set_query_range(
            mock_prometheus_client, AsyncMock(return_value=_make_query_range_response([]))
        )
        return mock_prometheus_client

    async def test_query_metric_empty_result(
        self,
        metric_repository: MetricRepository,
        mock_query_range_empty: PrometheusClient,
    ) -> None:
        result = await metric_repository.query_container_metric(
            metric_name="invalid_metric_name",
            label=ContainerMetricOptionalLabel(value_type=ValueType.CURRENT),
            time_range=QueryTimeRange(
                start="2024-01-01T00:00:00", end="2024-01-01T01:00:00", step="60"
            ),
        )

        assert len(result) == 0

    # -- query_container_metric: error propagation --

    @pytest.fixture
    def mock_query_range_failed_to_get_metric(
        self, mock_prometheus_client: PrometheusClient
    ) -> PrometheusClient:
        _set_query_range(
            mock_prometheus_client,
            AsyncMock(side_effect=FailedToGetMetric("Bad Request: Invalid query")),
        )
        return mock_prometheus_client

    async def test_query_metric_propagates_failed_to_get_metric(
        self,
        metric_repository: MetricRepository,
        mock_query_range_failed_to_get_metric: PrometheusClient,
    ) -> None:
        with pytest.raises(FailedToGetMetric):
            await metric_repository.query_container_metric(
                metric_name="container_cpu_percent",
                label=ContainerMetricOptionalLabel(value_type=ValueType.CURRENT),
                time_range=QueryTimeRange(
                    start="2024-01-01T00:00:00", end="2024-01-01T01:00:00", step="60"
                ),
            )

    @pytest.fixture
    def mock_query_range_connection_error(
        self, mock_prometheus_client: PrometheusClient
    ) -> PrometheusClient:
        _set_query_range(
            mock_prometheus_client,
            AsyncMock(side_effect=PrometheusConnectionError("Connection refused")),
        )
        return mock_prometheus_client

    async def test_query_metric_propagates_connection_error(
        self,
        metric_repository: MetricRepository,
        mock_query_range_connection_error: PrometheusClient,
    ) -> None:
        with pytest.raises(PrometheusConnectionError):
            await metric_repository.query_container_metric(
                metric_name="container_cpu_percent",
                label=ContainerMetricOptionalLabel(value_type=ValueType.CURRENT),
                time_range=QueryTimeRange(
                    start="2024-01-01T00:00:00", end="2024-01-01T01:00:00", step="60"
                ),
            )

    # -- query_container_metric: capacity value type --

    @pytest.fixture
    def mock_query_range_capacity(
        self, mock_prometheus_client: PrometheusClient
    ) -> PrometheusClient:
        _set_query_range(
            mock_prometheus_client,
            AsyncMock(
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
            ),
        )
        return mock_prometheus_client

    async def test_query_metric_capacity_value_type(
        self,
        metric_repository: MetricRepository,
        mock_query_range_capacity: PrometheusClient,
    ) -> None:
        result = await metric_repository.query_container_metric(
            metric_name="container_memory_capacity_bytes",
            label=ContainerMetricOptionalLabel(value_type=ValueType.CAPACITY),
            time_range=QueryTimeRange(
                start="2024-01-01T00:00:00", end="2024-01-01T01:00:00", step="60s"
            ),
        )

        assert result[0].metric.value_type == "capacity"


class TestMetricTypeDetection:
    """Test metric type detection logic."""

    @pytest.fixture
    def fixed_query_builder(self) -> FixedQueryBuilder:
        return FixedQueryBuilder("1m")

    def test_cpu_util_detected_as_diff_type(self, fixed_query_builder: FixedQueryBuilder) -> None:
        metric_type = fixed_query_builder.get_container_metric_type(
            "cpu_util", ContainerMetricOptionalLabel(value_type=ValueType.CURRENT)
        )
        assert metric_type == MetricType.DIFF

    def test_network_metrics_detected_as_rate_type(
        self, fixed_query_builder: FixedQueryBuilder
    ) -> None:
        for metric_name in ["net_rx", "net_tx"]:
            metric_type = fixed_query_builder.get_container_metric_type(
                metric_name, ContainerMetricOptionalLabel(value_type=ValueType.CURRENT)
            )
            assert metric_type == MetricType.RATE

    def test_memory_metrics_detected_as_gauge_type(
        self, fixed_query_builder: FixedQueryBuilder
    ) -> None:
        for metric_name in ["container_memory_used_bytes", "container_gpu_percent"]:
            metric_type = fixed_query_builder.get_container_metric_type(
                metric_name, ContainerMetricOptionalLabel(value_type=ValueType.CURRENT)
            )
            assert metric_type == MetricType.GAUGE


class TestContainerMetricDataTypes:
    """Test data types used in container metric service."""

    async def test_container_metric_action_fields(self) -> None:
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

    async def test_container_metric_response_fields(self) -> None:
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


class TestTimewindowInitialization:
    """Tests for timewindow initialization."""

    @pytest.mark.parametrize("timewindow", ["30s", "1m", "5m", "15m", "1h"])
    async def test_timewindow_stored_correctly(self, timewindow: str) -> None:
        fixed_query_builder = FixedQueryBuilder(timewindow)
        assert fixed_query_builder._timewindow == timewindow

    @pytest.mark.parametrize(
        "metric_name,value_type",
        [
            ("mem", ValueType.CURRENT),  # GAUGE
            ("net_rx", ValueType.CURRENT),  # RATE
            ("cpu_util", ValueType.CURRENT),  # DIFF
        ],
    )
    async def test_timewindow_applied_to_query(
        self, metric_name: str, value_type: ValueType
    ) -> None:
        fixed_query_builder = FixedQueryBuilder("3m")
        label = ContainerMetricOptionalLabel(value_type=value_type)

        query = fixed_query_builder.get_container_metric_query(metric_name, label)

        assert query.window == "3m"


@dataclass
class BuiltinQueryTestCase:
    id: str
    metric_name: str
    labels: ContainerMetricOptionalLabel
    timewindow: str
    expected_query: str


class TestBuiltinQueryProvider:
    """Characterization tests: verify container metric built-in queries produce expected PromQL."""

    @pytest.mark.parametrize(
        "case",
        [
            # GAUGE - no window in template
            BuiltinQueryTestCase(
                id="gauge_mem_current",
                metric_name="mem",
                labels=ContainerMetricOptionalLabel(value_type=ValueType.CURRENT),
                timewindow="5m",
                expected_query=(
                    "sum by (value_type)(backendai_container_utilization"
                    '{container_metric_name="mem",value_type="current"})'
                ),
            ),
            BuiltinQueryTestCase(
                id="gauge_mem_capacity_with_user_id",
                metric_name="mem",
                labels=ContainerMetricOptionalLabel(
                    value_type=ValueType.CAPACITY,
                    user_id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                ),
                timewindow="5m",
                expected_query=(
                    "sum by (user_id,value_type)(backendai_container_utilization"
                    '{container_metric_name="mem",value_type="capacity",'
                    'user_id="f38dea23-50fa-42a0-b5ae-338f5f4693f4"})'
                ),
            ),
            BuiltinQueryTestCase(
                id="gauge_cuda_util_with_user_id",
                metric_name="cuda_util",
                labels=ContainerMetricOptionalLabel(
                    value_type=ValueType.CURRENT,
                    user_id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                ),
                timewindow="5m",
                expected_query=(
                    "sum by (user_id,value_type)(backendai_container_utilization"
                    '{container_metric_name="cuda_util",value_type="current",'
                    'user_id="f38dea23-50fa-42a0-b5ae-338f5f4693f4"})'
                ),
            ),
            BuiltinQueryTestCase(
                id="gauge_io_read_with_user_id",
                metric_name="io_read",
                labels=ContainerMetricOptionalLabel(
                    value_type=ValueType.CURRENT,
                    user_id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                ),
                timewindow="5m",
                expected_query=(
                    "sum by (user_id,value_type)(backendai_container_utilization"
                    '{container_metric_name="io_read",value_type="current",'
                    'user_id="f38dea23-50fa-42a0-b5ae-338f5f4693f4"})'
                ),
            ),
            # RATE - rate() already returns per-second values.
            BuiltinQueryTestCase(
                id="rate_net_rx_current",
                metric_name="net_rx",
                labels=ContainerMetricOptionalLabel(value_type=ValueType.CURRENT),
                timewindow="5m",
                expected_query=(
                    "sum by (value_type)(rate(backendai_container_utilization"
                    '{container_metric_name="net_rx",value_type="current"}[5m]))'
                ),
            ),
            BuiltinQueryTestCase(
                id="rate_net_tx_with_user_id",
                metric_name="net_tx",
                labels=ContainerMetricOptionalLabel(
                    value_type=ValueType.CURRENT,
                    user_id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                ),
                timewindow="5m",
                expected_query=(
                    "sum by (user_id,value_type)(rate(backendai_container_utilization"
                    '{container_metric_name="net_tx",value_type="current",'
                    'user_id="f38dea23-50fa-42a0-b5ae-338f5f4693f4"}[5m]))'
                ),
            ),
            BuiltinQueryTestCase(
                id="rate_net_rx_capacity_with_user_id",
                metric_name="net_rx",
                labels=ContainerMetricOptionalLabel(
                    value_type=ValueType.CAPACITY,
                    user_id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                ),
                timewindow="5m",
                expected_query=(
                    "sum by (user_id,value_type)(rate(backendai_container_utilization"
                    '{container_metric_name="net_rx",value_type="capacity",'
                    'user_id="f38dea23-50fa-42a0-b5ae-338f5f4693f4"}[5m]))'
                ),
            ),
            # DIFF - uses window but no interval divisor
            BuiltinQueryTestCase(
                id="diff_cpu_util_current",
                metric_name="cpu_util",
                labels=ContainerMetricOptionalLabel(value_type=ValueType.CURRENT),
                timewindow="5m",
                expected_query=(
                    "sum by (value_type)(rate(backendai_container_utilization"
                    '{container_metric_name="cpu_util",value_type="current"}[5m]))'
                ),
            ),
            BuiltinQueryTestCase(
                id="diff_cpu_util_with_user_id",
                metric_name="cpu_util",
                labels=ContainerMetricOptionalLabel(
                    value_type=ValueType.CURRENT,
                    user_id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                ),
                timewindow="5m",
                expected_query=(
                    "sum by (user_id,value_type)(rate(backendai_container_utilization"
                    '{container_metric_name="cpu_util",value_type="current",'
                    'user_id="f38dea23-50fa-42a0-b5ae-338f5f4693f4"}[5m]))'
                ),
            ),
            # GAUGE for cpu_util with capacity (not DIFF since value_type != current)
            BuiltinQueryTestCase(
                id="gauge_cpu_util_capacity_with_user_id",
                metric_name="cpu_util",
                labels=ContainerMetricOptionalLabel(
                    value_type=ValueType.CAPACITY,
                    user_id=UUID("f38dea23-50fa-42a0-b5ae-338f5f4693f4"),
                ),
                timewindow="5m",
                expected_query=(
                    "sum by (user_id,value_type)(backendai_container_utilization"
                    '{container_metric_name="cpu_util",value_type="capacity",'
                    'user_id="f38dea23-50fa-42a0-b5ae-338f5f4693f4"})'
                ),
            ),
        ],
        ids=lambda c: c.id,
    )
    async def test_build_query_renders_expected_promql(self, case: BuiltinQueryTestCase) -> None:
        fixed_query_builder = FixedQueryBuilder(case.timewindow)

        query = fixed_query_builder.get_container_metric_query(case.metric_name, case.labels)
        rendered_query = query.render()

        assert rendered_query == case.expected_query


class TestContainerLiveStatQueries:
    """Characterization tests for container live stat PromQL."""

    @pytest.fixture()
    def queries(self) -> ContainerLiveStatQueries:
        kernel_id = KernelId(UUID("12345678-1234-5678-1234-567812345678"))
        fixed_query_builder = FixedQueryBuilder("5m")
        return fixed_query_builder.get_container_live_stat_queries([kernel_id])

    def test_instant_query_fetches_live_stat_fields(
        self, queries: ContainerLiveStatQueries
    ) -> None:
        rendered = queries.instant.render()

        assert "backendai_container_utilization" in rendered
        assert "sum by (container_metric_name,kernel_id,value_type)" in rendered
        assert 'value_type=~"current|capacity"' in rendered
        assert "pct" not in rendered

    def test_max_query_reads_current_series(self, queries: ContainerLiveStatQueries) -> None:
        rendered = queries.max.render()

        assert "label_replace" not in rendered
        assert "max_over_time" in rendered
        assert "sum by (container_metric_name,kernel_id)" in rendered
        assert 'value_type="current"' in rendered
        assert "rate(" not in rendered
        assert "backendai_container_utilization" in rendered

    def test_rate_max_query_reads_rate_series(self, queries: ContainerLiveStatQueries) -> None:
        rendered = queries.rate_max.render()

        assert "label_replace" not in rendered
        assert "max_over_time" in rendered
        assert "sum by (container_metric_name,kernel_id)" in rendered
        assert "rate(" in rendered
        assert 'container_metric_name=~"cpu_util|net_rx|net_tx"' in rendered
        assert 'value_type="current"' in rendered

    def test_avg_query_reads_current_series(self, queries: ContainerLiveStatQueries) -> None:
        rendered = queries.avg.render()

        assert "label_replace" not in rendered
        assert "avg_over_time" in rendered
        assert "sum by (container_metric_name,kernel_id)" in rendered
        assert 'value_type="current"' in rendered
        assert "rate(" not in rendered
        assert "backendai_container_utilization" in rendered

    def test_rate_avg_query_reads_rate_series(self, queries: ContainerLiveStatQueries) -> None:
        rendered = queries.rate_avg.render()

        assert "label_replace" not in rendered
        assert "avg_over_time" in rendered
        assert "sum by (container_metric_name,kernel_id)" in rendered
        assert "rate(" in rendered
        assert 'container_metric_name=~"cpu_util|net_rx|net_tx"' in rendered
        assert 'value_type="current"' in rendered


class TestKernelLiveStatBatchResultFromLiveStatResponse:
    @pytest.fixture()
    def kernel_id(self) -> KernelId:
        return KernelId(UUID("12345678-1234-5678-1234-567812345678"))

    def test_splits_instant_into_current_and_capacity(
        self,
        kernel_id: KernelId,
    ) -> None:
        instant = PrometheusResponse(
            status="success",
            data=PrometheusQueryData(
                result_type="vector",
                result=[
                    MetricResponse(
                        metric=MetricResponseInfo(
                            kernel_id=str(kernel_id),
                            container_metric_name="mem",
                            value_type="capacity",
                        ),
                        values=[(1704067200.0, "8192")],
                    ),
                    MetricResponse(
                        metric=MetricResponseInfo(
                            kernel_id=str(kernel_id),
                            container_metric_name="mem",
                            value_type="current",
                        ),
                        values=[(1704067200.0, "1024")],
                    ),
                ],
            ),
        )
        empty = PrometheusResponse(
            status="success",
            data=PrometheusQueryData(result_type="vector", result=[]),
        )
        batch = KernelLiveStatBatchResult.from_responses(
            instant=instant,
            rate_current=empty,
            max=empty,
            rate_max=empty,
            avg=empty,
            rate_avg=empty,
        )

        assert batch.by_kernel[kernel_id].instant_current["mem"] == "1024"
        assert batch.by_kernel[kernel_id].instant_capacity["mem"] == "8192"

    def test_routes_non_instant_response_into_named_slot(
        self,
        kernel_id: KernelId,
    ) -> None:
        max_response = PrometheusResponse(
            status="success",
            data=PrometheusQueryData(
                result_type="vector",
                result=[
                    MetricResponse(
                        metric=MetricResponseInfo(
                            kernel_id=str(kernel_id),
                            container_metric_name="mem",
                        ),
                        values=[(1704067200.0, "9001")],
                    )
                ],
            ),
        )
        empty = PrometheusResponse(
            status="success",
            data=PrometheusQueryData(result_type="vector", result=[]),
        )
        batch = KernelLiveStatBatchResult.from_responses(
            instant=empty,
            rate_current=empty,
            max=max_response,
            rate_max=empty,
            avg=empty,
            rate_avg=empty,
        )

        assert batch.by_kernel[kernel_id].max["mem"] == "9001"
        assert batch.by_kernel[kernel_id].instant_current == {}


class TestMetricResponseInfoParsing:
    """Unit tests for MetricResponseInfo parsing behavior."""

    def test_parse_general_prometheus_metric_without_value_type(self) -> None:
        info = MetricResponseInfo(name="up", instance="localhost:9090", job="prometheus")

        assert info.value_type is None
        assert info.name == "up"
        assert info.instance == "localhost:9090"

    def test_parse_backendai_metric_with_value_type(self) -> None:
        info = MetricResponseInfo(
            name="backendai_container_utilization",
            value_type="current",
            container_metric_name="cpu_util",
        )

        assert info.value_type == "current"
        assert info.name == "backendai_container_utilization"
        assert info.container_metric_name == "cpu_util"


class TestContainerMetricResponseInfoConversion:
    """Unit tests for ContainerMetricResponseInfo.from_metric_response_info()."""

    def test_from_metric_response_info_with_value_type_succeeds(self) -> None:
        info = MetricResponseInfo(
            name="backendai_container_utilization",
            value_type="current",
            container_metric_name="mem",
            agent_id="agent-1",
        )

        result = ContainerMetricResponseInfo.from_metric_response_info(info)

        assert result.value_type == "current"
        assert result.container_metric_name == "mem"
        assert result.agent_id == "agent-1"

    def test_from_metric_response_info_without_value_type_raises(self) -> None:
        info = MetricResponseInfo(name="up", instance="localhost:9090")

        with pytest.raises(InvalidAPIParameters):
            ContainerMetricResponseInfo.from_metric_response_info(info)
