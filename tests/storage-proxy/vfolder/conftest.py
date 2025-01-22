import uuid

import pytest

from ai.backend.storage.api.vfolder.manager_handler import VFolderHandler
from ai.backend.storage.api.vfolder.types import (
    QuotaConfigModel,
    QuotaScopeInfoModel,
    VFolderCloneModel,
    VFolderIDModel,
    VFolderInfoRequestModel,
    VolumeIDModel,
)

UUID = "8067790d-9a2e-4daf-8278-614ded1dc7f8"


@pytest.mark.asyncio
async def test_get_volume(mock_vfolder_service, mock_request):
    handler = VFolderHandler(storage_service=mock_vfolder_service)
    response = await handler.get_volume(mock_request)

    mock_vfolder_service.get_volume.assert_called_once_with(
        VolumeIDModel(volume_id=uuid.UUID(UUID))
    )
    result = await response.json()
    assert result["volume_id"] == str(uuid.UUID(UUID))
    assert result["backend"] == "default-backend"
    assert result["path"] == "/example/path"


@pytest.mark.asyncio
async def test_get_volumes(mock_vfolder_service):
    handler = VFolderHandler(storage_service=mock_vfolder_service)
    response = await handler.get_volumes(None)

    mock_vfolder_service.get_volumes.assert_called_once()
    result = await response.json()
    assert str(uuid.UUID(UUID)) in result
    assert result[str(uuid.UUID(UUID))]["backend"] == "default-backend"
    assert result[str(uuid.UUID(UUID))]["path"] == "/example/path"


@pytest.mark.asyncio
async def test_create_quota_scope(mock_vfolder_service, mock_request):
    handler = VFolderHandler(storage_service=mock_vfolder_service)
    response = await handler.create_quota_scope(mock_request)

    mock_vfolder_service.create_quota_scope.assert_called_once_with(
        QuotaConfigModel(volume_id=uuid.UUID(UUID), quota_scope_id="test-scope", options=None)
    )
    assert response.status == 204


@pytest.mark.asyncio
async def test_get_quota_scope(mock_vfolder_service, mock_request):
    handler = VFolderHandler(storage_service=mock_vfolder_service)
    response = await handler.get_quota_scope(mock_request)

    mock_vfolder_service.get_quota_scope.assert_called_once_with(
        QuotaScopeInfoModel(used_bytes=1024, limit_bytes=2048)
    )
    result = await response.json()
    assert result["used_bytes"] == 1024
    assert result["limit_bytes"] == 2048


@pytest.mark.asyncio
async def test_update_quota_scope(mock_vfolder_service, mock_request):
    handler = VFolderHandler(storage_service=mock_vfolder_service)
    response = await handler.update_quota_scope(mock_request)

    mock_vfolder_service.update_quota_scope.assert_called_once_with(
        QuotaConfigModel(volume_id=uuid.UUID(UUID), quota_scope_id="test-scope", options=None)
    )
    assert response.status == 204


@pytest.mark.asyncio
async def test_delete_quota_scope(mock_vfolder_service, mock_request):
    handler = VFolderHandler(storage_service=mock_vfolder_service)
    response = await handler.delete_quota_scope(mock_request)

    mock_vfolder_service.delete_quota_scope.assert_called_once_with(
        QuotaScopeInfoModel(used_bytes=1024, limit_bytes=2048)
    )
    assert response.status == 204


@pytest.mark.asyncio
async def test_create_vfolder(mock_vfolder_service, mock_request):
    handler = VFolderHandler(storage_service=mock_vfolder_service)
    response = await handler.create_vfolder(mock_request)

    mock_vfolder_service.create_vfolder.assert_called_once_with(
        VFolderIDModel(volume_id=uuid.UUID(UUID), vfolder_id="test-folder-id")
    )
    assert response.status == 204


@pytest.mark.asyncio
async def test_clone_vfolder(mock_vfolder_service, mock_request):
    handler = VFolderHandler(storage_service=mock_vfolder_service)
    response = await handler.clone_vfolder(mock_request)

    mock_vfolder_service.clone_vfolder.assert_called_once_with(
        VFolderCloneModel(
            volume_id=uuid.UUID(UUID),
            src_vfolder_id="source-folder",
            dst_vfolder_id="destination-folder",
        )
    )
    assert response.status == 204


@pytest.mark.asyncio
async def test_get_vfolder_info(mock_vfolder_service, mock_request):
    handler = VFolderHandler(storage_service=mock_vfolder_service)
    response = await handler.get_vfolder_info(mock_request)

    mock_vfolder_service.get_vfolder_info.assert_called_once_with(
        VFolderInfoRequestModel(
            volume_id=uuid.UUID(UUID),
            vfolder_id="test-folder-id",
            subpath="/test/path",
        )
    )
    result = await response.json()
    assert result["vfolder_mount"] == "/mount/point"
    assert result["vfolder_used_bytes"] == 2048


@pytest.mark.asyncio
async def test_delete_vfolder(mock_vfolder_service, mock_request):
    handler = VFolderHandler(storage_service=mock_vfolder_service)
    response = await handler.delete_vfolder(mock_request)

    mock_vfolder_service.delete_vfolder.assert_called_once_with(
        VFolderIDModel(volume_id=uuid.UUID(UUID), vfolder_id="test-folder-id")
    )
    assert response.status == 202
