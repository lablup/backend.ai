import json
import uuid
from pathlib import Path, PurePath
from unittest.mock import AsyncMock

import pytest
from aiohttp import web

from ai.backend.common.api_handlers import APIResponse
from ai.backend.common.types import QuotaScopeID, QuotaScopeType, VFolderID
from ai.backend.storage.api.vfolder.handler import VFolderHandler
from ai.backend.storage.volumes.types import QuotaScopeMeta, VFolderMeta, VolumeMeta

UUID = uuid.UUID("123e4567-e89b-12d3-a456-426614174000")
UUID1 = uuid.UUID("123e4567-e89b-12d3-a456-426614174001")
UUID2 = uuid.UUID("123e4567-e89b-12d3-a456-426614174002")


@pytest.fixture
def mock_vfolder_service():
    class MockVFolderService:
        async def get_volume(self, volume_id):
            return VolumeMeta(
                volume_id=volume_id,
                backend="vfs",
                path=Path("/mnt/test_volume"),
                fsprefix=PurePath("vfs-test"),
                capabilities=["read", "write"],
            )

        async def get_volumes(self):
            volumes = {
                UUID1: {"backend": "vfs", "path": "/mnt/volume1", "fsprefix": "vfs-test-1"},
                UUID2: {"backend": "nfs", "path": "/mnt/volume2", "fsprefix": "nfs-test-2"},
            }
            return [
                VolumeMeta(
                    volume_id=volume_id,
                    backend=info.get("backend", "vfs"),
                    path=Path(info.get("path", "/mnt/test_volume")),
                    fsprefix=PurePath(info.get("fsprefix", "vfs-test")),
                    capabilities=["read", "write"],
                )
                for volume_id, info in volumes.items()
            ]

        async def create_quota_scope(self, quota_scope_key, options):
            pass

        async def get_quota_scope(self, quota_scope_key):
            return QuotaScopeMeta.model_validate({
                "used_bytes": 1000,
                "limit_bytes": 2000,
            })

        async def update_quota_scope(self, quota_scope_key, options):
            pass

        async def delete_quota_scope(self, quota_scope_key):
            pass

        async def create_vfolder(self, vfolder_key):
            pass

        async def clone_vfolder(self, src_vfolder_key, dst_vfolder_key):
            pass

        async def get_vfolder_info(self, vfolder_key, subpath):
            return VFolderMeta.model_validate({
                "mount_path": subpath,
                "file_count": 100,
                "used_bytes": 1000,
                "capacity_bytes": 2000,
                "fs_used_bytes": 1000,
            })

        async def delete_vfolder(self, vfolder_key):
            pass

    return MockVFolderService()


@pytest.mark.asyncio
async def test_get_volume(mock_vfolder_service):
    handler = VFolderHandler(mock_vfolder_service)

    mock_request = AsyncMock(web.Request)
    mock_request.match_info = {"volume_id": str(UUID)}

    response: APIResponse = await handler.get_volume(mock_request)

    assert isinstance(response, web.Response)
    assert response.status == 200
    volume_response = json.loads(response.text)["item"]
    assert volume_response["volume_id"] == str(UUID)


@pytest.mark.asyncio
async def test_get_volumes(mock_vfolder_service):
    handler = VFolderHandler(mock_vfolder_service)

    mock_request = AsyncMock(web.Request)
    response: APIResponse = await handler.get_volumes(mock_request)

    assert isinstance(response, web.Response)
    assert response.status == 200
    volume_response = json.loads(response.text)["items"]
    assert volume_response[0]["volume_id"] == str(UUID1)


@pytest.mark.asyncio
async def test_create_quota_scope(mock_vfolder_service):
    handler = VFolderHandler(mock_vfolder_service)

    mock_request = AsyncMock(web.Request)
    mock_request.match_info = {
        "volume_id": str(UUID),
        "scope_type": "user",
        "scope_uuid": str(UUID),
    }
    mock_request.json.return_value = {"options": None}

    response: APIResponse = await handler.create_quota_scope(mock_request)

    assert isinstance(response, web.Response)
    assert response.status == 204


