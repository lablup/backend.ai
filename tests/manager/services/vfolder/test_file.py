"""
Simple tests for VFolder File Service functionality.
Tests the core file service actions to verify compatibility with test scenarios.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.types import ResultSet
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.errors.storage import VFolderPermissionError
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.repositories.vfolder.admin_repository import AdminVfolderRepository
from ai.backend.manager.repositories.vfolder.repository import VfolderRepository
from ai.backend.manager.services.vfolder.actions.file import (
    CreateDownloadSessionAction,
    CreateUploadSessionAction,
    DeleteFilesAction,
    ListFilesAction,
    MkdirAction,
    RenameFileAction,
)
from ai.backend.manager.services.vfolder.processors.file import VFolderFileProcessors
from ai.backend.manager.services.vfolder.services.file import VFolderFileService
from ai.backend.manager.services.vfolder.types import FileInfo


class TestFileServiceCompatibility:
    """Test compatibility of file service with test scenarios."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mocked dependencies for testing."""
        config_provider = MagicMock(spec=ManagerConfigProvider)
        storage_manager = MagicMock(spec=StorageSessionManager)
        vfolder_repository = MagicMock(spec=VfolderRepository)
        admin_vfolder_repository = MagicMock(spec=AdminVfolderRepository)
        action_monitor = MagicMock(spec=ActionMonitor)

        return {
            "config_provider": config_provider,
            "storage_manager": storage_manager,
            "vfolder_repository": vfolder_repository,
            "admin_vfolder_repository": admin_vfolder_repository,
            "action_monitor": action_monitor,
        }

    @pytest.fixture
    def file_service(self, mock_dependencies):
        """Create VFolderFileService instance with mocked dependencies."""
        return VFolderFileService(
            config_provider=mock_dependencies["config_provider"],
            storage_manager=mock_dependencies["storage_manager"],
            vfolder_repository=mock_dependencies["vfolder_repository"],
            admin_vfolder_repository=mock_dependencies["admin_vfolder_repository"],
        )

    @pytest.fixture
    def file_processors(self, file_service, mock_dependencies):
        """Create VFolderFileProcessors instance."""
        return VFolderFileProcessors(
            service=file_service,
            action_monitors=[mock_dependencies["action_monitor"]],
        )

    @pytest.fixture
    def sample_vfolder_info(self):
        """Sample VFolder information for testing."""
        return {
            "id": uuid.uuid4(),
            "name": "test-vfolder",
            "host": "storage1",
            "permission": "rw",
            "user": uuid.uuid4(),
            "group": None,
            "ownership_type": "user",
            "quota_scope_id": "12345",
        }

    @pytest.mark.asyncio
    async def test_create_upload_session_standard_file(self, file_processors, mock_dependencies):
        """Test 2.1: Single File Upload - Standard file upload."""
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Setup mock
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "permission": "rw",
            "host": "storage1",
        }
        mock_dependencies["storage_manager"].request_upload.return_value = AsyncMock(
            return_value=("upload-token-123", "http://storage.example.com/upload/upload-token-123")
        )()

        action = CreateUploadSessionAction(
            keypair_resource_policy={"max_vfolder_size": 10737418240},
            user_uuid=user_id,
            vfolder_uuid=vfolder_id,
            path="/datasets/data.csv",
            size="1048576",  # 1MB
        )

        result = await file_processors.create_upload_session(action)

        assert result.token == "upload-token-123"
        assert result.url == "http://storage.example.com/upload/upload-token-123"
        mock_dependencies["storage_manager"].request_upload.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_upload_session_large_file(self, file_processors, mock_dependencies):
        """Test 2.2: Large File Upload - Multipart upload support."""
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Setup mock
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "permission": "rw",
            "host": "storage1",
        }
        mock_dependencies["storage_manager"].request_upload.return_value = AsyncMock(
            return_value=(
                "multipart-upload-token-456",
                "http://storage.example.com/upload/multipart-upload-token-456",
            )
        )()

        action = CreateUploadSessionAction(
            keypair_resource_policy={"max_vfolder_size": 107374182400},
            user_uuid=user_id,
            vfolder_uuid=vfolder_id,
            path="/models/model.h5",
            size="5368709120",  # 5GB
        )

        result = await file_processors.create_upload_session(action)

        assert result.token == "multipart-upload-token-456"
        assert "multipart" in result.url
        mock_dependencies["storage_manager"].request_upload.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_upload_session_readonly_folder(self, file_processors, mock_dependencies):
        """Test 2.4: Unauthorized Upload - Read-only VFolder."""
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Setup mock for read-only permission
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "permission": "ro",  # Read-only
            "host": "storage1",
        }

        action = CreateUploadSessionAction(
            keypair_resource_policy={"max_vfolder_size": 10737418240},
            user_uuid=user_id,
            vfolder_uuid=vfolder_id,
            path="/readonly/file.txt",
            size="1024",
        )

        with pytest.raises(VFolderPermissionError):
            await file_processors.create_upload_session(action)

    @pytest.mark.asyncio
    async def test_list_files_root_directory(self, file_processors, mock_dependencies):
        """Test 3.1: Root Directory Listing - Basic file browsing."""
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Setup mock
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "permission": "rw",
            "host": "storage1",
        }

        expected_files = ResultSet(
            items=[
                FileInfo(
                    name="data",
                    path="/data",
                    is_dir=True,
                    size=0,
                    mode="drwxr-xr-x",
                    modified="2024-01-01T00:00:00Z",
                ),
                FileInfo(
                    name="model.py",
                    path="/model.py",
                    is_dir=False,
                    size=2048,
                    mode="-rw-r--r--",
                    modified="2024-01-01T00:00:00Z",
                ),
            ],
            total_count=2,
        )

        mock_dependencies["storage_manager"].scan_tree.return_value = AsyncMock(
            return_value=expected_files
        )()

        action = ListFilesAction(
            keypair_resource_policy={},
            user_uuid=user_id,
            vfolder_uuid=vfolder_id,
            path="/",
        )

        result = await file_processors.list_files(action)

        assert result.files.total_count == 2
        assert len(result.files.items) == 2
        assert result.files.items[0].name == "data"
        assert result.files.items[0].is_dir is True
        assert result.files.items[1].name == "model.py"
        assert result.files.items[1].is_dir is False

    @pytest.mark.asyncio
    async def test_list_files_with_filter(self, file_processors, mock_dependencies):
        """Test 3.3: Filtering and Sorting - CSV files only, size descending."""
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Setup mock
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "permission": "rw",
            "host": "storage1",
        }

        expected_files = ResultSet(
            items=[
                FileInfo(
                    name="large_data.csv",
                    path="/data/large_data.csv",
                    is_dir=False,
                    size=10485760,  # 10MB
                    mode="-rw-r--r--",
                    modified="2024-01-01T00:00:00Z",
                ),
                FileInfo(
                    name="small_data.csv",
                    path="/data/small_data.csv",
                    is_dir=False,
                    size=1024,  # 1KB
                    mode="-rw-r--r--",
                    modified="2024-01-01T00:00:00Z",
                ),
            ],
            total_count=2,
        )

        mock_dependencies["storage_manager"].scan_tree.return_value = AsyncMock(
            return_value=expected_files
        )()

        action = ListFilesAction(
            keypair_resource_policy={},
            user_uuid=user_id,
            vfolder_uuid=vfolder_id,
            path="/data",
            pattern="*.csv",
        )

        result = await file_processors.list_files(action)

        assert result.files.total_count == 2
        assert all(file.name.endswith(".csv") for file in result.files.items)
        assert result.files.items[0].size > result.files.items[1].size  # Descending order

    @pytest.mark.asyncio
    async def test_rename_file_success(self, file_processors, mock_dependencies):
        """Test File Rename - Normal file rename."""
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Setup mock
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "permission": "rw",
            "host": "storage1",
        }
        mock_dependencies["storage_manager"].rename_file.return_value = AsyncMock()()

        action = RenameFileAction(
            keypair_resource_policy={},
            user_uuid=user_id,
            vfolder_uuid=vfolder_id,
            old_path="/data/old_name.txt",
            new_path="/data/new_name.txt",
        )

        result = await file_processors.rename_file(action)

        assert result.old_path == "/data/old_name.txt"
        assert result.new_path == "/data/new_name.txt"
        mock_dependencies["storage_manager"].rename_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_rename_file_no_permission(self, file_processors, mock_dependencies):
        """Test File Rename - No permission."""
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Setup mock for read-only permission
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "permission": "ro",  # Read-only
            "host": "storage1",
        }

        action = RenameFileAction(
            keypair_resource_policy={},
            user_uuid=user_id,
            vfolder_uuid=vfolder_id,
            old_path="/readonly/file.txt",
            new_path="/readonly/renamed.txt",
        )

        with pytest.raises(VFolderPermissionError):
            await file_processors.rename_file(action)

    @pytest.mark.asyncio
    async def test_mkdir_success(self, file_processors, mock_dependencies):
        """Test Directory Creation - Normal directory creation."""
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Setup mock
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "permission": "rw",
            "host": "storage1",
        }
        mock_dependencies["storage_manager"].mkdir.return_value = AsyncMock()()

        action = MkdirAction(
            keypair_resource_policy={},
            user_uuid=user_id,
            vfolder_uuid=vfolder_id,
            path="/data/new_folder",
        )

        result = await file_processors.mkdir(action)

        assert result.path == "/data/new_folder"
        mock_dependencies["storage_manager"].mkdir.assert_called_once()

    @pytest.mark.asyncio
    async def test_mkdir_readonly_folder(self, file_processors, mock_dependencies):
        """Test Directory Creation - Read-only VFolder."""
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Setup mock for read-only permission
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "permission": "ro",  # Read-only
            "host": "storage1",
        }

        action = MkdirAction(
            keypair_resource_policy={},
            user_uuid=user_id,
            vfolder_uuid=vfolder_id,
            path="/readonly/new_folder",
        )

        with pytest.raises(VFolderPermissionError):
            await file_processors.mkdir(action)

    @pytest.mark.asyncio
    async def test_delete_single_file(self, file_processors, mock_dependencies):
        """Test File Deletion - Single file deletion."""
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Setup mock
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "permission": "rwd",  # Read-write-delete
            "host": "storage1",
        }
        mock_dependencies["storage_manager"].delete_files.return_value = AsyncMock()()

        action = DeleteFilesAction(
            keypair_resource_policy={},
            user_uuid=user_id,
            vfolder_uuid=vfolder_id,
            paths=["/data/unwanted.txt"],
        )

        result = await file_processors.delete_files(action)

        assert result.deleted_paths == ["/data/unwanted.txt"]
        mock_dependencies["storage_manager"].delete_files.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_multiple_files(self, file_processors, mock_dependencies):
        """Test File Deletion - Multiple files/directories deletion."""
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Setup mock
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "permission": "rwd",  # Read-write-delete
            "host": "storage1",
        }
        mock_dependencies["storage_manager"].delete_files.return_value = AsyncMock()()

        action = DeleteFilesAction(
            keypair_resource_policy={},
            user_uuid=user_id,
            vfolder_uuid=vfolder_id,
            paths=["/data/old_dir", "/logs/debug.log", "/temp/"],
        )

        result = await file_processors.delete_files(action)

        assert len(result.deleted_paths) == 3
        assert "/data/old_dir" in result.deleted_paths
        assert "/logs/debug.log" in result.deleted_paths
        assert "/temp/" in result.deleted_paths

    @pytest.mark.asyncio
    async def test_delete_files_no_permission(self, file_processors, mock_dependencies):
        """Test File Deletion - No delete permission."""
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Setup mock without delete permission
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "permission": "rw",  # No delete permission
            "host": "storage1",
        }

        action = DeleteFilesAction(
            keypair_resource_policy={},
            user_uuid=user_id,
            vfolder_uuid=vfolder_id,
            paths=["/protected/important.txt"],
        )

        with pytest.raises(VFolderPermissionError):
            await file_processors.delete_files(action)

    @pytest.mark.asyncio
    async def test_create_download_session(self, file_processors, mock_dependencies):
        """Test File Download - Normal file download."""
        vfolder_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Setup mock
        mock_dependencies["vfolder_repository"].get_vfolder_by_uuid.return_value = {
            "id": vfolder_id,
            "permission": "ro",  # Read permission is enough for download
            "host": "storage1",
        }
        mock_dependencies["storage_manager"].request_download.return_value = AsyncMock(
            return_value=(
                "download-token-789",
                "http://storage.example.com/download/download-token-789",
            )
        )()

        action = CreateDownloadSessionAction(
            keypair_resource_policy={},
            user_uuid=user_id,
            vfolder_uuid=vfolder_id,
            path="/data/report.pdf",
        )

        result = await file_processors.create_download_session(action)

        assert result.token == "download-token-789"
        assert result.url == "http://storage.example.com/download/download-token-789"
        mock_dependencies["storage_manager"].request_download.assert_called_once()
