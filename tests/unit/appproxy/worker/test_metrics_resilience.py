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

    async def test_unreachable_route_does_not_block_others(self) -> None:
        """Regression: one dead route must not prevent collection from healthy ones.

        Before the fix, a ConnectionError from a terminated route would
        propagate and abort the entire collection.
        """
        route_healthy = _make_route(kernel_host="10.0.0.1", kernel_port=8080)
        route_dead = _make_route(kernel_host="10.0.0.2", kernel_port=8081)

        client_pool = _make_client_pool({
            "http://10.0.0.1:8080": SAMPLE_PROMETHEUS_OUTPUT,
            "http://10.0.0.2:8081": ConnectionError("Connection refused"),
        })

        measures = await gather_prometheus_inference_measures(
            client_pool, [route_healthy, route_dead]
        )

        assert len(measures) > 0
        # Verify we got metrics from the healthy route
        metric_keys = {m.key for m in measures}
        assert "vllm:num_requests_running" in metric_keys

    async def test_all_routes_unreachable_returns_empty(self) -> None:
        """When all routes fail, should return empty list without raising."""
        route_a = _make_route(kernel_host="10.0.0.1", kernel_port=8080)
        route_b = _make_route(kernel_host="10.0.0.2", kernel_port=8081)

        client_pool = _make_client_pool({
            "http://10.0.0.1:8080": ConnectionError("Connection refused"),
            "http://10.0.0.2:8081": TimeoutError("Timed out"),
        })

        measures = await gather_prometheus_inference_measures(client_pool, [route_a, route_b])

        assert measures == []

    async def test_healthy_routes_collected_successfully(self) -> None:
        """Verify normal collection with all routes healthy."""
        route_a = _make_route(kernel_host="10.0.0.1", kernel_port=8080)
        route_b = _make_route(kernel_host="10.0.0.2", kernel_port=8081)

        client_pool = _make_client_pool({
            "http://10.0.0.1:8080": SAMPLE_PROMETHEUS_OUTPUT,
            "http://10.0.0.2:8081": SAMPLE_PROMETHEUS_OUTPUT,
        })

        measures = await gather_prometheus_inference_measures(client_pool, [route_a, route_b])

        assert len(measures) > 0
        # With 2 routes each reporting 3 running requests, aggregated = 6
        for m in measures:
            if m.key == "vllm:num_requests_running":
                assert isinstance(m.per_app, Measurement)
                assert m.per_app.value == Decimal(6)
                assert len(m.per_replica) == 2

    async def test_unhealthy_route_skipped(self) -> None:
        """Routes with non-HEALTHY status should be skipped entirely."""
        route_healthy = _make_route(
            kernel_host="10.0.0.1",
            kernel_port=8080,
            health_status=ModelServiceStatus.HEALTHY,
        )
        route_unhealthy = _make_route(
            kernel_host="10.0.0.2",
            kernel_port=8081,
            health_status=ModelServiceStatus.UNHEALTHY,
        )

        client_pool = _make_client_pool({
            "http://10.0.0.1:8080": SAMPLE_PROMETHEUS_OUTPUT,
            "http://10.0.0.2:8081": SAMPLE_PROMETHEUS_OUTPUT,
        })

        measures = await gather_prometheus_inference_measures(
            client_pool, [route_healthy, route_unhealthy]
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
