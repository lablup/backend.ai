import uuid
from pathlib import Path, PurePath
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.storage_volume import StorageVolumeName
from ai.backend.common.defs import NOOP_STORAGE_VOLUME_NAME
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventDispatcher, EventProducer
from ai.backend.common.types import VolumeID
from ai.backend.storage.errors import InvalidVolumeError
from ai.backend.storage.types import VolumeInfo
from ai.backend.storage.volumes.abc import AbstractVolume
from ai.backend.storage.volumes.pool import VolumePool


@pytest.fixture
def mock_etcd() -> AsyncMock:
    return AsyncMock(spec=AsyncEtcd)


@pytest.fixture
def mock_event_dispatcher() -> MagicMock:
    return MagicMock(spec=EventDispatcher)


@pytest.fixture
def mock_event_producer() -> MagicMock:
    return MagicMock(spec=EventProducer)


@pytest.fixture
def mock_volume() -> AsyncMock:
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


VOLUME_ID = VolumeID(uuid.UUID("550e8400-e29b-41d4-a716-446655440000"))


async def test_get_volume_by_name(mock_volume: AsyncMock) -> None:
    pool = VolumePool(volumes={StorageVolumeName("test_volume"): mock_volume})

    assert pool.get_volume_by_name(StorageVolumeName("test_volume")) is mock_volume

    with pytest.raises(InvalidVolumeError):
        pool.get_volume_by_name(StorageVolumeName("nonexistent"))


async def test_get_volume_by_id(mock_volume: AsyncMock) -> None:
    pool = VolumePool(
        volumes={
            StorageVolumeName(str(VOLUME_ID).upper()): mock_volume,
            StorageVolumeName("test_volume"): mock_volume,
        }
    )

    assert pool.get_volume(VOLUME_ID) is mock_volume
    assert set(pool.list_volumes_by_id()) == {VOLUME_ID}

    with pytest.raises(InvalidVolumeError):
        pool.get_volume(VolumeID(uuid.UUID("00000000-0000-0000-0000-000000000000")))


async def test_list_volumes_excludes_noop_volume(mock_volume: AsyncMock) -> None:
    pool = VolumePool(
        volumes={
            StorageVolumeName("test_volume"): mock_volume,
            StorageVolumeName(NOOP_STORAGE_VOLUME_NAME): mock_volume,
        }
    )

    assert set(pool.list_volumes()) == {StorageVolumeName("test_volume")}
