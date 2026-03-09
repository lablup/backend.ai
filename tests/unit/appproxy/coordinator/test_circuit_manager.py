"""
Regression tests for diff-based Traefik route updates.

The old implementation deleted ALL routes and the weighted service before
re-creating them, causing endpoint downtime during the gap.
These tests verify that routes which remain unchanged are never deleted.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, Mock, PropertyMock
from uuid import UUID, uuid4

import pytest

from ai.backend.appproxy.common.etcd import TraefikEtcd
from ai.backend.appproxy.common.types import ProxyProtocol, RouteInfo
from ai.backend.appproxy.coordinator.types import CircuitManager


@pytest.fixture
def mock_traefik_etcd() -> AsyncMock:
    etcd = AsyncMock(spec=TraefikEtcd)
    etcd.put_prefix = AsyncMock()
    etcd.delete_prefix = AsyncMock()
    return etcd


@pytest.fixture
def mock_local_config() -> Mock:
    config = Mock()
    config.proxy_coordinator.enable_traefik = True
    return config


@pytest.fixture
def mock_circuit_manager(
    mock_traefik_etcd: AsyncMock,
    mock_local_config: Mock,
) -> CircuitManager:
    return CircuitManager(
        event_dispatcher=Mock(),
        event_producer=Mock(),
        traefik_etcd=mock_traefik_etcd,
        local_config=mock_local_config,
    )


def make_route(
    session_id: UUID | None = None,
    kernel_host: str = "10.0.0.1",
    kernel_port: int = 8080,
    protocol: ProxyProtocol = ProxyProtocol.HTTP,
    traffic_ratio: float = 1.0,
) -> RouteInfo:
    return RouteInfo(
        route_id=None,
        session_id=session_id or uuid4(),
        session_name=None,
        kernel_host=kernel_host,
        kernel_port=kernel_port,
        protocol=protocol,
        traffic_ratio=traffic_ratio,
        health_status=None,
        last_health_check=None,
        consecutive_failures=0,
    )


def make_circuit(
    circuit_id: UUID,
    healthy_routes: list[RouteInfo],
    protocol: ProxyProtocol = ProxyProtocol.HTTP,
    worker_authority: str = "worker1.example.com:10200",
) -> Mock:
    circuit = Mock()
    circuit.id = circuit_id
    circuit.protocol = protocol
    type(circuit).healthy_routes = PropertyMock(return_value=healthy_routes)

    worker_row = Mock()
    worker_row.authority = worker_authority
    circuit.worker_row = worker_row

    # Build traefik_services dict matching the real Circuit.traefik_services property
    if not healthy_routes:
        circuit.traefik_services = {}
    else:
        services: dict[str, Any] = {
            f"bai_service_{circuit_id}": {
                "weighted": {
                    "services": [
                        {
                            "name": f"bai_session_{r.session_id}_{circuit_id}",
                            "weight": int(r.traffic_ratio),
                        }
                        for r in healthy_routes
                    ]
                }
            },
        }
        for r in healthy_routes:
            services[f"bai_session_{r.session_id}_{circuit_id}"] = {
                "loadBalancer": {
                    "servers": [{"url": f"http://{r.current_kernel_host}:{r.kernel_port}/"}],
                }
            }
        circuit.traefik_services = services

    return circuit


class TestUpdateTraefikCircuitRoutes:
    """Regression tests for diff-based Traefik route updates.

    The old implementation deleted ALL routes and the weighted service before
    re-creating them. This caused a window where no routes existed, resulting
    in endpoint downtime. The diff-based approach only deletes removed routes
    and adds new ones, leaving unchanged routes intact.
    """

    async def test_unchanged_routes_are_not_deleted(
        self,
        mock_circuit_manager: CircuitManager,
        mock_traefik_etcd: AsyncMock,
    ) -> None:
        """When routes don't change (A->A), no deletes should occur.

        Regression: old code would delete route_a then re-create it,
        causing a brief downtime window.
        """
        session_a = uuid4()
        circuit_id = uuid4()
        route_a = make_route(session_id=session_a)
        old_routes = [route_a]

        circuit = make_circuit(circuit_id=circuit_id, healthy_routes=[route_a])

        await mock_circuit_manager.update_traefik_circuit_routes(circuit, old_routes)

        mock_traefik_etcd.delete_prefix.assert_not_called()

        # put_prefix should be called once with only the weighted service
        mock_traefik_etcd.put_prefix.assert_called_once()
        put_args = mock_traefik_etcd.put_prefix.call_args
        prefix = put_args[0][0]
        services_dict = put_args[0][1]

        assert prefix == f"worker_{circuit.worker_row.authority}/http/services"
        assert f"bai_service_{circuit_id}" in services_dict
        assert f"bai_session_{session_a}_{circuit_id}" not in services_dict

    async def test_added_route_does_not_delete_existing(
        self,
        mock_circuit_manager: CircuitManager,
        mock_traefik_etcd: AsyncMock,
    ) -> None:
        """When a route is added (A->A,B), existing route A must not be deleted.

        Regression: old code would delete route_a before re-creating both A and B.
        """
        session_a = uuid4()
        session_b = uuid4()
        circuit_id = uuid4()
        route_a = make_route(session_id=session_a)
        route_b = make_route(session_id=session_b, kernel_host="10.0.0.2", kernel_port=8081)
        old_routes = [route_a]

        circuit = make_circuit(circuit_id=circuit_id, healthy_routes=[route_a, route_b])

        await mock_circuit_manager.update_traefik_circuit_routes(circuit, old_routes)

        mock_traefik_etcd.delete_prefix.assert_not_called()

        mock_traefik_etcd.put_prefix.assert_called_once()
        put_args = mock_traefik_etcd.put_prefix.call_args
        services_dict = put_args[0][1]

        # Weighted service should always be updated
        assert f"bai_service_{circuit_id}" in services_dict
        # Only the newly added route_b backend should be in services_to_put
        assert f"bai_session_{session_b}_{circuit_id}" in services_dict
        # Existing route_a backend should NOT be re-put
        assert f"bai_session_{session_a}_{circuit_id}" not in services_dict

    async def test_removed_route_only_deletes_removed(
        self,
        mock_circuit_manager: CircuitManager,
        mock_traefik_etcd: AsyncMock,
    ) -> None:
        """When a route is removed (A,B->A), only route B should be deleted.

        Regression: old code would delete both route_a and route_b.
        """
        session_a = uuid4()
        session_b = uuid4()
        circuit_id = uuid4()
        route_a = make_route(session_id=session_a)
        route_b = make_route(session_id=session_b, kernel_host="10.0.0.2", kernel_port=8081)
        old_routes = [route_a, route_b]

        circuit = make_circuit(circuit_id=circuit_id, healthy_routes=[route_a])

        await mock_circuit_manager.update_traefik_circuit_routes(circuit, old_routes)

        # Only route_b should be deleted
        expected_delete_prefix = (
            f"worker_{circuit.worker_row.authority}/http"
            f"/services/bai_session_{session_b}_{circuit_id}"
        )
        mock_traefik_etcd.delete_prefix.assert_called_once_with(expected_delete_prefix)

        # Route_a must NOT be deleted
        for delete_call in mock_traefik_etcd.delete_prefix.call_args_list:
            assert str(session_a) not in str(delete_call)

        # put_prefix should update weighted service with no added backends
        mock_traefik_etcd.put_prefix.assert_called_once()
        put_args = mock_traefik_etcd.put_prefix.call_args
        services_dict = put_args[0][1]
        assert f"bai_service_{circuit_id}" in services_dict
        assert f"bai_session_{session_a}_{circuit_id}" not in services_dict
        assert f"bai_session_{session_b}_{circuit_id}" not in services_dict

    async def test_swapped_route_deletes_old_adds_new(
        self,
        mock_circuit_manager: CircuitManager,
        mock_traefik_etcd: AsyncMock,
    ) -> None:
        """When routes are swapped (A->B), A should be deleted and B added.

        This verifies both deletion and addition happen correctly in the
        diff-based approach.
        """
        session_a = uuid4()
        session_b = uuid4()
        circuit_id = uuid4()
        route_a = make_route(session_id=session_a)
        route_b = make_route(session_id=session_b, kernel_host="10.0.0.2", kernel_port=8081)
        old_routes = [route_a]

        circuit = make_circuit(circuit_id=circuit_id, healthy_routes=[route_b])

        await mock_circuit_manager.update_traefik_circuit_routes(circuit, old_routes)

        # Route_a should be deleted
        expected_delete_prefix = (
            f"worker_{circuit.worker_row.authority}/http"
            f"/services/bai_session_{session_a}_{circuit_id}"
        )
        mock_traefik_etcd.delete_prefix.assert_called_once_with(expected_delete_prefix)

        # Route_b must NOT be deleted
        for delete_call in mock_traefik_etcd.delete_prefix.call_args_list:
            assert str(session_b) not in str(delete_call)

        # put_prefix should include weighted service + route_b backend
        mock_traefik_etcd.put_prefix.assert_called_once()
        put_args = mock_traefik_etcd.put_prefix.call_args
        services_dict = put_args[0][1]
        assert f"bai_service_{circuit_id}" in services_dict
        assert f"bai_session_{session_b}_{circuit_id}" in services_dict
