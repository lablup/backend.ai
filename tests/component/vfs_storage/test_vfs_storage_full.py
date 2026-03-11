"""Component tests for VFS storage full CRUD lifecycle via processors.

Tests create, get by ID/name, search, update, and delete operations
through the VFSStorageProcessors layer with a real database.
Verifies HTTP API visibility where applicable (list/get by name).
Quota management tests use AsyncMock of StorageProxyManagerFacingClient.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    OffsetPagination,
    Updater,
)
from ai.backend.manager.repositories.vfs_storage.creators import VFSStorageCreatorSpec
from ai.backend.manager.repositories.vfs_storage.updaters import VFSStorageUpdaterSpec
from ai.backend.manager.services.vfs_storage.actions import (
    CreateVFSStorageAction,
    DeleteVFSStorageAction,
    GetVFSStorageAction,
    ListVFSStorageAction,
    SearchVFSStoragesAction,
    UpdateVFSStorageAction,
)
from ai.backend.manager.services.vfs_storage.actions.get_quota_scope import (
    GetQuotaScopeAction,
)
from ai.backend.manager.services.vfs_storage.actions.set_quota_scope import (
    SetQuotaScopeAction,
)
from ai.backend.manager.services.vfs_storage.actions.unset_quota_scope import (
    UnsetQuotaScopeAction,
)
from ai.backend.manager.services.vfs_storage.processors import VFSStorageProcessors
from ai.backend.manager.types import OptionalState

VFSStorageFixtureData = dict[str, Any]
VFSStorageFactory = Callable[..., Coroutine[Any, Any, VFSStorageFixtureData]]


class TestVFSStorageCRUD:
    """Full CRUD lifecycle tests via processors with a real DB."""

    async def test_create_vfs_storage(
        self,
        vfs_storage_processors: VFSStorageProcessors,
    ) -> None:
        """Create VFS storage with name/host/base_path returns storage data."""
        action = CreateVFSStorageAction(
            creator=Creator(
                spec=VFSStorageCreatorSpec(
                    name="crud-create-test",
                    host="local:volume1",
                    base_path="/mnt/vfs/create-test",
                )
            )
        )
        result = await vfs_storage_processors.create.wait_for_complete(action)
        assert result.result.name == "crud-create-test"
        assert result.result.host == "local:volume1"
        assert result.result.base_path == Path("/mnt/vfs/create-test")
        assert result.result.id is not None

    async def test_get_vfs_storage_by_id(
        self,
        vfs_storage_processors: VFSStorageProcessors,
        target_vfs_storage: VFSStorageFixtureData,
    ) -> None:
        """Get VFS storage by ID returns correct data."""
        action = GetVFSStorageAction(storage_id=target_vfs_storage["id"])
        result = await vfs_storage_processors.get.wait_for_complete(action)
        assert result.result.id == target_vfs_storage["id"]
        assert result.result.name == target_vfs_storage["name"]
        assert result.result.host == target_vfs_storage["host"]

    async def test_get_vfs_storage_by_name(
        self,
        vfs_storage_processors: VFSStorageProcessors,
        target_vfs_storage: VFSStorageFixtureData,
    ) -> None:
        """Get VFS storage by name returns correct data."""
        action = GetVFSStorageAction(storage_name=target_vfs_storage["name"])
        result = await vfs_storage_processors.get.wait_for_complete(action)
        assert result.result.id == target_vfs_storage["id"]
        assert result.result.name == target_vfs_storage["name"]

    async def test_get_vfs_storage_by_name_via_http(
        self,
        admin_registry: BackendAIClientRegistry,
        vfs_storage_processors: VFSStorageProcessors,
    ) -> None:
        """Create via processor, verify get by name via HTTP API."""
        create_action = CreateVFSStorageAction(
            creator=Creator(
                spec=VFSStorageCreatorSpec(
                    name="http-get-test",
                    host="local:volume2",
                    base_path="/mnt/vfs/http-test",
                )
            )
        )
        await vfs_storage_processors.create.wait_for_complete(create_action)

        result = await admin_registry.storage.get_vfs_storage("http-get-test")
        assert result.storage.name == "http-get-test"
        assert result.storage.host == "local:volume2"
        assert result.storage.base_path == "/mnt/vfs/http-test"

    async def test_search_vfs_storages(
        self,
        vfs_storage_processors: VFSStorageProcessors,
        vfs_storage_factory: VFSStorageFactory,
    ) -> None:
        """Search VFS storages with pagination returns matching results."""
        await vfs_storage_factory(name="search-alpha", host="local:vol1")
        await vfs_storage_factory(name="search-beta", host="local:vol2")
        await vfs_storage_factory(name="search-gamma", host="nfs:share1")

        action = SearchVFSStoragesAction(
            querier=BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                conditions=[],
                orders=[],
            )
        )
        result = await vfs_storage_processors.search_vfs_storages.wait_for_complete(action)
        assert result.total_count >= 3
        storage_names = [s.name for s in result.storages]
        assert "search-alpha" in storage_names
        assert "search-beta" in storage_names
        assert "search-gamma" in storage_names

    async def test_update_vfs_storage(
        self,
        vfs_storage_processors: VFSStorageProcessors,
        target_vfs_storage: VFSStorageFixtureData,
    ) -> None:
        """Update VFS storage fields and verify changes reflected."""
        update_action = UpdateVFSStorageAction(
            updater=Updater(
                spec=VFSStorageUpdaterSpec(
                    name=OptionalState.update("updated-name"),
                    host=OptionalState.update("nfs:updated-host"),
                ),
                pk_value=target_vfs_storage["id"],
            )
        )
        update_result = await vfs_storage_processors.update.wait_for_complete(update_action)
        assert update_result.result.name == "updated-name"
        assert update_result.result.host == "nfs:updated-host"

        # Verify via get by ID
        get_action = GetVFSStorageAction(storage_id=target_vfs_storage["id"])
        get_result = await vfs_storage_processors.get.wait_for_complete(get_action)
        assert get_result.result.name == "updated-name"
        assert get_result.result.host == "nfs:updated-host"

    async def test_delete_vfs_storage(
        self,
        vfs_storage_processors: VFSStorageProcessors,
        vfs_storage_factory: VFSStorageFactory,
    ) -> None:
        """Delete VFS storage and verify removed from listings."""
        storage = await vfs_storage_factory(name="to-delete")

        delete_action = DeleteVFSStorageAction(storage_id=storage["id"])
        delete_result = await vfs_storage_processors.delete.wait_for_complete(delete_action)
        assert delete_result.deleted_storage_id == storage["id"]

        # Verify no longer in list
        list_action = ListVFSStorageAction()
        list_result = await vfs_storage_processors.list_storages.wait_for_complete(list_action)
        storage_names = [s.name for s in list_result.data]
        assert "to-delete" not in storage_names

    async def test_full_crud_lifecycle(
        self,
        vfs_storage_processors: VFSStorageProcessors,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Full lifecycle: create -> get by ID -> get by name -> update -> delete -> verify."""
        # Create
        create_result = await vfs_storage_processors.create.wait_for_complete(
            CreateVFSStorageAction(
                creator=Creator(
                    spec=VFSStorageCreatorSpec(
                        name="lifecycle-test",
                        host="local:lifecycle",
                        base_path="/mnt/vfs/lifecycle",
                    )
                )
            )
        )
        storage_id = create_result.result.id

        # Get by ID
        get_result = await vfs_storage_processors.get.wait_for_complete(
            GetVFSStorageAction(storage_id=storage_id)
        )
        assert get_result.result.name == "lifecycle-test"

        # Get by name via HTTP
        http_result = await admin_registry.storage.get_vfs_storage("lifecycle-test")
        assert http_result.storage.host == "local:lifecycle"

        # Update
        await vfs_storage_processors.update.wait_for_complete(
            UpdateVFSStorageAction(
                updater=Updater(
                    spec=VFSStorageUpdaterSpec(
                        host=OptionalState.update("nfs:updated-lifecycle"),
                    ),
                    pk_value=storage_id,
                )
            )
        )

        # Verify update via HTTP
        updated = await admin_registry.storage.get_vfs_storage("lifecycle-test")
        assert updated.storage.host == "nfs:updated-lifecycle"

        # Delete
        await vfs_storage_processors.delete.wait_for_complete(
            DeleteVFSStorageAction(storage_id=storage_id)
        )

        # Verify deleted via list
        list_after = await admin_registry.storage.list_vfs_storages()
        assert "lifecycle-test" not in [s.name for s in list_after.storages]


