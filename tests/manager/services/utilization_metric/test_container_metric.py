import asyncio
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from yarl import URL

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
    ContainerMetricResult,
    MetricResultValue,
    UtilizationMetricType,
    ValueType,
)


class TestScenario:
    def __init__(self, description: str, input: Any, expected: Any, expected_exception: Any = None):
        self.description = description
        self.input = input
        self.expected = expected
        self.expected_exception = expected_exception

    @classmethod
    def success(cls, description: str, input: Any, expected: Any):
        return cls(description, input, expected)

    @classmethod
    def failure(cls, description: str, input: Any, expected_exception: Any):
        return cls(description, input, None, expected_exception)


@pytest.fixture
def mock_config_provider():
    config_provider = MagicMock(spec=ManagerConfigProvider)
    config_provider.config.metric.address.to_legacy.return_value = "localhost:9090"
    config_provider.config.metric.timewindow = "1m"
    return config_provider


@pytest.fixture
def metric_service(mock_config_provider):
    return ContainerUtilizationMetricService(mock_config_provider)


class TestQueryMetadata:
    @pytest.mark.parametrize(
        "scenario",
        [
            TestScenario.success(
                description="전체 메트릭 목록 조회",
                input=ContainerMetricMetadataAction(),
                expected=ContainerMetricMetadataActionResult([
                    "container_cpu_percent",
                    "container_memory_used_bytes",
                    "container_network_rx_bytes",
                    "container_network_tx_bytes",
                ]),
            ),
            TestScenario.success(
                description="빈 메트릭 목록",
                input=ContainerMetricMetadataAction(),
                expected=ContainerMetricMetadataActionResult([]),
            ),
        ],
        ids=lambda s: s.description,
    )
    async def test_query_metadata_success(self, metric_service, scenario):
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.raise_for_status = AsyncMock()
            mock_response.json = AsyncMock(return_value={
                "status": "success",
                "data": scenario.expected.result
            })
            
            mock_session.get.return_value.__aenter__.return_value = mock_response
            
            result = await metric_service.query_metadata(scenario.input)
            assert result == scenario.expected

    async def test_query_metadata_prometheus_connection_failure(self, metric_service):
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            mock_session.get.side_effect = aiohttp.ClientError("Connection failed")
            
            with pytest.raises(aiohttp.ClientError):
                await metric_service.query_metadata(ContainerMetricMetadataAction())


