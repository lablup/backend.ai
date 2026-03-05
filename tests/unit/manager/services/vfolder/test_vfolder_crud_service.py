"""
Unit tests for VFolderService CRUD operations.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from ai.backend.common.data.permission.types import ScopeType
from ai.backend.common.types import (
    QuotaScopeID,
    QuotaScopeType,
    VFolderUsageMode,
)
from ai.backend.manager.data.vfolder.types import (
    VFolderAccessInfo,
    VFolderData,
    VFolderListResult,
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.errors.common import Forbidden
from ai.backend.manager.errors.storage import (
    TooManyVFoldersFound,
    VFolderAlreadyExists,
    VFolderCreationFailure,
    VFolderGone,
    VFolderInvalidParameter,
    VFolderNotFound,
)
from ai.backend.manager.models.group import ProjectType
from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.vfolder import VFolderPermission
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.repositories.vfolder.updaters import VFolderAttributeUpdaterSpec
from ai.backend.manager.services.vfolder.actions.base import (
    CloneVFolderAction,
    CloneVFolderActionResult,
    CreateVFolderAction,
    CreateVFolderActionResult,
    DeleteForeverVFolderAction,
    DeleteForeverVFolderActionResult,
    ForceDeleteVFolderAction,
    ForceDeleteVFolderActionResult,
    GetAccessibleVFolderAction,
    GetAccessibleVFolderActionResult,
    GetVFolderAction,
    GetVFolderActionResult,
    ListVFolderAction,
    ListVFolderActionResult,
    MoveToTrashVFolderAction,
    MoveToTrashVFolderActionResult,
    RestoreVFolderFromTrashAction,
    RestoreVFolderFromTrashActionResult,
    UpdateVFolderAttributeAction,
    UpdateVFolderAttributeActionResult,
)
from ai.backend.manager.services.vfolder.services.vfolder import VFolderService


@pytest.fixture
def user_uuid() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def vfolder_uuid() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def group_uuid() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def mock_vfolder_repository() -> MagicMock:
    return MagicMock(spec=VfolderRepository)


@pytest.fixture
def mock_config_provider() -> MagicMock:
    provider = MagicMock()
    provider.legacy_etcd_config_loader.get_vfolder_types = AsyncMock(return_value=["user", "group"])
    provider.config.volumes.default_host = "local:volume1"
    return provider


@pytest.fixture
def mock_storage_manager() -> MagicMock:
    manager = MagicMock()
    manager.get_proxy_and_volume.return_value = ("proxy1", "volume1")
    mock_client = MagicMock()
    mock_client.create_folder = AsyncMock()
    mock_client.delete_folder = AsyncMock()
    mock_client.get_folder_usage = AsyncMock(return_value={"used_bytes": 1024, "file_count": 10})
    manager.get_manager_facing_client.return_value = mock_client
    return manager


@pytest.fixture
def mock_user_repository() -> MagicMock:
    repo = MagicMock()
    user = MagicMock()
    user.id = uuid.uuid4()
    user.domain_name = "default"
    repo.get_user_by_uuid = AsyncMock(return_value=user)
    return repo


@pytest.fixture
def vfolder_service(
    mock_config_provider: MagicMock,
    mock_storage_manager: MagicMock,
    mock_vfolder_repository: MagicMock,
    mock_user_repository: MagicMock,
) -> VFolderService:
    return VFolderService(
        config_provider=mock_config_provider,
        etcd=MagicMock(),
        storage_manager=mock_storage_manager,
        background_task_manager=MagicMock(),
        vfolder_repository=mock_vfolder_repository,
        user_repository=mock_user_repository,
        valkey_stat_client=MagicMock(),
    )


def _make_vfolder_data(
    vfolder_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    name: str = "test-vfolder",
    host: str = "local:volume1",
    status: VFolderOperationStatus = VFolderOperationStatus.READY,
    ownership_type: VFolderOwnershipType = VFolderOwnershipType.USER,
    group: uuid.UUID | None = None,
    cloneable: bool = False,
    usage_mode: VFolderUsageMode = VFolderUsageMode.GENERAL,
    unmanaged_path: str | None = None,
) -> VFolderData:
    return VFolderData(
        id=vfolder_id,
        name=name,
        host=host,
        domain_name="default",
        quota_scope_id=QuotaScopeID(QuotaScopeType.USER, user_id),
        usage_mode=usage_mode,
        permission=VFolderMountPermission.READ_WRITE,
        max_files=0,
        max_size=None,
        num_files=0,
        cur_size=0,
        created_at=datetime(2025, 1, 1, tzinfo=UTC),
        last_used=None,
        creator="test@example.com",
        unmanaged_path=unmanaged_path,
        ownership_type=ownership_type,
        user=user_id,
        group=group,
        cloneable=cloneable,
        status=status,
    )


class TestCreateVFolderAction:
    async def test_valid_name_host_creates_vfolder(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.get_user_resource_info = AsyncMock(return_value=(10, 0, None))
        mock_vfolder_repository.ensure_host_permission_allowed = AsyncMock()
        mock_vfolder_repository.count_vfolders_by_user = AsyncMock(return_value=0)
        mock_vfolder_repository.check_vfolder_name_exists = AsyncMock(return_value=False)
        mock_vfolder_repository.create_vfolder_with_permission = AsyncMock()

        action = CreateVFolderAction(
            name="my-vfolder",
            keypair_resource_policy={"default": {}},
            domain_name="default",
            group_id_or_name=None,
            folder_host="local:volume1",
            unmanaged_path=None,
            mount_permission=VFolderPermission.READ_WRITE,
            usage_mode=VFolderUsageMode.GENERAL,
            cloneable=False,
            _scope_id=str(user_uuid),
            _scope_type=ScopeType.USER,
            user_uuid=user_uuid,
            user_role=UserRole.USER,
            creator_email="test@example.com",
        )

        result = await vfolder_service.create(action)

        assert isinstance(result, CreateVFolderActionResult)
        assert result.name == "my-vfolder"
        assert result.status == VFolderOperationStatus.READY
        mock_vfolder_repository.create_vfolder_with_permission.assert_called_once()

    async def test_non_admin_unmanaged_path_raises_forbidden(
        self,
        vfolder_service: VFolderService,
        user_uuid: uuid.UUID,
    ) -> None:
        action = CreateVFolderAction(
            name="my-vfolder",
            keypair_resource_policy={"default": {}},
            domain_name="default",
            group_id_or_name=None,
            folder_host="local:volume1",
            unmanaged_path="/some/path",
            mount_permission=VFolderPermission.READ_WRITE,
            usage_mode=VFolderUsageMode.GENERAL,
            cloneable=False,
            _scope_id=str(user_uuid),
            _scope_type=ScopeType.USER,
            user_uuid=user_uuid,
            user_role=UserRole.USER,
            creator_email="test@example.com",
        )

        with pytest.raises(Forbidden):
            await vfolder_service.create(action)

    async def test_group_ownership_sets_project_quota_scope(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
        group_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.get_group_resource_info = AsyncMock(
            return_value=(group_uuid, 10, 0, None)
        )
        mock_vfolder_repository.ensure_host_permission_allowed = AsyncMock()
        mock_vfolder_repository.count_vfolders_by_group = AsyncMock(return_value=0)
        mock_vfolder_repository.check_vfolder_name_exists = AsyncMock(return_value=False)
        mock_vfolder_repository.create_vfolder_with_permission = AsyncMock()

        action = CreateVFolderAction(
            name="group-vfolder",
            keypair_resource_policy={"default": {}},
            domain_name="default",
            group_id_or_name=str(group_uuid),
            folder_host="local:volume1",
            unmanaged_path=None,
            mount_permission=VFolderPermission.READ_WRITE,
            usage_mode=VFolderUsageMode.GENERAL,
            cloneable=False,
            _scope_id=str(group_uuid),
            _scope_type=ScopeType.PROJECT,
            user_uuid=user_uuid,
            user_role=UserRole.SUPERADMIN,
            creator_email="admin@example.com",
        )

        result = await vfolder_service.create(action)

        assert result.quota_scope_id.scope_type == QuotaScopeType.PROJECT
        assert result.group_uuid == group_uuid

    async def test_no_default_host_and_none_specified_raises_invalid_parameter(
        self,
        vfolder_service: VFolderService,
        mock_config_provider: MagicMock,
        user_uuid: uuid.UUID,
    ) -> None:
        mock_config_provider.config.volumes.default_host = None

        action = CreateVFolderAction(
            name="my-vfolder",
            keypair_resource_policy={"default": {}},
            domain_name="default",
            group_id_or_name=None,
            folder_host=None,
            unmanaged_path=None,
            mount_permission=VFolderPermission.READ_WRITE,
            usage_mode=VFolderUsageMode.GENERAL,
            cloneable=False,
            _scope_id=str(user_uuid),
            _scope_type=ScopeType.USER,
            user_uuid=user_uuid,
            user_role=UserRole.USER,
            creator_email="test@example.com",
        )

        with pytest.raises(VFolderInvalidParameter):
            await vfolder_service.create(action)

    async def test_max_vfolder_count_exceeded_raises_invalid_parameter(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.get_user_resource_info = AsyncMock(return_value=(5, 0, None))
        mock_vfolder_repository.ensure_host_permission_allowed = AsyncMock()
        mock_vfolder_repository.count_vfolders_by_user = AsyncMock(return_value=5)
        mock_vfolder_repository.check_vfolder_name_exists = AsyncMock(return_value=False)

        action = CreateVFolderAction(
            name="my-vfolder",
            keypair_resource_policy={"default": {}},
            domain_name="default",
            group_id_or_name=None,
            folder_host="local:volume1",
            unmanaged_path=None,
            mount_permission=VFolderPermission.READ_WRITE,
            usage_mode=VFolderUsageMode.GENERAL,
            cloneable=False,
            _scope_id=str(user_uuid),
            _scope_type=ScopeType.USER,
            user_uuid=user_uuid,
            user_role=UserRole.USER,
            creator_email="test@example.com",
        )

        with pytest.raises(VFolderInvalidParameter, match="cannot create more"):
            await vfolder_service.create(action)

    async def test_duplicate_name_raises_already_exists(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.get_user_resource_info = AsyncMock(return_value=(10, 0, None))
        mock_vfolder_repository.ensure_host_permission_allowed = AsyncMock()
        mock_vfolder_repository.count_vfolders_by_user = AsyncMock(return_value=0)
        mock_vfolder_repository.check_vfolder_name_exists = AsyncMock(return_value=True)

        action = CreateVFolderAction(
            name="existing-vfolder",
            keypair_resource_policy={"default": {}},
            domain_name="default",
            group_id_or_name=None,
            folder_host="local:volume1",
            unmanaged_path=None,
            mount_permission=VFolderPermission.READ_WRITE,
            usage_mode=VFolderUsageMode.GENERAL,
            cloneable=False,
            _scope_id=str(user_uuid),
            _scope_type=ScopeType.USER,
            user_uuid=user_uuid,
            user_role=UserRole.USER,
            creator_email="test@example.com",
        )

        with pytest.raises(VFolderAlreadyExists):
            await vfolder_service.create(action)

    async def test_dot_prefix_in_group_scope_raises_invalid_parameter(
        self,
        vfolder_service: VFolderService,
        user_uuid: uuid.UUID,
        group_uuid: uuid.UUID,
    ) -> None:
        action = CreateVFolderAction(
            name=".hidden",
            keypair_resource_policy={"default": {}},
            domain_name="default",
            group_id_or_name=str(group_uuid),
            folder_host="local:volume1",
            unmanaged_path=None,
            mount_permission=VFolderPermission.READ_WRITE,
            usage_mode=VFolderUsageMode.GENERAL,
            cloneable=False,
            _scope_id=str(group_uuid),
            _scope_type=ScopeType.PROJECT,
            user_uuid=user_uuid,
            user_role=UserRole.SUPERADMIN,
            creator_email="admin@example.com",
        )

        with pytest.raises(VFolderInvalidParameter, match="dot-prefixed"):
            await vfolder_service.create(action)

    async def test_model_usage_in_non_model_store_raises_invalid_parameter(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
        group_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.get_group_resource_info = AsyncMock(
            return_value=(group_uuid, 10, 0, ProjectType.MODEL_STORE)
        )
        mock_vfolder_repository.ensure_host_permission_allowed = AsyncMock()
        mock_vfolder_repository.count_vfolders_by_group = AsyncMock(return_value=0)
        mock_vfolder_repository.check_vfolder_name_exists = AsyncMock(return_value=False)

        action = CreateVFolderAction(
            name="non-model",
            keypair_resource_policy={"default": {}},
            domain_name="default",
            group_id_or_name=str(group_uuid),
            folder_host="local:volume1",
            unmanaged_path=None,
            mount_permission=VFolderPermission.READ_WRITE,
            usage_mode=VFolderUsageMode.GENERAL,
            cloneable=False,
            _scope_id=str(group_uuid),
            _scope_type=ScopeType.PROJECT,
            user_uuid=user_uuid,
            user_role=UserRole.SUPERADMIN,
            creator_email="admin@example.com",
        )

        with pytest.raises(VFolderInvalidParameter, match="Model VFolder"):
            await vfolder_service.create(action)

    async def test_storage_proxy_error_raises_creation_failure(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        mock_storage_manager: MagicMock,
        user_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.get_user_resource_info = AsyncMock(return_value=(10, 0, None))
        mock_vfolder_repository.ensure_host_permission_allowed = AsyncMock()
        mock_vfolder_repository.count_vfolders_by_user = AsyncMock(return_value=0)
        mock_vfolder_repository.check_vfolder_name_exists = AsyncMock(return_value=False)

        mock_client = mock_storage_manager.get_manager_facing_client.return_value
        mock_client.create_folder = AsyncMock(
            side_effect=aiohttp.ClientResponseError(
                request_info=MagicMock(),
                history=(),
                status=500,
                message="Internal Server Error",
            )
        )

        action = CreateVFolderAction(
            name="my-vfolder",
            keypair_resource_policy={"default": {}},
            domain_name="default",
            group_id_or_name=None,
            folder_host="local:volume1",
            unmanaged_path=None,
            mount_permission=VFolderPermission.READ_WRITE,
            usage_mode=VFolderUsageMode.GENERAL,
            cloneable=False,
            _scope_id=str(user_uuid),
            _scope_type=ScopeType.USER,
            user_uuid=user_uuid,
            user_role=UserRole.USER,
            creator_email="test@example.com",
        )

        with pytest.raises(VFolderCreationFailure):
            await vfolder_service.create(action)


class TestGetVFolderAction:
    async def test_owned_vfolder_returns_full_details(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        vfolder_data = _make_vfolder_data(vfolder_uuid, user_uuid)
        mock_vfolder_repository.get_user_info = AsyncMock(return_value=(UserRole.USER, "default"))
        mock_vfolder_repository.list_accessible_vfolders = AsyncMock(
            return_value=VFolderListResult(
                vfolders=[
                    VFolderAccessInfo(
                        vfolder_data=vfolder_data,
                        is_owner=True,
                        effective_permission=None,
                    )
                ]
            )
        )

        action = GetVFolderAction(
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
        )

        result = await vfolder_service.get(action)

        assert isinstance(result, GetVFolderActionResult)
        assert result.base_info.id == vfolder_uuid
        assert result.ownership_info.is_owner is True

    async def test_inaccessible_vfolder_raises_not_found(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.get_user_info = AsyncMock(return_value=(UserRole.USER, "default"))
        mock_vfolder_repository.list_accessible_vfolders = AsyncMock(
            return_value=VFolderListResult(vfolders=[])
        )

        action = GetVFolderAction(
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
        )

        with pytest.raises(VFolderNotFound):
            await vfolder_service.get(action)

    async def test_admin_non_owner_returns_effective_permission(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        vfolder_data = _make_vfolder_data(vfolder_uuid, uuid.uuid4())
        mock_vfolder_repository.get_user_info = AsyncMock(return_value=(UserRole.ADMIN, "default"))
        mock_vfolder_repository.list_accessible_vfolders = AsyncMock(
            return_value=VFolderListResult(
                vfolders=[
                    VFolderAccessInfo(
                        vfolder_data=vfolder_data,
                        is_owner=False,
                        effective_permission=VFolderMountPermission.READ_ONLY,
                    )
                ]
            )
        )

        action = GetVFolderAction(
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
        )

        result = await vfolder_service.get(action)

        assert result.ownership_info.is_owner is False
        assert result.base_info.mount_permission == VFolderMountPermission.READ_ONLY


class TestListVFolderAction:
    async def test_no_vfolders_returns_empty_list(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.get_user_info = AsyncMock(return_value=(UserRole.USER, "default"))
        mock_vfolder_repository.list_accessible_vfolders = AsyncMock(
            return_value=VFolderListResult(vfolders=[])
        )

        action = ListVFolderAction(
            user_uuid=user_uuid,
            _scope_type=ScopeType.USER,
            _scope_id=str(user_uuid),
        )

        result = await vfolder_service.list(action)

        assert isinstance(result, ListVFolderActionResult)
        assert result.vfolders == []

    async def test_returns_owned_and_shared_vfolders(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
    ) -> None:
        owned_data = _make_vfolder_data(uuid.uuid4(), user_uuid, name="owned")
        shared_data = _make_vfolder_data(uuid.uuid4(), uuid.uuid4(), name="shared")
        mock_vfolder_repository.get_user_info = AsyncMock(return_value=(UserRole.USER, "default"))
        mock_vfolder_repository.list_accessible_vfolders = AsyncMock(
            return_value=VFolderListResult(
                vfolders=[
                    VFolderAccessInfo(
                        vfolder_data=owned_data,
                        is_owner=True,
                        effective_permission=None,
                    ),
                    VFolderAccessInfo(
                        vfolder_data=shared_data,
                        is_owner=False,
                        effective_permission=VFolderMountPermission.READ_ONLY,
                    ),
                ]
            )
        )

        action = ListVFolderAction(
            user_uuid=user_uuid,
            _scope_type=ScopeType.USER,
            _scope_id=str(user_uuid),
        )

        result = await vfolder_service.list(action)

        assert len(result.vfolders) == 2

    async def test_admin_filtered_by_allowed_types(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        mock_config_provider: MagicMock,
        user_uuid: uuid.UUID,
    ) -> None:
        mock_config_provider.legacy_etcd_config_loader.get_vfolder_types = AsyncMock(
            return_value=["user"]
        )
        mock_vfolder_repository.get_user_info = AsyncMock(return_value=(UserRole.ADMIN, "default"))
        mock_vfolder_repository.list_accessible_vfolders = AsyncMock(
            return_value=VFolderListResult(vfolders=[])
        )

        action = ListVFolderAction(
            user_uuid=user_uuid,
            _scope_type=ScopeType.DOMAIN,
            _scope_id="default",
        )

        await vfolder_service.list(action)

        call_kwargs = mock_vfolder_repository.list_accessible_vfolders.call_args.kwargs
        assert call_kwargs["allowed_vfolder_types"] == ["user"]


class TestUpdateVFolderAttributeAction:
    async def test_unique_name_change_succeeds(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        vfolder_data = _make_vfolder_data(vfolder_uuid, user_uuid, name="old-name")
        mock_vfolder_repository.get_user_info = AsyncMock(return_value=(UserRole.USER, "default"))
        mock_vfolder_repository.list_accessible_vfolders = AsyncMock(
            return_value=VFolderListResult(
                vfolders=[
                    VFolderAccessInfo(
                        vfolder_data=vfolder_data,
                        is_owner=True,
                        effective_permission=None,
                    )
                ]
            )
        )
        mock_vfolder_repository.update_vfolder_attribute = AsyncMock()

        mock_name = MagicMock()
        mock_name.value.side_effect = ValueError
        spec = MagicMock()
        spec.name = mock_name
        updater = MagicMock()
        updater.spec = spec

        action = UpdateVFolderAttributeAction(
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
            updater=updater,
        )

        result = await vfolder_service.update_attribute(action)

        assert isinstance(result, UpdateVFolderAttributeActionResult)
        assert result.vfolder_uuid == vfolder_uuid

    async def test_duplicate_name_raises_invalid_parameter(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        vfolder_data = _make_vfolder_data(vfolder_uuid, user_uuid, name="existing-name")
        mock_vfolder_repository.get_user_info = AsyncMock(return_value=(UserRole.USER, "default"))
        mock_vfolder_repository.list_accessible_vfolders = AsyncMock(
            return_value=VFolderListResult(
                vfolders=[
                    VFolderAccessInfo(
                        vfolder_data=vfolder_data,
                        is_owner=True,
                        effective_permission=None,
                    )
                ]
            )
        )

        mock_name = MagicMock()
        mock_name.value.return_value = "existing-name"
        spec = MagicMock()
        spec.name = mock_name
        updater = MagicMock()
        updater.spec = spec

        action = UpdateVFolderAttributeAction(
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
            updater=updater,
        )

        with pytest.raises(VFolderInvalidParameter, match="already has the name"):
            await vfolder_service.update_attribute(action)

    async def test_no_accessible_vfolders_raises_not_found(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.get_user_info = AsyncMock(return_value=(UserRole.USER, "default"))
        mock_vfolder_repository.list_accessible_vfolders = AsyncMock(
            return_value=VFolderListResult(vfolders=[])
        )

        spec = MagicMock(spec=VFolderAttributeUpdaterSpec)
        updater = MagicMock()
        updater.spec = spec

        action = UpdateVFolderAttributeAction(
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
            updater=updater,
        )

        with pytest.raises(VFolderNotFound):
            await vfolder_service.update_attribute(action)


class TestMoveToTrashVFolderAction:
    async def test_status_changes_to_trash(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        vfolder_data = _make_vfolder_data(vfolder_uuid, user_uuid)
        mock_vfolder_repository.get_by_id_validated = AsyncMock(return_value=vfolder_data)
        mock_vfolder_repository.move_vfolders_to_trash = AsyncMock()

        action = MoveToTrashVFolderAction(
            user_uuid=user_uuid,
            keypair_resource_policy={"default": {}},
            vfolder_uuid=vfolder_uuid,
        )

        result = await vfolder_service.move_to_trash(action)

        assert isinstance(result, MoveToTrashVFolderActionResult)
        assert result.vfolder_uuid == vfolder_uuid
        mock_vfolder_repository.move_vfolders_to_trash.assert_called_once_with([vfolder_uuid])

    async def test_nonexistent_vfolder_raises_error(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.get_by_id_validated = AsyncMock(side_effect=VFolderNotFound())

        action = MoveToTrashVFolderAction(
            user_uuid=user_uuid,
            keypair_resource_policy={"default": {}},
            vfolder_uuid=vfolder_uuid,
        )

        with pytest.raises(VFolderNotFound):
            await vfolder_service.move_to_trash(action)


class TestRestoreVFolderFromTrashAction:
    async def test_status_restored_to_ready(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        vfolder_data = _make_vfolder_data(
            vfolder_uuid, user_uuid, status=VFolderOperationStatus.DELETE_PENDING
        )
        mock_vfolder_repository.get_by_id_validated = AsyncMock(return_value=vfolder_data)
        mock_vfolder_repository.restore_vfolders_from_trash = AsyncMock()

        action = RestoreVFolderFromTrashAction(
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
        )

        result = await vfolder_service.restore(action)

        assert isinstance(result, RestoreVFolderFromTrashActionResult)
        assert result.vfolder_uuid == vfolder_uuid
        mock_vfolder_repository.restore_vfolders_from_trash.assert_called_once_with([vfolder_uuid])

    async def test_nonexistent_vfolder_raises_error(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.get_by_id_validated = AsyncMock(side_effect=VFolderNotFound())

        action = RestoreVFolderFromTrashAction(
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
        )

        with pytest.raises(VFolderNotFound):
            await vfolder_service.restore(action)


class TestDeleteForeverVFolderAction:
    async def test_trash_state_removes_from_db_and_storage(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        mock_storage_manager: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        vfolder_data = _make_vfolder_data(
            vfolder_uuid, user_uuid, status=VFolderOperationStatus.DELETE_PENDING
        )
        mock_vfolder_repository.get_by_id_validated = AsyncMock(return_value=vfolder_data)
        mock_vfolder_repository.delete_vfolders_forever = AsyncMock()

        action = DeleteForeverVFolderAction(
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
        )

        result = await vfolder_service.delete_forever(action)

        assert isinstance(result, DeleteForeverVFolderActionResult)
        mock_vfolder_repository.delete_vfolders_forever.assert_called_once_with([vfolder_uuid])
        mock_client = mock_storage_manager.get_manager_facing_client.return_value
        mock_client.delete_folder.assert_called_once()

    async def test_storage_gone_catches_and_cleans_db(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        mock_storage_manager: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        vfolder_data = _make_vfolder_data(vfolder_uuid, user_uuid)
        mock_vfolder_repository.get_by_id_validated = AsyncMock(return_value=vfolder_data)
        mock_vfolder_repository.delete_vfolders_forever = AsyncMock()
        mock_client = mock_storage_manager.get_manager_facing_client.return_value
        mock_client.delete_folder = AsyncMock(side_effect=VFolderGone())

        action = DeleteForeverVFolderAction(
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
        )

        result = await vfolder_service.delete_forever(action)

        assert isinstance(result, DeleteForeverVFolderActionResult)
        mock_vfolder_repository.delete_vfolders_forever.assert_called_once()

    async def test_storage_not_found_catches_and_cleans_db(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        mock_storage_manager: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        vfolder_data = _make_vfolder_data(vfolder_uuid, user_uuid)
        mock_vfolder_repository.get_by_id_validated = AsyncMock(return_value=vfolder_data)
        mock_vfolder_repository.delete_vfolders_forever = AsyncMock()
        mock_client = mock_storage_manager.get_manager_facing_client.return_value
        mock_client.delete_folder = AsyncMock(side_effect=VFolderNotFound())

        action = DeleteForeverVFolderAction(
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
        )

        result = await vfolder_service.delete_forever(action)

        assert isinstance(result, DeleteForeverVFolderActionResult)
        mock_vfolder_repository.delete_vfolders_forever.assert_called_once()


class TestForceDeleteVFolderAction:
    async def test_ready_state_transitions_to_deletion(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        mock_storage_manager: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        vfolder_data = _make_vfolder_data(
            vfolder_uuid, user_uuid, status=VFolderOperationStatus.READY
        )
        mock_vfolder_repository.get_by_id_validated = AsyncMock(return_value=vfolder_data)
        mock_vfolder_repository.delete_vfolders_forever = AsyncMock()

        action = ForceDeleteVFolderAction(
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
        )

        result = await vfolder_service.force_delete(action)

        assert isinstance(result, ForceDeleteVFolderActionResult)
        assert result.vfolder_uuid == vfolder_uuid
        mock_vfolder_repository.delete_vfolders_forever.assert_called_once_with([vfolder_uuid])
        mock_client = mock_storage_manager.get_manager_facing_client.return_value
        mock_client.delete_folder.assert_called_once()


class TestCloneVFolderAction:
    async def test_clone_creates_target_vfolder_and_returns_task_id(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        source_data = _make_vfolder_data(vfolder_uuid, user_uuid, cloneable=True)
        task_id = uuid.uuid4()
        target_id = uuid.uuid4()

        mock_vfolder_repository.get_user_info = AsyncMock(return_value=(UserRole.USER, "default"))
        mock_vfolder_repository.list_accessible_vfolders = AsyncMock(
            return_value=VFolderListResult(
                vfolders=[
                    VFolderAccessInfo(
                        vfolder_data=source_data,
                        is_owner=True,
                        effective_permission=None,
                    )
                ]
            )
        )
        mock_vfolder_repository.check_vfolder_name_exists = AsyncMock(return_value=False)
        mock_vfolder_repository.get_allowed_vfolder_hosts = AsyncMock(
            return_value={"local:volume1": set()}
        )
        mock_vfolder_repository.ensure_host_permission_allowed = AsyncMock()
        mock_vfolder_repository.get_max_vfolder_count = AsyncMock(return_value=0)
        mock_vfolder_repository.get_user_email_by_id = AsyncMock(return_value="test@example.com")
        mock_vfolder_repository.initiate_vfolder_clone = AsyncMock(
            return_value=(task_id, target_id)
        )

        action = CloneVFolderAction(
            requester_user_uuid=user_uuid,
            source_vfolder_uuid=vfolder_uuid,
            target_name="cloned-vfolder",
            target_host=None,
            cloneable=True,
            usage_mode=VFolderUsageMode.GENERAL,
            mount_permission=VFolderPermission.READ_WRITE,
        )

        result = await vfolder_service.clone(action)

        assert isinstance(result, CloneVFolderActionResult)
        assert result.bgtask_id == task_id
        assert result.target_vfolder_id == target_id

    async def test_non_clonable_vfolder_raises_forbidden(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        source_data = _make_vfolder_data(vfolder_uuid, user_uuid, cloneable=False)
        mock_vfolder_repository.get_user_info = AsyncMock(return_value=(UserRole.USER, "default"))
        mock_vfolder_repository.list_accessible_vfolders = AsyncMock(
            return_value=VFolderListResult(
                vfolders=[
                    VFolderAccessInfo(
                        vfolder_data=source_data,
                        is_owner=True,
                        effective_permission=None,
                    )
                ]
            )
        )

        action = CloneVFolderAction(
            requester_user_uuid=user_uuid,
            source_vfolder_uuid=vfolder_uuid,
            target_name="cloned-vfolder",
            target_host=None,
            cloneable=True,
            usage_mode=VFolderUsageMode.GENERAL,
            mount_permission=VFolderPermission.READ_WRITE,
        )

        with pytest.raises(Forbidden, match="not permitted to be cloned"):
            await vfolder_service.clone(action)

    async def test_duplicate_target_name_raises_already_exists(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        source_data = _make_vfolder_data(vfolder_uuid, user_uuid, cloneable=True)
        mock_vfolder_repository.get_user_info = AsyncMock(return_value=(UserRole.USER, "default"))
        mock_vfolder_repository.list_accessible_vfolders = AsyncMock(
            return_value=VFolderListResult(
                vfolders=[
                    VFolderAccessInfo(
                        vfolder_data=source_data,
                        is_owner=True,
                        effective_permission=None,
                    )
                ]
            )
        )
        mock_vfolder_repository.check_vfolder_name_exists = AsyncMock(return_value=True)
        mock_vfolder_repository.get_allowed_vfolder_hosts = AsyncMock(
            return_value={"local:volume1": set()}
        )
        mock_vfolder_repository.ensure_host_permission_allowed = AsyncMock()

        action = CloneVFolderAction(
            requester_user_uuid=user_uuid,
            source_vfolder_uuid=vfolder_uuid,
            target_name="existing-name",
            target_host=None,
            cloneable=True,
            usage_mode=VFolderUsageMode.GENERAL,
            mount_permission=VFolderPermission.READ_WRITE,
        )

        with pytest.raises(VFolderAlreadyExists):
            await vfolder_service.clone(action)

    async def test_max_vfolder_count_exceeded_raises_invalid_parameter(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        source_data = _make_vfolder_data(vfolder_uuid, user_uuid, cloneable=True)
        mock_vfolder_repository.get_user_info = AsyncMock(return_value=(UserRole.USER, "default"))
        mock_vfolder_repository.list_accessible_vfolders = AsyncMock(
            return_value=VFolderListResult(
                vfolders=[
                    VFolderAccessInfo(
                        vfolder_data=source_data,
                        is_owner=True,
                        effective_permission=None,
                    )
                ]
            )
        )
        mock_vfolder_repository.check_vfolder_name_exists = AsyncMock(return_value=False)
        mock_vfolder_repository.get_allowed_vfolder_hosts = AsyncMock(
            return_value={"local:volume1": set()}
        )
        mock_vfolder_repository.ensure_host_permission_allowed = AsyncMock()
        mock_vfolder_repository.get_max_vfolder_count = AsyncMock(return_value=5)
        mock_vfolder_repository.count_vfolders_by_user = AsyncMock(return_value=5)

        action = CloneVFolderAction(
            requester_user_uuid=user_uuid,
            source_vfolder_uuid=vfolder_uuid,
            target_name="clone-target",
            target_host=None,
            cloneable=True,
            usage_mode=VFolderUsageMode.GENERAL,
            mount_permission=VFolderPermission.READ_WRITE,
        )

        with pytest.raises(VFolderInvalidParameter, match="cannot create more"):
            await vfolder_service.clone(action)


class TestGetAccessibleVFolderAction:
    async def test_lookup_by_uuid_succeeds(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.get_accessible_rows = AsyncMock(
            return_value=[{"id": vfolder_uuid, "name": "test-vfolder", "status": "ready"}]
        )

        action = GetAccessibleVFolderAction(
            user_uuid=user_uuid,
            user_role=UserRole.USER,
            domain_name="default",
            is_admin=False,
            perm=VFolderPermission.READ_ONLY,
            folder_id_or_name=vfolder_uuid,
        )

        result = await vfolder_service.get_accessible_vfolder(action)

        assert isinstance(result, GetAccessibleVFolderActionResult)
        assert result.row["id"] == vfolder_uuid

    async def test_lookup_by_name_succeeds(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.get_accessible_rows = AsyncMock(
            return_value=[{"id": vfolder_uuid, "name": "my-folder", "status": "ready"}]
        )

        action = GetAccessibleVFolderAction(
            user_uuid=user_uuid,
            user_role=UserRole.USER,
            domain_name="default",
            is_admin=False,
            perm=VFolderPermission.READ_ONLY,
            folder_id_or_name="my-folder",
        )

        result = await vfolder_service.get_accessible_vfolder(action)

        assert result.row["name"] == "my-folder"

    async def test_inaccessible_raises_not_found(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.get_accessible_rows = AsyncMock(return_value=[])

        action = GetAccessibleVFolderAction(
            user_uuid=user_uuid,
            user_role=UserRole.USER,
            domain_name="default",
            is_admin=False,
            perm=VFolderPermission.READ_ONLY,
            folder_id_or_name="nonexistent",
        )

        with pytest.raises(VFolderNotFound):
            await vfolder_service.get_accessible_vfolder(action)

    async def test_multiple_matches_raises_too_many(
        self,
        vfolder_service: VFolderService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.get_accessible_rows = AsyncMock(
            return_value=[
                {"id": uuid.uuid4(), "name": "dup", "status": "ready"},
                {"id": uuid.uuid4(), "name": "dup", "status": "ready"},
            ]
        )

        action = GetAccessibleVFolderAction(
            user_uuid=user_uuid,
            user_role=UserRole.USER,
            domain_name="default",
            is_admin=False,
            perm=VFolderPermission.READ_ONLY,
            folder_id_or_name="dup",
        )

        with pytest.raises(TooManyVFoldersFound):
            await vfolder_service.get_accessible_vfolder(action)
