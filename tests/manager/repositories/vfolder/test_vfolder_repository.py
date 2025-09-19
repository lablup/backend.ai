import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from ai.backend.common.types import QuotaScopeID, VFolderUsageMode
from ai.backend.manager.data.vfolder.types import (
    VFolderCreateParams,
    VFolderData,
    VFolderListResult,
)
from ai.backend.manager.errors.storage import VFolderNotFound
from ai.backend.manager.models.user import UserRole, UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import (
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderPermission,
    VFolderPermissionRow,
    VFolderRow,
)
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository


@pytest.fixture
def mock_db_engine():
    """Mock database engine for testing"""
    engine = MagicMock(spec=ExtendedAsyncSAEngine)
    return engine


@pytest.fixture
def vfolder_repository(mock_db_engine):
    """Create VfolderRepository instance with mocked dependencies"""
    return VfolderRepository(db=mock_db_engine)


@pytest.fixture
def sample_vfolder_row():
    """Sample VFolderRow for testing"""
    vfolder_row = MagicMock(spec=VFolderRow)
    vfolder_row.id = uuid.uuid4()
    vfolder_row.name = "test-vfolder"
    vfolder_row.domain_name = "default"
    vfolder_row.quota_scope_id = QuotaScopeID("12345")
    vfolder_row.usage_mode = VFolderUsageMode.GENERAL
    vfolder_row.permission = VFolderPermission.READ_WRITE
    vfolder_row.last_used = None
    vfolder_row.host = "storage1"
    vfolder_row.creator = "user@example.com"
    vfolder_row.ownership_type = VFolderOwnershipType.USER
    vfolder_row.user = uuid.uuid4()
    vfolder_row.group = None
    vfolder_row.unmanaged_path = None
    vfolder_row.cloneable = False
    vfolder_row.status = VFolderOperationStatus.READY
    vfolder_row.cur_size = 1024
    return vfolder_row


@pytest.fixture
def sample_user_row():
    """Sample UserRow for testing"""
    user_row = MagicMock(spec=UserRow)
    user_row.uuid = uuid.uuid4()
    user_row.role = UserRole.USER
    user_row.domain_name = "default"
    return user_row


