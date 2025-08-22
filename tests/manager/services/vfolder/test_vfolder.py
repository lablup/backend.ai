"""
Simple tests for VFolder Service functionality.
Tests the core vfolder service actions to verify compatibility with test scenarios.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
from ai.backend.common.types import QuotaScopeID, QuotaScopeType, VFolderUsageMode
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.errors.storage import (
    VFolderAlreadyExists,
    VFolderPermissionError,
)
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.vfolder import (
    VFolderOperationStatus,
    VFolderOwnershipType,
    VFolderPermission,
)
from ai.backend.manager.repositories.vfolder.admin_repository import AdminVfolderRepository
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.services.vfolder.actions.base import (
    CloneVFolderAction,
    CloneVFolderActionResult,
    CreateVFolderAction,
    CreateVFolderActionResult,
    DeleteForeverVFolderAction,
    ForceDeleteVFolderAction,
    GetVFolderAction,
    MoveToTrashVFolderAction,
    RestoreVFolderFromTrashAction,
    UpdateVFolderAttributeAction,
    VFolderAttributeModifier,
)
from ai.backend.manager.services.vfolder.exceptions import (
    VFolderInvalidParameter,
)
from ai.backend.manager.services.vfolder.processors.vfolder import VFolderProcessors
from ai.backend.manager.services.vfolder.services.vfolder import VFolderService
from ai.backend.manager.types import OptionalState


class TestVFolderServiceCompatibility:
    """Test compatibility of vfolder service with test scenarios."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mocked dependencies for testing."""
        config_provider = MagicMock(spec=ManagerConfigProvider)
        storage_manager = MagicMock(spec=StorageSessionManager)
        background_task_manager = MagicMock(spec=BackgroundTaskManager)
        vfolder_repository = MagicMock(spec=VfolderRepository)
        admin_vfolder_repository = MagicMock(spec=AdminVfolderRepository)
        action_monitor = MagicMock(spec=ActionMonitor)

        return {
            "config_provider": config_provider,
            "storage_manager": storage_manager,
            "background_task_manager": background_task_manager,
            "vfolder_repository": vfolder_repository,
            "admin_vfolder_repository": admin_vfolder_repository,
            "action_monitor": action_monitor,
        }

    @pytest.fixture
    def vfolder_service(self, mock_dependencies):
        """Create VFolderService instance with mocked dependencies."""
        return VFolderService(
            config_provider=mock_dependencies["config_provider"],
            storage_manager=mock_dependencies["storage_manager"],
            background_task_manager=mock_dependencies["background_task_manager"],
            vfolder_repository=mock_dependencies["vfolder_repository"],
            admin_vfolder_repository=mock_dependencies["admin_vfolder_repository"],
        )

    @pytest.fixture
    def vfolder_processors(self, vfolder_service, mock_dependencies):
        """Create VFolderProcessors instance."""
        return VFolderProcessors(
            service=vfolder_service,
            action_monitors=[mock_dependencies["action_monitor"]],
        )

    @pytest.mark.asyncio
    async def test_create_personal_vfolder(self, vfolder_processors, mock_dependencies):
        """Test 1.1: Personal VFolder Creation - Create personal workspace."""
        user_id = uuid.uuid4()
        vfolder_id = uuid.uuid4()

        # Setup mocks
        mock_dependencies["vfolder_repository"].get_vfolder_by_name.return_value = None
        mock_dependencies["vfolder_repository"].count_vfolders_by_user.return_value = 0
        mock_dependencies[
            "admin_vfolder_repository"
        ].create.return_value = CreateVFolderActionResult(
            id=vfolder_id,
            name="my-workspace",
            quota_scope_id=QuotaScopeID(scope_type=QuotaScopeType.USER, scope_id=user_id),
            host="storage1",
            unmanaged_path=None,
            mount_permission=VFolderPermission.READ_WRITE,
            usage_mode=VFolderUsageMode.GENERAL,
            creator_email="user@example.com",
            ownership_type=VFolderOwnershipType.USER,
            user_uuid=user_id,
            group_uuid=None,
            cloneable=False,
            status=VFolderOperationStatus.READY,
        )

        action = CreateVFolderAction(
            name="my-workspace",
            keypair_resource_policy={"max_vfolder_size": 10737418240},
            domain_name="default",
            group_id_or_name=None,
            folder_host="storage1",
            unmanaged_path=None,
            mount_permission=VFolderPermission.READ_WRITE,
            usage_mode=VFolderUsageMode.GENERAL,
            cloneable=False,
            user_uuid=user_id,
            user_role=UserRole.USER,
            creator_email="user@example.com",
        )

        result = await vfolder_processors.create_vfolder(action)

        assert result.name == "my-workspace"
        assert result.ownership_type == VFolderOwnershipType.USER
        assert result.user_uuid == user_id
        assert result.usage_mode == VFolderUsageMode.GENERAL
        mock_dependencies["admin_vfolder_repository"].create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_project_vfolder(self, vfolder_processors, mock_dependencies):
        """Test 1.2: Project VFolder Creation - Team shared storage."""
        project_id = uuid.uuid4()
        vfolder_id = uuid.uuid4()

        # Setup mocks
        mock_dependencies["vfolder_repository"].get_vfolder_by_name.return_value = None
        mock_dependencies["vfolder_repository"].count_vfolders_by_user.return_value = 0
        mock_dependencies[
            "admin_vfolder_repository"
        ].create.return_value = CreateVFolderActionResult(
            id=vfolder_id,
            name="team-data",
            quota_scope_id=QuotaScopeID(scope_type=QuotaScopeType.PROJECT, scope_id=project_id),
            host="storage1",
            unmanaged_path=None,
            mount_permission=VFolderPermission.READ_WRITE,
            usage_mode=VFolderUsageMode.DATA,
            creator_email="team@example.com",
            ownership_type=VFolderOwnershipType.GROUP,
            user_uuid=None,
            group_uuid=project_id,
            cloneable=True,
            status=VFolderOperationStatus.READY,
        )

        action = CreateVFolderAction(
            name="team-data",
            keypair_resource_policy={"max_vfolder_size": 107374182400},
            domain_name="default",
            group_id_or_name=project_id,
            folder_host="storage1",
            unmanaged_path=None,
            mount_permission=VFolderPermission.READ_WRITE,
            usage_mode=VFolderUsageMode.DATA,
            cloneable=True,
            user_uuid=uuid.uuid4(),
            user_role=UserRole.USER,
            creator_email="team@example.com",
        )

        result = await vfolder_processors.create_vfolder(action)

        assert result.name == "team-data"
        assert result.ownership_type == VFolderOwnershipType.GROUP
        assert result.group_uuid == project_id
        assert result.cloneable is True

    @pytest.mark.asyncio
    async def test_create_model_storage(self, vfolder_processors, mock_dependencies):
        """Test 1.3: Model Storage Creation - Storage for model deployment."""
        user_id = uuid.uuid4()
        vfolder_id = uuid.uuid4()

        # Setup mocks
        mock_dependencies["vfolder_repository"].get_vfolder_by_name.return_value = None
        mock_dependencies["vfolder_repository"].count_vfolders_by_user.return_value = 0
        mock_dependencies[
            "admin_vfolder_repository"
        ].create.return_value = CreateVFolderActionResult(
            id=vfolder_id,
            name="ml-models",
            quota_scope_id=QuotaScopeID(scope_type=QuotaScopeType.USER, scope_id=user_id),
            host="storage1",
            unmanaged_path=None,
            mount_permission=VFolderPermission.READ_ONLY,
            usage_mode=VFolderUsageMode.MODEL,
            creator_email="ml@example.com",
            ownership_type=VFolderOwnershipType.USER,
            user_uuid=user_id,
            group_uuid=None,
            cloneable=False,
            status=VFolderOperationStatus.READY,
        )

        action = CreateVFolderAction(
            name="ml-models",
            keypair_resource_policy={"max_vfolder_size": 53687091200},
            domain_name="default",
            group_id_or_name=None,
            folder_host="storage1",
            unmanaged_path=None,
            mount_permission=VFolderPermission.READ_ONLY,
            usage_mode=VFolderUsageMode.MODEL,
            cloneable=False,
            user_uuid=user_id,
            user_role=UserRole.USER,
            creator_email="ml@example.com",
        )

        result = await vfolder_processors.create_vfolder(action)

        assert result.name == "ml-models"
        assert result.usage_mode == VFolderUsageMode.MODEL
        assert result.mount_permission == VFolderPermission.READ_ONLY
        assert result.cloneable is False

    @pytest.mark.asyncio
    async def test_create_vfolder_duplicate_name(self, vfolder_processors, mock_dependencies):
        """Test 1.4: Duplicate Name - Unique name per owner."""
        # Setup mock to indicate folder already exists
        mock_dependencies["vfolder_repository"].get_vfolder_by_name.return_value = {
            "id": uuid.uuid4()
        }

        action = CreateVFolderAction(
            name="existing-folder",
            keypair_resource_policy={"max_vfolder_size": 10737418240},
            domain_name="default",
            group_id_or_name=None,
            folder_host="storage1",
            unmanaged_path=None,
            mount_permission=VFolderPermission.READ_WRITE,
            usage_mode=VFolderUsageMode.GENERAL,
            cloneable=False,
            user_uuid=uuid.uuid4(),
            user_role=UserRole.USER,
            creator_email="user@example.com",
        )

        with pytest.raises(VFolderAlreadyExists):
            await vfolder_processors.create_vfolder(action)

    @pytest.mark.asyncio
    async def test_create_vfolder_quota_exceeded(self, vfolder_processors, mock_dependencies):
        """Test 1.5: Quota Exceeded - Resource policy compliance."""
        # Setup mocks
        mock_dependencies["vfolder_repository"].get_vfolder_by_name.return_value = None
        mock_dependencies[
            "vfolder_repository"
        ].count_vfolders_by_user.return_value = 10  # Exceeds limit

        action = CreateVFolderAction(
            name="large-folder",
            keypair_resource_policy={"max_vfolder_count": 5},  # Max 5 vfolders
            domain_name="default",
            group_id_or_name=None,
            folder_host="storage1",
            unmanaged_path=None,
            mount_permission=VFolderPermission.READ_WRITE,
            usage_mode=VFolderUsageMode.GENERAL,
            cloneable=False,
            user_uuid=uuid.uuid4(),
            user_role=UserRole.USER,
            creator_email="user@example.com",
        )

        with pytest.raises(VFolderInvalidParameter):
            await vfolder_processors.create_vfolder(action)

    @pytest.mark.asyncio
    async def test_create_unmanaged_vfolder(self, vfolder_processors, mock_dependencies):
        """Test 1.6: Unmanaged VFolder - Access existing data."""
        admin_id = uuid.uuid4()
        vfolder_id = uuid.uuid4()

        # Setup mocks
        mock_dependencies["vfolder_repository"].get_vfolder_by_name.return_value = None
        mock_dependencies["vfolder_repository"].count_vfolders_by_user.return_value = 0
        mock_dependencies[
            "admin_vfolder_repository"
        ].create.return_value = CreateVFolderActionResult(
            id=vfolder_id,
            name="external-data",
            quota_scope_id=QuotaScopeID(scope_type=QuotaScopeType.USER, scope_id=admin_id),
            host="storage1",
            unmanaged_path="/mnt/external/data",
            mount_permission=VFolderPermission.READ_ONLY,
            usage_mode=VFolderUsageMode.DATA,
            creator_email="admin@example.com",
            ownership_type=VFolderOwnershipType.USER,
            user_uuid=admin_id,
            group_uuid=None,
            cloneable=False,
            status=VFolderOperationStatus.READY,
        )

        action = CreateVFolderAction(
            name="external-data",
            keypair_resource_policy={"max_vfolder_size": 0},  # No quota for unmanaged
            domain_name="default",
            group_id_or_name=None,
            folder_host="storage1",
            unmanaged_path="/mnt/external/data",
            mount_permission=VFolderPermission.READ_ONLY,
            usage_mode=VFolderUsageMode.DATA,
            cloneable=False,
            user_uuid=admin_id,
            user_role=UserRole.ADMIN,  # Admin only
            creator_email="admin@example.com",
        )

        result = await vfolder_processors.create_vfolder(action)

        assert result.name == "external-data"
        assert result.unmanaged_path == "/mnt/external/data"
        assert result.quota_scope_id == QuotaScopeID(
            scope_type=QuotaScopeType.USER, scope_id=admin_id
        )
        assert result.mount_permission == VFolderPermission.READ_ONLY

    @pytest.mark.asyncio
    async def test_update_vfolder_name(self, vfolder_processors, mock_dependencies):
        """Test 2: VFolder Attribute Modification - Name change."""
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Setup mock
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "user": user_id,
        }
        mock_dependencies["admin_vfolder_repository"].update_attribute.return_value = None

        action = UpdateVFolderAttributeAction(
            user_uuid=user_id,
            vfolder_uuid=vfolder_id,
            modifier=VFolderAttributeModifier(
                name=OptionalState.set("renamed-folder"),
            ),
        )

        result = await vfolder_processors.update_vfolder_attribute(action)

        assert result.vfolder_uuid == vfolder_id
        mock_dependencies["admin_vfolder_repository"].update_attribute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_vfolder_cloneable(self, vfolder_processors, mock_dependencies):
        """Test 2: VFolder Attribute Modification - Cloneable setting."""
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Setup mock
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "user": user_id,
        }
        mock_dependencies["admin_vfolder_repository"].update_attribute.return_value = None

        action = UpdateVFolderAttributeAction(
            user_uuid=user_id,
            vfolder_uuid=vfolder_id,
            modifier=VFolderAttributeModifier(
                cloneable=OptionalState.set(True),
            ),
        )

        result = await vfolder_processors.update_vfolder_attribute(action)

        assert result.vfolder_uuid == vfolder_id

    @pytest.mark.asyncio
    async def test_update_vfolder_permission(self, vfolder_processors, mock_dependencies):
        """Test 2: VFolder Attribute Modification - Permission change."""
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Setup mock
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "user": user_id,
        }
        mock_dependencies["admin_vfolder_repository"].update_attribute.return_value = None

        action = UpdateVFolderAttributeAction(
            user_uuid=user_id,
            vfolder_uuid=vfolder_id,
            modifier=VFolderAttributeModifier(
                mount_permission=OptionalState.set(VFolderPermission.RW_DELETE),
            ),
        )

        result = await vfolder_processors.update_vfolder_attribute(action)

        assert result.vfolder_uuid == vfolder_id

    @pytest.mark.asyncio
    async def test_get_vfolder_info(self, vfolder_processors, vfolder_service, mock_dependencies):
        """Test 3: VFolder Information Query - Including usage."""
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()
        owner_id = uuid.uuid4()

        # Setup mocks
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "user": user_id,
            "name": "my-vfolder",
            "host": "storage1",
            "usage_mode": VFolderUsageMode.GENERAL,
            "permission": VFolderPermission.READ_WRITE,
            "ownership_type": VFolderOwnershipType.USER,
            "status": VFolderOperationStatus.READY,
            "max_size": 10737418240,  # 10GB
            "cloneable": False,
        }

        # Mock usage info
        vfolder_service.storage_manager.get_usage.return_value = AsyncMock(
            return_value=(1073741824, 100)  # 1GB used, 100 files
        )()

        action = GetVFolderAction(
            user_uuid=user_id,
            vfolder_uuid=vfolder_id,
        )

        result = await vfolder_processors.get(action)

        assert result.base_info.name == "my-vfolder"
        assert result.base_info.quota == 10737418240
        assert result.usage_info.used_bytes == 1073741824
        assert result.usage_info.file_count == 100

    @pytest.mark.asyncio
    async def test_clone_vfolder_success(self, vfolder_processors, mock_dependencies):
        """Test 4.1: Full Clone - Backup or experiment."""
        source_id = uuid.uuid4()
        target_id = uuid.uuid4()
        user_id = uuid.uuid4()
        task_id = uuid.uuid4()

        # Setup mocks
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": source_id,
            "cloneable": True,
            "host": "storage1",
        }
        mock_dependencies["admin_vfolder_repository"].clone.return_value = CloneVFolderActionResult(
            vfolder_uuid=source_id,
            target_vfolder_id=target_id,
            target_vfolder_name="cloned-folder",
            target_vfolder_host="storage1",
            usage_mode=VFolderUsageMode.GENERAL,
            mount_permission=VFolderPermission.READ_WRITE,
            creator_email="user@example.com",
            ownership_type=VFolderOwnershipType.USER,
            owner_user_uuid=user_id,
            owner_group_uuid=None,
            cloneable=True,
            bgtask_id=task_id,
        )

        action = CloneVFolderAction(
            requester_user_uuid=user_id,
            source_vfolder_uuid=source_id,
            target_name="cloned-folder",
            target_host="storage1",
            cloneable=True,
            usage_mode=VFolderUsageMode.GENERAL,
            mount_permission=VFolderPermission.READ_WRITE,
        )

        result = await vfolder_processors.clone(action)

        assert result.target_vfolder_name == "cloned-folder"
        assert result.target_vfolder_id == target_id
        assert result.bgtask_id == task_id
        mock_dependencies["admin_vfolder_repository"].clone.assert_called_once()

    @pytest.mark.asyncio
    async def test_clone_vfolder_not_cloneable(self, vfolder_processors, mock_dependencies):
        """Test 4.3: Unauthorized Clone - Clone permission control."""
        source_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Setup mock - folder not cloneable
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": source_id,
            "cloneable": False,
            "host": "storage1",
        }

        action = CloneVFolderAction(
            requester_user_uuid=user_id,
            source_vfolder_uuid=source_id,
            target_name="unauthorized-clone",
            target_host="storage1",
            cloneable=False,
            usage_mode=VFolderUsageMode.GENERAL,
            mount_permission=VFolderPermission.READ_WRITE,
        )

        with pytest.raises(VFolderPermissionError):
            await vfolder_processors.clone(action)

    @pytest.mark.asyncio
    async def test_move_to_trash_success(self, vfolder_processors, mock_dependencies):
        """Test 6.1: Normal Deletion - Prevent mistakes."""
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Setup mocks
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "user": user_id,
            "status": VFolderOperationStatus.READY,
        }
        mock_dependencies["vfolder_repository"].is_vfolder_mounted.return_value = False
        mock_dependencies["admin_vfolder_repository"].move_to_trash.return_value = None

        action = MoveToTrashVFolderAction(
            user_uuid=user_id,
            keypair_resource_policy={},
            vfolder_uuid=vfolder_id,
        )

        result = await vfolder_processors.move_to_trash(action)

        assert result.vfolder_uuid == vfolder_id
        mock_dependencies["admin_vfolder_repository"].move_to_trash.assert_called_once()

    @pytest.mark.asyncio
    async def test_move_to_trash_in_use(self, vfolder_processors, mock_dependencies):
        """Test 6.2: Mounted VFolder - In-use protection."""
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Setup mocks - folder is mounted
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "user": user_id,
            "status": VFolderOperationStatus.READY,
        }
        mock_dependencies["vfolder_repository"].is_vfolder_mounted.return_value = True

        action = MoveToTrashVFolderAction(
            user_uuid=user_id,
            keypair_resource_policy={},
            vfolder_uuid=vfolder_id,
        )

        with pytest.raises(VFolderPermissionError):
            await vfolder_processors.move_to_trash(action)

    @pytest.mark.asyncio
    async def test_restore_from_trash(self, vfolder_processors, mock_dependencies):
        """Test: Restore from Trash - VFolder recovery."""
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Setup mocks
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "user": user_id,
            "status": VFolderOperationStatus.DELETE_PENDING,
        }
        mock_dependencies["admin_vfolder_repository"].restore_from_trash.return_value = None

        action = RestoreVFolderFromTrashAction(
            user_uuid=user_id,
            vfolder_uuid=vfolder_id,
        )

        result = await vfolder_processors.restore_from_trash(action)

        assert result.vfolder_uuid == vfolder_id
        mock_dependencies["admin_vfolder_repository"].restore_from_trash.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_forever(self, vfolder_processors, mock_dependencies):
        """Test: Permanent Deletion - Complete removal from trash."""
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Setup mocks
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "user": user_id,
            "status": VFolderOperationStatus.DELETE_PENDING,
        }
        mock_dependencies["admin_vfolder_repository"].delete_forever.return_value = None

        action = DeleteForeverVFolderAction(
            user_uuid=user_id,
            vfolder_uuid=vfolder_id,
        )

        result = await vfolder_processors.delete_forever(action)

        assert result.vfolder_uuid == vfolder_id
        mock_dependencies["admin_vfolder_repository"].delete_forever.assert_called_once()

    @pytest.mark.asyncio
    async def test_force_delete(self, vfolder_processors, mock_dependencies):
        """Test: Force Delete - Immediate permanent deletion."""
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Setup mocks
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "user": user_id,
            "status": VFolderOperationStatus.READY,
        }
        mock_dependencies["admin_vfolder_repository"].force_delete.return_value = None

        action = ForceDeleteVFolderAction(
            user_uuid=user_id,
            vfolder_uuid=vfolder_id,
        )

        result = await vfolder_processors.force_delete(action)

        assert result.vfolder_uuid == vfolder_id
        mock_dependencies["admin_vfolder_repository"].force_delete.assert_called_once()
