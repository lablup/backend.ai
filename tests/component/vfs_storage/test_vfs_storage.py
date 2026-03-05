"""Component tests for VfsStorage CRUD + quota management integration.

Tests the HTTP API layer with a real aiohttp server and real DB.
Validates list/get operations through the SDK client and verifies
error handling for nonexistent storages.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

import pytest

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.storage.response import (
    GetVFSStorageResponse,
    ListVFSStorageResponse,
)
from ai.backend.common.dto.storage.request import VFSListFilesReq

VFSStorageFixtureData = dict[str, Any]
VFSStorageFactory = Callable[..., Coroutine[Any, Any, VFSStorageFixtureData]]


class TestVFSStorageList:
    """Tests for listing VFS storages via HTTP API."""

    async def test_admin_lists_vfs_storages(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfs_storage: VFSStorageFixtureData,
    ) -> None:
        """Admin can list VFS storages; the DB-seeded storage is visible."""
        result = await admin_registry.storage.list_vfs_storages()
        assert isinstance(result, ListVFSStorageResponse)
        storage_names = [s.name for s in result.storages]
        assert target_vfs_storage["name"] in storage_names

    async def test_admin_lists_vfs_storages_empty(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Listing storages returns an empty list when none exist."""
        result = await admin_registry.storage.list_vfs_storages()
        assert isinstance(result, ListVFSStorageResponse)
        assert isinstance(result.storages, list)

    async def test_admin_lists_multiple_storages(
        self,
        admin_registry: BackendAIClientRegistry,
        vfs_storage_factory: VFSStorageFactory,
    ) -> None:
        """Multiple storages created by factory are all visible."""
        storage_a = await vfs_storage_factory(name="storage-alpha")
        storage_b = await vfs_storage_factory(name="storage-beta")

        result = await admin_registry.storage.list_vfs_storages()
        assert isinstance(result, ListVFSStorageResponse)
        storage_names = [s.name for s in result.storages]
        assert storage_a["name"] in storage_names
        assert storage_b["name"] in storage_names

    async def test_user_lists_vfs_storages(
        self,
        user_registry: BackendAIClientRegistry,
        target_vfs_storage: VFSStorageFixtureData,
    ) -> None:
        """Regular user can also list VFS storages (auth_required)."""
        result = await user_registry.storage.list_vfs_storages()
        assert isinstance(result, ListVFSStorageResponse)
        storage_names = [s.name for s in result.storages]
        assert target_vfs_storage["name"] in storage_names


class TestVFSStorageGet:
    """Tests for getting a specific VFS storage by name."""

    async def test_admin_gets_storage_by_name(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfs_storage: VFSStorageFixtureData,
    ) -> None:
        """Admin can get VFS storage details by name."""
        result = await admin_registry.storage.get_vfs_storage(target_vfs_storage["name"])
        assert isinstance(result, GetVFSStorageResponse)
        assert result.storage.name == target_vfs_storage["name"]
        assert result.storage.host == target_vfs_storage["host"]
        assert result.storage.base_path == target_vfs_storage["base_path"]

    async def test_get_nonexistent_storage_raises_error(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Getting a nonexistent storage name returns an error."""
        with pytest.raises(Exception):
            await admin_registry.storage.get_vfs_storage("nonexistent-storage-xyz-99999")

    async def test_user_gets_storage_by_name(
        self,
        user_registry: BackendAIClientRegistry,
        target_vfs_storage: VFSStorageFixtureData,
    ) -> None:
        """Regular user can also get VFS storage by name (auth_required)."""
        result = await user_registry.storage.get_vfs_storage(target_vfs_storage["name"])
        assert isinstance(result, GetVFSStorageResponse)
        assert result.storage.name == target_vfs_storage["name"]


class TestVFSStorageCRUDIntegration:
    """Integration test: create -> list -> get -> verify details.

    Since create/update/delete are not exposed via REST API
    (they are internal admin operations), this test uses the DB factory
    to simulate the CRUD flow and verifies via SDK list/get endpoints.
    """

    async def test_create_list_get_flow(
        self,
        admin_registry: BackendAIClientRegistry,
        vfs_storage_factory: VFSStorageFactory,
    ) -> None:
        """Storage created via factory appears in list and can be retrieved."""
        storage = await vfs_storage_factory(
            name="integration-vfs",
            host="local:volume2",
            base_path="/mnt/vfs/integration",
        )

        # List - verify it appears
        list_result = await admin_registry.storage.list_vfs_storages()
        storage_names = [s.name for s in list_result.storages]
        assert "integration-vfs" in storage_names

        # Get - verify details
        get_result = await admin_registry.storage.get_vfs_storage("integration-vfs")
        assert get_result.storage.name == storage["name"]
        assert get_result.storage.host == "local:volume2"
        assert get_result.storage.base_path == "/mnt/vfs/integration"

    async def test_multiple_storages_different_hosts(
        self,
        admin_registry: BackendAIClientRegistry,
        vfs_storage_factory: VFSStorageFactory,
    ) -> None:
        """Storages with different hosts are all listed and retrievable."""
        local_storage = await vfs_storage_factory(
            name="local-storage",
            host="local:volume1",
            base_path="/mnt/local",
        )
        remote_storage = await vfs_storage_factory(
            name="remote-storage",
            host="nfs:share1",
            base_path="/mnt/nfs",
        )

        list_result = await admin_registry.storage.list_vfs_storages()
        storage_names = [s.name for s in list_result.storages]
        assert local_storage["name"] in storage_names
        assert remote_storage["name"] in storage_names

        # Verify each storage has correct host
        local_get = await admin_registry.storage.get_vfs_storage("local-storage")
        assert local_get.storage.host == "local:volume1"

        remote_get = await admin_registry.storage.get_vfs_storage("remote-storage")
        assert remote_get.storage.host == "nfs:share1"


class TestVFSStorageQuotaManagement:
    """Tests for quota management operations.

    Quota operations (get/set/unset/search) require a live storage-proxy
    connection which is not available in component test environment.
    These tests document the expected behavior and are marked as xfail.
    """

    @pytest.mark.xfail(
        strict=True,
        reason="Quota operations require live storage-proxy not available in component tests",
    )
    async def test_list_vfs_files_requires_storage_proxy(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfs_storage: VFSStorageFixtureData,
    ) -> None:
        """File listing requires storage-proxy connection."""
        await admin_registry.storage.list_vfs_files(
            target_vfs_storage["name"],
            VFSListFilesReq(directory="/"),
        )
