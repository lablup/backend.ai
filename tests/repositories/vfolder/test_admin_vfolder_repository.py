import uuid
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.common.types import QuotaScopeID, VFolderUsageMode
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.errors.storage import VFolderNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import (
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderPermission,
    VFolderRow,
)
from ai.backend.manager.repositories.vfolder.admin_repository import AdminVfolderRepository


@pytest.fixture
def mock_db_engine():
    """Mock database engine for testing"""
    engine = MagicMock(spec=ExtendedAsyncSAEngine)
    return engine


@pytest.fixture
def admin_vfolder_repository(mock_db_engine):
    """Create AdminVfolderRepository instance with mocked dependencies"""
    return AdminVfolderRepository(db=mock_db_engine)


@pytest.fixture
def sample_vfolder_row():
    """Sample VFolderRow for testing"""
    vfolder_row = MagicMock(spec=VFolderRow)
    vfolder_row.id = uuid.uuid4()
    vfolder_row.name = "admin-test-vfolder"
    vfolder_row.domain_name = "default"
    vfolder_row.quota_scope_id = QuotaScopeID("admin-12345")
    vfolder_row.usage_mode = VFolderUsageMode.GENERAL
    vfolder_row.permission = VFolderPermission.READ_WRITE
    vfolder_row.last_used = None
    vfolder_row.host = "storage1"
    vfolder_row.creator = "admin@example.com"
    vfolder_row.ownership_type = VFolderOwnershipType.USER
    vfolder_row.user = uuid.uuid4()
    vfolder_row.group = None
    vfolder_row.unmanaged_path = None
    vfolder_row.cloneable = False
    vfolder_row.status = VFolderOperationStatus.READY
    vfolder_row.cur_size = 2048
    return vfolder_row


