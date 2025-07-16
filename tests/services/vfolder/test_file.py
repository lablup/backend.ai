import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Mapping
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.types import AccessKey, ResultSet
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.config.unified import ConfigProvider
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.vfolder.admin_vfolder_repository import AdminVFolderRepository
from ai.backend.manager.repositories.vfolder.vfolder_repository import VFolderRepository
from ai.backend.manager.services.vfolder.actions.file import (
    CreateDownloadSessionAction,
    CreateDownloadSessionActionResult,
    CreateUploadSessionAction,
    CreateUploadSessionActionResult,
    DeleteFilesAction,
    DeleteFilesActionResult,
    ListFilesAction,
    ListFilesActionResult,
    MkdirAction,
    MkdirActionResult,
    RenameFileAction,
    RenameFileActionResult,
)
from ai.backend.manager.services.vfolder.exceptions import VFolderPermissionError
from ai.backend.manager.services.vfolder.processors.file import FileProcessors
from ai.backend.manager.services.vfolder.services.file import FileService
from ai.backend.manager.services.vfolder.types import FileInfo

from ..test_utils import TestScenario


@pytest.fixture
def mock_config_provider():
    return MagicMock(spec=ConfigProvider)


@pytest.fixture
def mock_storage_manager():
    return MagicMock(spec=StorageSessionManager)


@pytest.fixture
def mock_vfolder_repository():
    return MagicMock(spec=VFolderRepository)


@pytest.fixture
def mock_admin_vfolder_repository():
    return MagicMock(spec=AdminVFolderRepository)


@pytest.fixture
def mock_action_monitor():
    return MagicMock(spec=ActionMonitor)


@pytest.fixture
def file_service(
    mock_config_provider,
    mock_storage_manager,
    mock_vfolder_repository,
    mock_admin_vfolder_repository,
):
    return FileService(
        config_provider=mock_config_provider,
        storage_manager=mock_storage_manager,
        vfolder_repository=mock_vfolder_repository,
        admin_vfolder_repository=mock_admin_vfolder_repository,
    )


@pytest.fixture
def file_processors(file_service, mock_action_monitor):
    return FileProcessors(file_service=file_service, action_monitors=[mock_action_monitor])


