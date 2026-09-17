"""
Unit tests for the caller-relative vfolder access rules and their enforcement on
the v2 write paths.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.bgtask.types import TaskID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.storage.response import FileDeleteAsyncResponse
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.common.types import QuotaScopeID, QuotaScopeType, VFolderUsageMode
from ai.backend.manager.data.vfolder.types import (
    VFolderData,
    VFolderMountPermission,
    VFolderOperationStatus,
    VFolderOwnershipType,
)
from ai.backend.manager.errors.storage import VFolderPermissionError
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.services.vfolder.access import ensure_writable, resolve_access_info
from ai.backend.manager.services.vfolder.actions.file_v2 import (
    DeleteFilesV2Action,
    MkdirV2Action,
    MoveFileV2Action,
)
from ai.backend.manager.services.vfolder.actions.upload_session_v2 import (
    CreateUploadSessionV2Action,
)
from ai.backend.manager.services.vfolder.services.file import VFolderFileService
from ai.backend.manager.services.vfolder.services.vfolder import VFolderService

VFolderDataFactory = Callable[..., VFolderData]


@pytest.fixture
def owner_uuid() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def invitee_uuid() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def vfolder_uuid() -> VFolderUUID:
    return VFolderUUID(uuid.uuid4())


@pytest.fixture
def make_vfolder_data(vfolder_uuid: VFolderUUID, owner_uuid: uuid.UUID) -> VFolderDataFactory:
    def _make(
        *,
        ownership_type: VFolderOwnershipType = VFolderOwnershipType.USER,
        permission: VFolderMountPermission | None = VFolderMountPermission.OWNER_PERM,
        user: uuid.UUID | None = None,
        group: uuid.UUID | None = None,
    ) -> VFolderData:
        now = datetime.now(UTC)
        return VFolderData(
            id=vfolder_uuid,
            name="shared-folder",
            host="local:volume1",
            domain_name="default",
            quota_scope_id=QuotaScopeID(QuotaScopeType.USER, owner_uuid),
            usage_mode=VFolderUsageMode.GENERAL,
            permission=permission,
            max_files=1000,
            max_size=None,
            num_files=0,
            cur_size=0,
            created_at=now,
            last_used=None,
            updated_at=now,
            creator="owner@example.com",
            creator_id=owner_uuid,
            unmanaged_path=None,
            ownership_type=ownership_type,
            user=owner_uuid
            if user is None and ownership_type is VFolderOwnershipType.USER
            else user,
            group=group,
            cloneable=False,
            status=VFolderOperationStatus.READY,
        )

    return _make


class TestResolveAccessInfo:
    def test_owner_of_user_folder_reads_the_folder_permission(
        self, make_vfolder_data: VFolderDataFactory, owner_uuid: uuid.UUID
    ) -> None:
        vfolder_data = make_vfolder_data(permission=VFolderMountPermission.READ_WRITE)

        access_info = resolve_access_info(vfolder_data, owner_uuid, None)

        assert access_info.is_owner is True
        assert access_info.effective_permission is VFolderMountPermission.READ_WRITE

    def test_invitee_holds_the_granted_permission_not_the_folder_default(
        self, make_vfolder_data: VFolderDataFactory, invitee_uuid: uuid.UUID
    ) -> None:
        # The folder's own column says rw-delete; the invitee was granted ro.
        access_info = resolve_access_info(
            make_vfolder_data(), invitee_uuid, VFolderMountPermission.READ_ONLY
        )

        assert access_info.is_owner is False
        assert access_info.effective_permission is VFolderMountPermission.READ_ONLY

    def test_stranger_of_user_folder_holds_no_permission(
        self, make_vfolder_data: VFolderDataFactory, invitee_uuid: uuid.UUID
    ) -> None:
        access_info = resolve_access_info(make_vfolder_data(), invitee_uuid, None)

        assert access_info.is_owner is False
        assert access_info.effective_permission is None

    def test_project_member_inherits_the_folder_permission(
        self, make_vfolder_data: VFolderDataFactory, invitee_uuid: uuid.UUID
    ) -> None:
        vfolder_data = make_vfolder_data(
            ownership_type=VFolderOwnershipType.GROUP,
            permission=VFolderMountPermission.READ_WRITE,
            group=uuid.uuid4(),
        )

        access_info = resolve_access_info(vfolder_data, invitee_uuid, None)

        assert access_info.is_owner is False
        assert access_info.effective_permission is VFolderMountPermission.READ_WRITE

    def test_explicit_grant_overrides_the_project_folder_permission(
        self, make_vfolder_data: VFolderDataFactory, invitee_uuid: uuid.UUID
    ) -> None:
        vfolder_data = make_vfolder_data(
            ownership_type=VFolderOwnershipType.GROUP,
            permission=VFolderMountPermission.READ_WRITE,
            group=uuid.uuid4(),
        )

        access_info = resolve_access_info(
            vfolder_data, invitee_uuid, VFolderMountPermission.READ_ONLY
        )

        assert access_info.effective_permission is VFolderMountPermission.READ_ONLY


class TestEnsureWritable:
    def test_read_only_permission_is_refused(
        self, make_vfolder_data: VFolderDataFactory, invitee_uuid: uuid.UUID
    ) -> None:
        access_info = resolve_access_info(
            make_vfolder_data(), invitee_uuid, VFolderMountPermission.READ_ONLY
        )

        with pytest.raises(VFolderPermissionError):
            ensure_writable(access_info, UserRole.USER)

    def test_absent_permission_is_refused(
        self, make_vfolder_data: VFolderDataFactory, invitee_uuid: uuid.UUID
    ) -> None:
        access_info = resolve_access_info(make_vfolder_data(), invitee_uuid, None)

        with pytest.raises(VFolderPermissionError):
            ensure_writable(access_info, UserRole.USER)

    @pytest.mark.parametrize(
        "permission",
        [VFolderMountPermission.READ_WRITE, VFolderMountPermission.RW_DELETE],
    )
    def test_writable_permissions_pass(
        self,
        make_vfolder_data: VFolderDataFactory,
        invitee_uuid: uuid.UUID,
        permission: VFolderMountPermission,
    ) -> None:
        access_info = resolve_access_info(make_vfolder_data(), invitee_uuid, permission)

        ensure_writable(access_info, UserRole.USER)

    def test_owner_passes_even_when_the_folder_permission_is_read_only(
        self, make_vfolder_data: VFolderDataFactory, owner_uuid: uuid.UUID
    ) -> None:
        vfolder_data = make_vfolder_data(permission=VFolderMountPermission.READ_ONLY)

        access_info = resolve_access_info(vfolder_data, owner_uuid, None)

        ensure_writable(access_info, UserRole.USER)

    @pytest.mark.parametrize("role", [UserRole.ADMIN, UserRole.SUPERADMIN])
    def test_admins_keep_privileged_access(
        self,
        make_vfolder_data: VFolderDataFactory,
        invitee_uuid: uuid.UUID,
        role: UserRole,
    ) -> None:
        access_info = resolve_access_info(
            make_vfolder_data(), invitee_uuid, VFolderMountPermission.READ_ONLY
        )

        ensure_writable(access_info, role)


@pytest.fixture
def mock_storage_manager() -> MagicMock:
    manager = MagicMock()
    manager.get_proxy_and_volume.return_value = ("proxy1", "volume1")
    client = MagicMock()
    client.upload_file = AsyncMock(return_value={"token": "upload-token-123"})
    client.mkdir = AsyncMock()
    client.move_file = AsyncMock()
    client.delete_files_async = AsyncMock(
        return_value=FileDeleteAsyncResponse(bgtask_id=TaskID(uuid.uuid4()))
    )
    manager.get_manager_facing_client.return_value = client
    manager.get_client_api_url.return_value = MagicMock(
        __truediv__=lambda self, path: f"http://storage:6021/{path}"
    )
    return manager


@pytest.fixture
def make_user_repository(invitee_uuid: uuid.UUID) -> Callable[[UserRole], MagicMock]:
    def _make(role: UserRole) -> MagicMock:
        repo = MagicMock()
        user = MagicMock()
        user.id = invitee_uuid
        user.domain_name = "default"
        user.role = role
        repo.get_user_by_uuid = AsyncMock(return_value=user)
        return repo

    return _make


@pytest.fixture
def make_vfolder_repository(
    make_vfolder_data: VFolderDataFactory, vfolder_uuid: VFolderUUID
) -> Callable[[VFolderMountPermission | None], MagicMock]:
    def _make(granted: VFolderMountPermission | None) -> MagicMock:
        repo = MagicMock(spec=VfolderRepository)
        repo.get_by_id_validated = AsyncMock(return_value=make_vfolder_data())
        repo.get_granted_mount_permissions = AsyncMock(
            return_value={vfolder_uuid: granted} if granted is not None else {}
        )
        repo.ensure_host_permission_allowed_by_user = AsyncMock()
        return repo

    return _make


class TestUploadSessionV2RefusesReadOnlyFolder:
    async def test_read_only_invitee_cannot_create_an_upload_session(
        self,
        mock_storage_manager: MagicMock,
        make_user_repository: Callable[[UserRole], MagicMock],
        make_vfolder_repository: Callable[[VFolderMountPermission | None], MagicMock],
        invitee_uuid: uuid.UUID,
        vfolder_uuid: VFolderUUID,
    ) -> None:
        vfolder_repository = make_vfolder_repository(VFolderMountPermission.READ_ONLY)
        service = VFolderService(
            config_provider=MagicMock(),
            etcd=MagicMock(),
            storage_manager=mock_storage_manager,
            background_task_manager=MagicMock(),
            vfolder_repository=vfolder_repository,
            user_repository=make_user_repository(UserRole.USER),
            valkey_stat_client=MagicMock(),
        )
        action = CreateUploadSessionV2Action(
            user_id=invitee_uuid,
            vfolder_id=vfolder_uuid,
            path="data/file.bin",
            size=4096,
        )

        with pytest.raises(VFolderPermissionError):
            await service.create_upload_session_v2(action)

        vfolder_repository.ensure_host_permission_allowed_by_user.assert_not_called()

    async def test_read_write_invitee_gets_a_token(
        self,
        mock_storage_manager: MagicMock,
        make_user_repository: Callable[[UserRole], MagicMock],
        make_vfolder_repository: Callable[[VFolderMountPermission | None], MagicMock],
        invitee_uuid: uuid.UUID,
        vfolder_uuid: VFolderUUID,
    ) -> None:
        service = VFolderService(
            config_provider=MagicMock(),
            etcd=MagicMock(),
            storage_manager=mock_storage_manager,
            background_task_manager=MagicMock(),
            vfolder_repository=make_vfolder_repository(VFolderMountPermission.READ_WRITE),
            user_repository=make_user_repository(UserRole.USER),
            valkey_stat_client=MagicMock(),
        )
        action = CreateUploadSessionV2Action(
            user_id=invitee_uuid,
            vfolder_id=vfolder_uuid,
            path="data/file.bin",
            size=4096,
        )

        result = await service.create_upload_session_v2(action)

        assert result.token == "upload-token-123"


class TestFileV2OperationsRefuseReadOnlyFolder:
    @pytest.fixture
    def file_service(
        self,
        mock_storage_manager: MagicMock,
        make_user_repository: Callable[[UserRole], MagicMock],
        make_vfolder_repository: Callable[[VFolderMountPermission | None], MagicMock],
    ) -> VFolderFileService:
        return VFolderFileService(
            config_provider=MagicMock(),
            storage_manager=mock_storage_manager,
            vfolder_repository=make_vfolder_repository(VFolderMountPermission.READ_ONLY),
            user_repository=make_user_repository(UserRole.USER),
        )

    async def test_mkdir_is_refused(
        self,
        file_service: VFolderFileService,
        invitee_uuid: uuid.UUID,
        vfolder_uuid: VFolderUUID,
    ) -> None:
        action = MkdirV2Action(user_id=invitee_uuid, vfolder_id=vfolder_uuid, path="newdir")

        with pytest.raises(VFolderPermissionError):
            await file_service.mkdir_v2(action)

    async def test_move_file_is_refused(
        self,
        file_service: VFolderFileService,
        invitee_uuid: uuid.UUID,
        vfolder_uuid: VFolderUUID,
    ) -> None:
        action = MoveFileV2Action(
            user_id=invitee_uuid, vfolder_id=vfolder_uuid, src="a.txt", dst="b.txt"
        )

        with pytest.raises(VFolderPermissionError):
            await file_service.move_file_v2(action)

    async def test_delete_files_is_refused(
        self,
        file_service: VFolderFileService,
        invitee_uuid: uuid.UUID,
        vfolder_uuid: VFolderUUID,
    ) -> None:
        action = DeleteFilesV2Action(user_id=invitee_uuid, vfolder_id=vfolder_uuid, files=["a.txt"])

        with pytest.raises(VFolderPermissionError):
            await file_service.delete_files_v2(action)
