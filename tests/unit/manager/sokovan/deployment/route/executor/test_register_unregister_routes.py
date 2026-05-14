"""Unit tests for RouteExecutor.register_routes_now / unregister_routes_now.

These cover the synchronous push channel that bypasses the long-cycle
``AppProxySyncRouteHandler``: HealthCheckRouteHandler invokes
``register_routes_now`` on first-time HEALTHY transition and
TerminatingRouteHandler invokes ``unregister_routes_now`` before
destroying kernels.

Test scenarios:
- RR-REG-001: Empty input is a no-op (no HTTP).
- RR-REG-002: Routes for one endpoint emit a single bulk_register call.
- RR-REG-003: Routes missing replica info are reported as errors.
- RR-REG-004: Per-endpoint failure isolated from other successes.
- RR-UNREG-001: Empty input is a no-op (no HTTP).
- RR-UNREG-002: Routes for one endpoint emit a single bulk_unregister call.
- RR-UNREG-003: Per-endpoint failure isolated from other successes.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

from dateutil.tz import tzutc

from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.response import (
    BulkRegisterRoutesResponse,
    BulkUnregisterRoutesResponse,
)
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.types import (
    RegisteredRoutesItem,
    UnregisteredRoutesItem,
)
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.replica import ReplicaID
from ai.backend.common.types import SessionId
from ai.backend.manager.data.deployment.types import (
    RouteHealthStatus,
    RouteStatus,
    RouteTrafficStatus,
)
from ai.backend.manager.data.resource.types import ScalingGroupProxyTarget
from ai.backend.manager.repositories.deployment.types import RouteData
from ai.backend.manager.sokovan.deployment.route.executor import RouteExecutor


def _route_with_replica(
    endpoint_id: DeploymentID,
    *,
    replica_host: str | None = "10.0.0.1",
    replica_port: int | None = 8000,
    session_id: SessionId | None = None,
) -> RouteData:
    return RouteData(
        route_id=ReplicaID(uuid4()),
        deployment_id=endpoint_id,
        session_id=session_id if session_id is not None else SessionId(uuid4()),
        status=RouteStatus.RUNNING,
        health_status=RouteHealthStatus.HEALTHY,
        traffic_ratio=1.0,
        revision_id=DeploymentRevisionID(uuid4()),
        traffic_status=RouteTrafficStatus.ACTIVE,
        replica_host=replica_host,
        replica_port=replica_port,
        created_at=datetime.now(tzutc()),
    )


def _make_deployment_mock(deployment_id: UUID, resource_group: str) -> MagicMock:
    deployment = MagicMock()
    deployment.id = deployment_id
    deployment.metadata.resource_group = resource_group
    return deployment


def _wire_proxy_target(
    mock_deployment_repo: AsyncMock,
    endpoint_ids: list[DeploymentID],
    *,
    resource_group: str = "default",
    addr: str = "http://appproxy:5000",
    token: str = "test-token",
) -> None:
    deployments = [_make_deployment_mock(UUID(str(eid)), resource_group) for eid in endpoint_ids]
    mock_deployment_repo.get_deployments_by_ids.return_value = deployments
    mock_deployment_repo.fetch_scaling_group_proxy_targets.return_value = {
        resource_group: ScalingGroupProxyTarget(addr=addr, api_token=token),
    }


class TestRegisterRoutesNow:
    """Tests for register_routes_now (synchronous bulk register)."""

    async def test_empty_routes_is_noop(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_appproxy_client_pool: MagicMock,
    ) -> None:
        """RR-REG-001: Empty input is a no-op."""
        result = await route_executor.register_routes_now([])

        assert result.successes == []
        assert result.errors == []
        mock_deployment_repo.get_deployments_by_ids.assert_not_awaited()
        mock_appproxy_client_pool.load_client.assert_not_called()

    async def test_single_endpoint_pushes_once(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_appproxy_client_pool: MagicMock,
    ) -> None:
        """RR-REG-002: Two routes for one endpoint collapse into one bulk call."""
        endpoint_id = DeploymentID(uuid4())
        routes = [_route_with_replica(endpoint_id), _route_with_replica(endpoint_id)]
        _wire_proxy_target(mock_deployment_repo, [endpoint_id])
        client = mock_appproxy_client_pool.load_client.return_value
        client.bulk_register_routes.return_value = BulkRegisterRoutesResponse(
            endpoints=[
                RegisteredRoutesItem(
                    deployment_id=endpoint_id,
                    success=True,
                    registered_route_ids=[r.route_id for r in routes],
                    already_registered_route_ids=[],
                )
            ]
        )

        result = await route_executor.register_routes_now(routes)

        assert len(result.successes) == 2
        assert result.errors == []
        client.bulk_register_routes.assert_awaited_once()
        request = client.bulk_register_routes.await_args.args[0]
        assert [item.deployment_id for item in request.endpoints] == [endpoint_id]
        # Each entry carries the replica host/port from RouteData.
        emitted = request.endpoints[0].routes
        assert {entry.route_id for entry in emitted} == {r.route_id for r in routes}
        assert all(entry.kernel_host == "10.0.0.1" for entry in emitted)
        assert all(entry.kernel_port == 8000 for entry in emitted)

    async def test_route_without_replica_info_is_error(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_appproxy_client_pool: MagicMock,
    ) -> None:
        """RR-REG-003: Routes missing replica info land in errors, not the request."""
        endpoint_id = DeploymentID(uuid4())
        good = _route_with_replica(endpoint_id)
        bad = _route_with_replica(endpoint_id, replica_host=None, replica_port=None)
        _wire_proxy_target(mock_deployment_repo, [endpoint_id])
        client = mock_appproxy_client_pool.load_client.return_value
        client.bulk_register_routes.return_value = BulkRegisterRoutesResponse(
            endpoints=[
                RegisteredRoutesItem(
                    deployment_id=endpoint_id,
                    success=True,
                    registered_route_ids=[good.route_id],
                    already_registered_route_ids=[],
                )
            ]
        )

        result = await route_executor.register_routes_now([good, bad])

        # The good route is reported by the bulk response; the bad one
        # never even makes it onto the wire.
        assert {r.route_id for r in result.successes} == {good.route_id}
        assert {e.route_info.route_id for e in result.errors} == {bad.route_id}
        emitted = client.bulk_register_routes.await_args.args[0].endpoints[0].routes
        assert {entry.route_id for entry in emitted} == {good.route_id}

    async def test_per_endpoint_failure_isolated(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_appproxy_client_pool: MagicMock,
    ) -> None:
        """RR-REG-004: One endpoint marked failed by AppProxy doesn't drop other successes."""
        endpoint_ids = [DeploymentID(uuid4()) for _ in range(3)]
        routes = [_route_with_replica(eid) for eid in endpoint_ids]
        _wire_proxy_target(mock_deployment_repo, endpoint_ids)
        client = mock_appproxy_client_pool.load_client.return_value
        client.bulk_register_routes.return_value = BulkRegisterRoutesResponse(
            endpoints=[
                RegisteredRoutesItem(
                    deployment_id=endpoint_ids[0],
                    success=False,
                    error="circuit gone",
                ),
                RegisteredRoutesItem(
                    deployment_id=endpoint_ids[1],
                    success=True,
                    registered_route_ids=[routes[1].route_id],
                ),
                RegisteredRoutesItem(
                    deployment_id=endpoint_ids[2],
                    success=True,
                    registered_route_ids=[routes[2].route_id],
                ),
            ]
        )

        result = await route_executor.register_routes_now(routes)

        assert len(result.successes) == 2
        assert len(result.errors) == 1
        assert result.errors[0].route_info.deployment_id == endpoint_ids[0]


