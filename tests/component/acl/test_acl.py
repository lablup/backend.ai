from __future__ import annotations

import pytest

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.acl import GetPermissionsResponse


class TestGetPermissions:
    @pytest.mark.asyncio
    async def test_admin_gets_permissions(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.acl.get_permissions()
        assert isinstance(result, GetPermissionsResponse)
        assert len(result.vfolder_host_permission_list) > 0

    @pytest.mark.asyncio
    async def test_regular_user_gets_own_permissions(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        result = await user_registry.acl.get_permissions()
        assert isinstance(result, GetPermissionsResponse)
        assert len(result.vfolder_host_permission_list) > 0

    @pytest.mark.asyncio
    async def test_permissions_response_is_valid_structure(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.acl.get_permissions()
        assert isinstance(result, GetPermissionsResponse)
        assert isinstance(result.vfolder_host_permission_list, list)
        for perm in result.vfolder_host_permission_list:
            assert isinstance(perm, str)
            assert len(perm) > 0

    @pytest.mark.asyncio
    async def test_admin_and_user_get_same_permissions(
        self,
        admin_registry: BackendAIClientRegistry,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        admin_result = await admin_registry.acl.get_permissions()
        user_result = await user_registry.acl.get_permissions()
        assert sorted(admin_result.vfolder_host_permission_list) == sorted(
            user_result.vfolder_host_permission_list
        )
