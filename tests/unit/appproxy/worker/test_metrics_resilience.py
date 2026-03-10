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

from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Any, NamedTuple
from unittest.mock import AsyncMock, MagicMock
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


def _make_client_pool(
    responses: dict[str, str | Exception],
) -> MagicMock:
    """Create a mock ClientPool that returns different responses per endpoint.

    Args:
        responses: mapping of endpoint URL to response text or Exception.
    """
    pool = MagicMock()

    def load_client_session(client_key: Any) -> MagicMock:
        endpoint = client_key.endpoint
        session = MagicMock()

        resp_value = responses.get(endpoint)
        if isinstance(resp_value, Exception):
            exc: Exception = resp_value

            def failing_get(path: str, _exc: Exception = exc) -> MagicMock:
                cm = MagicMock()
                cm.__aenter__ = AsyncMock(side_effect=_exc)
                cm.__aexit__ = AsyncMock(return_value=False)
                return cm

            session.get = failing_get
        else:
            resp_text = responses.get(endpoint, "")

            @asynccontextmanager
            async def successful_get(path: str) -> Any:
                resp = MagicMock()
                resp.raise_for_status = MagicMock()
                resp.text = AsyncMock(return_value=resp_text)
                yield resp

            session.get = successful_get

        return session

    pool.load_client_session = load_client_session
    return pool


class PartialFailureScenario(NamedTuple):
    """One healthy route + one unreachable route for resilience testing."""

    healthy_route: RouteInfo
    unreachable_route: RouteInfo


class AllFailureScenario(NamedTuple):
    """All routes unreachable."""

    connection_refused_route: RouteInfo
    timed_out_route: RouteInfo


class TwoHealthyRoutesScenario(NamedTuple):
    """Two healthy routes returning valid metrics."""

    first_route: RouteInfo
    second_route: RouteInfo


class HealthyUnhealthyScenario(NamedTuple):
    """One healthy route + one unhealthy route (health check failed)."""

    healthy_route: RouteInfo
    unhealthy_route: RouteInfo


class MalformedPayloadScenario(NamedTuple):
    """One healthy route + one route returning malformed metrics text."""

    healthy_route: RouteInfo
    malformed_route: RouteInfo