class TestVFSStorageQuota:
    """Quota get/set/unset tests with mocked storage-proxy client.

    Uses AsyncMock of StorageProxyManagerFacingClient instead of xfail,
    since no live storage-proxy is available in component tests.
    """

    @pytest.fixture()
    def mock_storage_proxy_client(
        self,
        monkeypatch: pytest.MonkeyPatch,
        storage_manager: StorageSessionManager,
    ) -> AsyncMock:
        """Configure storage_manager mock with a mock manager-facing client."""
        mock_client = AsyncMock()
        monkeypatch.setattr(
            StorageSessionManager,
            "get_proxy_and_volume",
            MagicMock(return_value=("proxy1", "volume1")),
        )
        storage_manager.get_manager_facing_client.return_value = mock_client
        return mock_client

    async def test_get_quota_scope(
        self,
        vfs_storage_processors: VFSStorageProcessors,
        mock_storage_proxy_client: AsyncMock,
    ) -> None:
        """Get quota via storage-proxy mock returns used_bytes/limit_bytes."""
        mock_storage_proxy_client.get_quota_scope.return_value = {
            "used_bytes": 1024,
            "limit_bytes": 4096,
        }

        action = GetQuotaScopeAction(
            storage_host_name="proxy1:volume1",
            quota_scope_id="scope-1",
        )
        result = await vfs_storage_processors.get_quota_scope.wait_for_complete(action)

        assert result.quota_scope_id == "scope-1"
        assert result.storage_host_name == "proxy1:volume1"
        assert result.usage_bytes == 1024
        assert result.hard_limit_bytes == 4096
        mock_storage_proxy_client.get_quota_scope.assert_called_once_with("volume1", "scope-1")

    async def test_set_quota_scope(
        self,
        vfs_storage_processors: VFSStorageProcessors,
        mock_storage_proxy_client: AsyncMock,
    ) -> None:
        """Set quota via storage-proxy mock updates quota limit."""
        mock_storage_proxy_client.get_quota_scope.return_value = {
            "used_bytes": 512,
            "limit_bytes": 8192,
        }

        action = SetQuotaScopeAction(
            storage_host_name="proxy1:volume1",
            quota_scope_id="scope-1",
            hard_limit_bytes=8192,
        )
        result = await vfs_storage_processors.set_quota_scope.wait_for_complete(action)

        assert result.quota_scope_id == "scope-1"
        assert result.usage_bytes == 512
        assert result.hard_limit_bytes == 8192
        mock_storage_proxy_client.update_quota_scope.assert_called_once_with(
            "volume1", "scope-1", 8192
        )

    async def test_unset_quota_scope(
        self,
        vfs_storage_processors: VFSStorageProcessors,
        mock_storage_proxy_client: AsyncMock,
    ) -> None:
        """Unset quota via storage-proxy mock removes quota limit."""
        action = UnsetQuotaScopeAction(
            storage_host_name="proxy1:volume1",
            quota_scope_id="scope-1",
        )
        result = await vfs_storage_processors.unset_quota_scope.wait_for_complete(action)

        assert result.quota_scope_id == "scope-1"
        assert result.storage_host_name == "proxy1:volume1"
        mock_storage_proxy_client.delete_quota_scope_quota.assert_called_once_with(
            "volume1", "scope-1"
        )
