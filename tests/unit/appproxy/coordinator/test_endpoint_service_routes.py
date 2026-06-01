"""Unit tests for EndpointService.register_routes_bulk / unregister_routes_bulk.

These exercise the service-layer fan-out: the repository owns the DB
write, and the service then propagates to workers via
``CircuitManager.update_circuit_routes_bulk``. Worker propagation
failures must surface as ``success=False`` so the long-cycle sync can
converge state on the next pass.
"""

from __future__ import annotations

from typing import cast
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from ai.backend.appproxy.coordinator.repositories.endpoint import (
    EndpointRepository,
    RegisteredRouteSet,
    UnregisteredRouteSet,
)
from ai.backend.appproxy.coordinator.services.endpoint import EndpointService
from ai.backend.appproxy.coordinator.types import CircuitManager
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.types import (
    RegisterRoutesItem,
    RouteEntry,
    UnregisterRoutesItem,
)
from ai.backend.common.identifier.deployment import DeploymentID


def _route_entry() -> RouteEntry:
    return RouteEntry(
        session_id=uuid4(),
        route_id=uuid4(),
        kernel_host="10.0.0.1",
        kernel_port=8000,
    )


def _make_circuit(endpoint_id: UUID) -> MagicMock:
    circuit = MagicMock()
    circuit.endpoint_id = endpoint_id
    return circuit


class TestRegisterRoutesBulk:
    """Tests for EndpointService.register_routes_bulk."""

    async def test_empty_input_is_noop(self) -> None:
        """No items → no repo / circuit-manager calls and an empty result."""
        repo = AsyncMock(spec=EndpointRepository)
        circuit_manager = AsyncMock(spec=CircuitManager)
        service = EndpointService(
            cast(EndpointRepository, repo),
            cast(CircuitManager, circuit_manager),
        )

        result = await service.register_routes_bulk([])

        assert result == []
        repo.register_routes.assert_not_awaited()
        circuit_manager.update_circuit_routes_bulk.assert_not_awaited()

    async def test_success_path_propagates_and_reports(self) -> None:
        """Repo result is forwarded to circuit_manager and reflected in the response."""
        endpoint_id = DeploymentID(uuid4())
        new_route = _route_entry()
        circuit = _make_circuit(UUID(str(endpoint_id)))
        repo = AsyncMock(spec=EndpointRepository)
        repo.register_routes = AsyncMock(
            return_value=[
                RegisteredRouteSet(
                    deployment_id=endpoint_id,
                    success=True,
                    error=None,
                    circuit=circuit,
                    old_routes=[],
                    registered_route_ids=[new_route.route_id],
                    already_registered_route_ids=[],
                )
            ]
        )
        circuit_manager = AsyncMock(spec=CircuitManager)
        service = EndpointService(
            cast(EndpointRepository, repo),
            cast(CircuitManager, circuit_manager),
        )

        result = await service.register_routes_bulk([
            RegisterRoutesItem(deployment_id=endpoint_id, routes=[new_route])
        ])

        assert len(result) == 1
        assert result[0].success is True
        assert result[0].registered_route_ids == [new_route.route_id]
        assert result[0].already_registered_route_ids == []
        repo.register_routes.assert_awaited_once()
        circuit_manager.update_circuit_routes_bulk.assert_awaited_once()

    async def test_repo_exception_marks_every_input_failed(self) -> None:
        """A repo-level error fails the whole batch (per request) and reports each entry."""
        endpoint_id = DeploymentID(uuid4())
        repo = AsyncMock(spec=EndpointRepository)
        repo.register_routes = AsyncMock(side_effect=RuntimeError("db down"))
        circuit_manager = AsyncMock(spec=CircuitManager)
        service = EndpointService(
            cast(EndpointRepository, repo),
            cast(CircuitManager, circuit_manager),
        )

        result = await service.register_routes_bulk([
            RegisterRoutesItem(deployment_id=endpoint_id, routes=[_route_entry()])
        ])

        assert len(result) == 1
        assert result[0].success is False
        assert "db down" in (result[0].error or "")
        circuit_manager.update_circuit_routes_bulk.assert_not_awaited()

    async def test_propagation_failure_surfaces_as_failed(self) -> None:
        """Worker propagation errors flip success → False so the next sync retries."""
        endpoint_id = DeploymentID(uuid4())
        circuit = _make_circuit(UUID(str(endpoint_id)))
        repo = AsyncMock(spec=EndpointRepository)
        repo.register_routes = AsyncMock(
            return_value=[
                RegisteredRouteSet(
                    deployment_id=endpoint_id,
                    success=True,
                    error=None,
                    circuit=circuit,
                    old_routes=[],
                    registered_route_ids=[uuid4()],
                    already_registered_route_ids=[],
                )
            ]
        )
        circuit_manager = AsyncMock(spec=CircuitManager)
        circuit_manager.update_circuit_routes_bulk = AsyncMock(
            side_effect=RuntimeError("traefik unreachable")
        )
        service = EndpointService(
            cast(EndpointRepository, repo),
            cast(CircuitManager, circuit_manager),
        )

        result = await service.register_routes_bulk([
            RegisterRoutesItem(deployment_id=endpoint_id, routes=[_route_entry()])
        ])

        assert len(result) == 1
        assert result[0].success is False
        assert "traefik unreachable" in (result[0].error or "")

    async def test_partial_failure_does_not_propagate_failed_entry(self) -> None:
        """Per-entry failures from the repo are forwarded as-is and skipped by propagation."""
        good_id = DeploymentID(uuid4())
        bad_id = DeploymentID(uuid4())
        good_circuit = _make_circuit(UUID(str(good_id)))
        repo = AsyncMock(spec=EndpointRepository)
        repo.register_routes = AsyncMock(
            return_value=[
                RegisteredRouteSet(
                    deployment_id=good_id,
                    success=True,
                    error=None,
                    circuit=good_circuit,
                    old_routes=[],
                    registered_route_ids=[uuid4()],
                    already_registered_route_ids=[],
                ),
                RegisteredRouteSet(
                    deployment_id=bad_id,
                    success=False,
                    error="No circuit registered for this endpoint yet.",
                    circuit=None,
                    old_routes=[],
                    registered_route_ids=[],
                    already_registered_route_ids=[],
                ),
            ]
        )
        circuit_manager = AsyncMock(spec=CircuitManager)
        service = EndpointService(
            cast(EndpointRepository, repo),
            cast(CircuitManager, circuit_manager),
        )

        result = await service.register_routes_bulk([
            RegisterRoutesItem(deployment_id=good_id, routes=[_route_entry()]),
            RegisterRoutesItem(deployment_id=bad_id, routes=[_route_entry()]),
        ])

        # Result preserves order and per-entry status.
        assert [r.success for r in result] == [True, False]
        # Only the good circuit is fanned out.
        update_args = circuit_manager.update_circuit_routes_bulk.await_args.args[0]
        assert [item.circuit for item in update_args] == [good_circuit]


