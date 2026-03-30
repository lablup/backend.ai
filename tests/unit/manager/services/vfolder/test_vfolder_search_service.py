"""
Tests for VFolderService.admin_search_vfolders() functionality.
Verifies that service methods correctly delegate to the repository and map results.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.types import QuotaScopeID, VFolderUsageMode
from ai.backend.manager.data.vfolder.types import (
    VFolderData,
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderSearchResult,
)
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.services.vfolder.actions.admin_search_vfolders import (
    AdminSearchVFoldersAction,
    AdminSearchVFoldersActionResult,
)
from ai.backend.manager.services.vfolder.services.vfolder import VFolderService


class TestVFolderServiceAdminSearchVFolders:
    """Tests for VFolderService.admin_search_vfolders()"""

    @pytest.fixture
    def mock_vfolder_repository(self) -> MagicMock:
        return MagicMock(spec=VfolderRepository)

    @pytest.fixture
    def vfolder_service(self, mock_vfolder_repository: MagicMock) -> VFolderService:
        return VFolderService(
            config_provider=MagicMock(),
            etcd=MagicMock(),
            storage_manager=MagicMock(),
            background_task_manager=MagicMock(),
            vfolder_repository=mock_vfolder_repository,
            user_repository=MagicMock(),
            valkey_stat_client=MagicMock(),
        )

    @pytest.fixture
    def user_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def vfolder_1(self, user_id: uuid.UUID) -> VFolderData:
        return VFolderData(
            id=uuid.uuid4(),
            name="vfolder-1",
            host="local:volume1",
            domain_name="default",
            quota_scope_id=QuotaScopeID.parse(f"user:{user_id}"),
            usage_mode=VFolderUsageMode.GENERAL,
            permission=VFolderMountPermission.READ_WRITE,
            max_files=0,
            max_size=None,
            num_files=0,
            cur_size=0,
            created_at=datetime(2025, 1, 1, tzinfo=UTC),
            last_used=None,
            creator="test@example.com",
            unmanaged_path=None,
            ownership_type=VFolderOwnershipType.USER,
            user=user_id,
            group=None,
            cloneable=False,
            status=VFolderOperationStatus.READY,
        )

    @pytest.fixture
    def vfolder_2(self, user_id: uuid.UUID) -> VFolderData:
        return VFolderData(
            id=uuid.uuid4(),
            name="vfolder-2",
            host="local:volume1",
            domain_name="default",
            quota_scope_id=QuotaScopeID.parse(f"user:{user_id}"),
            usage_mode=VFolderUsageMode.GENERAL,
            permission=VFolderMountPermission.READ_WRITE,
            max_files=0,
            max_size=None,
            num_files=0,
            cur_size=0,
            created_at=datetime(2025, 1, 1, tzinfo=UTC),
            last_used=None,
            creator="test@example.com",
            unmanaged_path=None,
            ownership_type=VFolderOwnershipType.USER,
            user=user_id,
            group=None,
            cloneable=False,
            status=VFolderOperationStatus.READY,
        )

    async def test_admin_search_vfolders_delegates_to_repository(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        vfolder_1: VFolderData,
        vfolder_2: VFolderData,
    ) -> None:
        """admin_search_vfolders delegates to repository and maps result correctly."""
        mock_vfolder_repository.search_vfolders = AsyncMock(
            return_value=VFolderSearchResult(
                items=[vfolder_1, vfolder_2],
                total_count=2,
                has_next_page=False,
                has_previous_page=False,
            )
        )
        querier = BatchQuerier(pagination=OffsetPagination(limit=10, offset=0))
        action = AdminSearchVFoldersAction(querier=querier)

        result = await vfolder_service.admin_search_vfolders(action)

        assert isinstance(result, AdminSearchVFoldersActionResult)
        assert result.data == [vfolder_1, vfolder_2]
        assert result.total_count == 2
        assert result.has_next_page is False
        assert result.has_previous_page is False
        mock_vfolder_repository.search_vfolders.assert_called_once_with(querier=querier)