class TestGatherPrometheusInferenceMeasures:
    """Regression tests for per-route error resilience in metric collection."""

    @pytest.fixture
    def partial_failure_scenario(self) -> PartialFailureScenario:
        """One route returns metrics, the other raises ConnectionError."""
        return PartialFailureScenario(
            healthy_route=_make_route(kernel_host="10.0.0.1", kernel_port=8080),
            unreachable_route=_make_route(kernel_host="10.0.0.2", kernel_port=8081),
        )

    @pytest.fixture
    def all_failure_scenario(self) -> AllFailureScenario:
        """Both routes fail with different errors."""
        return AllFailureScenario(
            connection_refused_route=_make_route(kernel_host="10.0.0.1", kernel_port=8080),
            timed_out_route=_make_route(kernel_host="10.0.0.2", kernel_port=8081),
        )

    @pytest.fixture
    def two_healthy_routes_scenario(self) -> TwoHealthyRoutesScenario:
        """Both routes healthy and returning valid metrics."""
        return TwoHealthyRoutesScenario(
            first_route=_make_route(kernel_host="10.0.0.1", kernel_port=8080),
            second_route=_make_route(kernel_host="10.0.0.2", kernel_port=8081),
        )

    @pytest.fixture
    def healthy_unhealthy_scenario(self) -> HealthyUnhealthyScenario:
        """One healthy route + one route marked UNHEALTHY by health check."""
        return HealthyUnhealthyScenario(
            healthy_route=_make_route(kernel_host="10.0.0.1", kernel_port=8080),
            unhealthy_route=_make_route(
                kernel_host="10.0.0.2",
                kernel_port=8081,
                health_status=ModelServiceStatus.UNHEALTHY,
            ),
        )

    @pytest.fixture
    def malformed_payload_scenario(self) -> MalformedPayloadScenario:
        """One healthy route + one route returning invalid prometheus text."""
        return MalformedPayloadScenario(
            healthy_route=_make_route(kernel_host="10.0.0.1", kernel_port=8080),
            malformed_route=_make_route(kernel_host="10.0.0.3", kernel_port=8082),
        )

    async def test_unreachable_route_does_not_block_others(
        self,
        partial_failure_scenario: PartialFailureScenario,
    ) -> None:
        """Regression: one dead route must not prevent collection from healthy ones.

        Before the fix, a ConnectionError from a terminated route would
        propagate and abort the entire collection.
        """
        scenario = partial_failure_scenario
        client_pool = _make_client_pool({
            _route_endpoint(scenario.healthy_route): SAMPLE_PROMETHEUS_OUTPUT,
            _route_endpoint(scenario.unreachable_route): ConnectionError("Connection refused"),
        })

        measures = await gather_prometheus_inference_measures(
            client_pool, [scenario.healthy_route, scenario.unreachable_route]
        )

        assert len(measures) > 0
        metric_keys = {m.key for m in measures}
        assert "vllm:num_requests_running" in metric_keys

    async def test_all_routes_unreachable_returns_empty(
        self,
        all_failure_scenario: AllFailureScenario,
    ) -> None:
        """When all routes fail, should return empty list without raising."""
        scenario = all_failure_scenario
        client_pool = _make_client_pool({
            _route_endpoint(scenario.connection_refused_route): ConnectionError(
                "Connection refused"
            ),
            _route_endpoint(scenario.timed_out_route): TimeoutError("Timed out"),
        })

        measures = await gather_prometheus_inference_measures(
            client_pool,
            [scenario.connection_refused_route, scenario.timed_out_route],
        )

        assert measures == []

    async def test_healthy_routes_collected_successfully(
        self,
        two_healthy_routes_scenario: TwoHealthyRoutesScenario,
    ) -> None:
        """Verify normal collection with all routes healthy."""
        scenario = two_healthy_routes_scenario
        client_pool = _make_client_pool({
            _route_endpoint(scenario.first_route): SAMPLE_PROMETHEUS_OUTPUT,
            _route_endpoint(scenario.second_route): SAMPLE_PROMETHEUS_OUTPUT,
        })

        measures = await gather_prometheus_inference_measures(
            client_pool, [scenario.first_route, scenario.second_route]
        )

        assert len(measures) > 0
        # With 2 routes each reporting 3 running requests, aggregated = 6
        for m in measures:
            if m.key == "vllm:num_requests_running":
                assert isinstance(m.per_app, Measurement)
                assert m.per_app.value == Decimal(6)
                assert len(m.per_replica) == 2

    async def test_unhealthy_route_skipped(
        self,
        healthy_unhealthy_scenario: HealthyUnhealthyScenario,
    ) -> None:
        """Routes with non-HEALTHY status should be skipped entirely."""
        scenario = healthy_unhealthy_scenario
        client_pool = _make_client_pool({
            _route_endpoint(scenario.healthy_route): SAMPLE_PROMETHEUS_OUTPUT,
            _route_endpoint(scenario.unhealthy_route): SAMPLE_PROMETHEUS_OUTPUT,
        })

        measures = await gather_prometheus_inference_measures(
            client_pool, [scenario.healthy_route, scenario.unhealthy_route]
        )

        # Only the healthy route should contribute
        for m in measures:
            if m.key == "vllm:num_requests_running":
                assert isinstance(m.per_app, Measurement)
                assert m.per_app.value == Decimal(3)
                assert len(m.per_replica) == 1

    async def test_malformed_metrics_payload_does_not_block_others(
        self,
        malformed_payload_scenario: MalformedPayloadScenario,
    ) -> None:
        """A route returning malformed /metrics text must not abort the entire collection.

        The parsing try/except should catch the error and skip that route,
        allowing other routes' metrics to be collected normally.
        """
        scenario = malformed_payload_scenario
        client_pool = _make_client_pool({
            _route_endpoint(scenario.healthy_route): SAMPLE_PROMETHEUS_OUTPUT,
            _route_endpoint(scenario.malformed_route): MALFORMED_PROMETHEUS_OUTPUT,
        })

        measures = await gather_prometheus_inference_measures(
            client_pool, [scenario.healthy_route, scenario.malformed_route]
        )

        assert len(measures) > 0
        metric_keys = {m.key for m in measures}
        assert "vllm:num_requests_running" in metric_keys

    async def test_route_without_route_id_skipped(self) -> None:
        """Routes with route_id=None (temporary) should be skipped."""
        route = _make_route()
        route.route_id = None

        client_pool = _make_client_pool({})

        measures = await gather_prometheus_inference_measures(client_pool, [route])

        assert measures == []