@pytest.mark.asyncio
async def test_get_quota_scope(mock_vfolder_service):
    handler = VFolderHandler(mock_vfolder_service)

    mock_request = AsyncMock(web.Request)
    mock_request.match_info = {
        "volume_id": str(UUID),
        "scope_type": "user",
        "scope_uuid": str(UUID),
    }

    response: APIResponse = await handler.get_quota_scope(mock_request)

    assert isinstance(response, web.Response)
    assert response.status == 200
    quota_response = json.loads(response.text)
    assert quota_response["used_bytes"] == 1000
    assert quota_response["limit_bytes"] == 2000


@pytest.mark.asyncio
async def test_update_quota_scope(mock_vfolder_service):
    handler = VFolderHandler(mock_vfolder_service)

    mock_request = AsyncMock(web.Request)
    mock_request.match_info = {
        "volume_id": str(UUID),
        "scope_type": "user",
        "scope_uuid": str(UUID),
    }
    mock_request.json.return_value = {"options": None}

    response: APIResponse = await handler.update_quota_scope(mock_request)

    assert isinstance(response, web.Response)
    assert response.status == 204


@pytest.mark.asyncio
async def test_delete_quota_scope(mock_vfolder_service):
    handler = VFolderHandler(mock_vfolder_service)

    mock_request = AsyncMock(web.Request)
    mock_request.match_info = {
        "volume_id": str(UUID),
        "scope_type": "user",
        "scope_uuid": str(UUID),
    }

    response: APIResponse = await handler.delete_quota_scope(mock_request)

    assert isinstance(response, web.Response)
    assert response.status == 204


@pytest.mark.asyncio
async def test_create_vfolder(mock_vfolder_service):
    handler = VFolderHandler(mock_vfolder_service)

    mock_request = AsyncMock(web.Request)
    mock_request.match_info = {
        "volume_id": str(UUID),
        "scope_type": "user",
        "scope_uuid": str(UUID),
        "folder_uuid": str(UUID),
    }

    response: APIResponse = await handler.create_vfolder(mock_request)

    assert isinstance(response, web.Response)
    assert response.status == 204


@pytest.mark.asyncio
async def test_clone_vfolder(mock_vfolder_service):
    handler = VFolderHandler(mock_vfolder_service)

    mock_request = AsyncMock(web.Request)
    mock_request.match_info = {
        "volume_id": str(UUID),
        "scope_type": "user",
        "scope_uuid": str(UUID),
        "folder_uuid": str(UUID),
    }
    mock_request.json.return_value = {
        "dst_vfolder_id": VFolderID(
            quota_scope_id=QuotaScopeID(scope_type=QuotaScopeType.USER, scope_id=UUID),
            folder_id=UUID,
        )
    }

    response: APIResponse = await handler.clone_vfolder(mock_request)

    assert isinstance(response, web.Response)
    assert response.status == 204


@pytest.mark.asyncio
async def test_get_vfolder_info(mock_vfolder_service):
    handler = VFolderHandler(mock_vfolder_service)

    mock_request = AsyncMock(web.Request)
    mock_request.match_info = {
        "volume_id": str(UUID),
        "scope_type": "user",
        "scope_uuid": str(UUID),
        "folder_uuid": str(UUID),
    }
    mock_request.json.return_value = {"subpath": "/mnt/test_volume"}

    response: APIResponse = await handler.get_vfolder_info(mock_request)

    assert isinstance(response, web.Response)
    assert response.status == 200
    vfolder_response = json.loads(response.text)["item"]
    assert vfolder_response["mount_path"] == "/mnt/test_volume"
    assert vfolder_response["file_count"] == 100
    assert vfolder_response["used_bytes"] == 1000
    assert vfolder_response["capacity_bytes"] == 2000
    assert vfolder_response["fs_used_bytes"] == 1000


@pytest.mark.asyncio
async def test_delete_vfolder(mock_vfolder_service):
    handler = VFolderHandler(mock_vfolder_service)

    mock_request = AsyncMock(web.Request)
    mock_request.match_info = {
        "volume_id": str(UUID),
        "scope_type": "user",
        "scope_uuid": str(UUID),
        "folder_uuid": str(UUID),
    }

    response: APIResponse = await handler.delete_vfolder(mock_request)

    assert isinstance(response, web.Response)
    assert response.status == 204
