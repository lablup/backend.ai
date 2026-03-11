"""
Regression tests for circuit route_info synchronization on route updates.

The bug: when `update_circuit_route_info()` was called (e.g., during scale-in),
only the backend was updated but `circuit.route_info` remained stale.
This caused the metric collector to try scraping terminated routes,
ultimately breaking the auto-scaling feedback loop.

The fix: `self.circuits[key].route_info = new_routes` is now called
after updating the backend, keeping the circuit's route_info in sync.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any, NamedTuple
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


class TwoReplicaScenario(NamedTuple):
    """A circuit with two healthy replicas registered in the frontend."""

    circuit: Circuit
    healthy_route: RouteInfo
    scaled_in_route: RouteInfo


class SingleReplicaScenario(NamedTuple):
    """A circuit with a single healthy replica."""

    circuit: Circuit
    route: RouteInfo


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
    def two_replica_scenario(self) -> TwoReplicaScenario:
        """Two-replica circuit: healthy_route stays, scaled_in_route gets removed on scale-in."""
        healthy_route = _make_route(kernel_host="10.0.0.1", kernel_port=8080)
        scaled_in_route = _make_route(kernel_host="10.0.0.2", kernel_port=8081)
        circuit = _make_circuit([healthy_route, scaled_in_route], port=self.FRONTEND_PORT)
        return TwoReplicaScenario(circuit, healthy_route, scaled_in_route)

    @pytest.fixture
    def single_replica_scenario(self) -> SingleReplicaScenario:
        """Single-replica circuit for full scale-in and inactive circuit tests."""
        route = _make_route(kernel_host="10.0.0.1", kernel_port=8080)
        circuit = _make_circuit([route], port=self.FRONTEND_PORT)
        return SingleReplicaScenario(circuit, route)

    @pytest.fixture
    def registered_two_replica_frontend(
        self,
        mocker: pytest_mock.MockerFixture,
        port_frontend: PortFrontend,
        two_replica_scenario: TwoReplicaScenario,
    ) -> tuple[PortFrontend, TwoReplicaScenario]:
        """Frontend with the two-replica circuit already registered."""
        port_frontend.circuits[self.FRONTEND_PORT] = two_replica_scenario.circuit
        port_frontend.backends[self.FRONTEND_PORT] = mocker.MagicMock()
        mocker.patch.object(port_frontend, "update_backend", new_callable=AsyncMock)
        return port_frontend, two_replica_scenario

    async def test_route_info_synced_on_update(
        self,
        registered_two_replica_frontend: tuple[PortFrontend, TwoReplicaScenario],
    ) -> None:
        """Regression: circuit.route_info must reflect new routes after update.

        Before the fix, only the backend was updated while circuit.route_info
        kept stale routes, causing the metric collector to target terminated
        endpoints.
        """
        frontend, scenario = registered_two_replica_frontend

        # Scale-in: remove scaled_in_route
        new_routes = [scenario.healthy_route]
        await frontend.update_circuit_route_info(scenario.circuit, new_routes)

        assert frontend.circuits[self.FRONTEND_PORT].route_info == new_routes
        assert len(frontend.circuits[self.FRONTEND_PORT].route_info) == 1
        assert (
            frontend.circuits[self.FRONTEND_PORT].route_info[0].session_id
            == scenario.healthy_route.session_id
        )

    async def test_route_info_synced_after_backend_update(
        self,
        mocker: pytest_mock.MockerFixture,
        port_frontend: PortFrontend,
        two_replica_scenario: TwoReplicaScenario,
    ) -> None:
        """Verify route_info is updated only after backend update succeeds.

        Circuit starts with [healthy_route, scaled_in_route].
        Scale-in removes scaled_in_route -> new_routes = [healthy_route].
        During update_backend, route_info should still be the old 2-route list.
        """
        scenario = two_replica_scenario
        initial_routes = list(scenario.circuit.route_info)
        port_frontend.circuits[self.FRONTEND_PORT] = scenario.circuit
        port_frontend.backends[self.FRONTEND_PORT] = mocker.MagicMock()

        captured_route_info: list[list[RouteInfo]] = []

        async def capture_update_backend(backend: object, routes: list[RouteInfo]) -> object:
            # Capture route_info at the moment update_backend is called
            captured_route_info.append(list(port_frontend.circuits[self.FRONTEND_PORT].route_info))
            return backend

        mocker.patch.object(port_frontend, "update_backend", side_effect=capture_update_backend)

        # Scale-in: remove scaled_in_route
        new_routes = [scenario.healthy_route]
        await port_frontend.update_circuit_route_info(scenario.circuit, new_routes)

        # At the time update_backend was called, route_info should still be the old 2-route list
        assert len(captured_route_info) == 1
        assert captured_route_info[0] == initial_routes
        assert len(captured_route_info[0]) == 2
        # After the call completes, route_info should be updated to new_routes
        assert port_frontend.circuits[self.FRONTEND_PORT].route_info == new_routes
        assert len(port_frontend.circuits[self.FRONTEND_PORT].route_info) == 1

    async def test_route_info_unchanged_on_backend_update_failure(
        self,
        mocker: pytest_mock.MockerFixture,
        port_frontend: PortFrontend,
        two_replica_scenario: TwoReplicaScenario,
    ) -> None:
        """If update_backend raises, route_info must remain unchanged.

        This ensures consistency: the backend keeps the old routes, and
        circuit.route_info matches that state.
        """
        scenario = two_replica_scenario
        initial_routes = list(scenario.circuit.route_info)
        port_frontend.circuits[self.FRONTEND_PORT] = scenario.circuit
        port_frontend.backends[self.FRONTEND_PORT] = mocker.MagicMock()

        mocker.patch.object(
            port_frontend,
            "update_backend",
            side_effect=RuntimeError("backend update failed"),
        )

        with pytest.raises(RuntimeError, match="backend update failed"):
            await port_frontend.update_circuit_route_info(
                scenario.circuit, [scenario.healthy_route]
            )

        # route_info must still be the original 2-route list
        assert port_frontend.circuits[self.FRONTEND_PORT].route_info == initial_routes
        assert len(port_frontend.circuits[self.FRONTEND_PORT].route_info) == 2

    async def test_route_info_empty_after_full_scale_in(
        self,
        mocker: pytest_mock.MockerFixture,
        port_frontend: PortFrontend,
        single_replica_scenario: SingleReplicaScenario,
    ) -> None:
        """When all routes are removed, circuit.route_info should be empty."""
        scenario = single_replica_scenario
        port_frontend.circuits[self.FRONTEND_PORT] = scenario.circuit
        port_frontend.backends[self.FRONTEND_PORT] = mocker.MagicMock()
        mocker.patch.object(port_frontend, "update_backend", new_callable=AsyncMock)

        await port_frontend.update_circuit_route_info(scenario.circuit, [])

        assert port_frontend.circuits[self.FRONTEND_PORT].route_info == []

    async def test_inactive_circuit_update_is_noop(
        self,
        mocker: pytest_mock.MockerFixture,
        port_frontend: PortFrontend,
        single_replica_scenario: SingleReplicaScenario,
    ) -> None:
        """Updating an unregistered circuit should log warning and do nothing."""
        mock_update_backend = mocker.patch.object(
            port_frontend, "update_backend", new_callable=AsyncMock
        )

        await port_frontend.update_circuit_route_info(single_replica_scenario.circuit, [])

        mock_update_backend.assert_not_called()

    async def test_metric_collection_uses_updated_route_info(
        self,
        registered_two_replica_frontend: tuple[PortFrontend, TwoReplicaScenario],
    ) -> None:
        """Regression: the full bug chain from stale route_info to metric failure.

        This test verifies the end-to-end scenario:
        1. Scale-in removes scaled_in_route via update_circuit_route_info
        2. Metric collector (gather_inference_measures) reads circuit.route_info
        3. Only healthy_route's endpoint is accessed; scaled_in_route's is never contacted

        Before the fix, circuit.route_info stayed [healthy, scaled_in] after
        scale-in, so the metric collector would try to scrape the terminated
        scaled_in_route's /metrics endpoint, causing collection failure.
        """
        frontend, scenario = registered_two_replica_frontend

        # Step 1: Scale-in removes scaled_in_route
        await frontend.update_circuit_route_info(scenario.circuit, [scenario.healthy_route])

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

        updated_circuit = frontend.circuits[self.FRONTEND_PORT]
        measures = await gather_inference_measures(client_pool, updated_circuit)

        # Step 3: Verify only healthy_route was accessed, scaled_in_route was NOT
        healthy_endpoint = (
            f"http://{scenario.healthy_route.current_kernel_host}"
            f":{scenario.healthy_route.kernel_port}"
        )
        scaled_in_endpoint = (
            f"http://{scenario.scaled_in_route.current_kernel_host}"
            f":{scenario.scaled_in_route.kernel_port}"
        )
        assert healthy_endpoint in accessed_endpoints
        assert scaled_in_endpoint not in accessed_endpoints
        assert measures is not None
        assert len(measures) > 0
