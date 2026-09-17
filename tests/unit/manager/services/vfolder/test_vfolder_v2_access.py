"""
Unit tests for the v2 vfolder write paths refusing a folder shared read-only.
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
def vfolder_data(vfolder_uuid: VFolderUUID, owner_uuid: uuid.UUID) -> VFolderData:
    """A folder owned by someone else, whose own permission allows writing."""
    now = datetime.now(UTC)
    return VFolderData(
        id=vfolder_uuid,
        name="shared-folder",
        host="local:volume1",
        domain_name="default",
        quota_scope_id=QuotaScopeID(QuotaScopeType.USER, owner_uuid),
        usage_mode=VFolderUsageMode.GENERAL,
        permission=VFolderMountPermission.RW_DELETE,
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
        ownership_type=VFolderOwnershipType.USER,
        user=owner_uuid,
        group=None,
        cloneable=False,
        status=VFolderOperationStatus.READY,
    )


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
def mock_user_repository(invitee_uuid: uuid.UUID) -> MagicMock:
    repo = MagicMock()
    user = MagicMock()
    user.id = invitee_uuid
    user.domain_name = "default"
    user.role = UserRole.USER
    repo.get_user_by_uuid = AsyncMock(return_value=user)
    return repo


@pytest.fixture
def make_vfolder_repository(
    vfolder_data: VFolderData, invitee_uuid: uuid.UUID
) -> Callable[[VFolderMountPermission], MagicMock]:
    """Build a repository whose caller holds ``granted`` on the folder.

    ``ensure_writable`` stays the real rule so the refusal under test is the
    production one, not a mock's.
    """

    def _make(granted: VFolderMountPermission) -> MagicMock:
        repo = MagicMock(spec=VfolderRepository)
        repo.get_by_id_validated = AsyncMock(return_value=vfolder_data)
        repo.get_access_infos = AsyncMock(
            return_value=[
                VfolderRepository._resolve_access_info(vfolder_data, invitee_uuid, granted)
            ]
        )
        repo.ensure_writable = VfolderRepository.ensure_writable
        repo.ensure_host_permission_allowed_by_user = AsyncMock()
        return repo

    return _make


class TestUploadSessionV2RefusesReadOnlyFolder:
    async def test_read_only_invitee_cannot_create_an_upload_session(
        self,
        mock_storage_manager: MagicMock,
        mock_user_repository: MagicMock,
        make_vfolder_repository: Callable[[VFolderMountPermission], MagicMock],
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
            user_repository=mock_user_repository,
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
        mock_user_repository: MagicMock,
        make_vfolder_repository: Callable[[VFolderMountPermission], MagicMock],
        invitee_uuid: uuid.UUID,
        vfolder_uuid: VFolderUUID,
    ) -> None:
        service = VFolderService(
            config_provider=MagicMock(),
            etcd=MagicMock(),
            storage_manager=mock_storage_manager,
            background_task_manager=MagicMock(),
            vfolder_repository=make_vfolder_repository(VFolderMountPermission.READ_WRITE),
            user_repository=mock_user_repository,
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
        mock_user_repository: MagicMock,
        make_vfolder_repository: Callable[[VFolderMountPermission], MagicMock],
    ) -> VFolderFileService:
        return VFolderFileService(
            config_provider=MagicMock(),
            storage_manager=mock_storage_manager,
            vfolder_repository=make_vfolder_repository(VFolderMountPermission.READ_ONLY),
            user_repository=mock_user_repository,
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
