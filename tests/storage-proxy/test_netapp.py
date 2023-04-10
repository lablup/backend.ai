import logging
import secrets
import uuid
from collections.abc import AsyncIterator
from pathlib import PurePath, PurePosixPath

import pytest

from ai.backend.storage.config import load_local_config
from ai.backend.storage.netapp import NetAppVolume
from ai.backend.storage.types import VFolderID

# module-level marker
pytestmark = pytest.mark.integration


@pytest.fixture
async def netapp_volume(vfroot) -> AsyncIterator[NetAppVolume]:
    # Get the first NetApp volume config from storage-proxy.toml
    log = logging.getLogger()
    local_config = load_local_config(None, debug=True)
    for volume_name, volume_config in local_config["volume"].items():
        if volume_config["backend"] == "netapp":
            options = volume_config["options"]
            log.info(f"Using volume {volume_name} for the integration test...")
            break
    else:
        raise RuntimeError(
            "Cannot proceed the integration test for the NetApp volume without actual configuration"
        )
    netapp = NetAppVolume(
        {
            "storage-proxy": {
                "scandir-limit": 1000,
            },
        },
        volume_config["path"],
        fsprefix=PurePath("fsprefix"),
        options=options,
    )
    await netapp.init()
    try:
        yield netapp
    finally:
        await netapp.shutdown()


@pytest.fixture
async def empty_vfolder(netapp_volume: NetAppVolume) -> AsyncIterator[VFolderID]:
    qsid = f"qs-{secrets.token_hex(16)}-0"
    vfid = VFolderID(qsid, uuid.uuid4())
    await netapp_volume.quota_model.create_quota_scope(qsid)
    await netapp_volume.create_vfolder(vfid)
    yield vfid
    await netapp_volume.delete_vfolder(vfid)
    await netapp_volume.quota_model.delete_quota_scope(qsid)


def test_dummy() -> None:
    # prevent pants error due to when no tests are selected.
    pass


@pytest.mark.integration
@pytest.mark.asyncio
async def test_netapp_get_usage(netapp_volume: NetAppVolume, empty_vfolder: VFolderID) -> None:
    vfpath = netapp_volume.mangle_vfpath(empty_vfolder)
    (vfpath / "test.txt").write_bytes(b"12345")
    (vfpath / "inner").mkdir()
    (vfpath / "inner" / "hello.txt").write_bytes(b"678")
    (vfpath / "inner" / "world.txt").write_bytes(b"901")
    (vfpath / "test2.txt").symlink_to((vfpath / "inner" / "hello.txt"))
    (vfpath / "inner2").symlink_to((vfpath / "inner"))
    usage = await netapp_volume.get_usage(empty_vfolder)
    assert usage.file_count == 7
    # This may vary depending on the device block size.
    assert 92 <= usage.used_bytes <= 4096 * 4


@pytest.mark.integration
@pytest.mark.asyncio
async def test_netapp_scandir(netapp_volume: NetAppVolume, empty_vfolder: VFolderID) -> None:
    vfpath = netapp_volume.mangle_vfpath(empty_vfolder)
    (vfpath / "test.txt").write_bytes(b"12345")
    (vfpath / "inner").mkdir()
    (vfpath / "inner" / "hello.txt").write_bytes(b"678")
    (vfpath / "inner" / "world.txt").write_bytes(b"901")
    (vfpath / "test2.txt").symlink_to((vfpath / "inner" / "hello.txt"))
    (vfpath / "inner2").symlink_to((vfpath / "inner"))
    async for entry in netapp_volume.scandir(empty_vfolder, PurePosixPath(".")):
        print(entry)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_netapp_clone(netapp_volume: NetAppVolume) -> None:
    qsid_base = secrets.token_hex(16)
    qsid1 = f"qs-{qsid_base}-0"
    qsid2 = f"qs-{qsid_base}-1"
    vfid1 = VFolderID(qsid1, uuid.uuid4())
    vfid2 = VFolderID(qsid2, uuid.uuid4())
    vfpath1 = netapp_volume.mangle_vfpath(vfid1)
    vfpath2 = netapp_volume.mangle_vfpath(vfid2)
    await netapp_volume.quota_model.create_quota_scope(qsid1)
    await netapp_volume.quota_model.create_quota_scope(qsid2)
    await netapp_volume.create_vfolder(vfid1)
    assert vfpath1.is_dir()
    (vfpath1 / "test.txt").write_bytes(b"12345")
    (vfpath1 / "inner").mkdir()
    (vfpath1 / "inner" / "hello.txt").write_bytes(b"678")
    await netapp_volume.clone_vfolder(vfid1, vfid2, None)
    assert vfpath2.is_dir()
    assert (vfpath2 / "test.txt").is_file()
    assert (vfpath2 / "inner").is_dir()
    assert (vfpath2 / "inner" / "hello.txt").is_file()
    await netapp_volume.delete_vfolder(vfid1)
    await netapp_volume.delete_vfolder(vfid2)
    await netapp_volume.quota_model.delete_quota_scope(qsid1)
    await netapp_volume.quota_model.delete_quota_scope(qsid2)
