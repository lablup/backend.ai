"""
Tests for Custom inference runtime variant metrics collection.

Verifies that RuntimeVariant.CUSTOM:
- Returns all metrics without prefix filtering (same as HUGGINGFACE_TGI)
- Handles multiple replicas correctly
- Returns a list (not None) so metrics are collected

Contrast with NIM/CMD which fall through to the catch-all case and return None.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import pytest

from ai.backend.appproxy.common.types import (
    AppMode,
    FrontendMode,
    ProxyProtocol,
    RouteInfo,
)
from ai.backend.appproxy.worker.metrics import gather_inference_measures
from ai.backend.appproxy.worker.types import (
    Circuit,
    InferenceAppInfo,
    Measurement,
    PortFrontendInfo,
)
from ai.backend.common.types import ModelServiceStatus, RuntimeVariant

# Sample Prometheus output that intentionally mixes multiple prefixes
# to verify that CUSTOM variant returns ALL metrics without any filtering.
SAMPLE_CUSTOM_METRICS = """\
# HELP custom_metric_a A custom metric
# TYPE custom_metric_a gauge
custom_metric_a 42
# HELP vllm:num_requests_running vLLM metric included in custom endpoint
# TYPE vllm:num_requests_running gauge
vllm:num_requests_running 5
# HELP app_requests_total Total requests processed
# TYPE app_requests_total gauge
app_requests_total 100
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


def _make_custom_circuit(routes: list[RouteInfo], port: int = 10300) -> Circuit:
    return Circuit(
        id=uuid4(),
        app="custom-model",
        protocol=ProxyProtocol.HTTP,
        worker=UUID("00000000-0000-0000-0000-000000000000"),
        app_mode=AppMode.INFERENCE,
        frontend_mode=FrontendMode.PORT,
        frontend=PortFrontendInfo(port),
        port=port,
        app_info=InferenceAppInfo(
            endpoint_id=uuid4(),
            runtime_variant=RuntimeVariant.CUSTOM,
        ),
        subdomain=None,
        runtime_variant=RuntimeVariant.CUSTOM,
        envs={},
        arguments=None,
        open_to_public=False,
        allowed_client_ips=None,
        user_id=uuid4(),
        access_key="TESTKEY",
        endpoint_id=None,
        route_info=routes,
        session_ids=[r.session_id for r in routes],
        created_at=datetime(2024, 7, 16, 5, 45, 45, tzinfo=UTC),
        updated_at=datetime(2024, 7, 16, 5, 45, 45, tzinfo=UTC),
    )


def _make_unsupported_circuit(
    variant: RuntimeVariant, routes: list[RouteInfo], port: int = 10301
) -> Circuit:
    return Circuit(
        id=uuid4(),
        app="model",
        protocol=ProxyProtocol.HTTP,
        worker=UUID("00000000-0000-0000-0000-000000000000"),
        app_mode=AppMode.INFERENCE,
        frontend_mode=FrontendMode.PORT,
        frontend=PortFrontendInfo(port),
        port=port,
        app_info=InferenceAppInfo(
            endpoint_id=uuid4(),
            runtime_variant=variant,
        ),
        subdomain=None,
        runtime_variant=variant,
        envs={},
        arguments=None,
        open_to_public=False,
        allowed_client_ips=None,
        user_id=uuid4(),
        access_key="TESTKEY",
        endpoint_id=None,
        route_info=routes,
        session_ids=[r.session_id for r in routes],
        created_at=datetime(2024, 7, 16, 5, 45, 45, tzinfo=UTC),
        updated_at=datetime(2024, 7, 16, 5, 45, 45, tzinfo=UTC),
    )


