"""
Regression tests for circuit route_info synchronization on route updates.

The bug: when `update_circuit_route_info()` was called (e.g., during scale-in),
only the backend was updated but `circuit.route_info` remained stale.
This caused the metric collector to try scraping terminated routes,
ultimately breaking the auto-scaling feedback loop.

The fix: `self.circuits[key].route_info = new_routes` is now called
before updating the backend, keeping the circuit's route_info in sync.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
import pytest_mock

from ai.backend.appproxy.common.types import (
    AppMode,
    FrontendMode,
    ProxyProtocol,
    RouteInfo,
)
from ai.backend.appproxy.worker.metrics import gather_inference_measures
from ai.backend.appproxy.worker.proxy.frontend.http.port import PortFrontend
from ai.backend.appproxy.worker.types import (
    Circuit,
    InferenceAppInfo,
    PortFrontendInfo,
)
from ai.backend.common.types import ModelServiceStatus, RuntimeVariant

SAMPLE_PROMETHEUS_OUTPUT = """\
# HELP vllm:num_requests_running Number of requests running
# TYPE vllm:num_requests_running gauge
vllm:num_requests_running 3
"""


def _make_route(
    route_id: UUID | None = None,
    session_id: UUID | None = None,
    kernel_host: str = "10.0.0.1",
    kernel_port: int = 8080,
) -> RouteInfo:
    return RouteInfo(
        route_id=route_id or uuid4(),
        session_id=session_id or uuid4(),
        session_name=None,
        kernel_host=kernel_host,
        kernel_port=kernel_port,
        protocol=ProxyProtocol.HTTP,
        traffic_ratio=1.0,
        health_status=ModelServiceStatus.HEALTHY,
        last_health_check=None,
        consecutive_failures=0,
    )


def _make_circuit(routes: list[RouteInfo], port: int = 10200) -> Circuit:
    return Circuit(
        id=uuid4(),
        app="vllm",
        protocol=ProxyProtocol.HTTP,
        worker=UUID("00000000-0000-0000-0000-000000000000"),
        app_mode=AppMode.INFERENCE,
        frontend_mode=FrontendMode.PORT,
        frontend=PortFrontendInfo(port),
        port=port,
        app_info=InferenceAppInfo(
            endpoint_id=uuid4(),
            runtime_variant=RuntimeVariant.VLLM,
        ),
        subdomain=None,
        runtime_variant=RuntimeVariant.VLLM,
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


class TestUpdateCircuitRouteInfo:
    """Regression tests for circuit.route_info synchronization."""

    FRONTEND_PORT = 10200

    @pytest.fixture
    def port_frontend(self, mocker: pytest_mock.MockerFixture) -> PortFrontend:
        frontend = PortFrontend(root_context=mocker.MagicMock())
        frontend.circuits = {}
        frontend.backends = {}
        return frontend

    @pytest.fixture
    def route_a(self) -> RouteInfo:
        return _make_route(kernel_host="10.0.0.1", kernel_port=8080)

    @pytest.fixture
    def route_b(self) -> RouteInfo:
        return _make_route(kernel_host="10.0.0.2", kernel_port=8081)

    async def test_route_info_synced_on_update(
        self,
        mocker: pytest_mock.MockerFixture,
        port_frontend: PortFrontend,
        route_a: RouteInfo,
        route_b: RouteInfo,
    ) -> None:
        """Regression: circuit.route_info must reflect new routes after update.

        Before the fix, only the backend was updated while circuit.route_info
        kept stale routes, causing the metric collector to target terminated
        endpoints.
        """
        circuit = _make_circuit([route_a, route_b], port=self.FRONTEND_PORT)

        port_frontend.circuits[self.FRONTEND_PORT] = circuit
        port_frontend.backends[self.FRONTEND_PORT] = mocker.MagicMock()
        mocker.patch.object(port_frontend, "update_backend", new_callable=AsyncMock)

        # Scale-in: remove route_b
        new_routes = [route_a]
        await port_frontend.update_circuit_route_info(circuit, new_routes)

        assert port_frontend.circuits[self.FRONTEND_PORT].route_info == new_routes
        assert len(port_frontend.circuits[self.FRONTEND_PORT].route_info) == 1
        assert (
            port_frontend.circuits[self.FRONTEND_PORT].route_info[0].session_id
            == route_a.session_id
        )

    async def test_route_info_synced_before_backend_update(
        self,
        mocker: pytest_mock.MockerFixture,
        port_frontend: PortFrontend,
        route_a: RouteInfo,
        route_b: RouteInfo,
    ) -> None:
        """Verify route_info is updated before backend update is called."""
        circuit = _make_circuit([route_a], port=self.FRONTEND_PORT)

        port_frontend.circuits[self.FRONTEND_PORT] = circuit
        port_frontend.backends[self.FRONTEND_PORT] = mocker.MagicMock()

        captured_route_info: list[list[RouteInfo]] = []

        async def capture_update_backend(backend: object, routes: list[RouteInfo]) -> object:
            captured_route_info.append(list(port_frontend.circuits[self.FRONTEND_PORT].route_info))
            return backend

        mocker.patch.object(port_frontend, "update_backend", side_effect=capture_update_backend)

        new_routes = [route_a, route_b]
        await port_frontend.update_circuit_route_info(circuit, new_routes)

        # At the time update_backend was called, route_info should already be synced
        assert len(captured_route_info) == 1
        assert captured_route_info[0] == new_routes

    async def test_route_info_empty_after_full_scale_in(
        self,
        mocker: pytest_mock.MockerFixture,
        port_frontend: PortFrontend,
        route_a: RouteInfo,
    ) -> None:
        """When all routes are removed, circuit.route_info should be empty."""
        circuit = _make_circuit([route_a], port=self.FRONTEND_PORT)

        port_frontend.circuits[self.FRONTEND_PORT] = circuit
        port_frontend.backends[self.FRONTEND_PORT] = mocker.MagicMock()
        mocker.patch.object(port_frontend, "update_backend", new_callable=AsyncMock)

        await port_frontend.update_circuit_route_info(circuit, [])

        assert port_frontend.circuits[self.FRONTEND_PORT].route_info == []

    async def test_inactive_circuit_update_is_noop(
        self,
        mocker: pytest_mock.MockerFixture,
        port_frontend: PortFrontend,
        route_a: RouteInfo,
    ) -> None:
        """Updating an unregistered circuit should log warning and do nothing."""
        circuit = _make_circuit([route_a], port=self.FRONTEND_PORT)

        mock_update_backend = mocker.patch.object(
            port_frontend, "update_backend", new_callable=AsyncMock
        )

        await port_frontend.update_circuit_route_info(circuit, [])

        mock_update_backend.assert_not_called()

    async def test_metric_collection_uses_updated_route_info(
        self,
        mocker: pytest_mock.MockerFixture,
        port_frontend: PortFrontend,
        route_a: RouteInfo,
        route_b: RouteInfo,
    ) -> None:
        """Regression: the full bug chain from stale route_info to metric failure.

        This test verifies the end-to-end scenario:
        1. Scale-in removes route_b via update_circuit_route_info
        2. Metric collector (gather_inference_measures) reads circuit.route_info
        3. Only route_a's endpoint is accessed; route_b's is never contacted

        Before the fix, circuit.route_info stayed [route_a, route_b] after
        scale-in, so the metric collector would try to scrape the terminated
        route_b's /metrics endpoint, causing collection failure.
        """
        circuit = _make_circuit([route_a, route_b], port=self.FRONTEND_PORT)

        port_frontend.circuits[self.FRONTEND_PORT] = circuit
        port_frontend.backends[self.FRONTEND_PORT] = mocker.MagicMock()
        mocker.patch.object(port_frontend, "update_backend", new_callable=AsyncMock)

        # Step 1: Scale-in removes route_b
        await port_frontend.update_circuit_route_info(circuit, [route_a])

        # Step 2: Metric collector runs — track which endpoints are accessed
        accessed_endpoints: list[str] = []

        def mock_load_client_session(client_key: Any) -> MagicMock:
            accessed_endpoints.append(client_key.endpoint)
            session = MagicMock()

            @asynccontextmanager
            async def mock_get(path: str) -> Any:
                resp = MagicMock()
                resp.raise_for_status = MagicMock()
                resp.text = AsyncMock(return_value=SAMPLE_PROMETHEUS_OUTPUT)
                yield resp

            session.get = mock_get
            return session

        client_pool = MagicMock()
        client_pool.load_client_session = mock_load_client_session

        updated_circuit = port_frontend.circuits[self.FRONTEND_PORT]
        measures = await gather_inference_measures(client_pool, updated_circuit)

        # Step 3: Verify only route_a was accessed, route_b was NOT
        route_a_endpoint = f"http://{route_a.current_kernel_host}:{route_a.kernel_port}"
        route_b_endpoint = f"http://{route_b.current_kernel_host}:{route_b.kernel_port}"
        assert route_a_endpoint in accessed_endpoints
        assert route_b_endpoint not in accessed_endpoints
        assert measures is not None
        assert len(measures) > 0
