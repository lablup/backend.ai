import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web

from ai.backend.common.types import QuotaConfig, QuotaScopeID, QuotaScopeType, VFolderID
from ai.backend.storage.errors import VFolderNotFoundError
from ai.backend.storage.services.service import VolumeService
from ai.backend.storage.services.service import log as service_log
from ai.backend.storage.volumes.pool import VolumePool
from ai.backend.storage.volumes.types import (
    QuotaScopeKey,
    QuotaScopeMeta,
    VFolderKey,
    VolumeMeta,
)

UUID = uuid.UUID("12345678-1234-5678-1234-567812345678")
UUID1 = uuid.UUID("12345678-1234-5678-1234-567812345679")
UUID2 = uuid.UUID("12345678-1234-5678-1234-567812345680")


@pytest.fixture
def mock_volume_pool():
    mock_pool = MagicMock(spec=VolumePool)
    return mock_pool


@pytest.fixture
def mock_service(mock_volume_pool):
    service = VolumeService(volume_pool=mock_volume_pool, event_producer=MagicMock())
    service._get_capabilities = AsyncMock(return_value=["capability1", "capability2"])

    service.log = service_log

    return service


@pytest.mark.asyncio
@patch("ai.backend.storage.services.service.log_manager_api_entry_new", new_callable=AsyncMock)
async def test_get_volume(mock_log, mock_service, mock_volume_pool):
    mock_volume_info = MagicMock()
    mock_volume_info.backend = "mock-backend"
    mock_volume_info.path = "/mock/path"
    mock_volume_info.fsprefix = "mock-fsprefix"

    mock_volume_pool.get_volume_info.return_value = mock_volume_info

    volume_id = UUID
    result = await mock_service.get_volume(volume_id)

    mock_log.assert_called_once_with(service_log, "get_volume", volume_id)
    mock_volume_pool.get_volume_info.assert_called_once_with(volume_id)
    mock_service._get_capabilities.assert_called_once_with(volume_id)

    assert isinstance(result, VolumeMeta)
    assert result.volume_id == volume_id
    assert result.backend == "mock-backend"
    assert result.path == "/mock/path"
    assert result.fsprefix == "mock-fsprefix"
    assert result.capabilities == ["capability1", "capability2"]


@pytest.mark.asyncio
@patch("ai.backend.storage.services.service.log_manager_api_entry_new", new_callable=AsyncMock)
async def test_get_volumes(mock_log, mock_service, mock_volume_pool):
    mock_volumes = {
        str(UUID1): MagicMock(backend="backend1", path="/path1", fsprefix="fsprefix1"),
        str(UUID2): MagicMock(backend="backend2", path="/path2", fsprefix="fsprefix2"),
    }
    mock_volume_pool.list_volumes.return_value = mock_volumes

    mock_service._get_capabilities.side_effect = [
        ["capability1", "capability2"],
        ["capability3"],
    ]

    result = await mock_service.get_volumes()

    mock_log.assert_called_once_with(service_log, "get_volumes", params=None)
    mock_volume_pool.list_volumes.assert_called_once()

    assert len(result) == 2
    assert result[0].volume_id == UUID1
    assert result[0].backend == "backend1"
    assert result[0].path == "/path1"
    assert result[0].fsprefix == "fsprefix1"
    assert result[0].capabilities == ["capability1", "capability2"]

    assert result[1].volume_id == UUID2
    assert result[1].backend == "backend2"
    assert result[1].path == "/path2"
    assert result[1].fsprefix == "fsprefix2"
    assert result[1].capabilities == ["capability3"]


@pytest.mark.asyncio
@patch("ai.backend.storage.services.service.log_manager_api_entry_new", new_callable=AsyncMock)
async def test_create_quota_scope(mock_log, mock_service, mock_volume_pool):
    mock_volume = MagicMock()
    mock_volume.quota_model.create_quota_scope = AsyncMock()

    mock_volume_pool.get_volume.return_value.__aenter__.return_value = mock_volume

    quota_scope_key = QuotaScopeKey(
        volume_id=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        quota_scope_id=UUID,
    )
    options = QuotaConfig(limit_bytes=1024 * 1024 * 1024)

    await mock_service.create_quota_scope(quota_scope_key, options)

    mock_log.assert_called_once_with(service_log, "create_quota_scope", quota_scope_key)
    mock_volume.quota_model.create_quota_scope.assert_called_once_with(
        quota_scope_id=UUID, options=options, extra_args=None
    )


