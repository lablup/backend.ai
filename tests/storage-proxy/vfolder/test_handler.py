import uuid
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from aiohttp import web

from ai.backend.common.types import BinarySize, QuotaConfig, QuotaScopeID, QuotaScopeType, VFolderID
from ai.backend.storage.api.vfolder.manager_handler import VFolderHandler
from ai.backend.storage.api.vfolder.response_model import (
    GetVolumeResponseModel,
    NoContentResponseModel,
    ProcessingResponseModel,
    QuotaScopeResponseModel,
    VFolderMetadataResponseModel,
)
from ai.backend.storage.api.vfolder.types import (
    QuotaScopeIDModel,
    QuotaScopeMetadataModel,
    VFolderIDModel,
    VFolderMetadataModel,
    VolumeIDModel,
    VolumeMetadataListModel,
    VolumeMetadataModel,
)


@pytest.fixture
def mock_vfolder_service():
    class MockVFolderService:
        async def get_volume(self, volume_data: VolumeIDModel) -> VolumeMetadataListModel:
            return VolumeMetadataListModel(
                volumes=[
                    VolumeMetadataModel(
                        volume_id=volume_data.volume_id,
                        backend="mock-backend",
                        path=Path("/mock/path"),
                        fsprefix=None,
                        capabilities=["read", "write"],
                    )
                ]
            )

        async def get_volumes(self) -> VolumeMetadataListModel:
            return VolumeMetadataListModel(
                volumes=[
                    VolumeMetadataModel(
                        volume_id=uuid.UUID("123e4567-e89b-12d3-a456-426614174000"),
                        backend="mock-backend",
                        path=Path("/mock/path"),
                        fsprefix=None,
                        capabilities=["read", "write"],
                    )
                ]
            )

        async def create_quota_scope(self, quota_data: QuotaScopeIDModel) -> None:
            pass

        async def get_quota_scope(self, quota_data: QuotaScopeIDModel) -> QuotaScopeMetadataModel:
            return QuotaScopeMetadataModel(
                used_bytes=1024,
                limit_bytes=2048,
            )

        async def update_quota_scope(self, quota_data: QuotaScopeIDModel) -> None:
            pass

        async def delete_quota_scope(self, quota_data: QuotaScopeIDModel) -> None:
            pass

        async def create_vfolder(self, vfolder_data: VFolderIDModel) -> None:
            pass

        async def clone_vfolder(self, vfolder_data: VFolderIDModel) -> None:
            pass

        async def get_vfolder_info(self, vfolder_data: VFolderIDModel) -> VFolderMetadataModel:
            return VFolderMetadataModel(
                mount_path=Path("/mock/mount/path"),
                file_count=100,
                capacity_bytes=1024 * 1024 * 1024,
                used_bytes=BinarySize(1024),
            )

        async def delete_vfolder(self, vfolder_data: VFolderIDModel) -> None:
            pass

    return MockVFolderService()


@pytest.mark.asyncio
async def test_get_volume(mock_vfolder_service):
    handler = VFolderHandler(storage_service=mock_vfolder_service)

    async def mock_request():
        request = AsyncMock(spec=web.Request)
        request.json.return_value = {"volume_id": "123e4567-e89b-12d3-a456-426614174000"}
        return request

    response = await handler.get_volume(await mock_request())

    assert isinstance(response, GetVolumeResponseModel)
    assert len(response.volumes) == 1
    assert response.volumes[0].volume_id == "123e4567-e89b-12d3-a456-426614174000"


@pytest.mark.asyncio
async def test_get_volumes(mock_vfolder_service):
    handler = VFolderHandler(storage_service=mock_vfolder_service)

    async def mock_request():
        request = AsyncMock(spec=web.Request)
        return request

    response = await handler.get_volumes(await mock_request())

    assert isinstance(response, GetVolumeResponseModel)
    assert len(response.volumes) == 1


@pytest.mark.asyncio
async def test_create_quota_scope(mock_vfolder_service):
    handler = VFolderHandler(storage_service=mock_vfolder_service)

    async def mock_request():
        request = AsyncMock(spec=web.Request)
        quota_scope_id = QuotaScopeID(
            scope_type=QuotaScopeType.USER,
            scope_id=uuid.UUID("123e4567-e89b-12d3-a456-426614174000"),
        )
        request.json.return_value = {
            "volume_id": "123e4567-e89b-12d3-a456-426614174000",
            "quota_scope_id": quota_scope_id,
        }
        return request

    response = await handler.create_quota_scope(await mock_request())

    assert isinstance(response, NoContentResponseModel)


