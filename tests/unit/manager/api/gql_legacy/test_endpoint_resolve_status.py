from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai.backend.common.data.endpoint.types import EndpointLifecycle, EndpointStatus
from ai.backend.manager.api.gql_legacy.endpoint import Endpoint
from ai.backend.manager.data.deployment.types import RouteStatus


class TestEndpointResolveStatus:
    """Regression tests for endpoint routings resolution with empty or None routings."""

    @pytest.fixture
    def info(self) -> MagicMock:
        return MagicMock()

    async def test_none_routings_returns_degraded(self, info: MagicMock) -> None:
        ep = Endpoint()
        ep.lifecycle_stage = EndpointLifecycle.READY.name
        ep.routings = None
        result = await ep.resolve_status(info)
        assert result == EndpointStatus.DEGRADED

    async def test_empty_routings_returns_degraded(self, info: MagicMock) -> None:
        ep = Endpoint()
        ep.lifecycle_stage = EndpointLifecycle.READY.name
        ep.routings = []
        result = await ep.resolve_status(info)
        assert result == EndpointStatus.DEGRADED

    async def test_all_inactive_routings_returns_unhealthy(self, info: MagicMock) -> None:
        routing = MagicMock()
        routing.status = RouteStatus.TERMINATED.name
        ep = Endpoint()
        ep.lifecycle_stage = EndpointLifecycle.READY.name
        ep.routings = [routing]
        result = await ep.resolve_status(info)
        assert result == EndpointStatus.UNHEALTHY

    async def test_none_routings_resolve_errors_returns_empty(self, info: MagicMock) -> None:
        ep = Endpoint()
        ep.routings = None
        result = await ep.resolve_errors(info)
        assert result == []
