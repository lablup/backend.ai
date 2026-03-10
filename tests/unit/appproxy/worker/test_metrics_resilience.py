"""
Regression tests for inference metric collection resilience.

The bug: when a single route's /metrics endpoint was unreachable
(e.g., after scale-in removed a replica), the entire metric collection
for that circuit failed. This caused app-level metrics to go stale,
preventing auto-scaling from re-triggering scale-out.

The fix: each route's HTTP request is wrapped in a try/except that
logs a warning and continues to the next route on failure.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Any
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


class TestGatherPrometheusInferenceMeasures:
    """Regression tests for per-route error resilience in metric collection."""

    @pytest.fixture
    def route_a(self) -> RouteInfo:
        return _make_route(kernel_host="10.0.0.1", kernel_port=8080)

    @pytest.fixture
    def route_b(self) -> RouteInfo:
        return _make_route(kernel_host="10.0.0.2", kernel_port=8081)

    async def test_unreachable_route_does_not_block_others(
        self,
        route_a: RouteInfo,
        route_b: RouteInfo,
    ) -> None:
        """Regression: one dead route must not prevent collection from healthy ones.

        Before the fix, a ConnectionError from a terminated route would
        propagate and abort the entire collection.
        """
        client_pool = _make_client_pool({
            _route_endpoint(route_a): SAMPLE_PROMETHEUS_OUTPUT,
            _route_endpoint(route_b): ConnectionError("Connection refused"),
        })

        measures = await gather_prometheus_inference_measures(client_pool, [route_a, route_b])

        assert len(measures) > 0
        metric_keys = {m.key for m in measures}
        assert "vllm:num_requests_running" in metric_keys

    async def test_all_routes_unreachable_returns_empty(
        self,
        route_a: RouteInfo,
        route_b: RouteInfo,
    ) -> None:
        """When all routes fail, should return empty list without raising."""
        client_pool = _make_client_pool({
            _route_endpoint(route_a): ConnectionError("Connection refused"),
            _route_endpoint(route_b): TimeoutError("Timed out"),
        })

        measures = await gather_prometheus_inference_measures(client_pool, [route_a, route_b])

        assert measures == []

    async def test_healthy_routes_collected_successfully(
        self,
        route_a: RouteInfo,
        route_b: RouteInfo,
    ) -> None:
        """Verify normal collection with all routes healthy."""
        client_pool = _make_client_pool({
            _route_endpoint(route_a): SAMPLE_PROMETHEUS_OUTPUT,
            _route_endpoint(route_b): SAMPLE_PROMETHEUS_OUTPUT,
        })

        measures = await gather_prometheus_inference_measures(client_pool, [route_a, route_b])

        assert len(measures) > 0
        # With 2 routes each reporting 3 running requests, aggregated = 6
        for m in measures:
            if m.key == "vllm:num_requests_running":
                assert isinstance(m.per_app, Measurement)
                assert m.per_app.value == Decimal(6)
                assert len(m.per_replica) == 2

    @pytest.fixture
    def route_unhealthy(self) -> RouteInfo:
        return _make_route(
            kernel_host="10.0.0.2",
            kernel_port=8081,
            health_status=ModelServiceStatus.UNHEALTHY,
        )

    async def test_unhealthy_route_skipped(
        self,
        route_a: RouteInfo,
        route_unhealthy: RouteInfo,
    ) -> None:
        """Routes with non-HEALTHY status should be skipped entirely."""
        client_pool = _make_client_pool({
            _route_endpoint(route_a): SAMPLE_PROMETHEUS_OUTPUT,
            _route_endpoint(route_unhealthy): SAMPLE_PROMETHEUS_OUTPUT,
        })

        measures = await gather_prometheus_inference_measures(
            client_pool, [route_a, route_unhealthy]
        )

        # Only the healthy route should contribute
        for m in measures:
            if m.key == "vllm:num_requests_running":
                assert isinstance(m.per_app, Measurement)
                assert m.per_app.value == Decimal(3)
                assert len(m.per_replica) == 1

    async def test_route_without_route_id_skipped(self) -> None:
        """Routes with route_id=None (temporary) should be skipped."""
        route = _make_route()
        route.route_id = None

        client_pool = _make_client_pool({})

        measures = await gather_prometheus_inference_measures(client_pool, [route])

        assert measures == []