class TestAdminVfolderRepository:
    """Test cases for AdminVfolderRepository"""

    @pytest.mark.asyncio
    async def test_get_by_id_force_success(
        self, admin_vfolder_repository, mock_db_engine, sample_vfolder_row
    ):
        """Test admin force retrieval of vfolder without validation"""
        vfolder_id = sample_vfolder_row.id

        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Mock _get_vfolder_by_id to return sample vfolder
        with patch.object(
            admin_vfolder_repository, "_get_vfolder_by_id", return_value=sample_vfolder_row
        ):
            # Mock _vfolder_row_to_data
            expected_data = VFolderData(
                id=vfolder_id,
                name="admin-test-vfolder",
                domain_name="default",
                quota_scope_id=QuotaScopeID("admin-12345"),
                usage_mode=VFolderUsageMode.GENERAL,
                permission=VFolderPermission.READ_WRITE,
                last_used=None,
                host="storage1",
                creator="admin@example.com",
                ownership_type=VFolderOwnershipType.USER,
                user=sample_vfolder_row.user,
                group=None,
                unmanaged_path=None,
                cloneable=False,
                status=VFolderOperationStatus.READY,
                cur_size=2048,
            )
            with patch.object(
                admin_vfolder_repository, "_vfolder_row_to_data", return_value=expected_data
            ):
                result = await admin_vfolder_repository.get_by_id_force(vfolder_id)

                assert result == expected_data
                assert result.id == vfolder_id
                assert result.name == "admin-test-vfolder"

    @pytest.mark.asyncio
    async def test_get_by_id_force_not_found(self, admin_vfolder_repository, mock_db_engine):
        """Test admin force retrieval when vfolder doesn't exist"""
        vfolder_id = uuid.uuid4()

        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Mock _get_vfolder_by_id to return None
        with patch.object(admin_vfolder_repository, "_get_vfolder_by_id", return_value=None):
            with pytest.raises(VFolderNotFound):
                await admin_vfolder_repository.get_by_id_force(vfolder_id)

    @pytest.mark.asyncio
    async def test_update_vfolder_status_force(self, admin_vfolder_repository, mock_db_engine):
        """Test admin force update of vfolder status"""
        vfolder_ids = [uuid.uuid4(), uuid.uuid4()]
        new_status = VFolderOperationStatus.DELETE_PENDING

        # Mock update_vfolder_status function
        with patch(
            "ai.backend.manager.repositories.vfolder.admin_repository.update_vfolder_status"
        ) as mock_update:
            await admin_vfolder_repository.update_vfolder_status_force(vfolder_ids, new_status)

            mock_update.assert_called_once_with(mock_db_engine, vfolder_ids, new_status)

    @pytest.mark.asyncio
    async def test_delete_vfolder_force_success(
        self, admin_vfolder_repository, mock_db_engine, sample_vfolder_row
    ):
        """Test admin force deletion of vfolder"""
        vfolder_id = sample_vfolder_row.id

        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Mock _get_vfolder_by_id to return sample vfolder
        with patch.object(
            admin_vfolder_repository, "_get_vfolder_by_id", return_value=sample_vfolder_row
        ):
            # Mock _vfolder_row_to_data
            expected_data = VFolderData(
                id=vfolder_id,
                name="admin-test-vfolder",
                domain_name="default",
                quota_scope_id=QuotaScopeID("admin-12345"),
                usage_mode=VFolderUsageMode.GENERAL,
                permission=VFolderPermission.READ_WRITE,
                last_used=None,
                host="storage1",
                creator="admin@example.com",
                ownership_type=VFolderOwnershipType.USER,
                user=sample_vfolder_row.user,
                group=None,
                unmanaged_path=None,
                cloneable=False,
                status=VFolderOperationStatus.READY,
                cur_size=2048,
            )
            with patch.object(
                admin_vfolder_repository, "_vfolder_row_to_data", return_value=expected_data
            ):
                result = await admin_vfolder_repository.delete_vfolder_force(vfolder_id)

                assert result == expected_data
                mock_session.delete.assert_called_once_with(sample_vfolder_row)

    @pytest.mark.asyncio
    async def test_delete_vfolder_force_not_found(self, admin_vfolder_repository, mock_db_engine):
        """Test admin force deletion when vfolder doesn't exist"""
        vfolder_id = uuid.uuid4()

        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Mock _get_vfolder_by_id to return None
        with patch.object(admin_vfolder_repository, "_get_vfolder_by_id", return_value=None):
            with pytest.raises(VFolderNotFound):
                await admin_vfolder_repository.delete_vfolder_force(vfolder_id)

    @pytest.mark.asyncio
    async def test_update_vfolder_attribute_force_success(
        self, admin_vfolder_repository, mock_db_engine, sample_vfolder_row
    ):
        """Test admin force update of vfolder attributes"""
        vfolder_id = sample_vfolder_row.id
        field_updates = {
            "name": "admin-updated-name",
            "cloneable": True,
            "permission": VFolderPermission.RW_DELETE,
        }

        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Mock the vfolder with updated attributes
        updated_vfolder_row = MagicMock(spec=VFolderRow)
        updated_vfolder_row.id = vfolder_id
        updated_vfolder_row.name = "admin-updated-name"
        updated_vfolder_row.cloneable = True
        updated_vfolder_row.permission = VFolderPermission.RW_DELETE

        # First call returns original, second call would reflect updates
        with patch.object(
            admin_vfolder_repository, "_get_vfolder_by_id", return_value=sample_vfolder_row
        ):
            # Mock the attribute updates
            for key, value in field_updates.items():
                setattr(sample_vfolder_row, key, value)

            expected_data = VFolderData(
                id=vfolder_id,
                name="admin-updated-name",
                domain_name="default",
                quota_scope_id=QuotaScopeID("admin-12345"),
                usage_mode=VFolderUsageMode.GENERAL,
                permission=VFolderPermission.RW_DELETE,
                last_used=None,
                host="storage1",
                creator="admin@example.com",
                ownership_type=VFolderOwnershipType.USER,
                user=sample_vfolder_row.user,
                group=None,
                unmanaged_path=None,
                cloneable=True,
                status=VFolderOperationStatus.READY,
                cur_size=2048,
            )

            with patch.object(
                admin_vfolder_repository, "_vfolder_row_to_data", return_value=expected_data
            ):
                result = await admin_vfolder_repository.update_vfolder_attribute_force(
                    vfolder_id, field_updates
                )

                assert result.name == "admin-updated-name"
                assert result.cloneable is True
                assert result.permission == VFolderPermission.RW_DELETE
                mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_vfolder_attribute_force_not_found(
        self, admin_vfolder_repository, mock_db_engine
    ):
        """Test admin force update when vfolder doesn't exist"""
        vfolder_id = uuid.uuid4()
        field_updates = {"name": "admin-updated-name"}

        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Mock _get_vfolder_by_id to return None
        with patch.object(admin_vfolder_repository, "_get_vfolder_by_id", return_value=None):
            with pytest.raises(VFolderNotFound):
                await admin_vfolder_repository.update_vfolder_attribute_force(
                    vfolder_id, field_updates
                )

    @pytest.mark.asyncio
    async def test_move_vfolders_to_trash_force(self, admin_vfolder_repository, mock_db_engine):
        """Test admin force move multiple vfolders to trash"""
        vfolder_id1 = uuid.uuid4()
        vfolder_id2 = uuid.uuid4()
        vfolder_ids = [vfolder_id1, vfolder_id2]

        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Create mock vfolder rows
        vfolder_row1 = MagicMock(spec=VFolderRow)
        vfolder_row1.id = vfolder_id1
        vfolder_row1.name = "vfolder1"
        vfolder_row1.status = VFolderOperationStatus.READY

        vfolder_row2 = MagicMock(spec=VFolderRow)
        vfolder_row2.id = vfolder_id2
        vfolder_row2.name = "vfolder2"
        vfolder_row2.status = VFolderOperationStatus.READY

        # Mock _get_vfolder_by_id to return vfolders in sequence
        side_effects = [vfolder_row1, vfolder_row2]
        with patch.object(admin_vfolder_repository, "_get_vfolder_by_id", side_effect=side_effects):
            # Mock _vfolder_row_to_data
            def mock_row_to_data(row):
                return VFolderData(
                    id=row.id,
                    name=row.name,
                    domain_name="default",
                    quota_scope_id=QuotaScopeID("12345"),
                    usage_mode=VFolderUsageMode.GENERAL,
                    permission=VFolderPermission.READ_WRITE,
                    last_used=None,
                    host="storage1",
                    creator="admin@example.com",
                    ownership_type=VFolderOwnershipType.USER,
                    user=uuid.uuid4(),
                    group=None,
                    unmanaged_path=None,
                    cloneable=False,
                    status=VFolderOperationStatus.DELETE_PENDING,
                    cur_size=1024,
                )

            with patch.object(
                admin_vfolder_repository, "_vfolder_row_to_data", side_effect=mock_row_to_data
            ):
                # Note: The actual implementation seems incomplete in the original file
                # This test assumes the method will be completed to return the affected vfolders
                result = await admin_vfolder_repository.move_vfolders_to_trash_force(vfolder_ids)

                # Verify the vfolders were retrieved
                assert admin_vfolder_repository._get_vfolder_by_id.call_count == 2


