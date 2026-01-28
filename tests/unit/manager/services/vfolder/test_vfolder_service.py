"""
Tests for VFolderService.purge() functionality.
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
)
from ai.backend.manager.errors.storage import VFolderFilterStatusFailed, VFolderNotFound
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.repositories.base.rbac.entity_purger import RBACEntityPurger
from ai.backend.manager.repositories.vfolder.purgers import VFolderPurgerSpec
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.services.vfolder.actions.base import (
    PurgeVFolderAction,
    PurgeVFolderActionResult,
)
from ai.backend.manager.services.vfolder.services.vfolder import VFolderService


class TestVFolderServicePurge:
    """Tests for VFolderService.purge() method.

    Note: Validation logic (not found, invalid status) is tested in repository tests.
    Service tests verify that the repository method is called correctly and
    exceptions are propagated.
    """

    @pytest.fixture
    def mock_vfolder_repository(self) -> MagicMock:
        return MagicMock(spec=VfolderRepository)

    @pytest.fixture
    def vfolder_service(self, mock_vfolder_repository: MagicMock) -> VFolderService:
        return VFolderService(
            config_provider=MagicMock(),
            storage_manager=MagicMock(),
            background_task_manager=MagicMock(),
            vfolder_repository=mock_vfolder_repository,
            user_repository=MagicMock(),
        )

    @pytest.fixture
    def sample_vfolder_uuid(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def sample_purger(self, sample_vfolder_uuid: uuid.UUID) -> RBACEntityPurger[VFolderRow]:
        return RBACEntityPurger(
            row_class=VFolderRow,
            pk_value=sample_vfolder_uuid,
            spec=VFolderPurgerSpec(vfolder_id=sample_vfolder_uuid),
        )

    @pytest.fixture
    def sample_action(self, sample_purger: RBACEntityPurger[VFolderRow]) -> PurgeVFolderAction:
        return PurgeVFolderAction(purger=sample_purger)

    @pytest.fixture
    def sample_vfolder_data(self, sample_vfolder_uuid: uuid.UUID) -> VFolderData:
        """Create mock VFolderData with DELETE_COMPLETE status."""
        return VFolderData(
            id=sample_vfolder_uuid,
            name="test-vfolder",
            host="local:volume1",
            domain_name="default",
            quota_scope_id=QuotaScopeID.parse(f"user:{sample_vfolder_uuid}"),
            usage_mode=VFolderUsageMode.GENERAL,
            permission=VFolderMountPermission.READ_WRITE,
            max_files=0,
            max_size=None,
            num_files=0,
            cur_size=0,
            created_at=datetime.now(tz=UTC),
            last_used=None,
            creator="test@example.com",
            unmanaged_path=None,
            ownership_type=VFolderOwnershipType.USER,
            user=sample_vfolder_uuid,
            group=None,
            cloneable=False,
            status=VFolderOperationStatus.DELETE_COMPLETE,
        )

    async def test_purge_vfolder_success(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        sample_vfolder_uuid: uuid.UUID,
        sample_action: PurgeVFolderAction,
        sample_vfolder_data: VFolderData,
    ) -> None:
        """Test successful purge of vfolder."""
        mock_vfolder_repository.purge_vfolder = AsyncMock(return_value=sample_vfolder_data)

        result = await vfolder_service.purge(sample_action)

        assert isinstance(result, PurgeVFolderActionResult)
        assert result.vfolder_uuid == sample_vfolder_uuid
        mock_vfolder_repository.purge_vfolder.assert_called_once_with(sample_action.purger)

    async def test_purge_vfolder_not_found_propagates(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        sample_vfolder_uuid: uuid.UUID,
        sample_action: PurgeVFolderAction,
    ) -> None:
        """Test that VFolderNotFound from repository is propagated."""
        mock_vfolder_repository.purge_vfolder = AsyncMock(
            side_effect=VFolderNotFound(extra_data=str(sample_vfolder_uuid))
        )

        with pytest.raises(VFolderNotFound):
            await vfolder_service.purge(sample_action)

        mock_vfolder_repository.purge_vfolder.assert_called_once_with(sample_action.purger)

    async def test_purge_vfolder_invalid_status_propagates(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        sample_action: PurgeVFolderAction,
    ) -> None:
        """Test that VFolderFilterStatusFailed from repository is propagated."""
        mock_vfolder_repository.purge_vfolder = AsyncMock(side_effect=VFolderFilterStatusFailed)

        with pytest.raises(VFolderFilterStatusFailed):
            await vfolder_service.purge(sample_action)

        mock_vfolder_repository.purge_vfolder.assert_called_once_with(sample_action.purger)
