from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai.backend.common.data.endpoint.types import EndpointLifecycle, EndpointStatus
from ai.backend.manager.api.gql_legacy.endpoint import Endpoint


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
