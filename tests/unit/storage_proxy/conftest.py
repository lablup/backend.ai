import secrets
import tempfile
import uuid
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.exception import ConfigurationError
from ai.backend.common.types import HostPortPair, QuotaScopeID, QuotaScopeType
from ai.backend.logging import LogLevel
from ai.backend.storage.config.loaders import load_local_config
from ai.backend.storage.types import VFolderID
from ai.backend.storage.volumes.abc import AbstractVolume
from ai.backend.storage.volumes.cephfs import CephFSVolume
from ai.backend.storage.volumes.gpfs import GPFSVolume
from ai.backend.storage.volumes.netapp import NetAppVolume
from ai.backend.storage.volumes.purestorage import FlashBladeVolume
from ai.backend.storage.volumes.vfs import BaseVolume
from ai.backend.storage.volumes.weka import WekaVolume
from ai.backend.storage.volumes.xfs import XfsVolume


@pytest.fixture(scope="session")
def test_id() -> str:
    return secrets.token_hex(6)


@pytest.fixture
def vfroot() -> Iterator[Path]:
    with tempfile.TemporaryDirectory(prefix="bai-storage-test-") as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def local_volume(vfroot: Path) -> Iterator[Path]:
    volume = vfroot / "local"
    volume.mkdir(parents=True, exist_ok=True)
    yield volume


@pytest.fixture
async def mock_etcd() -> AsyncIterator[AsyncEtcd]:
    async with AsyncEtcd(
        addrs=[HostPortPair("", 0)],
        namespace="",
        scope_prefix_map={
            ConfigScopes.GLOBAL: "",
        },
    ) as etcd:
        yield etcd


def has_backend(backend_name: str) -> dict[str, Any] | None:
    try:
        local_config = load_local_config(None, log_level=LogLevel.DEBUG)
    except ConfigurationError:
        return None
    for _, info in local_config.volume.items():
        if info.backend == backend_name:
            return info.model_dump(by_alias=True)
    return None


@pytest.fixture(
    params=[
        "cephfs",
        "gpfs",
        "netapp",
        "purestorage",
        "vfs",
        "weka",
        "xfs",
    ]
)
async def volume(
    request: Any,
    local_volume: Path,
    mock_etcd: AsyncEtcd,
) -> AsyncIterator[AbstractVolume]:
    volume_cls: type[AbstractVolume]
    backend_options = {}
    volume_path = local_volume
    if request.param != "vfs":
        backend_config = has_backend(request.param)
        if backend_config is None:
            pytest.skip(f"{request.param} backend is not installed")
        backend_options = backend_config.get("options", {})
        volume_path = Path(backend_config["path"])
    match request.param:
        case "cephfs":
            volume_cls = CephFSVolume
        case "gpfs":
            volume_cls = GPFSVolume
        case "netapp":
            volume_cls = NetAppVolume
        case "purestorage":
            volume_cls = FlashBladeVolume
        case "vfs":
            volume_cls = BaseVolume
        case "weka":
            volume_cls = WekaVolume
        case "xfs":
            volume_cls = XfsVolume
        case _:
            raise RuntimeError(f"Unknown volume backend: {request.param}")
    mock_event_dispatcher = MagicMock()
    mock_event_producer = MagicMock()
    volume = volume_cls(
        {
            "storage-proxy": {
                "scandir-limit": 1000,
            },
        },
        volume_path,
        etcd=mock_etcd,
        options=backend_options,
        event_dispatcher=mock_event_dispatcher,
        event_producer=mock_event_producer,
    )
    await volume.init()
    try:
        yield volume
    finally:
        await volume.shutdown()


@pytest.fixture
async def empty_vfolder(volume: AbstractVolume) -> AsyncIterator[VFolderID]:
    qsid = QuotaScopeID(QuotaScopeType.USER, uuid.uuid4())
    vfid = VFolderID(qsid, uuid.uuid4())
    await volume.quota_model.create_quota_scope(qsid)
    await volume.create_vfolder(vfid)
    yield vfid
    await volume.delete_vfolder(vfid)
    await volume.quota_model.delete_quota_scope(qsid)
