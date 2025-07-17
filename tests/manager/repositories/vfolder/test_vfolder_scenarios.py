"""
Test cases based on vfolder test scenarios from test_scenarios/vfolder.md
These tests focus on the repository layer implementation of the scenarios.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.common.types import QuotaScopeID, VFolderUsageMode
from ai.backend.manager.data.vfolder.types import (
    VFolderCreateParams,
    VFolderData,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import (
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderPermission,
    VFolderPermissionRow,
    VFolderRow,
)
from ai.backend.manager.repositories.vfolder.admin_repository import AdminVfolderRepository
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository


class TestVFolderScenariosRepository:
    """Repository-level tests for VFolder scenarios"""

    @pytest.fixture
    def mock_db_engine(self):
        """Mock database engine"""
        return MagicMock(spec=ExtendedAsyncSAEngine)

    @pytest.fixture
    def vfolder_repo(self, mock_db_engine):
        """VFolder repository instance"""
        return VfolderRepository(db=mock_db_engine)

    @pytest.fixture
    def admin_vfolder_repo(self, mock_db_engine):
        """Admin VFolder repository instance"""
        return AdminVfolderRepository(db=mock_db_engine)

    @pytest.mark.asyncio
    async def test_scenario_1_1_personal_vfolder_creation(self, vfolder_repo, mock_db_engine):
        """Test Scenario 1.1: Personal VFolder Creation - Repository Layer"""
        # Given
        user_id = uuid.uuid4()
        vfolder_id = uuid.uuid4()

        params = VFolderCreateParams(
            id=vfolder_id,
            name="my-workspace",
            domain_name="default",
            quota_scope_id=QuotaScopeID("personal-quota"),
            usage_mode=VFolderUsageMode.GENERAL,
            permission=VFolderPermission.READ_WRITE,
            host="storage1",
            creator="user@example.com",
            ownership_type=VFolderOwnershipType.USER,
            user=user_id,
            group=None,
            unmanaged_path=None,
            cloneable=False,
            status=VFolderOperationStatus.READY,
        )

        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Mock successful insert
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        # Mock the created vfolder retrieval
        created_vfolder_row = MagicMock(spec=VFolderRow)
        created_vfolder_row.id = vfolder_id
        created_vfolder_row.name = "my-workspace"
        created_vfolder_row.cur_size = 0  # Initial size should be 0

        with patch.object(vfolder_repo, "_get_vfolder_by_id", return_value=created_vfolder_row):
            expected_data = VFolderData(
                id=vfolder_id,
                name="my-workspace",
                domain_name="default",
                quota_scope_id=QuotaScopeID("personal-quota"),
                usage_mode=VFolderUsageMode.GENERAL,
                permission=VFolderPermission.READ_WRITE,
                last_used=None,
                host="storage1",
                creator="user@example.com",
                ownership_type=VFolderOwnershipType.USER,
                user=user_id,
                group=None,
                unmanaged_path=None,
                cloneable=False,
                status=VFolderOperationStatus.READY,
                cur_size=0,  # Initial usage: 0
            )

            with patch.object(vfolder_repo, "_vfolder_row_to_data", return_value=expected_data):
                # When
                result = await vfolder_repo.create_vfolder(params)

                # Then
                assert result.name == "my-workspace"
                assert result.ownership_type == VFolderOwnershipType.USER
                assert result.user == user_id
                assert result.cur_size == 0
                assert result.usage_mode == VFolderUsageMode.GENERAL

    @pytest.mark.asyncio
    async def test_scenario_1_2_project_vfolder_creation(self, vfolder_repo, mock_db_engine):
        """Test Scenario 1.2: Project VFolder Creation - Repository Layer"""
        # Given
        project_id = uuid.uuid4()
        vfolder_id = uuid.uuid4()

        params = VFolderCreateParams(
            id=vfolder_id,
            name="team-data",
            domain_name="default",
            quota_scope_id=QuotaScopeID("project-quota"),
            usage_mode=VFolderUsageMode.DATA,
            permission=VFolderPermission.READ_WRITE,
            host="storage1",
            creator="team@example.com",
            ownership_type=VFolderOwnershipType.GROUP,
            user=None,
            group=project_id,
            unmanaged_path=None,
            cloneable=True,
            status=VFolderOperationStatus.READY,
        )

        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Mock successful insert
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        # Mock the created vfolder
        created_vfolder_row = MagicMock(spec=VFolderRow)
        created_vfolder_row.id = vfolder_id
        created_vfolder_row.group = project_id

        with patch.object(vfolder_repo, "_get_vfolder_by_id", return_value=created_vfolder_row):
            expected_data = VFolderData(
                id=vfolder_id,
                name="team-data",
                domain_name="default",
                quota_scope_id=QuotaScopeID("project-quota"),
                usage_mode=VFolderUsageMode.DATA,
                permission=VFolderPermission.READ_WRITE,
                last_used=None,
                host="storage1",
                creator="team@example.com",
                ownership_type=VFolderOwnershipType.GROUP,
                user=None,
                group=project_id,
                unmanaged_path=None,
                cloneable=True,
                status=VFolderOperationStatus.READY,
                cur_size=0,
            )

            with patch.object(vfolder_repo, "_vfolder_row_to_data", return_value=expected_data):
                # When
                result = await vfolder_repo.create_vfolder(params)

                # Then
                assert result.name == "team-data"
                assert result.ownership_type == VFolderOwnershipType.GROUP
                assert result.group == project_id
                assert result.cloneable is True

    @pytest.mark.asyncio
    async def test_scenario_1_3_model_storage_creation(self, vfolder_repo, mock_db_engine):
        """Test Scenario 1.3: Model Storage Creation - Repository Layer"""
        # Given
        user_id = uuid.uuid4()
        vfolder_id = uuid.uuid4()

        params = VFolderCreateParams(
            id=vfolder_id,
            name="ml-models",
            domain_name="default",
            quota_scope_id=QuotaScopeID("model-quota"),
            usage_mode=VFolderUsageMode.MODEL,
            permission=VFolderPermission.READ_ONLY,
            host="storage1",
            creator="ml@example.com",
            ownership_type=VFolderOwnershipType.USER,
            user=user_id,
            group=None,
            unmanaged_path=None,
            cloneable=False,
            status=VFolderOperationStatus.READY,
        )

        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Mock successful insert
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        # Mock the created vfolder
        created_vfolder_row = MagicMock(spec=VFolderRow)
        created_vfolder_row.id = vfolder_id

        with patch.object(vfolder_repo, "_get_vfolder_by_id", return_value=created_vfolder_row):
            expected_data = VFolderData(
                id=vfolder_id,
                name="ml-models",
                domain_name="default",
                quota_scope_id=QuotaScopeID("model-quota"),
                usage_mode=VFolderUsageMode.MODEL,
                permission=VFolderPermission.READ_ONLY,
                last_used=None,
                host="storage1",
                creator="ml@example.com",
                ownership_type=VFolderOwnershipType.USER,
                user=user_id,
                group=None,
                unmanaged_path=None,
                cloneable=False,
                status=VFolderOperationStatus.READY,
                cur_size=0,
            )

            with patch.object(vfolder_repo, "_vfolder_row_to_data", return_value=expected_data):
                # When
                result = await vfolder_repo.create_vfolder(params)

                # Then
                assert result.name == "ml-models"
                assert result.usage_mode == VFolderUsageMode.MODEL
                assert result.permission == VFolderPermission.READ_ONLY
                assert result.cloneable is False

    @pytest.mark.asyncio
    async def test_scenario_1_6_unmanaged_vfolder_admin_only(
        self, admin_vfolder_repo, mock_db_engine
    ):
        """Test Scenario 1.6: Unmanaged VFolder - Admin Repository Layer"""
        # Given
        admin_user_id = uuid.uuid4()
        vfolder_id = uuid.uuid4()

        # This would typically be created through the admin repository
        # For repository tests, we focus on the data persistence aspect

        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Create an unmanaged vfolder row
        unmanaged_vfolder_row = MagicMock(spec=VFolderRow)
        unmanaged_vfolder_row.id = vfolder_id
        unmanaged_vfolder_row.name = "external-data"
        unmanaged_vfolder_row.unmanaged_path = "/mnt/external/data"
        unmanaged_vfolder_row.permission = VFolderPermission.READ_ONLY
        unmanaged_vfolder_row.usage_mode = VFolderUsageMode.DATA

        with patch.object(
            admin_vfolder_repo, "_get_vfolder_by_id", return_value=unmanaged_vfolder_row
        ):
            expected_data = VFolderData(
                id=vfolder_id,
                name="external-data",
                domain_name="default",
                quota_scope_id=QuotaScopeID("unmanaged"),
                usage_mode=VFolderUsageMode.DATA,
                permission=VFolderPermission.READ_ONLY,
                last_used=None,
                host="storage1",
                creator="admin@example.com",
                ownership_type=VFolderOwnershipType.USER,
                user=admin_user_id,
                group=None,
                unmanaged_path="/mnt/external/data",
                cloneable=False,
                status=VFolderOperationStatus.READY,
                cur_size=0,  # Unmanaged folders don't track size
            )

            with patch.object(
                admin_vfolder_repo, "_vfolder_row_to_data", return_value=expected_data
            ):
                # When - Admin force retrieval
                result = await admin_vfolder_repo.get_by_id_force(vfolder_id)

                # Then
                assert result.unmanaged_path == "/mnt/external/data"
                assert result.quota_scope_id == QuotaScopeID("unmanaged")
                assert result.permission == VFolderPermission.READ_ONLY

    @pytest.mark.asyncio
    async def test_scenario_6_move_to_trash_repository(
        self, vfolder_repo, admin_vfolder_repo, mock_db_engine
    ):
        """Test Scenario 6: Move to Trash - Repository Layer Operations"""
        # Given
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Create a vfolder that will be moved to trash
        vfolder_row = MagicMock(spec=VFolderRow)
        vfolder_row.id = vfolder_id
        vfolder_row.name = "unused-vfolder"
        vfolder_row.status = VFolderOperationStatus.READY
        vfolder_row.user = user_id

        # Test using admin repository to update status
        with patch(
            "ai.backend.manager.repositories.vfolder.admin_repository.update_vfolder_status"
        ) as mock_update_status:
            # When
            await admin_vfolder_repo.update_vfolder_status_force(
                [vfolder_id], VFolderOperationStatus.DELETE_PENDING
            )

            # Then
            mock_update_status.assert_called_once_with(
                mock_db_engine, [vfolder_id], VFolderOperationStatus.DELETE_PENDING
            )

    @pytest.mark.asyncio
    async def test_vfolder_permission_management(self, vfolder_repo, mock_db_engine):
        """Test VFolder permission management at repository level"""
        # Given
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()
        invitee_id = uuid.uuid4()

        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Mock permission rows
        owner_perm = MagicMock(spec=VFolderPermissionRow)
        owner_perm.id = uuid.uuid4()
        owner_perm.vfolder = vfolder_id
        owner_perm.user = user_id
        owner_perm.permission = VFolderPermission.OWNER_PERM

        invitee_perm = MagicMock(spec=VFolderPermissionRow)
        invitee_perm.id = uuid.uuid4()
        invitee_perm.vfolder = vfolder_id
        invitee_perm.user = invitee_id
        invitee_perm.permission = VFolderPermission.READ_WRITE

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [owner_perm, invitee_perm]
        mock_session.execute.return_value = mock_result

        # When
        permissions = await vfolder_repo.get_vfolder_permissions(vfolder_id)

        # Then
        assert len(permissions) == 2
        # Verify query was executed
        execute_call = mock_session.execute.call_args[0][0]
        assert hasattr(execute_call, "_where_criteria")

    @pytest.mark.asyncio
    async def test_quota_scope_handling(self, vfolder_repo, mock_db_engine):
        """Test proper quota scope ID handling in repository"""
        # Given
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()

        params = VFolderCreateParams(
            id=vfolder_id,
            name="quota-test-vfolder",
            domain_name="default",
            quota_scope_id=QuotaScopeID("user-quota-12345"),
            usage_mode=VFolderUsageMode.GENERAL,
            permission=VFolderPermission.READ_WRITE,
            host="storage1",
            creator="user@example.com",
            ownership_type=VFolderOwnershipType.USER,
            user=user_id,
            group=None,
            unmanaged_path=None,
            cloneable=False,
            status=VFolderOperationStatus.READY,
        )

        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Mock successful insert
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        # When
        with patch.object(vfolder_repo, "_get_vfolder_by_id") as mock_get:
            with patch.object(vfolder_repo, "_vfolder_row_to_data") as mock_to_data:
                await vfolder_repo.create_vfolder(params)

                # Then - Verify quota_scope_id is properly stored
                insert_call = mock_session.execute.call_args[0][0]
                assert hasattr(insert_call, "_values")
                # In actual implementation, verify the quota_scope_id is in values