class TestQueryMetric:
    @pytest.mark.parametrize(
        "scenario",
        [
            TestScenario.success(
                description="CPU 사용률 조회",
                input=ContainerMetricAction(
                    metric_name="container_cpu_percent",
                    start="2024-01-01T00:00:00",
                    end="2024-01-01T01:00:00",
                    step="60s",
                    labels=ContainerMetricOptionalLabel(
                        value_type="current",
                        kernel_id="kernel-123",
                    ),
                ),
                expected=ContainerMetricActionResult(
                    result=[
                        ContainerMetricResult(
                            metric=ContainerMetricResponseInfo(
                                value_type="current",
                                container_metric_name="cpu_util",
                                agent_id=None,
                                instance=None,
                                job=None,
                                kernel_id="kernel-123",
                                owner_project_id= None,
                                owner_user_id= None,
                                session_id= None,
                            ),
                            values=[
                                MetricResultValue(1704067200.0, "10.5"),
                                MetricResultValue(1704067260.0, "12.3"),
                                MetricResultValue(1704067320.0, "15.7"),
                            ],
                        )
                    ]
                ),
            ),
            TestScenario.success(
                description="메모리 사용량 RATE 조회",
                input=ContainerMetricAction(
                    metric_name="container_memory_used_bytes",
                    start="2024-01-01T00:00:00",
                    end="2024-01-01T00:05:00",
                    step="60s",
                    labels=ContainerMetricOptionalLabel(
                        value_type="current",
                    ),
                ),
                expected=ContainerMetricActionResult(
                    result=[
                        ContainerMetricResult(
                            metric=ContainerMetricResponseInfo(
                                value_type="current",
                                container_metric_name="container_memory_used_bytes",
                            ),
                            values=[
                                MetricResultValue(1704067200.0, "1048576"),
                                MetricResultValue(1704067260.0, "2097152"),
                            ],
                        )
                    ]
                ),
            ),
            TestScenario.success(
                description="네트워크 전송량 DIFF 조회",
                input=ContainerMetricAction(
                    metric_name="container_network_tx_bytes",
                    start="2024-01-01T00:00:00",
                    end="2024-01-01T00:15:00",
                    step=300,
                    labels=ContainerMetricOptionalLabel(
                        agent_id="agent-1",
                    ),
                ),
                expected=ContainerMetricActionResult(
                    result=[
                        ContainerMetricResult(
                            metric=ContainerMetricResponseInfo(
                                agent_id="agent-1",
                                container_metric_name="container_network_tx_bytes",
                            ),
                            values=[
                                MetricResultValue(1704067200.0, "1024000"),
                                MetricResultValue(1704067500.0, "2048000"),
                            ],
                        )
                    ]
                ),
            ),
            TestScenario.success(
                description="프로젝트별 집계",
                input=ContainerMetricAction(
                    metric_name="container_cpu_percent",
                    start="2024-01-01T00:00:00",
                    end="2024-01-01T01:00:00",
                    step=60,
                    labels=ContainerMetricOptionalLabel(
                        project_id="research-team",
                    ),
                ),
                expected=ContainerMetricActionResult(
                    result=[
                        ContainerMetricResult(
                            metric=ContainerMetricResponseInfo(
                                owner_project_id="research-team",
                                container_metric_name="container_cpu_percent",
                            ),
                            values=[
                                MetricResultValue(1704067200.0, "45.2"),
                            ],
                        )
                    ]
                ),
            ),
            TestScenario.success(
                description="사용자별 GPU 사용률",
                input=ContainerMetricAction(
                    metric_name="container_gpu_percent",
                    start="2024-01-01T00:00:00",
                    end="2024-01-01T01:00:00",
                    step=60,
                    labels=ContainerMetricOptionalLabel(
                        user_id="user@example.com",
                    ),
                ),
                expected=ContainerMetricActionResult(
                    result=[
                        ContainerMetricResult(
                            metric=ContainerMetricResponseInfo(
                                owner_user_id="user@example.com",
                                container_metric_name="container_gpu_percent",
                            ),
                            values=[
                                MetricResultValue(1704067200.0, "80.5"),
                            ],
                        )
                    ]
                ),
            ),
            TestScenario.success(
                description="레이블 필터링",
                input=ContainerMetricAction(
                    metric_name="container_cpu_percent",
                    start="2024-01-01T00:00:00",
                    end="2024-01-01T01:00:00",
                    step=60,
                    labels=ContainerMetricOptionalLabel(
                        agent_id="agent-1",
                        kernel_id="kernel-456",
                    ),
                ),
                expected=ContainerMetricActionResult(
                    result=[
                        ContainerMetricResult(
                            metric=ContainerMetricResponseInfo(
                                agent_id="agent-1",
                                kernel_id="kernel-456",
                                container_metric_name="container_cpu_percent",
                            ),
                            values=[
                                MetricResultValue(1704067200.0, "25.3"),
                            ],
                        )
                    ]
                ),
            ),
            TestScenario.success(
                description="용량 값 조회",
                input=ContainerMetricAction(
                    metric_name="container_memory_capacity_bytes",
                    start="2024-01-01T00:00:00",
                    end="2024-01-01T01:00:00",
                    step="60s",
                    labels=ContainerMetricOptionalLabel(
                        value_type="capacity",
                    ),
                ),
                expected=ContainerMetricActionResult(
                    result=[
                        ContainerMetricResult(
                            metric=ContainerMetricResponseInfo(
                                value_type="capacity",
                                container_metric_name="mem",
                            ),
                            values=[
                                MetricResultValue(1704067200.0, "8589934592"),
                            ],
                        )
                    ]
                ),
            ),
            TestScenario.success(
                description="빈 결과 - 잘못된 메트릭 이름",
                input=ContainerMetricAction(
                    metric_name="invalid_metric_name",
                    start="2024-01-01T00:00:00",
                    end="2024-01-01T01:00:00",
                    step=60,
                    labels=ContainerMetricOptionalLabel(),
                ),
                expected=ContainerMetricActionResult(result=[]),
            ),
        ],
        ids=lambda s: s.description,
    )
    async def test_query_metric_success(self, metric_service, scenario):
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            mock_response = AsyncMock()
            mock_response.status = 200
            
            # Prepare response data based on expected result
            response_data = {
                "status": "success",
                "data": {
                    "result": []
                }
            }
            
            for result in scenario.expected.result:
                metric_data = {
                    "metric": {
                        "value_type": result.metric.value_type or "usage",
                        "__name__": "backendai_container_utilization",
                        "container_metric_name": result.metric.container_metric_name,
                    },
                    "values": [[v.timestamp, v.value] for v in result.values]
                }
                
                # Add optional fields if present
                if result.metric.agent_id:
                    metric_data["metric"]["agent_id"] = result.metric.agent_id
                if result.metric.kernel_id:
                    metric_data["metric"]["kernel_id"] = result.metric.kernel_id
                if result.metric.owner_project_id:
                    metric_data["metric"]["owner_project_id"] = result.metric.owner_project_id
                if result.metric.owner_user_id:
                    metric_data["metric"]["owner_user_id"] = result.metric.owner_user_id
                    
                response_data["data"]["result"].append(metric_data)
            
            mock_response.json = AsyncMock(return_value=response_data)
            mock_session.post.return_value.__aenter__.return_value = mock_response
            
            result = await metric_service.query_metric(scenario.input)
            assert result == scenario.expected

    async def test_query_metric_prometheus_error(self, metric_service):
        action = ContainerMetricAction(
            metric_name="container_cpu_percent",
            start="2024-01-01T00:00:00",
            end="2024-01-01T01:00:00",
            step=60,
            labels=ContainerMetricOptionalLabel(),
        )
        
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            mock_response = AsyncMock()
            mock_response.status = 400
            mock_response.json = AsyncMock(return_value={
                "status": "error",
                "error": "Bad Request: Invalid query"
            })
            
            mock_session.post.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(FailedToGetMetric, match="Bad Request: Invalid query"):
                await metric_service.query_metric(action)

    async def test_query_metric_server_error(self, metric_service):
        action = ContainerMetricAction(
            metric_name="container_cpu_percent",
            start="2024-01-01T00:00:00",
            end="2024-01-01T01:00:00",
            step=60,
            labels=ContainerMetricOptionalLabel(),
        )
        
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            mock_response = AsyncMock()
            mock_response.status = 500
            
            mock_session.post.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(FailedToGetMetric):
                await metric_service.query_metric(action)


