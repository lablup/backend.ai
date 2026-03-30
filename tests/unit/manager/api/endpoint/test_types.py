from __future__ import annotations

from unittest.mock import Mock

from ai.backend.common.data.endpoint.types import EndpointLifecycle, EndpointStatus
from ai.backend.manager.api.gql_legacy.endpoint import Endpoint
from ai.backend.manager.data.deployment.types import RouteStatus


class TestEndpointType:
    async def test_status_unhealthy_when_no_healthy_routes(self) -> None:
        """
        Regression test: When all routes are unhealthy, status should be UNHEALTHY.

        Previously, the code returned DEGRADED even when no healthy routes existed,
        making it impossible to determine endpoint accessibility from status alone.
        See: https://github.com/lablup/backend.ai/issues/7688
        """
        mock_endpoint = Mock(spec=Endpoint)
        mock_endpoint.lifecycle_stage = EndpointLifecycle.READY.name

        unhealthy_route = Mock()
        unhealthy_route.status = RouteStatus.UNHEALTHY.name
        mock_endpoint.routings = [unhealthy_route, unhealthy_route]

        result = await Endpoint.resolve_status(mock_endpoint, info=Mock())
        assert result == EndpointStatus.UNHEALTHY

    async def test_status_degraded_when_healthy_and_degraded_routes_mixed(self) -> None:
        """
        When some routes are healthy and others are degraded/unhealthy,
        the endpoint status should be DEGRADED.
        """
        mock_endpoint = Mock(spec=Endpoint)
        mock_endpoint.lifecycle_stage = EndpointLifecycle.READY.name

        healthy_route = Mock()
        healthy_route.status = RouteStatus.HEALTHY.name
        degraded_route = Mock()
        degraded_route.status = RouteStatus.DEGRADED.name

        mock_endpoint.routings = [healthy_route, degraded_route]

        result = await Endpoint.resolve_status(mock_endpoint, info=Mock())
        assert result == EndpointStatus.DEGRADED

    async def test_status_degraded_when_healthy_and_provisioning_routes_mixed(self) -> None:
        """
        When some routes are healthy and others are still provisioning,
        the endpoint status should be DEGRADED (not PROVISIONING).

        Previously returned PROVISIONING, but this was changed to DEGRADED
        for clearer status semantics.
        """
        mock_endpoint = Mock(spec=Endpoint)
        mock_endpoint.lifecycle_stage = EndpointLifecycle.READY.name

        healthy_route = Mock()
        healthy_route.status = RouteStatus.HEALTHY.name
        provisioning_route = Mock()
        provisioning_route.status = RouteStatus.PROVISIONING.name

        mock_endpoint.routings = [healthy_route, provisioning_route]

        result = await Endpoint.resolve_status(mock_endpoint, info=Mock())
        assert result == EndpointStatus.DEGRADED

    async def test_status_unhealthy_when_all_routes_terminated(self) -> None:
        """
        When all routes are terminated, the endpoint status should be UNHEALTHY.

        No active routes means the endpoint cannot serve any requests.
        """
        mock_endpoint = Mock(spec=Endpoint)
        mock_endpoint.lifecycle_stage = EndpointLifecycle.READY.name

        terminated_route = Mock()
        terminated_route.status = RouteStatus.TERMINATED.name

        mock_endpoint.routings = [terminated_route, terminated_route]

        result = await Endpoint.resolve_status(mock_endpoint, info=Mock())
        assert result == EndpointStatus.UNHEALTHY

    async def test_status_healthy_when_terminated_routes_are_mixed_with_healthy(self) -> None:
        """
        Regression test: Terminated routes should be excluded from status calculation.

        When all active routes are healthy but terminated routes also exist,
        the endpoint status should be HEALTHY, not DEGRADED.
        Previously, terminated routes were included in the total count, causing
        the status to incorrectly report DEGRADED.
        """
        mock_endpoint = Mock(spec=Endpoint)
        mock_endpoint.lifecycle_stage = EndpointLifecycle.READY.name

        healthy_route = Mock()
        healthy_route.status = RouteStatus.HEALTHY.name
        terminated_route = Mock()
        terminated_route.status = RouteStatus.TERMINATED.name

        mock_endpoint.routings = [healthy_route, healthy_route, terminated_route]

        result = await Endpoint.resolve_status(mock_endpoint, info=Mock())
        assert result == EndpointStatus.HEALTHY

    async def test_status_unhealthy_when_no_routes(self) -> None:
        """
        When there are no routes at all, the endpoint status should be UNHEALTHY.

        An endpoint with no routes cannot serve any requests.
        """
        mock_endpoint = Mock(spec=Endpoint)
        mock_endpoint.lifecycle_stage = EndpointLifecycle.READY.name
        mock_endpoint.routings = []

        result = await Endpoint.resolve_status(mock_endpoint, info=Mock())
        assert result == EndpointStatus.UNHEALTHY
