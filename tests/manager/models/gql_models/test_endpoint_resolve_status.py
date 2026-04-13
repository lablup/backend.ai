from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai.backend.common.data.endpoint.types import EndpointStatus
from ai.backend.manager.data.deployment.types import EndpointLifecycle, RouteStatus
from ai.backend.manager.models.gql_models.endpoint import Endpoint


class TestEndpointResolveStatus:
    """Regression test for BA-5664: empty routings must not resolve to HEALTHY."""

    @pytest.fixture
    def info(self) -> MagicMock:
        return MagicMock()

    async def test_empty_routings_returns_degraded(self, info: MagicMock) -> None:
        ep = Endpoint()
        ep.lifecycle_stage = EndpointLifecycle.READY.name
        ep.routings = []
        result = await ep.resolve_status(info)
        assert result == EndpointStatus.DEGRADED

    async def test_all_healthy_routings_returns_healthy(self, info: MagicMock) -> None:
        routing = MagicMock()
        routing.status = RouteStatus.HEALTHY.name
        ep = Endpoint()
        ep.lifecycle_stage = EndpointLifecycle.READY.name
        ep.retries = 0
        ep.routings = [routing]
        result = await ep.resolve_status(info)
        assert result == EndpointStatus.HEALTHY