class TestMetricTypeDetection:
    @pytest.mark.parametrize(
        "metric_name,label,expected_type",
        [
            ("cpu_util", ContainerMetricOptionalLabel(value_type="current"), UtilizationMetricType.DIFF),
            ("net_rx", ContainerMetricOptionalLabel(), UtilizationMetricType.RATE),
            ("net_tx", ContainerMetricOptionalLabel(), UtilizationMetricType.RATE),
            ("container_memory_used_bytes", ContainerMetricOptionalLabel(), UtilizationMetricType.GAUGE),
            ("container_gpu_percent", ContainerMetricOptionalLabel(), UtilizationMetricType.GAUGE),
        ],
    )
    def test_get_metric_type(self, metric_service, metric_name, label, expected_type):
        result = metric_service._get_metric_type(metric_name, label)
        assert result == expected_type


class TestQueryStringGeneration:
    async def test_gauge_query_string(self, metric_service):
        query = await metric_service._get_query_string(
            "container_memory_used_bytes",
            ContainerMetricOptionalLabel(kernel_id="kernel-123", value_type="usage"),
        )
        assert "sum by(value_type, kernel_id)" in query
        assert 'container_metric_name="container_memory_used_bytes"' in query
        assert 'kernel_id="kernel-123"' in query
        assert 'value_type="usage"' in query

    async def test_rate_query_string(self, metric_service):
        query = await metric_service._get_query_string(
            "net_rx",
            ContainerMetricOptionalLabel(agent_id="agent-1"),
        )
        assert "rate(" in query
        assert "[1m]" in query  # timewindow
        assert 'container_metric_name="net_rx"' in query
        assert 'agent_id="agent-1"' in query

    async def test_diff_query_string(self, metric_service):
        query = await metric_service._get_query_string(
            "cpu_util",
            ContainerMetricOptionalLabel(value_type="current", session_id="session-123"),
        )
        assert "rate(" in query
        assert "[1m]" in query
        assert 'value_type="current"' in query
        assert 'session_id="session-123"' in query


