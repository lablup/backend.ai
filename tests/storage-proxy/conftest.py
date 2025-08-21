import secrets
import tempfile
import uuid
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import aioboto3
import pytest
from botocore.exceptions import ClientError

from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.exception import ConfigurationError
from ai.backend.common.types import HostPortPair, QuotaScopeID, QuotaScopeType
from ai.backend.logging import LogLevel
from ai.backend.storage.client.s3 import S3Client
from ai.backend.storage.config.loaders import load_local_config
from ai.backend.storage.types import VFolderID
from ai.backend.storage.volumes.abc import AbstractVolume
from ai.backend.testutils.bootstrap import minio_container  # noqa: F401


@pytest.fixture(scope="session")
def test_id() -> str:
    return secrets.token_hex(6)


@pytest.fixture
def vfroot() -> Iterator[Path]:
    with tempfile.TemporaryDirectory(prefix="bai-storage-test-") as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def local_volume(vfroot) -> Iterator[Path]:
    volume = vfroot / "local"
    volume.mkdir(parents=True, exist_ok=True)
    yield volume


@pytest.fixture
def mock_etcd() -> Iterator[AsyncEtcd]:
    yield AsyncEtcd(
        addrs=[HostPortPair("", 0)],
        namespace="",
        scope_prefix_map={
            ConfigScopes.GLOBAL: "",
        },
    )


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
    request,
    local_volume,
    mock_etcd,
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
            from ai.backend.storage.volumes.cephfs import CephFSVolume

            volume_cls = CephFSVolume
        case "gpfs":
            from ai.backend.storage.volumes.gpfs import GPFSVolume

            volume_cls = GPFSVolume
        case "netapp":
            from ai.backend.storage.volumes.netapp import NetAppVolume

            volume_cls = NetAppVolume
        case "purestorage":
            from ai.backend.storage.volumes.purestorage import FlashBladeVolume

            volume_cls = FlashBladeVolume
        case "vfs":
            from ai.backend.storage.volumes.vfs import BaseVolume

            volume_cls = BaseVolume
        case "weka":
            from ai.backend.storage.volumes.weka import WekaVolume

            volume_cls = WekaVolume
        case "xfs":
            from ai.backend.storage.volumes.xfs import XfsVolume

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


@pytest.fixture
async def s3_client(minio_container):  # noqa: F811
    """Create S3Client instance for testing with MinIO container"""
    container_id, host_port = minio_container

    client = S3Client(
        bucket_name="test-bucket",
        endpoint_url=f"http://{host_port.host}:{host_port.port}",
        region_name="us-east-1",
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
    )

    # Create test bucket
    session = aioboto3.Session()
    async with session.client(
        "s3",
        endpoint_url=f"http://{host_port.host}:{host_port.port}",
        region_name="us-east-1",
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
    ) as s3_admin:
        try:
            await s3_admin.create_bucket(Bucket="test-bucket")
        except ClientError as e:
            # Bucket might already exist
            if e.response["Error"]["Code"] != "BucketAlreadyOwnedByYou":
                raise

    return client