@pytest.mark.asyncio
@patch("ai.backend.storage.services.service.log_manager_api_entry_new", new_callable=AsyncMock)
async def test_get_quota_scope(mock_log, mock_service, mock_volume_pool):
    mock_volume = MagicMock()
    quota_scope_meta = QuotaScopeMeta(used_bytes=500, limit_bytes=1000)
    mock_volume.quota_model.describe_quota_scope = AsyncMock(return_value=quota_scope_meta)

    mock_volume_pool.get_volume.return_value.__aenter__.return_value = mock_volume

    quota_scope_key = QuotaScopeKey(volume_id=UUID, quota_scope_id=UUID)

    result = await mock_service.get_quota_scope(quota_scope_key)

    mock_log.assert_called_once_with(service_log, "get_quota_scope", quota_scope_key)
    mock_volume.quota_model.describe_quota_scope.assert_called_once_with(UUID)

    assert result.used_bytes == 500
    assert result.limit_bytes == 1000


@pytest.mark.asyncio
@patch("ai.backend.storage.services.service.log_manager_api_entry_new", new_callable=AsyncMock)
async def test_update_quota_scope(mock_log, mock_service, mock_volume_pool):
    mock_volume = MagicMock()
    quota_scope_meta = QuotaScopeMeta(used_bytes=500, limit_bytes=1000)
    mock_volume.quota_model.describe_quota_scope = AsyncMock(return_value=quota_scope_meta)
    mock_volume.quota_model.update_quota_scope = AsyncMock()

    mock_volume_pool.get_volume.return_value.__aenter__.return_value = mock_volume

    quota_scope_key = QuotaScopeKey(volume_id=UUID, quota_scope_id=UUID)
    options = QuotaConfig(limit_bytes=2000)

    await mock_service.update_quota_scope(quota_scope_key, options)

    mock_log.assert_called_once_with(service_log, "update_quota_scope", quota_scope_key)
    mock_volume.quota_model.describe_quota_scope.assert_called_once_with(UUID)
    mock_volume.quota_model.update_quota_scope.assert_called_once_with(
        quota_scope_id=UUID, config=options
    )


@pytest.mark.asyncio
@patch("ai.backend.storage.services.service.log_manager_api_entry_new", new_callable=AsyncMock)
async def test_delete_quota_scope(mock_log, mock_service, mock_volume_pool):
    mock_volume = MagicMock()
    mock_volume.quota_model.describe_quota_scope = AsyncMock(
        return_value=MagicMock(used_bytes=500, limit_bytes=1000)
    )
    mock_volume.quota_model.unset_quota = AsyncMock()

    mock_volume_pool.get_volume.return_value.__aenter__.return_value = mock_volume

    quota_scope_key = QuotaScopeKey(volume_id=UUID, quota_scope_id=UUID)

    await mock_service.delete_quota_scope(quota_scope_key)

    mock_log.assert_called_once_with(service_log, "delete_quota_scope", quota_scope_key)
    mock_volume.quota_model.describe_quota_scope.assert_called_once_with(UUID)
    mock_volume.quota_model.unset_quota.assert_called_once_with(UUID)


@pytest.mark.asyncio
@patch("ai.backend.storage.services.service.log_manager_api_entry_new", new_callable=AsyncMock)
async def test_create_vfolder(mock_log, mock_service, mock_volume_pool):
    mock_volume = MagicMock()
    mock_volume.create_vfolder = AsyncMock()
    mock_volume.quota_model.create_quota_scope = AsyncMock()

    mock_volume_pool.get_volume.return_value.__aenter__.return_value = mock_volume

    vfolder_id = VFolderID(
        quota_scope_id=QuotaScopeID(scope_type=QuotaScopeType.USER, scope_id=UUID),
        folder_id=UUID,
    )
    vfolder_key = VFolderKey(volume_id=UUID, vfolder_id=vfolder_id)

    await mock_service.create_vfolder(vfolder_key)

    mock_log.assert_called_once_with(service_log, "create_vfolder", vfolder_key)
    mock_volume.create_vfolder.assert_called_once_with(vfolder_id)