class TestUnregisterRoutesNow:
    """Tests for unregister_routes_now (synchronous bulk unregister)."""

    async def test_empty_routes_is_noop(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_appproxy_client_pool: MagicMock,
    ) -> None:
        """RR-UNREG-001: Empty input is a no-op."""
        result = await route_executor.unregister_routes_now([])

        assert result.successes == []
        assert result.errors == []
        mock_deployment_repo.get_deployments_by_ids.assert_not_awaited()
        mock_appproxy_client_pool.load_client.assert_not_called()

    async def test_single_endpoint_unregister_once(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_appproxy_client_pool: MagicMock,
    ) -> None:
        """RR-UNREG-002: Two routes for one endpoint collapse into one unregister call."""
        endpoint_id = DeploymentID(uuid4())
        routes = [_route_with_replica(endpoint_id), _route_with_replica(endpoint_id)]
        _wire_proxy_target(mock_deployment_repo, [endpoint_id])
        client = mock_appproxy_client_pool.load_client.return_value
        client.bulk_unregister_routes.return_value = BulkUnregisterRoutesResponse(
            endpoints=[
                UnregisteredRoutesItem(
                    deployment_id=endpoint_id,
                    success=True,
                    unregistered_route_ids=[r.route_id for r in routes],
                    already_absent_route_ids=[],
                )
            ]
        )

        result = await route_executor.unregister_routes_now(routes)

        assert len(result.successes) == 2
        assert result.errors == []
        client.bulk_unregister_routes.assert_awaited_once()
        request = client.bulk_unregister_routes.await_args.args[0]
        assert [item.deployment_id for item in request.endpoints] == [endpoint_id]
        # Unregister is keyed only on route_id, so kernel host/port is
        # not transmitted.
        emitted_ids = request.endpoints[0].route_ids
        assert set(emitted_ids) == {r.route_id for r in routes}

    async def test_per_endpoint_failure_isolated(
        self,
        route_executor: RouteExecutor,
        mock_deployment_repo: AsyncMock,
        mock_appproxy_client_pool: MagicMock,
    ) -> None:
        """RR-UNREG-003: One endpoint marked failed by AppProxy doesn't drop other successes."""
        endpoint_ids = [DeploymentID(uuid4()) for _ in range(3)]
        routes = [_route_with_replica(eid) for eid in endpoint_ids]
        _wire_proxy_target(mock_deployment_repo, endpoint_ids)
        client = mock_appproxy_client_pool.load_client.return_value
        client.bulk_unregister_routes.return_value = BulkUnregisterRoutesResponse(
            endpoints=[
                UnregisteredRoutesItem(
                    deployment_id=endpoint_ids[0],
                    success=False,
                    error="circuit gone",
                ),
                UnregisteredRoutesItem(
                    deployment_id=endpoint_ids[1],
                    success=True,
                    unregistered_route_ids=[routes[1].route_id],
                ),
                UnregisteredRoutesItem(
                    deployment_id=endpoint_ids[2],
                    success=True,
                    unregistered_route_ids=[routes[2].route_id],
                ),
            ]
        )

        result = await route_executor.unregister_routes_now(routes)

        assert len(result.successes) == 2
        assert len(result.errors) == 1
        assert result.errors[0].route_info.deployment_id == endpoint_ids[0]
