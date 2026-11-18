from __future__ import annotations

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.streaming.response import GetStreamAppsResponse

from .conftest import SessionSeedData


class TestGetStreamApps:
    async def test_empty_stream_apps(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed_no_ports: SessionSeedData,
    ) -> None:
        """Session with no service_ports returns an empty list."""
        result = await admin_registry.streaming.get_stream_apps(
            session_seed_no_ports.session_name,
        )
        assert isinstance(result, GetStreamAppsResponse)
        assert result.root == []
