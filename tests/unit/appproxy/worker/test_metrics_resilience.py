"""
Regression tests for inference metric collection resilience.

The bug: when a single route's /metrics endpoint was unreachable
(e.g., after scale-in removed a replica), the entire metric collection
for that circuit failed. This caused app-level metrics to go stale,
preventing auto-scaling from re-triggering scale-out.

The fix: each route's HTTP request and response parsing is wrapped in
try/except that logs a warning and continues to the next route on failure.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from ai.backend.appproxy.common.types import ProxyProtocol, RouteInfo
from ai.backend.appproxy.worker.metrics import gather_prometheus_inference_measures
from ai.backend.appproxy.worker.types import Measurement
from ai.backend.common.types import ModelServiceStatus

SAMPLE_PROMETHEUS_OUTPUT = """\
# HELP vllm:num_requests_running Number of requests running
# TYPE vllm:num_requests_running gauge
vllm:num_requests_running 3
# HELP vllm:num_requests_waiting Number of requests waiting
# TYPE vllm:num_requests_waiting gauge
vllm:num_requests_waiting 0
"""

MALFORMED_PROMETHEUS_OUTPUT = "this is not valid prometheus metrics {{{{"


def _make_route(
    kernel_host: str = "10.0.0.1",
    kernel_port: int = 8080,
    health_status: ModelServiceStatus | None = ModelServiceStatus.HEALTHY,
) -> RouteInfo:
    return RouteInfo(
        route_id=uuid4(),
        session_id=uuid4(),
        session_name=None,
        kernel_host=kernel_host,
        kernel_port=kernel_port,
        protocol=ProxyProtocol.HTTP,
        traffic_ratio=1.0,
        health_status=health_status,
        last_health_check=None,
        consecutive_failures=0,
    )


def _route_endpoint(route: RouteInfo) -> str:
    return f"http://{route.current_kernel_host}:{route.kernel_port}"


@dataclass(frozen=True)
class RouteInput:
    """Configuration for a single route in a test scenario."""

    kernel_host: str
    kernel_port: int
    health_status: ModelServiceStatus | None
    mock_response: str | Exception


@dataclass(frozen=True)
class MetricsScenario:
    """Describes a metric collection test case."""

    routes: list[RouteInfo]
    responses: dict[str, str | Exception]
    # None means measures should be empty
    expected_num_requests_running: Decimal | None
    expected_collected_replica_count: int


def _create_metrics_scenario(
    route_configs: list[RouteInput],
    *,
    expected_num_requests_running: Decimal | None,
    expected_collected_replica_count: int,
) -> MetricsScenario:
    """Build a scenario from (host, port, health_status, response) tuples."""
    routes: list[RouteInfo] = []
    responses: dict[str, str | Exception] = {}
    for cfg in route_configs:
        route = _make_route(
            kernel_host=cfg.kernel_host,
            kernel_port=cfg.kernel_port,
            health_status=cfg.health_status,
        )
        routes.append(route)
        responses[_route_endpoint(route)] = cfg.mock_response
    return MetricsScenario(
        routes=routes,
        responses=responses,
        expected_num_requests_running=expected_num_requests_running,
        expected_collected_replica_count=expected_collected_replica_count,
    )


class TestGatherPrometheusInferenceMeasures:
    """Regression tests for per-route error resilience in metric collection."""

    @pytest.mark.parametrize(
        "scenario",
        [
            pytest.param(
                _create_metrics_scenario(
                    [
                        RouteInput(
                            kernel_host="10.0.0.1",
                            kernel_port=8080,
                            health_status=ModelServiceStatus.HEALTHY,
                            mock_response=SAMPLE_PROMETHEUS_OUTPUT,
                        ),
                        RouteInput(
                            kernel_host="10.0.0.2",
                            kernel_port=8081,
                            health_status=ModelServiceStatus.HEALTHY,
                            mock_response=ConnectionError("Connection refused"),
                        ),
                    ],
                    expected_num_requests_running=Decimal(3),
                    expected_collected_replica_count=1,
                ),
                id="partial-failure-connection-error",
            ),
            pytest.param(
                _create_metrics_scenario(
                    [
                        RouteInput(
                            kernel_host="10.0.0.1",
                            kernel_port=8080,
                            health_status=ModelServiceStatus.HEALTHY,
                            mock_response=ConnectionError("Connection refused"),
                        ),
                        RouteInput(
                            kernel_host="10.0.0.2",
                            kernel_port=8081,
                            health_status=ModelServiceStatus.HEALTHY,
                            mock_response=TimeoutError("Timed out"),
                        ),
                    ],
                    expected_num_requests_running=None,
                    expected_collected_replica_count=0,
                ),
                id="all-routes-unreachable",
            ),
            pytest.param(
                _create_metrics_scenario(
                    [
                        RouteInput(
                            kernel_host="10.0.0.1",
                            kernel_port=8080,
                            health_status=ModelServiceStatus.HEALTHY,
                            mock_response=SAMPLE_PROMETHEUS_OUTPUT,
                        ),
                        RouteInput(
                            kernel_host="10.0.0.2",
                            kernel_port=8081,
                            health_status=ModelServiceStatus.HEALTHY,
                            mock_response=SAMPLE_PROMETHEUS_OUTPUT,
                        ),
                    ],
                    expected_num_requests_running=Decimal(6),
                    expected_collected_replica_count=2,
                ),
                id="two-healthy-routes",
            ),
            pytest.param(
                _create_metrics_scenario(
                    [
                        RouteInput(
                            kernel_host="10.0.0.1",
                            kernel_port=8080,
                            health_status=ModelServiceStatus.HEALTHY,
                            mock_response=SAMPLE_PROMETHEUS_OUTPUT,
                        ),
                        RouteInput(
                            kernel_host="10.0.0.2",
                            kernel_port=8081,
                            health_status=ModelServiceStatus.UNHEALTHY,
                            mock_response=SAMPLE_PROMETHEUS_OUTPUT,
                        ),
                    ],
                    expected_num_requests_running=Decimal(3),
                    expected_collected_replica_count=1,
                ),
                id="unhealthy-route-skipped",
            ),
            pytest.param(
                _create_metrics_scenario(
                    [
                        RouteInput(
                            kernel_host="10.0.0.1",
                            kernel_port=8080,
                            health_status=ModelServiceStatus.HEALTHY,
                            mock_response=SAMPLE_PROMETHEUS_OUTPUT,
                        ),
                        RouteInput(
                            kernel_host="10.0.0.3",
                            kernel_port=8082,
                            health_status=ModelServiceStatus.HEALTHY,
                            mock_response=MALFORMED_PROMETHEUS_OUTPUT,
                        ),
                    ],
                    expected_num_requests_running=Decimal(3),
                    expected_collected_replica_count=1,
                ),
                id="malformed-payload",
            ),
        ],
    )
    async def test_metric_collection(
        self, scenario: MetricsScenario, mock_metrics_client_pool: Any
    ) -> None:
        async with mock_metrics_client_pool(scenario.responses) as (client_pool, _):
            measures = await gather_prometheus_inference_measures(client_pool, scenario.routes)

            if scenario.expected_num_requests_running is None:
                assert measures == []
            else:
                running_measures = [m for m in measures if m.key == "vllm:num_requests_running"]
                assert len(running_measures) == 1, (
                    f"Expected exactly 1 'vllm:num_requests_running' measure, "
                    f"got {len(running_measures)}"
                )
                running_measure = running_measures[0]
                assert isinstance(running_measure.per_app, Measurement)
                assert running_measure.per_app.value == scenario.expected_num_requests_running
                assert len(running_measure.per_replica) == scenario.expected_collected_replica_count

    async def test_route_without_route_id_skipped(self) -> None:
        """Routes with route_id=None (temporary) should be skipped."""
        route = _make_route()
        route.route_id = None

        client_pool = MagicMock()

        measures = await gather_prometheus_inference_measures(client_pool, [route])

        assert measures == []
