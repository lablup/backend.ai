import uuid
from pathlib import PurePath

import pytest

from ai.backend.storage.netapp import NetAppVolume

# module-level marker
pytestmark = pytest.mark.integration


@pytest.fixture
async def netapp_volume(vfroot):
    options = {
        # TODO: mock options
    }
    netapp = NetAppVolume(
        {},
        vfroot / "netapp",
        fsprefix=PurePath("fsprefix"),
        options=options,
    )
    await netapp.init()
    try:
        yield netapp
    finally:
        await netapp.shutdown()


@pytest.fixture
async def empty_vfolder(netapp_volume):
    vfid = uuid.uuid4()
    await netapp_volume.create_vfolder(vfid)
    yield vfid
    await netapp_volume.delete_vfolder(vfid)


def test_dummy():
    # prevent pants error due to when no tests are selected.
    pass


@pytest.mark.integration
@pytest.mark.asyncio
async def test_netapp_get_usage(netapp_volume, empty_vfolder):
    vfpath = netapp_volume.mangle_vfpath(empty_vfolder)
    (vfpath / "test.txt").write_bytes(b"12345")
    (vfpath / "inner").mkdir()
    (vfpath / "inner" / "hello.txt").write_bytes(b"678")
    (vfpath / "inner" / "world.txt").write_bytes(b"901")
    (vfpath / "test2.txt").symlink_to((vfpath / "inner" / "hello.txt"))
    (vfpath / "inner2").symlink_to((vfpath / "inner"))
    usage = await netapp_volume.get_usage(empty_vfolder)
    assert usage.file_count == 6
    assert usage.used_bytes == 92


@pytest.mark.integration
@pytest.mark.asyncio
async def test_netapp_clone(netapp_volume):
    vfid1 = uuid.uuid4()
    vfid2 = uuid.uuid4()
    vfpath1 = netapp_volume.mount_path / vfid1.hex[0:2] / vfid1.hex[2:4] / vfid1.hex[4:]
    vfpath2 = netapp_volume.mount_path / vfid2.hex[0:2] / vfid2.hex[2:4] / vfid2.hex[4:]
    await netapp_volume.create_vfolder(vfid1)
    assert vfpath1.is_dir()
    (vfpath1 / "test.txt").write_bytes(b"12345")
    (vfpath1 / "inner").mkdir()
    (vfpath1 / "inner" / "hello.txt").write_bytes(b"678")
    await netapp_volume.clone_vfolder(vfid1, netapp_volume, vfid2, None)
    assert vfpath2.is_dir()
    assert (vfpath2 / "test.txt").is_file()
    assert (vfpath2 / "inner").is_dir()
    assert (vfpath2 / "inner" / "hello.txt").is_file()
    await netapp_volume.delete_vfolder(vfid1)
    await netapp_volume.delete_vfolder(vfid2)