class TestComplexScenarios:
    async def test_multi_kernel_session_monitoring(self, metric_service):
        # Simulate monitoring multiple kernels in a cluster session
        kernel_ids = ["kernel-1", "kernel-2", "kernel-3"]
        
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            results = []
            for kernel_id in kernel_ids:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json = AsyncMock(return_value={
                    "status": "success",
                    "data": {
                        "result": [{
                            "metric": {
                                "value_type": "usage",
                                "__name__": "backendai_container_utilization",
                                "container_metric_name": "container_cpu_percent",
                                "kernel_id": kernel_id,
                            },
                            "values": [[1704067200.0, "10.5"]]
                        }]
                    }
                })
                
                mock_session.post.return_value.__aenter__.return_value = mock_response
                
                action = ContainerMetricAction(
                    metric_name="container_cpu_percent",
                    start="2024-01-01T00:00:00",
                    end="2024-01-01T01:00:00",
                    step=60,
                    labels=ContainerMetricOptionalLabel(kernel_id=kernel_id),
                )
                
                result = await metric_service.query_metric(action)
                results.append(result)
            
            # Verify we got results for all kernels
            assert len(results) == 3
            for i, result in enumerate(results):
                assert result.result[0].metric.kernel_id == kernel_ids[i]

    async def test_resource_usage_trend_analysis(self, metric_service):
        # Test retrieving 24-hour resource usage trends
        metrics_to_query = ["container_cpu_percent", "container_memory_used_bytes", "container_disk_io_bytes"]
        
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__.return_value = mock_session
            
            # Mock response for trend data
            mock_response = AsyncMock()
            mock_response.status = 200
            
            # Generate hourly data points
            hourly_values = []
            base_timestamp = 1704067200.0  # 2024-01-01 00:00:00
            for i in range(24):
                hourly_values.append([base_timestamp + (i * 3600), str(10 + i * 2)])
            
            mock_response.json = AsyncMock(return_value={
                "status": "success",
                "data": {
                    "result": [{
                        "metric": {
                            "value_type": "usage",
                            "__name__": "backendai_container_utilization",
                            "container_metric_name": "container_cpu_percent",
                        },
                        "values": hourly_values
                    }]
                }
            })
            
            mock_session.post.return_value.__aenter__.return_value = mock_response
            
            action = ContainerMetricAction(
                metric_name="container_cpu_percent",
                start="2024-01-01T00:00:00",
                end="2024-01-02T00:00:00",
                step=3600,  # 1 hour intervals
                labels=ContainerMetricOptionalLabel(),
            )
            
            result = await metric_service.query_metric(action)
            
            # Verify trend data
            assert len(result.result[0].values) == 24
            # Check if values show increasing trend (simulated peak usage)
            first_value = float(result.result[0].values[0].value)
            last_value = float(result.result[0].values[-1].value)
            assert last_value > first_value  # Usage increased over time