@pytest.mark.asyncio
@patch("ai.backend.storage.services.service.log_manager_api_entry_new", new_callable=AsyncMock)
async def test_clone_vfolder(mock_log, mock_service, mock_volume_pool):
    mock_volume = MagicMock()
    mock_volume.clone_vfolder = AsyncMock()

    mock_volume_pool.get_volume.return_value.__aenter__.return_value = mock_volume

    src_vfolder_id = VFolderID(
        quota_scope_id=QuotaScopeID(scope_type=QuotaScopeType.USER, scope_id=UUID),
        folder_id=UUID,
    )
    dst_vfolder_id = VFolderID(
        quota_scope_id=QuotaScopeID(scope_type=QuotaScopeType.USER, scope_id=UUID1),
        folder_id=UUID2,
    )
    vfolder_key = VFolderKey(volume_id=UUID, vfolder_id=src_vfolder_id)

    await mock_service.clone_vfolder(vfolder_key, dst_vfolder_id)

    mock_log.assert_called_once_with(service_log, "clone_vfolder", vfolder_key)
    mock_volume.clone_vfolder.assert_called_once_with(src_vfolder_id, dst_vfolder_id)


@pytest.mark.asyncio
@patch("ai.backend.storage.services.service.log_manager_api_entry_new", new_callable=AsyncMock)
async def test_get_vfolder_info(mock_log, mock_service, mock_volume_pool):
    mock_volume = MagicMock()
    mock_volume.get_vfolder_mount = AsyncMock(return_value=Path("/mock/mount"))

    usage_data = MagicMock(spec=["file_count", "used_bytes"])
    usage_data.file_count = 10
    usage_data.used_bytes = 5000

    fs_usage_data = MagicMock(spec=["capacity_bytes", "used_bytes"])
    fs_usage_data.capacity_bytes = 100000
    fs_usage_data.used_bytes = 20000

    mock_volume.get_usage = AsyncMock(return_value=usage_data)
    mock_volume.get_fs_usage = AsyncMock(return_value=fs_usage_data)

    mock_volume_pool.get_volume.return_value.__aenter__.return_value = mock_volume

    vfolder_id = VFolderID(
        quota_scope_id=QuotaScopeID(scope_type=QuotaScopeType.USER, scope_id=UUID),
        folder_id=UUID,
    )
    vfolder_key = VFolderKey(volume_id=UUID, vfolder_id=vfolder_id)
    subpath = "test_subpath"

    result = await mock_service.get_vfolder_info(vfolder_key, subpath)

    mock_log.assert_called_once_with(service_log, "get_vfolder_info", vfolder_key)
    mock_volume.get_vfolder_mount.assert_called_once_with(vfolder_id, subpath)
    mock_volume.get_usage.assert_called_once_with(vfolder_id)
    mock_volume.get_fs_usage.assert_called_once()

    assert isinstance(result.mount_path, Path)
    assert result.mount_path == Path("/mock/mount")
    assert result.file_count == 10
    assert result.used_bytes == 5000
    assert result.capacity_bytes == 100000
    assert result.fs_used_bytes == 20000


@pytest.mark.asyncio
@patch("ai.backend.storage.services.service.log_manager_api_entry_new", new_callable=AsyncMock)
async def test_delete_vfolder(mock_log, mock_service, mock_volume_pool):
    mock_volume = MagicMock()
    mock_volume.get_vfolder_mount = AsyncMock(side_effect=VFolderNotFoundError)

    mock_volume_pool.get_volume.return_value.__aenter__.return_value = mock_volume

    vfolder_id = VFolderID(
        quota_scope_id=QuotaScopeID(scope_type=QuotaScopeType.USER, scope_id=UUID),
        folder_id=UUID,
    )
    vfolder_key = VFolderKey(volume_id=UUID, vfolder_id=vfolder_id)

    with pytest.raises(web.HTTPGone, match="VFolder not found"):
        await mock_service.delete_vfolder(vfolder_key)

    mock_log.assert_called_once_with(service_log, "delete_vfolder", vfolder_key)
    mock_volume.get_vfolder_mount.assert_called_once_with(vfolder_id, ".")
