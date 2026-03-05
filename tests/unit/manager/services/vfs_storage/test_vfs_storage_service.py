"""
Tests for VFSStorageService functionality.
Tests the service layer with mocked repository operations.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.data.vfs_storage.types import VFSStorageData, VFSStorageListResult
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.vfs_storage.creators import VFSStorageCreatorSpec
from ai.backend.manager.repositories.vfs_storage.repository import VFSStorageRepository
from ai.backend.manager.repositories.vfs_storage.updaters import VFSStorageUpdaterSpec
from ai.backend.manager.services.vfs_storage.actions.create import (
    CreateVFSStorageAction,
    CreateVFSStorageActionResult,
)
from ai.backend.manager.services.vfs_storage.actions.delete import (
    DeleteVFSStorageAction,
    DeleteVFSStorageActionResult,
)
from ai.backend.manager.services.vfs_storage.actions.get import (
    GetVFSStorageAction,
    GetVFSStorageActionResult,
)
from ai.backend.manager.services.vfs_storage.actions.get_quota_scope import (
    GetQuotaScopeAction,
    GetQuotaScopeActionResult,
)
from ai.backend.manager.services.vfs_storage.actions.list import (
    ListVFSStorageAction,
    ListVFSStorageActionResult,
)
from ai.backend.manager.services.vfs_storage.actions.search import (
    SearchVFSStoragesAction,
    SearchVFSStoragesActionResult,
)
from ai.backend.manager.services.vfs_storage.actions.search_quota_scopes import (
    SearchQuotaScopesAction,
    SearchQuotaScopesActionResult,
)
from ai.backend.manager.services.vfs_storage.actions.set_quota_scope import (
    SetQuotaScopeAction,
    SetQuotaScopeActionResult,
)
from ai.backend.manager.services.vfs_storage.actions.unset_quota_scope import (
    UnsetQuotaScopeAction,
    UnsetQuotaScopeActionResult,
)
from ai.backend.manager.services.vfs_storage.actions.update import (
    UpdateVFSStorageAction,
    UpdateVFSStorageActionResult,
)
from ai.backend.manager.services.vfs_storage.service import VFSStorageService
from ai.backend.manager.types import OptionalState


class TestVFSStorageServiceCRUD:
    """Test cases for VFSStorageService CRUD operations."""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=VFSStorageRepository)

    @pytest.fixture
    def vfs_storage_service(self, mock_repository: MagicMock) -> VFSStorageService:
        return VFSStorageService(vfs_storage_repository=mock_repository)

    @pytest.fixture
    def sample_vfs_storage_data(self) -> VFSStorageData:
        return VFSStorageData(
            id=uuid4(),
            name="test-vfs-storage",
            host="localhost",
            base_path=Path("/mnt/vfs/test"),
        )

    # =========================================================================
    # Create
    # =========================================================================

    async def test_create_vfs_storage(
        self,
        vfs_storage_service: VFSStorageService,
        mock_repository: MagicMock,
        sample_vfs_storage_data: VFSStorageData,
    ) -> None:
        """Test creating a VFS storage returns VFSStorageData with id."""
        mock_repository.create = AsyncMock(return_value=sample_vfs_storage_data)

        creator = Creator(
            spec=VFSStorageCreatorSpec(
                name="test-vfs-storage",
                host="localhost",
                base_path="/mnt/vfs/test",
            )
        )
        action = CreateVFSStorageAction(creator=creator)
        result = await vfs_storage_service.create(action)

        assert isinstance(result, CreateVFSStorageActionResult)
        assert result.result.id == sample_vfs_storage_data.id
        assert result.result.name == "test-vfs-storage"
        mock_repository.create.assert_called_once_with(creator)

    # =========================================================================
    # Get
    # =========================================================================

    async def test_get_vfs_storage_by_id(
        self,
        vfs_storage_service: VFSStorageService,
        mock_repository: MagicMock,
        sample_vfs_storage_data: VFSStorageData,
    ) -> None:
        """Test lookup by storage_id."""
        mock_repository.get_by_id = AsyncMock(return_value=sample_vfs_storage_data)

        action = GetVFSStorageAction(
            storage_id=sample_vfs_storage_data.id,
            storage_name=None,
        )
        result = await vfs_storage_service.get(action)

        assert isinstance(result, GetVFSStorageActionResult)
        assert result.result.id == sample_vfs_storage_data.id
        mock_repository.get_by_id.assert_called_once_with(sample_vfs_storage_data.id)

    async def test_get_vfs_storage_by_name(
        self,
        vfs_storage_service: VFSStorageService,
        mock_repository: MagicMock,
        sample_vfs_storage_data: VFSStorageData,
    ) -> None:
        """Test lookup by storage_name."""
        mock_repository.get_by_name = AsyncMock(return_value=sample_vfs_storage_data)

        action = GetVFSStorageAction(storage_id=None, storage_name="test-vfs-storage")
        result = await vfs_storage_service.get(action)

        assert isinstance(result, GetVFSStorageActionResult)
        assert result.result.name == "test-vfs-storage"
        mock_repository.get_by_name.assert_called_once_with("test-vfs-storage")

    async def test_get_vfs_storage_both_null_raises_error(
        self,
        vfs_storage_service: VFSStorageService,
    ) -> None:
        """Test both null raises GenericBadRequest."""
        action = GetVFSStorageAction(storage_id=None, storage_name=None)

        with pytest.raises(GenericBadRequest):
            await vfs_storage_service.get(action)

    async def test_get_vfs_storage_nonexistent_id(
        self,
        vfs_storage_service: VFSStorageService,
        mock_repository: MagicMock,
    ) -> None:
        """Test non-existent id raises error from repository."""
        mock_repository.get_by_id = AsyncMock(side_effect=Exception("Not found"))

        action = GetVFSStorageAction(storage_id=uuid4(), storage_name=None)

        with pytest.raises(Exception, match="Not found"):
            await vfs_storage_service.get(action)

    # =========================================================================
    # List
    # =========================================================================

    async def test_list_vfs_storages(
        self,
        vfs_storage_service: VFSStorageService,
        mock_repository: MagicMock,
        sample_vfs_storage_data: VFSStorageData,
    ) -> None:
        """Test returns full VFSStorageData list."""
        second_storage = VFSStorageData(
            id=uuid4(),
            name="second-storage",
            host="remote-host",
            base_path=Path("/mnt/vfs/second"),
        )
        mock_repository.list_vfs_storages = AsyncMock(
            return_value=[sample_vfs_storage_data, second_storage]
        )

        action = ListVFSStorageAction()
        result = await vfs_storage_service.list(action)

        assert isinstance(result, ListVFSStorageActionResult)
        assert len(result.data) == 2
        assert result.data[0].name == "test-vfs-storage"
        assert result.data[1].name == "second-storage"

    async def test_list_vfs_storages_empty(
        self,
        vfs_storage_service: VFSStorageService,
        mock_repository: MagicMock,
    ) -> None:
        """Test returns empty list when no storages exist."""
        mock_repository.list_vfs_storages = AsyncMock(return_value=[])

        action = ListVFSStorageAction()
        result = await vfs_storage_service.list(action)

        assert result.data == []

    # =========================================================================
    # Update
    # =========================================================================

    async def test_update_vfs_storage(
        self,
        vfs_storage_service: VFSStorageService,
        mock_repository: MagicMock,
    ) -> None:
        """Test updater spec returns updated data."""
        storage_id = uuid4()
        updated_data = VFSStorageData(
            id=storage_id,
            name="updated-name",
            host="new-host",
            base_path=Path("/mnt/vfs/updated"),
        )
        mock_repository.update = AsyncMock(return_value=updated_data)

        updater = Updater(
            spec=VFSStorageUpdaterSpec(
                name=OptionalState.update("updated-name"),
                host=OptionalState.update("new-host"),
            ),
            pk_value=storage_id,
        )
        action = UpdateVFSStorageAction(updater=updater)
        result = await vfs_storage_service.update(action)

        assert isinstance(result, UpdateVFSStorageActionResult)
        assert result.result.name == "updated-name"
        assert result.result.host == "new-host"
        mock_repository.update.assert_called_once_with(updater)

    # =========================================================================
    # Delete
    # =========================================================================

    async def test_delete_vfs_storage(
        self,
        vfs_storage_service: VFSStorageService,
        mock_repository: MagicMock,
    ) -> None:
        """Test storage_id deletion returns deleted_storage_id."""
        storage_id = uuid4()
        mock_repository.delete = AsyncMock(return_value=storage_id)

        action = DeleteVFSStorageAction(storage_id=storage_id)
        result = await vfs_storage_service.delete(action)

        assert isinstance(result, DeleteVFSStorageActionResult)
        assert result.deleted_storage_id == storage_id
        mock_repository.delete.assert_called_once_with(storage_id)

    # =========================================================================
    # Search
    # =========================================================================

    async def test_search_vfs_storages(
        self,
        vfs_storage_service: VFSStorageService,
        mock_repository: MagicMock,
        sample_vfs_storage_data: VFSStorageData,
    ) -> None:
        """Test querier batch query + pagination."""
        mock_repository.search = AsyncMock(
            return_value=VFSStorageListResult(
                items=[sample_vfs_storage_data],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        action = SearchVFSStoragesAction(querier=querier)
        result = await vfs_storage_service.search(action)

        assert isinstance(result, SearchVFSStoragesActionResult)
        assert result.storages == [sample_vfs_storage_data]
        assert result.total_count == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False

    async def test_search_vfs_storages_with_pagination(
        self,
        vfs_storage_service: VFSStorageService,
        mock_repository: MagicMock,
        sample_vfs_storage_data: VFSStorageData,
    ) -> None:
        """Test pagination flags (total_count/has_next_page/has_previous_page)."""
        mock_repository.search = AsyncMock(
            return_value=VFSStorageListResult(
                items=[sample_vfs_storage_data],
                total_count=25,
                has_next_page=True,
                has_previous_page=True,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=10),
            conditions=[],
            orders=[],
        )
        action = SearchVFSStoragesAction(querier=querier)
        result = await vfs_storage_service.search(action)

        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is True

    async def test_search_vfs_storages_empty(
        self,
        vfs_storage_service: VFSStorageService,
        mock_repository: MagicMock,
    ) -> None:
        """Test empty search result."""
        mock_repository.search = AsyncMock(
            return_value=VFSStorageListResult(
                items=[],
                total_count=0,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        querier = BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )
        action = SearchVFSStoragesAction(querier=querier)
        result = await vfs_storage_service.search(action)

        assert result.storages == []
        assert result.total_count == 0


class TestVFSStorageServiceQuotaScope:
    """Test cases for VFSStorageService quota scope operations."""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=VFSStorageRepository)

    @pytest.fixture
    def mock_storage_manager(self) -> MagicMock:
        return MagicMock(spec=StorageSessionManager)

    @pytest.fixture
    def mock_manager_client(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service_with_storage_manager(
        self,
        mock_repository: MagicMock,
        mock_storage_manager: MagicMock,
    ) -> VFSStorageService:
        return VFSStorageService(
            vfs_storage_repository=mock_repository,
            storage_manager=mock_storage_manager,
        )

    @pytest.fixture
    def service_without_storage_manager(
        self,
        mock_repository: MagicMock,
    ) -> VFSStorageService:
        return VFSStorageService(
            vfs_storage_repository=mock_repository,
            storage_manager=None,
        )

    def _setup_proxy_and_client(
        self,
        mock_storage_manager: MagicMock,
        mock_manager_client: AsyncMock,
    ) -> None:
        """Helper to mock get_proxy_and_volume and get_manager_facing_client."""
        StorageSessionManager.get_proxy_and_volume = MagicMock(return_value=("proxy1", "volume1"))
        mock_storage_manager.get_manager_facing_client.return_value = mock_manager_client

    # =========================================================================
    # GetQuotaScope
    # =========================================================================

    async def test_get_quota_scope(
        self,
        service_with_storage_manager: VFSStorageService,
        mock_storage_manager: MagicMock,
        mock_manager_client: AsyncMock,
    ) -> None:
        """Test valid storage_host_name/quota_scope_id returns usage/limit."""
        self._setup_proxy_and_client(mock_storage_manager, mock_manager_client)
        mock_manager_client.get_quota_scope.return_value = {
            "used_bytes": 1024,
            "limit_bytes": 4096,
        }

        action = GetQuotaScopeAction(
            storage_host_name="proxy1:volume1",
            quota_scope_id="scope-1",
        )
        result = await service_with_storage_manager.get_quota_scope(action)

        assert isinstance(result, GetQuotaScopeActionResult)
        assert result.quota_scope_id == "scope-1"
        assert result.storage_host_name == "proxy1:volume1"
        assert result.usage_bytes == 1024
        assert result.hard_limit_bytes == 4096

    async def test_get_quota_scope_negative_usage_bytes_converted_to_none(
        self,
        service_with_storage_manager: VFSStorageService,
        mock_storage_manager: MagicMock,
        mock_manager_client: AsyncMock,
    ) -> None:
        """Test negative usage_bytes converted to None."""
        self._setup_proxy_and_client(mock_storage_manager, mock_manager_client)
        mock_manager_client.get_quota_scope.return_value = {
            "used_bytes": -1,
            "limit_bytes": 4096,
        }

        action = GetQuotaScopeAction(
            storage_host_name="proxy1:volume1",
            quota_scope_id="scope-1",
        )
        result = await service_with_storage_manager.get_quota_scope(action)

        assert result.usage_bytes is None
        assert result.hard_limit_bytes == 4096

    async def test_get_quota_scope_no_storage_manager_raises_runtime_error(
        self,
        service_without_storage_manager: VFSStorageService,
    ) -> None:
        """Test no storage_manager raises RuntimeError."""
        action = GetQuotaScopeAction(
            storage_host_name="proxy1:volume1",
            quota_scope_id="scope-1",
        )

        with pytest.raises(RuntimeError, match="Storage manager is not configured"):
            await service_without_storage_manager.get_quota_scope(action)

    # =========================================================================
    # SetQuotaScope
    # =========================================================================

    async def test_set_quota_scope(
        self,
        service_with_storage_manager: VFSStorageService,
        mock_storage_manager: MagicMock,
        mock_manager_client: AsyncMock,
    ) -> None:
        """Test hard_limit_bytes updates storage proxy + returns updated state."""
        self._setup_proxy_and_client(mock_storage_manager, mock_manager_client)
        mock_manager_client.update_quota_scope = AsyncMock()
        mock_manager_client.get_quota_scope.return_value = {
            "used_bytes": 512,
            "limit_bytes": 8192,
        }

        action = SetQuotaScopeAction(
            storage_host_name="proxy1:volume1",
            quota_scope_id="scope-1",
            hard_limit_bytes=8192,
        )
        result = await service_with_storage_manager.set_quota_scope(action)

        assert isinstance(result, SetQuotaScopeActionResult)
        assert result.usage_bytes == 512
        assert result.hard_limit_bytes == 8192
        mock_manager_client.update_quota_scope.assert_called_once_with("volume1", "scope-1", 8192)

    async def test_set_quota_scope_negative_usage_bytes_converted_to_none(
        self,
        service_with_storage_manager: VFSStorageService,
        mock_storage_manager: MagicMock,
        mock_manager_client: AsyncMock,
    ) -> None:
        """Test negative usage_bytes converted to None after set."""
        self._setup_proxy_and_client(mock_storage_manager, mock_manager_client)
        mock_manager_client.update_quota_scope = AsyncMock()
        mock_manager_client.get_quota_scope.return_value = {
            "used_bytes": -1,
            "limit_bytes": 8192,
        }

        action = SetQuotaScopeAction(
            storage_host_name="proxy1:volume1",
            quota_scope_id="scope-1",
            hard_limit_bytes=8192,
        )
        result = await service_with_storage_manager.set_quota_scope(action)

        assert result.usage_bytes is None
        assert result.hard_limit_bytes == 8192

    # =========================================================================
    # UnsetQuotaScope
    # =========================================================================

    async def test_unset_quota_scope(
        self,
        service_with_storage_manager: VFSStorageService,
        mock_storage_manager: MagicMock,
        mock_manager_client: AsyncMock,
    ) -> None:
        """Test quota deletion returns quota_scope_id."""
        self._setup_proxy_and_client(mock_storage_manager, mock_manager_client)
        mock_manager_client.delete_quota_scope_quota = AsyncMock()

        action = UnsetQuotaScopeAction(
            storage_host_name="proxy1:volume1",
            quota_scope_id="scope-1",
        )
        result = await service_with_storage_manager.unset_quota_scope(action)

        assert isinstance(result, UnsetQuotaScopeActionResult)
        assert result.quota_scope_id == "scope-1"
        assert result.storage_host_name == "proxy1:volume1"
        mock_manager_client.delete_quota_scope_quota.assert_called_once_with("volume1", "scope-1")

    async def test_unset_quota_scope_no_storage_manager_raises_runtime_error(
        self,
        service_without_storage_manager: VFSStorageService,
    ) -> None:
        """Test no storage_manager raises RuntimeError."""
        action = UnsetQuotaScopeAction(
            storage_host_name="proxy1:volume1",
            quota_scope_id="scope-1",
        )

        with pytest.raises(RuntimeError, match="Storage manager is not configured"):
            await service_without_storage_manager.unset_quota_scope(action)

    # =========================================================================
    # SearchQuotaScopes
    # =========================================================================

    async def test_search_quota_scopes(
        self,
        service_with_storage_manager: VFSStorageService,
        mock_storage_manager: MagicMock,
        mock_manager_client: AsyncMock,
    ) -> None:
        """Test aggregates volumes across all storage hosts."""
        self._setup_proxy_and_client(mock_storage_manager, mock_manager_client)
        mock_storage_manager.get_all_volumes = AsyncMock(
            return_value=[
                ("proxy1:volume1", {"some": "info"}),
                ("proxy1:volume2", {"other": "info"}),
            ]
        )
        mock_manager_client.get_quota_scope.side_effect = [
            {"used_bytes": 100, "limit_bytes": 1000},
            {"used_bytes": 200, "limit_bytes": 2000},
        ]

        action = SearchQuotaScopesAction()
        result = await service_with_storage_manager.search_quota_scopes(action)

        assert isinstance(result, SearchQuotaScopesActionResult)
        assert len(result.quota_scopes) == 2
        assert result.quota_scopes[0].storage_host_name == "proxy1:volume1"
        assert result.quota_scopes[0].usage_bytes == 100
        assert result.quota_scopes[0].hard_limit_bytes == 1000
        assert result.quota_scopes[1].storage_host_name == "proxy1:volume2"
        assert result.quota_scopes[1].usage_bytes == 200
        assert result.quota_scopes[1].hard_limit_bytes == 2000

    async def test_search_quota_scopes_error_handled(
        self,
        service_with_storage_manager: VFSStorageService,
        mock_storage_manager: MagicMock,
        mock_manager_client: AsyncMock,
    ) -> None:
        """Test storage proxy error handled via try/except — errored volumes skipped."""
        self._setup_proxy_and_client(mock_storage_manager, mock_manager_client)
        mock_storage_manager.get_all_volumes = AsyncMock(
            return_value=[
                ("proxy1:volume1", {}),
                ("proxy1:volume2", {}),
            ]
        )
        mock_manager_client.get_quota_scope.side_effect = [
            Exception("Connection refused"),
            {"used_bytes": 200, "limit_bytes": 2000},
        ]

        action = SearchQuotaScopesAction()
        result = await service_with_storage_manager.search_quota_scopes(action)

        assert len(result.quota_scopes) == 1
        assert result.quota_scopes[0].storage_host_name == "proxy1:volume2"

    async def test_search_quota_scopes_negative_usage_bytes_converted_to_none(
        self,
        service_with_storage_manager: VFSStorageService,
        mock_storage_manager: MagicMock,
        mock_manager_client: AsyncMock,
    ) -> None:
        """Test negative usage_bytes converted to None in search results."""
        self._setup_proxy_and_client(mock_storage_manager, mock_manager_client)
        mock_storage_manager.get_all_volumes = AsyncMock(return_value=[("proxy1:volume1", {})])
        mock_manager_client.get_quota_scope.return_value = {
            "used_bytes": -1,
            "limit_bytes": 5000,
        }

        action = SearchQuotaScopesAction()
        result = await service_with_storage_manager.search_quota_scopes(action)

        assert len(result.quota_scopes) == 1
        assert result.quota_scopes[0].usage_bytes is None
        assert result.quota_scopes[0].hard_limit_bytes == 5000

    async def test_search_quota_scopes_no_storage_manager_raises_runtime_error(
        self,
        service_without_storage_manager: VFSStorageService,
    ) -> None:
        """Test no storage_manager raises RuntimeError."""
        action = SearchQuotaScopesAction()

        with pytest.raises(RuntimeError, match="Storage manager is not configured"):
            await service_without_storage_manager.search_quota_scopes(action)
