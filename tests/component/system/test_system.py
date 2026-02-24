from __future__ import annotations

import pytest

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.system import SystemVersionResponse


class TestGetVersions:
    @pytest.mark.asyncio
    async def test_admin_gets_versions(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.system.get_versions()
        assert isinstance(result, SystemVersionResponse)

    @pytest.mark.asyncio
    async def test_user_gets_versions(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        result = await user_registry.system.get_versions()
        assert isinstance(result, SystemVersionResponse)

    @pytest.mark.asyncio
    async def test_response_contains_valid_version_strings(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.system.get_versions()
        assert isinstance(result, SystemVersionResponse)
        assert result.version.startswith("v")
        assert len(result.manager) > 0