class TestAdminVfolderRepositoryIntegration:
    """Integration tests for admin vfolder repository operations"""

    @pytest.mark.asyncio
    async def test_admin_workflow_create_update_delete(
        self, admin_vfolder_repository, mock_db_engine
    ):
        """Test a complete admin workflow: get, update, and delete"""
        vfolder_id = uuid.uuid4()

        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Step 1: Get vfolder
        vfolder_row = MagicMock(spec=VFolderRow)
        vfolder_row.id = vfolder_id
        vfolder_row.name = "test-vfolder"
        vfolder_row.status = VFolderOperationStatus.READY
        vfolder_row.cloneable = False

        with patch.object(admin_vfolder_repository, "_get_vfolder_by_id", return_value=vfolder_row):
            vfolder_data = VFolderData(
                id=vfolder_id,
                name="test-vfolder",
                domain_name="default",
                quota_scope_id=QuotaScopeID("12345"),
                usage_mode=VFolderUsageMode.GENERAL,
                permission=VFolderPermission.READ_WRITE,
                last_used=None,
                host="storage1",
                creator="admin@example.com",
                ownership_type=VFolderOwnershipType.USER,
                user=uuid.uuid4(),
                group=None,
                unmanaged_path=None,
                cloneable=False,
                status=VFolderOperationStatus.READY,
                cur_size=1024,
            )

            with patch.object(
                admin_vfolder_repository, "_vfolder_row_to_data", return_value=vfolder_data
            ):
                # Get vfolder
                result = await admin_vfolder_repository.get_by_id_force(vfolder_id)
                assert result.name == "test-vfolder"

                # Step 2: Update vfolder
                field_updates = {"name": "updated-vfolder", "cloneable": True}

                # Update the mock to reflect changes
                vfolder_row.name = "updated-vfolder"
                vfolder_row.cloneable = True
                updated_data = VFolderData(
                    id=vfolder_id,
                    name="updated-vfolder",
                    domain_name="default",
                    quota_scope_id=QuotaScopeID("12345"),
                    usage_mode=VFolderUsageMode.GENERAL,
                    permission=VFolderPermission.READ_WRITE,
                    last_used=None,
                    host="storage1",
                    creator="admin@example.com",
                    ownership_type=VFolderOwnershipType.USER,
                    user=vfolder_data.user,
                    group=None,
                    unmanaged_path=None,
                    cloneable=True,
                    status=VFolderOperationStatus.READY,
                    cur_size=1024,
                )

                with patch.object(
                    admin_vfolder_repository, "_vfolder_row_to_data", return_value=updated_data
                ):
                    updated_result = await admin_vfolder_repository.update_vfolder_attribute_force(
                        vfolder_id, field_updates
                    )
                    assert updated_result.name == "updated-vfolder"
                    assert updated_result.cloneable is True

                # Step 3: Delete vfolder
                deleted_result = await admin_vfolder_repository.delete_vfolder_force(vfolder_id)
                mock_session.delete.assert_called_once()
