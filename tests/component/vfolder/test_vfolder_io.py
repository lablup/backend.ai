"""Component tests for VFolder IO operations: file operations and mount operations.

These tests verify HTTP API routing, auth decorators, and request/response serialization.
Business logic is tested in unit tests.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
import yarl
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.vfolder import (
    CreateDownloadSessionReq,
    CreateDownloadSessionResponse,
    CreateUploadSessionReq,
    CreateUploadSessionResponse,
    DeleteFilesAsyncBodyParam,
    DeleteFilesAsyncResponse,
    DeleteFilesReq,
    GetFstabContentsQuery,
    GetFstabContentsResponse,
    ListFilesQuery,
    ListFilesResponse,
    ListMountsResponse,
    MessageResponse,
    MkdirReq,
    MkdirResponse,
    MountHostReq,
    MoveFileReq,
    RenameFileReq,
    UmountHostReq,
)
from ai.backend.common.types import VFolderHostPermission, VFolderHostPermissionMap
from ai.backend.manager.models.domain import domains
from ai.backend.manager.models.resource_policy import keypair_resource_policies
from ai.backend.manager.models.storage import StorageSessionManager

VFolderFixtureData = dict[str, Any]
VFolderFactory = Callable[..., Coroutine[Any, Any, VFolderFixtureData]]


def _configure_storage_mock(storage_manager: StorageSessionManager) -> AsyncMock:
    """Configure storage_manager mock with sensible defaults for file operations.

    Returns the mock client so tests can further configure it.
    """
    mock_client = AsyncMock()
    storage_manager.get_proxy_and_volume.return_value = ("local", "volume1")  # type: ignore[attr-defined]
    storage_manager.get_manager_facing_client.return_value = mock_client  # type: ignore[attr-defined]
    storage_manager.get_client_api_url.return_value = yarl.URL("http://storage-proxy:8080")  # type: ignore[attr-defined]

    # Default return values for all storage proxy client methods
    mock_client.upload_file.return_value = {
        "token": "upload-token-abc",
        "url": "http://storage-proxy:8080/upload",
    }
    mock_client.download_file.return_value = {
        "token": "download-token-xyz",
        "url": "http://storage-proxy:8080/download",
    }
    mock_client.list_files.return_value = {"items": []}
    mock_client.rename_file.return_value = None
    mock_client.move_file.return_value = None
    mock_client.delete_files.return_value = None
    mock_client.mkdir.return_value = {"results": []}

    # delete_files_async needs a response with bgtask_id
    async_response = MagicMock()
    async_response.bgtask_id = uuid.uuid4()
    mock_client.delete_files_async.return_value = async_response

    return mock_client


@pytest.fixture()
async def no_upload_permission_vfolder(
    db_engine: SAEngine,
    domain_fixture: str,
    resource_policy_fixture: str,
    vfolder_factory: VFolderFactory,
) -> AsyncIterator[VFolderFixtureData]:
    """Create a vfolder and restrict the host to disallow UPLOAD_FILE.

    The vfolder is created while all permissions are in place (via vfolder_factory's
    transitive dependency on vfolder_host_permission_fixture). Afterwards the host
    permissions are narrowed to exclude UPLOAD_FILE.
    """
    vf = await vfolder_factory()
    restricted: set[VFolderHostPermission] = set(VFolderHostPermission) - {
        VFolderHostPermission.UPLOAD_FILE
    }
    host_perms = VFolderHostPermissionMap({"local": restricted})
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.update(domains)
            .where(domains.c.name == domain_fixture)
            .values(allowed_vfolder_hosts=host_perms)
        )
        await conn.execute(
            sa.update(keypair_resource_policies)
            .where(keypair_resource_policies.c.name == resource_policy_fixture)
            .values(allowed_vfolder_hosts=host_perms)
        )
        await conn.execute(
            sa.update(keypair_resource_policies)
            .where(keypair_resource_policies.c.name == "default")
            .values(allowed_vfolder_hosts=host_perms)
        )
    yield vf
    # vfolder_host_permission_fixture teardown restores empty perms automatically.


@pytest.fixture()
async def no_download_permission_vfolder(
    db_engine: SAEngine,
    domain_fixture: str,
    resource_policy_fixture: str,
    vfolder_factory: VFolderFactory,
) -> AsyncIterator[VFolderFixtureData]:
    """Create a vfolder and restrict the host to disallow DOWNLOAD_FILE."""
    vf = await vfolder_factory()
    restricted: set[VFolderHostPermission] = set(VFolderHostPermission) - {
        VFolderHostPermission.DOWNLOAD_FILE
    }
    host_perms = VFolderHostPermissionMap({"local": restricted})
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.update(domains)
            .where(domains.c.name == domain_fixture)
            .values(allowed_vfolder_hosts=host_perms)
        )
        await conn.execute(
            sa.update(keypair_resource_policies)
            .where(keypair_resource_policies.c.name == resource_policy_fixture)
            .values(allowed_vfolder_hosts=host_perms)
        )
        await conn.execute(
            sa.update(keypair_resource_policies)
            .where(keypair_resource_policies.c.name == "default")
            .values(allowed_vfolder_hosts=host_perms)
        )
    yield vf


# ===========================================================================
# File Operations — Upload
# ===========================================================================


class TestUploadSession:
    """Tests for POST /{name}/request-upload."""

    async def test_create_upload_session_succeeds(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
        storage_manager: StorageSessionManager,
    ) -> None:
        """S-1: Upload session creation returns token + url for accessible vfolder."""
        _configure_storage_mock(storage_manager)

        result = await admin_registry.vfolder.create_upload_session(
            target_vfolder["name"],
            CreateUploadSessionReq(path="test-file.txt", size=1024),
        )

        assert isinstance(result, CreateUploadSessionResponse)
        assert result.token == "upload-token-abc"
        assert "upload" in result.url

    async def test_upload_without_upload_permission_raises_error(
        self,
        admin_registry: BackendAIClientRegistry,
        no_upload_permission_vfolder: VFolderFixtureData,
        storage_manager: StorageSessionManager,
    ) -> None:
        """F-UPLOAD-1: Upload to host without UPLOAD_FILE permission → error."""
        _configure_storage_mock(storage_manager)

        with pytest.raises(BackendAPIError):
            await admin_registry.vfolder.create_upload_session(
                no_upload_permission_vfolder["name"],
                CreateUploadSessionReq(path="test-file.txt", size=1024),
            )

    async def test_upload_to_nonexistent_vfolder_raises_error(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_host_permission_fixture: None,
        storage_manager: StorageSessionManager,
    ) -> None:
        """F-UPLOAD-2: Upload to inaccessible (nonexistent) vfolder → error."""
        _configure_storage_mock(storage_manager)

        with pytest.raises(BackendAPIError):
            await admin_registry.vfolder.create_upload_session(
                "nonexistent-vfolder-xyz-abc",
                CreateUploadSessionReq(path="test-file.txt", size=1024),
            )


# ===========================================================================
# File Operations — Download
# ===========================================================================


class TestDownloadSession:
    """Tests for POST /{name}/request-download."""

    async def test_create_download_session_succeeds(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
        storage_manager: StorageSessionManager,
    ) -> None:
        """S-2: Download session creation returns token + url."""
        _configure_storage_mock(storage_manager)

        result = await admin_registry.vfolder.create_download_session(
            target_vfolder["name"],
            CreateDownloadSessionReq(path="test-file.txt", archive=False),
        )

        assert isinstance(result, CreateDownloadSessionResponse)
        assert result.token == "download-token-xyz"
        assert "download" in result.url

    async def test_download_without_download_permission_raises_error(
        self,
        admin_registry: BackendAIClientRegistry,
        no_download_permission_vfolder: VFolderFixtureData,
        storage_manager: StorageSessionManager,
    ) -> None:
        """F-DOWNLOAD-1: Download from host without DOWNLOAD_FILE permission → error."""
        _configure_storage_mock(storage_manager)

        with pytest.raises(BackendAPIError):
            await admin_registry.vfolder.create_download_session(
                no_download_permission_vfolder["name"],
                CreateDownloadSessionReq(path="test-file.txt", archive=False),
            )


# ===========================================================================
# File Operations — List Files
# ===========================================================================


class TestListFiles:
    """Tests for GET /{name}/files."""

    async def test_list_files_at_root_returns_response(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
        storage_manager: StorageSessionManager,
    ) -> None:
        """S-4: List files at root path returns ListFilesResponse."""
        _configure_storage_mock(storage_manager)

        result = await admin_registry.vfolder.list_files(
            target_vfolder["name"],
            ListFilesQuery(path=""),
        )

        assert isinstance(result, ListFilesResponse)
        assert isinstance(result.items, list)


# ===========================================================================
# File Operations — Rename File
# ===========================================================================


class TestRenameFile:
    """Tests for POST /{name}/rename-file."""

    async def test_rename_file_with_modify_permission_succeeds(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
        storage_manager: StorageSessionManager,
    ) -> None:
        """S-6: Rename file with MODIFY permission succeeds."""
        _configure_storage_mock(storage_manager)

        result = await admin_registry.vfolder.rename_file(
            target_vfolder["name"],
            RenameFileReq(target_path="old-file.txt", new_name="new-file.txt"),
        )

        assert isinstance(result, MessageResponse)


# ===========================================================================
# File Operations — Move File
# ===========================================================================


class TestMoveFile:
    """Tests for POST /{name}/move-file."""

    async def test_move_file_in_accessible_vfolder_succeeds(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
        storage_manager: StorageSessionManager,
    ) -> None:
        """S-7: Move file in accessible vfolder succeeds."""
        _configure_storage_mock(storage_manager)

        result = await admin_registry.vfolder.move_file(
            target_vfolder["name"],
            MoveFileReq(src="src/file.txt", dst="dst/file.txt"),
        )

        assert isinstance(result, MessageResponse)


# ===========================================================================
# File Operations — Delete Files
# ===========================================================================


class TestDeleteFiles:
    """Tests for POST /{name}/delete-files and POST /{name}/delete-files-async."""

    async def test_synchronous_single_file_delete_succeeds(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
        storage_manager: StorageSessionManager,
    ) -> None:
        """S-8: Synchronous single file delete succeeds."""
        _configure_storage_mock(storage_manager)

        result = await admin_registry.vfolder.delete_files(
            target_vfolder["name"],
            DeleteFilesReq(files=["file-to-delete.txt"], recursive=False),
        )

        assert isinstance(result, MessageResponse)

    async def test_async_delete_returns_task_id(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
        storage_manager: StorageSessionManager,
    ) -> None:
        """S-10: Async delete returns task_id."""
        _configure_storage_mock(storage_manager)

        result = await admin_registry.vfolder.delete_files_async(
            target_vfolder["name"],
            DeleteFilesAsyncBodyParam(files=["file-to-delete-async.txt"], recursive=False),
        )

        assert isinstance(result, DeleteFilesAsyncResponse)
        assert result.bgtask_id is not None


# ===========================================================================
# File Operations — Mkdir
# ===========================================================================


class TestMkdir:
    """Tests for POST /{name}/mkdir."""

    async def test_single_directory_creation_returns_response(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
        storage_manager: StorageSessionManager,
    ) -> None:
        """S-11: Single directory creation returns MkdirResponse."""
        _configure_storage_mock(storage_manager)

        result = await admin_registry.vfolder.mkdir(
            target_vfolder["name"],
            MkdirReq(path="new-directory", parents=False, exist_ok=False),
        )

        assert isinstance(result, MkdirResponse)

    async def test_mkdir_with_parents_true_succeeds(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
        storage_manager: StorageSessionManager,
    ) -> None:
        """S-12: Directory creation with parents=True succeeds."""
        _configure_storage_mock(storage_manager)

        result = await admin_registry.vfolder.mkdir(
            target_vfolder["name"],
            MkdirReq(path="parent/child/grandchild", parents=True, exist_ok=False),
        )

        assert isinstance(result, MkdirResponse)

    async def test_mkdir_batch_creation_succeeds(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
        storage_manager: StorageSessionManager,
    ) -> None:
        """S-13: Multiple directories batch creation succeeds."""
        _configure_storage_mock(storage_manager)

        result = await admin_registry.vfolder.mkdir(
            target_vfolder["name"],
            MkdirReq(path=["dir-a", "dir-b", "dir-c"], parents=False, exist_ok=True),
        )

        assert isinstance(result, MkdirResponse)

    async def test_mkdir_more_than_50_dirs_raises_error(
        self,
        admin_registry: BackendAIClientRegistry,
        target_vfolder: VFolderFixtureData,
        storage_manager: StorageSessionManager,
    ) -> None:
        """F-MKDIR-1: More than 50 directories → VFolderInvalidParameter (400)."""
        _configure_storage_mock(storage_manager)

        with pytest.raises(BackendAPIError):
            await admin_registry.vfolder.mkdir(
                target_vfolder["name"],
                MkdirReq(
                    path=[f"dir-{i}" for i in range(51)],
                    parents=False,
                    exist_ok=False,
                ),
            )

    async def test_mkdir_on_nonexistent_vfolder_raises_error(
        self,
        admin_registry: BackendAIClientRegistry,
        vfolder_host_permission_fixture: None,
        storage_manager: StorageSessionManager,
    ) -> None:
        """F-MKDIR-2: Mkdir on inaccessible (nonexistent) vfolder → error."""
        _configure_storage_mock(storage_manager)

        with pytest.raises(BackendAPIError):
            await admin_registry.vfolder.mkdir(
                "nonexistent-vfolder-xyz-abc",
                MkdirReq(path="new-dir", parents=False, exist_ok=False),
            )


# ===========================================================================
# Mount Operations
# ===========================================================================


class TestListMounts:
    """Tests for GET /_/mounts (superadmin only)."""

    @pytest.mark.xfail(
        strict=False,
        reason="list_mounts requires agent watchers not available in component tests",
    )
    async def test_list_mounts_returns_response(
        self,
        admin_registry: BackendAIClientRegistry,
        storage_manager: StorageSessionManager,
    ) -> None:
        """S-1(mount): List mounts returns manager, storage_proxy, agents data."""
        result = await admin_registry.vfolder.list_mounts()
        assert isinstance(result, ListMountsResponse)
        assert result.manager is not None


class TestGetFstabContents:
    """Tests for GET /_/fstab (superadmin only)."""

    async def test_no_agent_id_returns_manager_stub(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """S-9(mount): No agent_id for fstab returns manager stub message."""
        result = await admin_registry.vfolder.get_fstab_contents(
            GetFstabContentsQuery(agent_id=None),
        )

        assert isinstance(result, GetFstabContentsResponse)
        assert result.node == "manager"
        assert result.node_id == "manager"
        # The manager stub message since v20.09
        assert "20.09" in result.content or "no longer supported" in result.content


class TestMountAuth:
    """Tests that mount/umount endpoints require superadmin access."""

    async def test_non_superadmin_cannot_list_mounts(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """F-AUTH-2(mount): Non-superadmin mount attempt → 403."""
        with pytest.raises(BackendAPIError) as exc_info:
            await user_registry.vfolder.list_mounts()
        assert exc_info.value.status == 403

    async def test_non_superadmin_cannot_mount_host(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """F-AUTH-2(mount): Non-superadmin mount_host attempt → 403."""
        with pytest.raises(BackendAPIError) as exc_info:
            await user_registry.vfolder.mount_host(
                MountHostReq(name="test-mount", fs_location="/mnt/test"),
            )
        assert exc_info.value.status == 403

    async def test_non_superadmin_cannot_umount_host(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """F-AUTH-2(mount): Non-superadmin umount_host attempt → 403."""
        with pytest.raises(BackendAPIError) as exc_info:
            await user_registry.vfolder.umount_host(
                UmountHostReq(name="test-mount"),
            )
        assert exc_info.value.status == 403

    async def test_non_superadmin_cannot_get_fstab(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """F-AUTH-2(mount): Non-superadmin get_fstab attempt → 403."""
        with pytest.raises(BackendAPIError) as exc_info:
            await user_registry.vfolder.get_fstab_contents(
                GetFstabContentsQuery(agent_id=None),
            )
        assert exc_info.value.status == 403