@pytest.fixture
def sample_vfolder_info():
    """Sample VFolder information for testing"""
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


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "2.1 단일 파일 업로드 - 표준 파일 업로드",
            CreateUploadSessionAction(
                keypair_resource_policy={"max_vfolder_size": 10737418240},
                user_uuid=uuid.uuid4(),
                vfolder_uuid=uuid.uuid4(),
                path="/datasets/data.csv",
                size="1048576",  # 1MB
            ),
            CreateUploadSessionActionResult(
                vfolder_uuid=uuid.uuid4(),
                token="upload-token-123",
                url="http://storage.example.com/upload/upload-token-123",
            ),
        ),
        TestScenario.success(
            "2.2 대용량 파일 업로드 - 멀티파트 업로드 지원",
            CreateUploadSessionAction(
                keypair_resource_policy={"max_vfolder_size": 107374182400},
                user_uuid=uuid.uuid4(),
                vfolder_uuid=uuid.uuid4(),
                path="/models/model.h5",
                size="5368709120",  # 5GB
            ),
            CreateUploadSessionActionResult(
                vfolder_uuid=uuid.uuid4(),
                token="multipart-upload-token-456",
                url="http://storage.example.com/upload/multipart-upload-token-456",
            ),
        ),
        TestScenario.failure(
            "2.4 권한 없는 업로드 - 읽기 전용 VFolder",
            CreateUploadSessionAction(
                keypair_resource_policy={"max_vfolder_size": 10737418240},
                user_uuid=uuid.uuid4(),
                vfolder_uuid=uuid.uuid4(),
                path="/readonly/file.txt",
                size="1024",
            ),
            VFolderPermissionError,
        ),
    ],
)
async def test_create_upload_session(
    file_processors: FileProcessors,
    file_service: FileService,
    mock_vfolder_repository: MagicMock,
    test_scenario: TestScenario[CreateUploadSessionAction, CreateUploadSessionActionResult],
):
    """Test file upload session creation"""
    if test_scenario.expected_exception is None:
        # Setup mock for successful case
        mock_vfolder_repository.get_vfolder_by_uuid.return_value = {
            "id": test_scenario.input.vfolder_uuid,
            "permission": "rw",
            "host": "storage1",
        }
        file_service.storage_manager.request_upload.return_value = AsyncMock(
            return_value=(test_scenario.expected.token, test_scenario.expected.url)
        )()
    else:
        # Setup mock for failure case - read-only permission
        mock_vfolder_repository.get_vfolder_by_uuid.return_value = {
            "id": test_scenario.input.vfolder_uuid,
            "permission": "ro",  # Read-only
            "host": "storage1",
        }

    await test_scenario.test(file_processors.create_upload_session)


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "3.1 루트 디렉토리 조회 - 기본 파일 탐색",
            ListFilesAction(
                keypair_resource_policy={},
                user_uuid=uuid.uuid4(),
                vfolder_uuid=uuid.uuid4(),
                path="/",
            ),
            ListFilesActionResult(
                vfolder_uuid=uuid.uuid4(),
                files=ResultSet(
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
                ),
            ),
        ),
        TestScenario.success(
            "3.3 필터링 및 정렬 - CSV 파일만 크기 역순",
            ListFilesAction(
                keypair_resource_policy={},
                user_uuid=uuid.uuid4(),
                vfolder_uuid=uuid.uuid4(),
                path="/data",
                pattern="*.csv",
            ),
            ListFilesActionResult(
                vfolder_uuid=uuid.uuid4(),
                files=ResultSet(
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
                ),
            ),
        ),
    ],
)
async def test_list_files(
    file_processors: FileProcessors,
    file_service: FileService,
    mock_vfolder_repository: MagicMock,
    test_scenario: TestScenario[ListFilesAction, ListFilesActionResult],
):
    """Test file listing functionality"""
    # Setup mock
    mock_vfolder_repository.get_vfolder_by_uuid.return_value = {
        "id": test_scenario.input.vfolder_uuid,
        "permission": "rw",
        "host": "storage1",
    }

    # Mock the scan_tree response
    file_service.storage_manager.scan_tree.return_value = AsyncMock(
        return_value=test_scenario.expected.files
    )()

    await test_scenario.test(file_processors.list_files)


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "파일 이름 변경 - 정상적인 파일 이름 변경",
            RenameFileAction(
                keypair_resource_policy={},
                user_uuid=uuid.uuid4(),
                vfolder_uuid=uuid.uuid4(),
                old_path="/data/old_name.txt",
                new_path="/data/new_name.txt",
            ),
            RenameFileActionResult(
                vfolder_uuid=uuid.uuid4(),
                old_path="/data/old_name.txt",
                new_path="/data/new_name.txt",
            ),
        ),
        TestScenario.failure(
            "파일 이름 변경 - 권한 없음",
            RenameFileAction(
                keypair_resource_policy={},
                user_uuid=uuid.uuid4(),
                vfolder_uuid=uuid.uuid4(),
                old_path="/readonly/file.txt",
                new_path="/readonly/renamed.txt",
            ),
            VFolderPermissionError,
        ),
    ],
)
async def test_rename_file(
    file_processors: FileProcessors,
    file_service: FileService,
    mock_vfolder_repository: MagicMock,
    test_scenario: TestScenario[RenameFileAction, RenameFileActionResult],
):
    """Test file rename functionality"""
    if test_scenario.expected_exception is None:
        # Setup mock for successful case
        mock_vfolder_repository.get_vfolder_by_uuid.return_value = {
            "id": test_scenario.input.vfolder_uuid,
            "permission": "rw",
            "host": "storage1",
        }
        file_service.storage_manager.rename_file.return_value = AsyncMock()()
    else:
        # Setup mock for failure case
        mock_vfolder_repository.get_vfolder_by_uuid.return_value = {
            "id": test_scenario.input.vfolder_uuid,
            "permission": "ro",  # Read-only
            "host": "storage1",
        }

    await test_scenario.test(file_processors.rename_file)


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "디렉토리 생성 - 정상적인 디렉토리 생성",
            MkdirAction(
                keypair_resource_policy={},
                user_uuid=uuid.uuid4(),
                vfolder_uuid=uuid.uuid4(),
                path="/data/new_folder",
            ),
            MkdirActionResult(
                vfolder_uuid=uuid.uuid4(),
                path="/data/new_folder",
            ),
        ),
        TestScenario.failure(
            "디렉토리 생성 - 읽기 전용 VFolder",
            MkdirAction(
                keypair_resource_policy={},
                user_uuid=uuid.uuid4(),
                vfolder_uuid=uuid.uuid4(),
                path="/readonly/new_folder",
            ),
            VFolderPermissionError,
        ),
    ],
)
async def test_mkdir(
    file_processors: FileProcessors,
    file_service: FileService,
    mock_vfolder_repository: MagicMock,
    test_scenario: TestScenario[MkdirAction, MkdirActionResult],
):
    """Test directory creation functionality"""
    if test_scenario.expected_exception is None:
        # Setup mock for successful case
        mock_vfolder_repository.get_vfolder_by_uuid.return_value = {
            "id": test_scenario.input.vfolder_uuid,
            "permission": "rw",
            "host": "storage1",
        }
        file_service.storage_manager.mkdir.return_value = AsyncMock()()
    else:
        # Setup mock for failure case
        mock_vfolder_repository.get_vfolder_by_uuid.return_value = {
            "id": test_scenario.input.vfolder_uuid,
            "permission": "ro",  # Read-only
            "host": "storage1",
        }

    await test_scenario.test(file_processors.mkdir)


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "파일 삭제 - 단일 파일 삭제",
            DeleteFilesAction(
                keypair_resource_policy={},
                user_uuid=uuid.uuid4(),
                vfolder_uuid=uuid.uuid4(),
                paths=["/data/unwanted.txt"],
            ),
            DeleteFilesActionResult(
                vfolder_uuid=uuid.uuid4(),
                deleted_paths=["/data/unwanted.txt"],
            ),
        ),
        TestScenario.success(
            "파일 삭제 - 다중 파일/디렉토리 삭제",
            DeleteFilesAction(
                keypair_resource_policy={},
                user_uuid=uuid.uuid4(),
                vfolder_uuid=uuid.uuid4(),
                paths=["/data/old_dir", "/logs/debug.log", "/temp/"],
            ),
            DeleteFilesActionResult(
                vfolder_uuid=uuid.uuid4(),
                deleted_paths=["/data/old_dir", "/logs/debug.log", "/temp/"],
            ),
        ),
        TestScenario.failure(
            "파일 삭제 - 삭제 권한 없음",
            DeleteFilesAction(
                keypair_resource_policy={},
                user_uuid=uuid.uuid4(),
                vfolder_uuid=uuid.uuid4(),
                paths=["/protected/important.txt"],
            ),
            VFolderPermissionError,
        ),
    ],
)
async def test_delete_files(
    file_processors: FileProcessors,
    file_service: FileService,
    mock_vfolder_repository: MagicMock,
    test_scenario: TestScenario[DeleteFilesAction, DeleteFilesActionResult],
):
    """Test file deletion functionality"""
    if test_scenario.expected_exception is None:
        # Setup mock for successful case
        mock_vfolder_repository.get_vfolder_by_uuid.return_value = {
            "id": test_scenario.input.vfolder_uuid,
            "permission": "rwd",  # Read-write-delete
            "host": "storage1",
        }
        file_service.storage_manager.delete_files.return_value = AsyncMock()()
    else:
        # Setup mock for failure case - no delete permission
        mock_vfolder_repository.get_vfolder_by_uuid.return_value = {
            "id": test_scenario.input.vfolder_uuid,
            "permission": "rw",  # No delete permission
            "host": "storage1",
        }

    await test_scenario.test(file_processors.delete_files)


