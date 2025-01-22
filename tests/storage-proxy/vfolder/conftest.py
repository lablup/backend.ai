import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp.web import Request

from ai.backend.storage.api.vfolder.manager_service import VFolderService
from ai.backend.storage.api.vfolder.types import (
    QuotaScopeInfoModel,
    VFolderCloneModel,
    VFolderIDModel,
    VFolderInfoRequestModel,
)

UUID = "8067790d-9a2e-4daf-8278-614ded1dc7f8"


@pytest.fixture
def mock_vfolder_service():
    service = AsyncMock(spec=VFolderService)

    # Mocked return value for get_volume
    service.get_volume.return_value = {
        "volume_id": str(uuid.UUID(UUID)),  # UUID를 문자열로 반환
        "backend": "default-backend",
        "path": "/example/path",  # Path 객체 대신 문자열
        "fsprefix": "/fsprefix",
        "capabilities": ["read", "write"],
        "options": {"option1": "value1"},
    }

    # Mocked return value for get_volumes
    service.get_volumes.return_value = {
        str(uuid.UUID(UUID)): {  # UUID 키를 문자열로 변환
            "volume_id": str(uuid.UUID(UUID)),
            "backend": "default-backend",
            "path": "/example/path",
            "fsprefix": "/fsprefix",
            "capabilities": ["read", "write"],
            "options": {"option1": "value1"},
        }
    }

    # Mocked return value for get_quota_scope
    service.get_quota_scope.return_value = {
        "used_bytes": 1024,
        "limit_bytes": 2048,
    }

    # Mocked return values for quota scope actions
    service.create_quota_scope.return_value = None
    service.update_quota_scope.return_value = None
    service.delete_quota_scope.return_value = None

    # Mocked return value for create_vfolder
    service.create_vfolder.return_value = None

    # Mocked return value for clone_vfolder
    service.clone_vfolder.return_value = None

    # Mocked return value for get_vfolder_info
    service.get_vfolder_info.return_value = {
        "vfolder_mount": "/mount/point",  # Path 대신 문자열
        "vfolder_metadata": "metadata",  # bytes 대신 문자열
        "vfolder_usage": {"tree": {}, "usage": 1024},
        "vfolder_used_bytes": 2048,
        "vfolder_fs_usage": {"capacity": 4096},
    }

    # Mocked return value for delete_vfolder
    service.delete_vfolder.return_value = None

    return service


@pytest.fixture
def mock_request():
    """Mocked request object."""
    request = MagicMock(spec=Request)
    request.json = AsyncMock(return_value={"volume_id": UUID})  # 문자열로 반환
    return request


@pytest.fixture
def mock_quota_scope_request():
    """Mocked request for quota scope."""
    return QuotaScopeInfoModel(used_bytes=1024, limit_bytes=2048)


@pytest.fixture
def mock_vfolder_id_request():
    """Mocked request for VFolder ID."""
    return VFolderIDModel(volume_id=UUID, vfolder_id="test-folder-id")


@pytest.fixture
def mock_vfolder_clone_request():
    """Mocked request for cloning a VFolder."""
    return VFolderCloneModel(
        volume_id=UUID,
        src_vfolder_id="source-folder",
        dst_vfolder_id="destination-folder",
    )


@pytest.fixture
def mock_vfolder_info_request():
    """Mocked request for VFolder info."""
    return VFolderInfoRequestModel(
        volume_id=UUID,
        vfolder_id="test-folder-id",
        subpath="/test/path",
    )