class TestUnregisterRoutesBulk:
    """Tests for EndpointService.unregister_routes_bulk."""

    async def test_empty_input_is_noop(self) -> None:
        """No items → no repo / circuit-manager calls."""
        repo = AsyncMock(spec=EndpointRepository)
        circuit_manager = AsyncMock(spec=CircuitManager)
        service = EndpointService(
            cast(EndpointRepository, repo),
            cast(CircuitManager, circuit_manager),
        )

        result = await service.unregister_routes_bulk([])

        assert result == []
        repo.unregister_routes.assert_not_awaited()
        circuit_manager.update_circuit_routes_bulk.assert_not_awaited()

    async def test_success_path_propagates_and_reports(self) -> None:
        """Repo result is forwarded to circuit_manager and reflected in the response."""
        endpoint_id = DeploymentID(uuid4())
        circuit = _make_circuit(UUID(str(endpoint_id)))
        dropped_id = uuid4()
        repo = AsyncMock(spec=EndpointRepository)
        repo.unregister_routes = AsyncMock(
            return_value=[
                UnregisteredRouteSet(
                    deployment_id=endpoint_id,
                    success=True,
                    error=None,
                    circuit=circuit,
                    old_routes=[],
                    unregistered_route_ids=[dropped_id],
                    already_absent_route_ids=[],
                )
            ]
        )
        circuit_manager = AsyncMock(spec=CircuitManager)
        service = EndpointService(
            cast(EndpointRepository, repo),
            cast(CircuitManager, circuit_manager),
        )

        result = await service.unregister_routes_bulk([
            UnregisterRoutesItem(deployment_id=endpoint_id, route_ids=[dropped_id])
        ])

        assert len(result) == 1
        assert result[0].success is True
        assert result[0].unregistered_route_ids == [dropped_id]
        repo.unregister_routes.assert_awaited_once()
        circuit_manager.update_circuit_routes_bulk.assert_awaited_once()

    async def test_repo_exception_marks_every_input_failed(self) -> None:
        """A repo-level error reports each input entry as failed."""
        endpoint_id = DeploymentID(uuid4())
        repo = AsyncMock(spec=EndpointRepository)
        repo.unregister_routes = AsyncMock(side_effect=RuntimeError("db down"))
        circuit_manager = AsyncMock(spec=CircuitManager)
        service = EndpointService(
            cast(EndpointRepository, repo),
            cast(CircuitManager, circuit_manager),
        )

        result = await service.unregister_routes_bulk([
            UnregisterRoutesItem(deployment_id=endpoint_id, route_ids=[uuid4()])
        ])

        assert len(result) == 1
        assert result[0].success is False
        assert "db down" in (result[0].error or "")
        circuit_manager.update_circuit_routes_bulk.assert_not_awaited()

    async def test_propagation_failure_surfaces_as_failed(self) -> None:
        """Worker propagation errors flip success → False so the next sync retries."""
        endpoint_id = DeploymentID(uuid4())
        circuit = _make_circuit(UUID(str(endpoint_id)))
        repo = AsyncMock(spec=EndpointRepository)
        repo.unregister_routes = AsyncMock(
            return_value=[
                UnregisteredRouteSet(
                    deployment_id=endpoint_id,
                    success=True,
                    error=None,
                    circuit=circuit,
                    old_routes=[],
                    unregistered_route_ids=[uuid4()],
                    already_absent_route_ids=[],
                )
            ]
        )
        circuit_manager = AsyncMock(spec=CircuitManager)
        circuit_manager.update_circuit_routes_bulk = AsyncMock(
            side_effect=RuntimeError("traefik unreachable")
        )
        service = EndpointService(
            cast(EndpointRepository, repo),
            cast(CircuitManager, circuit_manager),
        )

        result = await service.unregister_routes_bulk([
            UnregisterRoutesItem(deployment_id=endpoint_id, route_ids=[uuid4()])
        ])

        assert len(result) == 1
        assert result[0].success is False
        assert "traefik unreachable" in (result[0].error or "")


# Avoid unused-import warning for pytest when the file is loaded but no
# fixture is referenced; keeps mypy/ruff/pants check quiet without
# adding suppression directives.
_ = pytest