@pytest.mark.parametrize(
    "test_scenario",
    [
        TestScenario.success(
            "파일 다운로드 - 정상적인 파일 다운로드",
            CreateDownloadSessionAction(
                keypair_resource_policy={},
                user_uuid=uuid.uuid4(),
                vfolder_uuid=uuid.uuid4(),
                path="/data/report.pdf",
            ),
            CreateDownloadSessionActionResult(
                vfolder_uuid=uuid.uuid4(),
                token="download-token-789",
                url="http://storage.example.com/download/download-token-789",
            ),
        ),
    ],
)
async def test_create_download_session(
    file_processors: FileProcessors,
    file_service: FileService,
    mock_vfolder_repository: MagicMock,
    test_scenario: TestScenario[CreateDownloadSessionAction, CreateDownloadSessionActionResult],
):
    """Test file download session creation"""
    # Setup mock
    mock_vfolder_repository.get_vfolder_by_uuid.return_value = {
        "id": test_scenario.input.vfolder_uuid,
        "permission": "ro",  # Read permission is enough for download
        "host": "storage1",
    }
    file_service.storage_manager.request_download.return_value = AsyncMock(
        return_value=(test_scenario.expected.token, test_scenario.expected.url)
    )()

    await test_scenario.test(file_processors.create_download_session)
