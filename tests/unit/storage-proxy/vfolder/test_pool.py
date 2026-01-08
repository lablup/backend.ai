from pathlib import Path, PurePath
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.types import VolumeID
from ai.backend.storage.errors import InvalidVolumeError
from ai.backend.storage.plugin import StoragePluginContext
from ai.backend.storage.types import VolumeInfo
from ai.backend.storage.volumes.abc import AbstractVolume
from ai.backend.storage.volumes.pool import VolumePool


@pytest.fixture
def mock_etcd():
    return AsyncMock(spec=AsyncEtcd)


@pytest.fixture
def mock_event_dispatcher():
    return MagicMock(spec=EventDispatcher)


@pytest.fixture
def mock_event_producer():
    return MagicMock(spec=EventProducer)


@pytest.fixture
def mock_volume():
    volume = AsyncMock(spec=AbstractVolume)
    volume.info.return_value = VolumeInfo(
        backend="vfs",
        path=Path("/mnt/test_volume"),
        fsprefix=PurePath("vfs-test"),
        options={},
    )
    volume.init = AsyncMock()
    volume.shutdown = AsyncMock()
    return volume


@pytest.fixture
def mock_storage_plugin_ctx():
    ctx = AsyncMock(spec=StoragePluginContext)
    ctx.init = AsyncMock()
    ctx.cleanup = AsyncMock()
    ctx.plugins = {}
    return ctx


@pytest.mark.asyncio
async def test_get_volume(mock_volume, mock_storage_plugin_ctx):
    # Create a VolumePool with mocked volumes
    volume_id = VolumeID("550e8400-e29b-41d4-a716-446655440000")
    volumes = {volume_id: mock_volume}
    volumes_by_name = {"test_volume": mock_volume}

    pool = VolumePool(
        volumes=volumes,
        volumes_by_name=volumes_by_name,
        storage_backend_plugin_ctx=mock_storage_plugin_ctx,
    )

    # Test get_volume with valid volume ID
    async with pool.get_volume(volume_id) as volume:
        assert volume is mock_volume

    # Test get_volume_by_name with valid name
    async with pool.get_volume_by_name("test_volume") as volume:
        assert volume is mock_volume

    # Test get_volume with invalid volume ID
    invalid_id = VolumeID("00000000-0000-0000-0000-000000000000")
    with pytest.raises(InvalidVolumeError):
        async with pool.get_volume(invalid_id) as volume:
            pass

    # Test get_volume_by_name with invalid name
    with pytest.raises(InvalidVolumeError):
        async with pool.get_volume_by_name("nonexistent") as volume:
            pass