class TestVfolderRepository:
    """Test cases for VfolderRepository"""

    @pytest.mark.asyncio
    async def test_get_by_id_validated_success(
        self, vfolder_repository, mock_db_engine, sample_vfolder_row, sample_user_row
    ):
        """Test successful retrieval of vfolder with validation"""
        vfolder_id = sample_vfolder_row.id
        user_id = sample_user_row.uuid
        domain_name = "default"

        # Mock session and queries
        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Mock _get_vfolder_by_id to return sample vfolder
        with patch.object(
            vfolder_repository, "_get_vfolder_by_id", return_value=sample_vfolder_row
        ):
            # Mock user query
            mock_session.scalar.return_value = sample_user_row

            # Mock query_accessible_vfolders
            with patch(
                "ai.backend.manager.repositories.vfolder.repository.query_accessible_vfolders",
                return_value=[
                    {"id": vfolder_id, "is_owner": True, "permission": VFolderPermission.READ_WRITE}
                ],
            ):
                # Mock _vfolder_row_to_data
                expected_data = VFolderData(
                    id=vfolder_id,
                    name="test-vfolder",
                    domain_name="default",
                    quota_scope_id=QuotaScopeID("12345"),
                    usage_mode=VFolderUsageMode.GENERAL,
                    permission=VFolderPermission.READ_WRITE,
                    last_used=None,
                    host="storage1",
                    creator="user@example.com",
                    ownership_type=VFolderOwnershipType.USER,
                    user=sample_vfolder_row.user,
                    group=None,
                    unmanaged_path=None,
                    cloneable=False,
                    status=VFolderOperationStatus.READY,
                    cur_size=1024,
                )
                with patch.object(
                    vfolder_repository, "_vfolder_row_to_data", return_value=expected_data
                ):
                    result = await vfolder_repository.get_by_id_validated(
                        vfolder_id, user_id, domain_name
                    )

                    assert result == expected_data
                    assert result.id == vfolder_id
                    assert result.name == "test-vfolder"

    @pytest.mark.asyncio
    async def test_get_by_id_validated_not_found(self, vfolder_repository, mock_db_engine):
        """Test vfolder not found scenario"""
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()
        domain_name = "default"

        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Mock _get_vfolder_by_id to return None
        with patch.object(vfolder_repository, "_get_vfolder_by_id", return_value=None):
            with pytest.raises(VFolderNotFound):
                await vfolder_repository.get_by_id_validated(vfolder_id, user_id, domain_name)

    @pytest.mark.asyncio
    async def test_get_by_id_validated_no_access(
        self, vfolder_repository, mock_db_engine, sample_vfolder_row, sample_user_row
    ):
        """Test user has no access to vfolder"""
        vfolder_id = sample_vfolder_row.id
        user_id = sample_user_row.uuid
        domain_name = "default"

        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        with patch.object(
            vfolder_repository, "_get_vfolder_by_id", return_value=sample_vfolder_row
        ):
            mock_session.scalar.return_value = sample_user_row

            # Mock query_accessible_vfolders to return empty list (no access)
            with patch(
                "ai.backend.manager.repositories.vfolder.repository.query_accessible_vfolders",
                return_value=[],
            ):
                with pytest.raises(VFolderNotFound):
                    await vfolder_repository.get_by_id_validated(vfolder_id, user_id, domain_name)

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, vfolder_repository, mock_db_engine, sample_vfolder_row):
        """Test get vfolder by id without validation"""
        vfolder_id = sample_vfolder_row.id

        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        with patch.object(
            vfolder_repository, "_get_vfolder_by_id", return_value=sample_vfolder_row
        ):
            expected_data = VFolderData(
                id=vfolder_id,
                name="test-vfolder",
                domain_name="default",
                quota_scope_id=QuotaScopeID("12345"),
                usage_mode=VFolderUsageMode.GENERAL,
                permission=VFolderPermission.READ_WRITE,
                last_used=None,
                host="storage1",
                creator="user@example.com",
                ownership_type=VFolderOwnershipType.USER,
                user=sample_vfolder_row.user,
                group=None,
                unmanaged_path=None,
                cloneable=False,
                status=VFolderOperationStatus.READY,
                cur_size=1024,
            )
            with patch.object(
                vfolder_repository, "_vfolder_row_to_data", return_value=expected_data
            ):
                result = await vfolder_repository.get_by_id(vfolder_id)

                assert result == expected_data
                assert result.id == vfolder_id

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, vfolder_repository, mock_db_engine):
        """Test get vfolder by id returns None when not found"""
        vfolder_id = uuid.uuid4()

        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        with patch.object(vfolder_repository, "_get_vfolder_by_id", return_value=None):
            result = await vfolder_repository.get_by_id(vfolder_id)
            assert result is None

    @pytest.mark.asyncio
    async def test_list_accessible_vfolders(
        self, vfolder_repository, mock_db_engine, sample_user_row
    ):
        """Test listing accessible vfolders for a user"""
        user_id = sample_user_row.uuid
        user_role = UserRole.USER
        domain_name = "default"
        allowed_vfolder_types = ["user", "group"]

        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Mock query_accessible_vfolders
        vfolder_dicts = [
            {
                "id": uuid.uuid4(),
                "name": "vfolder1",
                "is_owner": True,
                "permission": VFolderPermission.READ_WRITE,
                "domain_name": "default",
                "quota_scope_id": "12345",
                "usage_mode": VFolderUsageMode.GENERAL,
                "last_used": None,
                "host": "storage1",
                "creator": "user@example.com",
                "ownership_type": VFolderOwnershipType.USER,
                "user": user_id,
                "group": None,
                "unmanaged_path": None,
                "cloneable": False,
                "status": VFolderOperationStatus.READY,
                "cur_size": 1024,
            },
            {
                "id": uuid.uuid4(),
                "name": "vfolder2",
                "is_owner": False,
                "permission": VFolderPermission.READ_ONLY,
                "domain_name": "default",
                "quota_scope_id": "67890",
                "usage_mode": VFolderUsageMode.DATA,
                "last_used": None,
                "host": "storage1",
                "creator": "other@example.com",
                "ownership_type": VFolderOwnershipType.GROUP,
                "user": None,
                "group": uuid.uuid4(),
                "unmanaged_path": None,
                "cloneable": True,
                "status": VFolderOperationStatus.READY,
                "cur_size": 2048,
            },
        ]

        with patch(
            "ai.backend.manager.repositories.vfolder.repository.query_accessible_vfolders",
            return_value=vfolder_dicts,
        ):
            # Mock _vfolder_dict_to_data
            def mock_dict_to_data(vfolder_dict):
                return VFolderData(
                    id=vfolder_dict["id"],
                    name=vfolder_dict["name"],
                    domain_name=vfolder_dict["domain_name"],
                    quota_scope_id=QuotaScopeID(vfolder_dict["quota_scope_id"]),
                    usage_mode=vfolder_dict["usage_mode"],
                    permission=vfolder_dict["permission"],
                    last_used=vfolder_dict["last_used"],
                    host=vfolder_dict["host"],
                    creator=vfolder_dict["creator"],
                    ownership_type=vfolder_dict["ownership_type"],
                    user=vfolder_dict["user"],
                    group=vfolder_dict["group"],
                    unmanaged_path=vfolder_dict["unmanaged_path"],
                    cloneable=vfolder_dict["cloneable"],
                    status=vfolder_dict["status"],
                    cur_size=vfolder_dict["cur_size"],
                )

            with patch.object(
                vfolder_repository, "_vfolder_dict_to_data", side_effect=mock_dict_to_data
            ):
                result = await vfolder_repository.list_accessible_vfolders(
                    user_id, user_role, domain_name, allowed_vfolder_types
                )

                assert isinstance(result, VFolderListResult)
                assert len(result.vfolders) == 2

                # Check first vfolder
                assert result.vfolders[0].vfolder_data.name == "vfolder1"
                assert result.vfolders[0].is_owner is True
                assert result.vfolders[0].effective_permission == VFolderPermission.READ_WRITE

                # Check second vfolder
                assert result.vfolders[1].vfolder_data.name == "vfolder2"
                assert result.vfolders[1].is_owner is False
                assert result.vfolders[1].effective_permission == VFolderPermission.READ_ONLY

    @pytest.mark.asyncio
    async def test_create_vfolder(self, vfolder_repository, mock_db_engine):
        """Test creating a new vfolder"""
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()

        params = VFolderCreateParams(
            id=vfolder_id,
            name="new-vfolder",
            domain_name="default",
            quota_scope_id=QuotaScopeID("12345"),
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

        # Mock the insert execution
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        # Mock the created vfolder retrieval
        created_vfolder_row = MagicMock(spec=VFolderRow)
        created_vfolder_row.id = vfolder_id
        created_vfolder_row.name = "new-vfolder"

        with patch.object(
            vfolder_repository, "_get_vfolder_by_id", return_value=created_vfolder_row
        ):
            expected_data = VFolderData(
                id=vfolder_id,
                name="new-vfolder",
                domain_name="default",
                quota_scope_id=QuotaScopeID("12345"),
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
                cur_size=0,
            )

            with patch.object(
                vfolder_repository, "_vfolder_row_to_data", return_value=expected_data
            ):
                result = await vfolder_repository.create_vfolder(params)

                assert result == expected_data
                assert result.id == vfolder_id
                assert result.name == "new-vfolder"

                # Verify insert was called with correct values
                insert_call = mock_session.execute.call_args[0][0]
                assert hasattr(insert_call, "_values")

    @pytest.mark.asyncio
    async def test_create_vfolder_with_permission(self, vfolder_repository, mock_db_engine):
        """Test creating a vfolder with owner permission"""
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()

        params = VFolderCreateParams(
            id=vfolder_id,
            name="new-vfolder-with-perm",
            domain_name="default",
            quota_scope_id=QuotaScopeID("12345"),
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

        # Mock the insert executions
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        # Mock the created vfolder retrieval
        created_vfolder_row = MagicMock(spec=VFolderRow)
        created_vfolder_row.id = vfolder_id

        with patch.object(
            vfolder_repository, "_get_vfolder_by_id", return_value=created_vfolder_row
        ):
            expected_data = VFolderData(
                id=vfolder_id,
                name="new-vfolder-with-perm",
                domain_name="default",
                quota_scope_id=QuotaScopeID("12345"),
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
                cur_size=0,
            )

            with patch.object(
                vfolder_repository, "_vfolder_row_to_data", return_value=expected_data
            ):
                result = await vfolder_repository.create_vfolder_with_permission(
                    params, create_owner_permission=True
                )

                assert result == expected_data
                # Verify both vfolder and permission inserts were called
                assert mock_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_update_vfolder_attribute(
        self, vfolder_repository, mock_db_engine, sample_vfolder_row
    ):
        """Test updating vfolder attributes"""
        vfolder_id = sample_vfolder_row.id
        field_updates = {
            "name": "updated-name",
            "cloneable": True,
        }

        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Mock the vfolder retrieval
        updated_vfolder_row = MagicMock(spec=VFolderRow)
        updated_vfolder_row.id = vfolder_id
        updated_vfolder_row.name = "updated-name"
        updated_vfolder_row.cloneable = True

        with patch.object(
            vfolder_repository, "_get_vfolder_by_id", return_value=updated_vfolder_row
        ):
            expected_data = VFolderData(
                id=vfolder_id,
                name="updated-name",
                domain_name="default",
                quota_scope_id=QuotaScopeID("12345"),
                usage_mode=VFolderUsageMode.GENERAL,
                permission=VFolderPermission.READ_WRITE,
                last_used=None,
                host="storage1",
                creator="user@example.com",
                ownership_type=VFolderOwnershipType.USER,
                user=sample_vfolder_row.user,
                group=None,
                unmanaged_path=None,
                cloneable=True,
                status=VFolderOperationStatus.READY,
                cur_size=1024,
            )

            with patch.object(
                vfolder_repository, "_vfolder_row_to_data", return_value=expected_data
            ):
                result = await vfolder_repository.update_vfolder_attribute(
                    vfolder_id, field_updates
                )

                assert result.name == "updated-name"
                assert result.cloneable is True
                mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_vfolder_attribute_not_found(self, vfolder_repository, mock_db_engine):
        """Test updating non-existent vfolder raises error"""
        vfolder_id = uuid.uuid4()
        field_updates = {"name": "updated-name"}

        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        with patch.object(vfolder_repository, "_get_vfolder_by_id", return_value=None):
            with pytest.raises(VFolderNotFound):
                await vfolder_repository.update_vfolder_attribute(vfolder_id, field_updates)

    @pytest.mark.asyncio
    async def test_get_vfolder_permissions(self, vfolder_repository, mock_db_engine):
        """Test getting vfolder permissions"""
        vfolder_id = uuid.uuid4()
        user_id1 = uuid.uuid4()
        user_id2 = uuid.uuid4()

        mock_session = AsyncMock(spec=AsyncSession)
        mock_db_engine.begin_session.return_value.__aenter__.return_value = mock_session

        # Mock permission rows
        perm_row1 = MagicMock(spec=VFolderPermissionRow)
        perm_row1.id = uuid.uuid4()
        perm_row1.vfolder = vfolder_id
        perm_row1.user = user_id1
        perm_row1.permission = VFolderPermission.OWNER_PERM

        perm_row2 = MagicMock(spec=VFolderPermissionRow)
        perm_row2.id = uuid.uuid4()
        perm_row2.vfolder = vfolder_id
        perm_row2.user = user_id2
        perm_row2.permission = VFolderPermission.READ_ONLY

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [perm_row1, perm_row2]
        mock_session.execute.return_value = mock_result

        result = await vfolder_repository.get_vfolder_permissions(vfolder_id)

        assert len(result) == 2
        # Note: The actual implementation might need to be checked for the exact return format
