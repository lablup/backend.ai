"""
Unit tests for VFolderFileService file operations.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.bgtask.types import TaskID
from ai.backend.common.dto.storage.response import FileDeleteAsyncResponse
from ai.backend.common.types import (
    QuotaScopeID,
    QuotaScopeType,
)
from ai.backend.manager.errors.storage import VFolderInvalidParameter
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.services.vfolder.actions.file import (
    CreateDownloadSessionAction,
    CreateUploadSessionAction,
    DeleteFilesAction,
    DeleteFilesAsyncAction,
    ListFilesAction,
    MkdirAction,
    RenameFileAction,
)
from ai.backend.manager.services.vfolder.services.file import VFolderFileService


@pytest.fixture
def user_uuid() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def vfolder_uuid() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def mock_vfolder_repository() -> MagicMock:
    return MagicMock(spec=VfolderRepository)


@pytest.fixture
def mock_config_provider() -> MagicMock:
    provider = MagicMock()
    provider.legacy_etcd_config_loader.get_vfolder_types = AsyncMock(return_value=["user", "group"])
    return provider


@pytest.fixture
def mock_storage_manager() -> MagicMock:
    manager = MagicMock()
    manager.get_proxy_and_volume.return_value = ("proxy1", "volume1")
    mock_client = MagicMock()
    mock_client.upload_file = AsyncMock(return_value={"token": "upload-token-123"})
    mock_client.download_file = AsyncMock(return_value={"token": "download-token-456"})
    mock_client.create_archive_download_token = AsyncMock(
        return_value={"token": "archive-token-789"}
    )
    mock_client.list_files = AsyncMock(
        return_value={
            "items": [
                {
                    "name": "test.txt",
                    "type": "FILE",
                    "stat": {
                        "size": 1024,
                        "mode": "0644",
                        "created": "2025-01-01T00:00:00",
                        "modified": "2025-01-02T00:00:00",
                    },
                },
            ]
        }
    )
    mock_client.rename_file = AsyncMock()
    mock_client.delete_files = AsyncMock()
    mock_client.delete_files_async = AsyncMock(
        return_value=FileDeleteAsyncResponse(bgtask_id=TaskID(uuid.uuid4()))
    )
    mock_client.mkdir = AsyncMock(
        return_value={"results": {"success": [{"item": "newdir", "msg": None}], "failed": []}}
    )
    manager.get_manager_facing_client.return_value = mock_client
    manager.get_client_api_url.return_value = MagicMock(
        __truediv__=lambda self, path: f"http://storage:6021/{path}"
    )
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
def keypair_resource_policy() -> dict[str, str]:
    return {"default_for_unspecified": "UNLIMITED"}


@pytest.fixture
def mock_vfolder_data(vfolder_uuid: uuid.UUID) -> MagicMock:
    data = MagicMock()
    data.id = vfolder_uuid
    data.host = "local:volume1"
    data.domain_name = "default"
    data.quota_scope_id = QuotaScopeID(QuotaScopeType.USER, uuid.uuid4())
    data.unmanaged_path = None
    return data


@pytest.fixture
def file_service(
    mock_config_provider: MagicMock,
    mock_storage_manager: MagicMock,
    mock_vfolder_repository: MagicMock,
    mock_user_repository: MagicMock,
) -> VFolderFileService:
    return VFolderFileService(
        config_provider=mock_config_provider,
        storage_manager=mock_storage_manager,
        vfolder_repository=mock_vfolder_repository,
        user_repository=mock_user_repository,
    )


class TestCreateUploadSessionAction:
    async def test_accessible_vfolder_returns_token_and_url(
        self,
        file_service: VFolderFileService,
        mock_vfolder_repository: MagicMock,
        mock_vfolder_data: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
        keypair_resource_policy: dict[str, str],
    ) -> None:
        mock_vfolder_repository.get_by_id_validated = AsyncMock(return_value=mock_vfolder_data)
        mock_vfolder_repository.ensure_host_permission_allowed = AsyncMock()

        action = CreateUploadSessionAction(
            keypair_resource_policy=keypair_resource_policy,
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
            path="data/file.bin",
            size="4096",
        )
        result = await file_service.upload_file(action)

        assert result.token == "upload-token-123"
        assert "upload" in result.url
        assert result.vfolder_uuid == vfolder_uuid

    async def test_inaccessible_vfolder_raises_invalid_parameter(
        self,
        file_service: VFolderFileService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
        keypair_resource_policy: dict[str, str],
    ) -> None:
        mock_vfolder_repository.get_by_id_validated = AsyncMock(return_value=None)

        action = CreateUploadSessionAction(
            keypair_resource_policy=keypair_resource_policy,
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
            path="data/file.bin",
            size="4096",
        )
        with pytest.raises(VFolderInvalidParameter):
            await file_service.upload_file(action)

    async def test_no_upload_permission_raises_error(
        self,
        file_service: VFolderFileService,
        mock_vfolder_repository: MagicMock,
        mock_vfolder_data: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
        keypair_resource_policy: dict[str, str],
    ) -> None:
        mock_vfolder_repository.get_by_id_validated = AsyncMock(return_value=mock_vfolder_data)
        mock_vfolder_repository.ensure_host_permission_allowed = AsyncMock(
            side_effect=VFolderInvalidParameter("No permission")
        )

        action = CreateUploadSessionAction(
            keypair_resource_policy=keypair_resource_policy,
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
            path="data/file.bin",
            size="4096",
        )
        with pytest.raises(VFolderInvalidParameter):
            await file_service.upload_file(action)


class TestCreateDownloadSessionAction:
    async def test_existing_file_returns_token_and_url(
        self,
        file_service: VFolderFileService,
        mock_vfolder_repository: MagicMock,
        mock_vfolder_data: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
        keypair_resource_policy: dict[str, str],
    ) -> None:
        mock_vfolder_repository.get_by_id_validated = AsyncMock(return_value=mock_vfolder_data)
        mock_vfolder_repository.ensure_host_permission_allowed = AsyncMock()

        action = CreateDownloadSessionAction(
            keypair_resource_policy=keypair_resource_policy,
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
            path="data/file.bin",
            archive=False,
        )
        result = await file_service.download_file(action)

        assert result.token == "download-token-456"
        assert "download" in result.url
        assert result.vfolder_uuid == vfolder_uuid

    async def test_archive_true_creates_archive_session(
        self,
        file_service: VFolderFileService,
        mock_vfolder_repository: MagicMock,
        mock_storage_manager: MagicMock,
        mock_vfolder_data: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
        keypair_resource_policy: dict[str, str],
    ) -> None:
        mock_vfolder_repository.get_by_id_validated = AsyncMock(return_value=mock_vfolder_data)
        mock_vfolder_repository.ensure_host_permission_allowed = AsyncMock()

        action = CreateDownloadSessionAction(
            keypair_resource_policy=keypair_resource_policy,
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
            path="data/",
            archive=True,
        )
        result = await file_service.download_file(action)

        mock_client = mock_storage_manager.get_manager_facing_client.return_value
        mock_client.download_file.assert_called_once()
        call_kwargs = mock_client.download_file.call_args
        assert call_kwargs.kwargs["archive"] is True
        assert result.token == "download-token-456"

    async def test_no_download_permission_raises_error(
        self,
        file_service: VFolderFileService,
        mock_vfolder_repository: MagicMock,
        mock_vfolder_data: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
        keypair_resource_policy: dict[str, str],
    ) -> None:
        mock_vfolder_repository.get_by_id_validated = AsyncMock(return_value=mock_vfolder_data)
        mock_vfolder_repository.ensure_host_permission_allowed = AsyncMock(
            side_effect=VFolderInvalidParameter("No permission")
        )

        action = CreateDownloadSessionAction(
            keypair_resource_policy=keypair_resource_policy,
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
            path="data/file.bin",
            archive=False,
        )
        with pytest.raises(VFolderInvalidParameter):
            await file_service.download_file(action)


class TestListFilesAction:
    async def test_root_returns_file_metadata(
        self,
        file_service: VFolderFileService,
        mock_vfolder_repository: MagicMock,
        mock_vfolder_data: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.get_by_id_validated = AsyncMock(return_value=mock_vfolder_data)

        action = ListFilesAction(
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
            path=".",
        )
        result = await file_service.list_files(action)

        assert len(result.files) == 1
        file_info = result.files[0]
        assert file_info.name == "test.txt"
        assert file_info.type == "FILE"
        assert file_info.size == 1024
        assert file_info.mode == "0644"
        assert file_info.created == "2025-01-01T00:00:00"
        assert file_info.modified == "2025-01-02T00:00:00"

    async def test_nested_directory_passes_path_parameter(
        self,
        file_service: VFolderFileService,
        mock_vfolder_repository: MagicMock,
        mock_storage_manager: MagicMock,
        mock_vfolder_data: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.get_by_id_validated = AsyncMock(return_value=mock_vfolder_data)

        action = ListFilesAction(
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
            path="subdir/nested",
        )
        await file_service.list_files(action)

        mock_client = mock_storage_manager.get_manager_facing_client.return_value
        mock_client.list_files.assert_called_once()
        call_args = mock_client.list_files.call_args[0]
        assert call_args[2] == "subdir/nested"


class TestRenameFileAction:
    async def test_modify_permission_executes_rename(
        self,
        file_service: VFolderFileService,
        mock_vfolder_repository: MagicMock,
        mock_storage_manager: MagicMock,
        mock_vfolder_data: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
        keypair_resource_policy: dict[str, str],
    ) -> None:
        mock_vfolder_repository.get_by_id_validated = AsyncMock(return_value=mock_vfolder_data)
        mock_vfolder_repository.ensure_host_permission_allowed = AsyncMock()

        action = RenameFileAction(
            user_uuid=user_uuid,
            keypair_resource_policy=keypair_resource_policy,
            vfolder_uuid=vfolder_uuid,
            target_path="old_name.txt",
            new_name="new_name.txt",
        )
        result = await file_service.rename_file(action)

        assert result.vfolder_uuid == vfolder_uuid
        mock_client = mock_storage_manager.get_manager_facing_client.return_value
        mock_client.rename_file.assert_called_once()

    async def test_no_modify_permission_raises_error(
        self,
        file_service: VFolderFileService,
        mock_vfolder_repository: MagicMock,
        mock_vfolder_data: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
        keypair_resource_policy: dict[str, str],
    ) -> None:
        mock_vfolder_repository.get_by_id_validated = AsyncMock(return_value=mock_vfolder_data)
        mock_vfolder_repository.ensure_host_permission_allowed = AsyncMock(
            side_effect=VFolderInvalidParameter("No permission")
        )

        action = RenameFileAction(
            user_uuid=user_uuid,
            keypair_resource_policy=keypair_resource_policy,
            vfolder_uuid=vfolder_uuid,
            target_path="old_name.txt",
            new_name="new_name.txt",
        )
        with pytest.raises(VFolderInvalidParameter):
            await file_service.rename_file(action)


class TestDeleteFilesAction:
    async def test_single_file_sync_deletion(
        self,
        file_service: VFolderFileService,
        mock_vfolder_repository: MagicMock,
        mock_storage_manager: MagicMock,
        mock_vfolder_data: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.get_by_id_validated = AsyncMock(return_value=mock_vfolder_data)

        action = DeleteFilesAction(
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
            files=["file.txt"],
            recursive=False,
        )
        result = await file_service.delete_files(action)

        assert result.vfolder_uuid == vfolder_uuid
        mock_client = mock_storage_manager.get_manager_facing_client.return_value
        mock_client.delete_files.assert_called_once()

    async def test_multiple_files_with_recursive_flag(
        self,
        file_service: VFolderFileService,
        mock_vfolder_repository: MagicMock,
        mock_storage_manager: MagicMock,
        mock_vfolder_data: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.get_by_id_validated = AsyncMock(return_value=mock_vfolder_data)

        action = DeleteFilesAction(
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
            files=["dir1/", "dir2/", "file.txt"],
            recursive=True,
        )
        result = await file_service.delete_files(action)

        assert result.vfolder_uuid == vfolder_uuid
        mock_client = mock_storage_manager.get_manager_facing_client.return_value
        call_args = mock_client.delete_files.call_args[0]
        assert call_args[2] == ["dir1/", "dir2/", "file.txt"]
        assert call_args[3] is True


class TestDeleteFilesAsyncAction:
    async def test_async_deletion_returns_task_id(
        self,
        file_service: VFolderFileService,
        mock_vfolder_repository: MagicMock,
        mock_vfolder_data: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.get_by_id_validated = AsyncMock(return_value=mock_vfolder_data)

        action = DeleteFilesAsyncAction(
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
            files=["large_dir/"],
            recursive=True,
        )
        result = await file_service.delete_files_async(action)

        assert result.vfolder_uuid == vfolder_uuid
        assert result.task_id is not None

    async def test_inaccessible_vfolder_raises_invalid_parameter(
        self,
        file_service: VFolderFileService,
        mock_vfolder_repository: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.get_by_id_validated = AsyncMock(return_value=None)

        action = DeleteFilesAsyncAction(
            user_uuid=user_uuid,
            vfolder_uuid=vfolder_uuid,
            files=["file.txt"],
            recursive=False,
        )
        with pytest.raises(VFolderInvalidParameter):
            await file_service.delete_files_async(action)


class TestMkdirAction:
    async def test_single_directory_creation(
        self,
        file_service: VFolderFileService,
        mock_vfolder_repository: MagicMock,
        mock_vfolder_data: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.get_by_id_validated = AsyncMock(return_value=mock_vfolder_data)

        action = MkdirAction(
            user_id=user_uuid,
            vfolder_uuid=vfolder_uuid,
            path="newdir",
            parents=False,
            exist_ok=False,
        )
        result = await file_service.mkdir(action)

        assert result.vfolder_uuid == vfolder_uuid
        assert result.storage_resp_status == 200
        assert result.results == {"success": [{"item": "newdir", "msg": None}], "failed": []}

    async def test_parents_true_creates_intermediate_dirs(
        self,
        file_service: VFolderFileService,
        mock_vfolder_repository: MagicMock,
        mock_storage_manager: MagicMock,
        mock_vfolder_data: MagicMock,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        mock_vfolder_repository.get_by_id_validated = AsyncMock(return_value=mock_vfolder_data)

        action = MkdirAction(
            user_id=user_uuid,
            vfolder_uuid=vfolder_uuid,
            path="a/b/c",
            parents=True,
            exist_ok=False,
        )
        await file_service.mkdir(action)

        mock_client = mock_storage_manager.get_manager_facing_client.return_value
        call_kwargs = mock_client.mkdir.call_args.kwargs
        assert call_kwargs["parents"] is True

    async def test_over_50_dirs_raises_invalid_parameter(
        self,
        file_service: VFolderFileService,
        user_uuid: uuid.UUID,
        vfolder_uuid: uuid.UUID,
    ) -> None:
        dirs = [f"dir{i}" for i in range(51)]
        action = MkdirAction(
            user_id=user_uuid,
            vfolder_uuid=vfolder_uuid,
            path=dirs,
            parents=False,
            exist_ok=False,
        )
        with pytest.raises(VFolderInvalidParameter):
            await file_service.mkdir(action)
