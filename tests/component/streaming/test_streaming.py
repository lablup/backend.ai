from __future__ import annotations

import pytest

from ai.backend.client.v2.exceptions import NotFoundError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.streaming.response import GetStreamAppsResponse

from .conftest import SessionSeedData


class TestGetStreamApps:
    async def test_admin_gets_stream_apps(
        self,
        admin_registry: BackendAIClientRegistry,
        session_seed: SessionSeedData,
    ) -> None:
        """Admin retrieves apps for a RUNNING session with service_ports."""
        result = await admin_registry.streaming.get_stream_apps(session_seed.session_name)
        assert isinstance(result, GetStreamAppsResponse)
        apps = result.root
        assert len(apps) == 2

        app_names = {app.name for app in apps}
        assert app_names == {"jupyter", "ttyd"}

        jupyter_app = next(a for a in apps if a.name == "jupyter")
        assert jupyter_app.protocol == "http"
        assert jupyter_app.ports == [8888]

        ttyd_app = next(a for a in apps if a.name == "ttyd")
        assert ttyd_app.protocol == "http"
        assert ttyd_app.ports == [7681]

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

    async def test_session_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Nonexistent session name raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await admin_registry.streaming.get_stream_apps("nonexistent-session-xyz-99999")