class TestCustomRuntimeVariantMetrics:
    """Tests for RuntimeVariant.CUSTOM metrics collection."""

    async def test_custom_variant_collects_all_metrics_without_filtering(
        self, mock_metrics_client_pool: Any
    ) -> None:
        """CUSTOM variant must return all metrics regardless of prefix."""
        route = _make_route(kernel_host="10.0.0.1", kernel_port=8080)
        circuit = _make_custom_circuit([route])

        responses = {
            f"http://{route.current_kernel_host}:{route.kernel_port}": SAMPLE_CUSTOM_METRICS
        }

        async with mock_metrics_client_pool(responses) as (client_pool, _):
            measures = await gather_inference_measures(client_pool, circuit)

        assert measures is not None, "CUSTOM variant must return a list, not None"
        assert len(measures) > 0, "CUSTOM variant must return at least one measure"

        metric_keys = {m.key for m in measures}
        # All three metrics from SAMPLE_CUSTOM_METRICS should be present — no prefix filtering
        assert "custom_metric_a" in metric_keys
        assert "vllm:num_requests_running" in metric_keys
        assert "app_requests_total" in metric_keys

    async def test_custom_variant_handles_multiple_replicas(
        self, mock_metrics_client_pool: Any
    ) -> None:
        """CUSTOM variant must aggregate metrics across multiple replicas."""
        route1 = _make_route(kernel_host="10.0.0.1", kernel_port=8080)
        route2 = _make_route(kernel_host="10.0.0.2", kernel_port=8081)
        circuit = _make_custom_circuit([route1, route2])

        REPLICA_METRICS = """\
# HELP custom_metric_a A custom metric
# TYPE custom_metric_a gauge
custom_metric_a 10
"""
        responses = {
            f"http://{route1.current_kernel_host}:{route1.kernel_port}": REPLICA_METRICS,
            f"http://{route2.current_kernel_host}:{route2.kernel_port}": REPLICA_METRICS,
        }

        async with mock_metrics_client_pool(responses) as (client_pool, _):
            measures = await gather_inference_measures(client_pool, circuit)

        assert measures is not None
        custom_a_measures = [m for m in measures if m.key == "custom_metric_a"]
        assert len(custom_a_measures) == 1

        measure = custom_a_measures[0]
        # per_app should aggregate both replicas: 10 + 10 = 20
        assert isinstance(measure.per_app, Measurement)
        assert measure.per_app.value == Decimal(20)
        # per_replica should have one entry per route
        assert len(measure.per_replica) == 2

    async def test_custom_variant_returns_empty_list_when_all_routes_fail(
        self, mock_metrics_client_pool: Any
    ) -> None:
        """CUSTOM variant returns empty list (not None) when all routes are unreachable."""
        route = _make_route(kernel_host="10.0.0.1", kernel_port=8080)
        circuit = _make_custom_circuit([route])

        responses = {
            f"http://{route.current_kernel_host}:{route.kernel_port}": ConnectionError(
                "Connection refused"
            )
        }

        async with mock_metrics_client_pool(responses) as (client_pool, _):
            measures = await gather_inference_measures(client_pool, circuit)

        # gather_inference_measures returns the result of gather_prometheus_inference_measures,
        # which returns an empty list on failure — not None.
        assert measures is not None
        assert measures == []

    @pytest.mark.parametrize(
        "variant",
        [
            pytest.param(RuntimeVariant.NIM, id="nim"),
            pytest.param(RuntimeVariant.CMD, id="cmd"),
        ],
    )
    async def test_unsupported_variants_return_none(
        self, variant: RuntimeVariant, mock_metrics_client_pool: Any
    ) -> None:
        """NIM and CMD variants must still return None (unchanged behavior)."""
        route = _make_route()
        circuit = _make_unsupported_circuit(variant, [route])

        responses = {
            f"http://{route.current_kernel_host}:{route.kernel_port}": SAMPLE_CUSTOM_METRICS
        }

        async with mock_metrics_client_pool(responses) as (client_pool, _):
            measures = await gather_inference_measures(client_pool, circuit)

        assert measures is None, f"{variant} must return None (unsupported variant)"
