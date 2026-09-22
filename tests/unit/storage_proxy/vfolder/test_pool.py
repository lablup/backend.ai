import uuid
from pathlib import Path, PurePath
from unittest.mock import AsyncMock, MagicMock

import pytest

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


async def test_get_volume(mock_volume: AsyncMock) -> None:
    # Create a VolumePool with mocked volumes
    volume_id = VolumeID(uuid.UUID("550e8400-e29b-41d4-a716-446655440000"))
    pool = VolumePool(volumes={str(volume_id): mock_volume, "test_volume": mock_volume})

    # Test get_volume with valid volume ID
    assert pool.get_volume(volume_id) is mock_volume

    # Test get_volume_by_name with valid name, including a UUID key
    assert pool.get_volume_by_name("test_volume") is mock_volume
    assert pool.get_volume_by_name(str(volume_id).upper()) is mock_volume

    # Test get_volume with invalid volume ID
    invalid_id = VolumeID(uuid.UUID("00000000-0000-0000-0000-000000000000"))
    with pytest.raises(InvalidVolumeError):
        pool.get_volume(invalid_id)

    # Test get_volume_by_name with invalid name
    with pytest.raises(InvalidVolumeError):
        pool.get_volume_by_name("nonexistent")
