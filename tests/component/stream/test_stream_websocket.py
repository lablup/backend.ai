from __future__ import annotations

import pytest

from ai.backend.client.v2.exceptions import NotFoundError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.streaming.response import GetStreamAppsResponse

from .conftest import SessionSeedData


class TestStreamWebSocketGetApps:
    """Tests for the GET /stream/session/{name}/apps REST endpoint."""

    async def test_get_stream_apps_returns_services(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """Valid session returns the configured service_ports as stream apps."""
        result = await admin_registry.streaming.get_stream_apps(session_seed.session_name)
        assert isinstance(result, GetStreamAppsResponse)
        apps = result.root
        assert len(apps) == 2
        app_names = {app.name for app in apps}
        assert app_names == {"jupyter", "ttyd"}

    async def test_get_stream_apps_nonexistent_session(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Nonexistent session name raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await admin_registry.streaming.get_stream_apps("nonexistent-session-xyz-99999")


class TestStreamWebSocketConnect:
    """Tests for WebSocket stream endpoint connectivity.

    Full execute -> interrupt -> restart lifecycle requires a real agent/kernel
    infrastructure and is covered by unit service tests.  These component tests
    verify the HTTP/WebSocket routing and auth layers.
    """

    async def test_terminal_nonexistent_session_closes_ws(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Connecting terminal WS to a nonexistent session should fail."""
        with pytest.raises(Exception):
            async with admin_registry.streaming.connect_terminal(
                "nonexistent-session-xyz-99999",
            ) as ws:
                await ws.receive_str()

    async def test_execute_nonexistent_session_closes_ws(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Connecting execute WS to a nonexistent session should fail."""
        with pytest.raises(Exception):
            async with admin_registry.streaming.connect_execute(
                "nonexistent-session-xyz-99999",
            ) as ws:
                await ws.receive_str()
