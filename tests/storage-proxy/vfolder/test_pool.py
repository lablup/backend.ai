from typing import Mapping
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.dto.identifiers import VolumeID
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events import EventDispatcher, EventProducer
from ai.backend.storage.exception import InvalidVolumeError
from ai.backend.storage.types import VolumeInfo
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


def list_volumes(self) -> Mapping[str, VolumeInfo]:
    return {
        volume_id: VolumeInfo(
            backend=info["backend"],
            path=info["path"],
            fsprefix=info.get("fsprefix", ""),
            options=None,
        )
        for volume_id, info in self._local_config["volume"].items()
    }


def get_volume_info(self, volume_id: VolumeID) -> VolumeInfo:
    if volume_id not in self._local_config["volume"]:
        raise InvalidVolumeError(volume_id)
    volume_config = self._local_config["volume"][volume_id]
    return VolumeInfo(
        backend=volume_config["backend"],
        path=volume_config["path"],
        fsprefix=volume_config.get("fsprefix", ""),
        options=None,
    )


@pytest.mark.asyncio
async def test_get_volume():
    local_config = {
        "volume": {
            "test_volume": {
                "backend": "vfs",
                "path": "/mnt/test_volume",
                "options": {},
                "fsprefix": "vfs-test",
            }
        },
        "storage-proxy": {"scandir-limit": 1000},
    }

    mock_etcd = AsyncMock()
    mock_event_dispatcher = MagicMock()
    mock_event_producer = MagicMock()

    pool = VolumePool(local_config, mock_etcd, mock_event_dispatcher, mock_event_producer)
    await pool.__aenter__()
    async with pool.get_volume("test_volume") as volume:
        assert volume is not None

    async with pool.get_volume("test_volume") as volume2:
        assert volume is volume2
