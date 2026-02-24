from __future__ import annotations

import pytest

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.storage.response import (
    ListVFSStorageResponse,
    ObjectStorageListResponse,
)


@pytest.mark.integration
class TestObjectStorageLifecycle:
    @pytest.mark.asyncio
    async def test_list_object_storages(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """list_object_storages → verify response structure."""
        result = await admin_registry.storage.list_object_storages()
        assert isinstance(result, ObjectStorageListResponse)
        assert isinstance(result.storages, list)
        for storage in result.storages:
            assert storage.id
            assert storage.name


@pytest.mark.integration
class TestVFSStorageLifecycle:
    @pytest.mark.asyncio
    async def test_list_vfs_storages(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """list_vfs_storages → verify response structure."""
        result = await admin_registry.storage.list_vfs_storages()
        assert isinstance(result, ListVFSStorageResponse)
        assert isinstance(result.storages, list)
        for storage in result.storages:
            assert storage.name
            assert storage.host
            assert storage.base_path