@pytest.mark.asyncio
async def test_get_quota_scope(mock_vfolder_service):
    handler = VFolderHandler(storage_service=mock_vfolder_service)

    async def mock_request():
        request = AsyncMock(spec=web.Request)
        quota_scope_id = QuotaScopeID(
            scope_type=QuotaScopeType.USER,
            scope_id=uuid.UUID("123e4567-e89b-12d3-a456-426614174000"),
        )
        request.json.return_value = {
            "volume_id": "123e4567-e89b-12d3-a456-426614174000",
            "quota_scope_id": quota_scope_id,
        }
        return request

    response = await handler.get_quota_scope(await mock_request())

    assert isinstance(response, QuotaScopeResponseModel)
    assert response.used_bytes == 1024
    assert response.limit_bytes == 2048


@pytest.mark.asyncio
async def test_update_quota_scope(mock_vfolder_service):
    handler = VFolderHandler(storage_service=mock_vfolder_service)

    async def mock_request():
        request = AsyncMock(spec=web.Request)
        quota_scope_id = QuotaScopeID(
            scope_type=QuotaScopeType.USER,
            scope_id=uuid.UUID("123e4567-e89b-12d3-a456-426614174000"),
        )
        request.json.return_value = {
            "volume_id": "123e4567-e89b-12d3-a456-426614174000",
            "quota_scope_id": quota_scope_id,
            "options": QuotaConfig(limit_bytes=2048),  # QuotaConfig 객체 사용
        }
        return request

    response = await handler.update_quota_scope(await mock_request())

    assert isinstance(response, NoContentResponseModel)


@pytest.mark.asyncio
async def test_delete_quota_scope(mock_vfolder_service):
    handler = VFolderHandler(storage_service=mock_vfolder_service)

    async def mock_request():
        request = AsyncMock(spec=web.Request)
        quota_scope_id = QuotaScopeID(
            scope_type=QuotaScopeType.USER,
            scope_id=uuid.UUID("123e4567-e89b-12d3-a456-426614174000"),
        )
        request.json.return_value = {
            "volume_id": "123e4567-e89b-12d3-a456-426614174000",
            "quota_scope_id": quota_scope_id,
        }
        return request

    response = await handler.delete_quota_scope(await mock_request())

    assert isinstance(response, NoContentResponseModel)


@pytest.mark.asyncio
async def test_create_vfolder(mock_vfolder_service):
    handler = VFolderHandler(storage_service=mock_vfolder_service)

    async def mock_request():
        request = AsyncMock(spec=web.Request)
        vfolder_id = VFolderID(
            folder_id=uuid.UUID("123e4567-e89b-12d3-a456-426614174000"), quota_scope_id=None
        )
        request.json.return_value = {
            "volume_id": "123e4567-e89b-12d3-a456-426614174000",
            "vfolder_id": vfolder_id,
        }
        return request

    response = await handler.create_vfolder(await mock_request())

    assert isinstance(response, NoContentResponseModel)


@pytest.mark.asyncio
async def test_clone_vfolder(mock_vfolder_service):
    handler = VFolderHandler(storage_service=mock_vfolder_service)

    async def mock_request():
        request = AsyncMock(spec=web.Request)
        vfolder_id = VFolderID(
            folder_id=uuid.UUID("123e4567-e89b-12d3-a456-426614174000"), quota_scope_id=None
        )
        request.json.return_value = {
            "volume_id": "123e4567-e89b-12d3-a456-426614174000",
            "vfolder_id": vfolder_id,
            "dst_vfolder_id": vfolder_id,
        }
        return request

    response = await handler.clone_vfolder(await mock_request())

    assert isinstance(response, NoContentResponseModel)


@pytest.mark.asyncio
async def test_get_vfolder_info(mock_vfolder_service):
    handler = VFolderHandler(storage_service=mock_vfolder_service)

    async def mock_request():
        request = AsyncMock(spec=web.Request)
        vfolder_id = VFolderID(
            folder_id=uuid.UUID("123e4567-e89b-12d3-a456-426614174000"), quota_scope_id=None
        )
        request.json.return_value = {
            "volume_id": "123e4567-e89b-12d3-a456-426614174000",
            "vfolder_id": vfolder_id,
        }
        return request

    response = await handler.get_vfolder_info(await mock_request())

    assert isinstance(response, VFolderMetadataResponseModel)
    assert response.mount_path == "/mock/mount/path"
    assert response.file_count == 100
    assert response.capacity_bytes == 1024 * 1024 * 1024
    assert response.used_bytes == 1024


@pytest.mark.asyncio
async def test_delete_vfolder(mock_vfolder_service):
    handler = VFolderHandler(storage_service=mock_vfolder_service)

    async def mock_request():
        request = AsyncMock(spec=web.Request)
        vfolder_id = VFolderID(
            folder_id=uuid.UUID("123e4567-e89b-12d3-a456-426614174000"), quota_scope_id=None
        )
        request.json.return_value = {
            "volume_id": "123e4567-e89b-12d3-a456-426614174000",
            "vfolder_id": vfolder_id,
        }
        return request

    response = await handler.delete_vfolder(await mock_request())

    assert isinstance(response, ProcessingResponseModel)
