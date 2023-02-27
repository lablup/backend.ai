import os
import secrets
import shutil
import uuid
from pathlib import Path, PurePath, PurePosixPath

import pytest

from ai.backend.storage.purestorage import FlashBladeVolume
from ai.backend.storage.types import DirEntryType

# module-level marker
pytestmark = pytest.mark.integration


@pytest.fixture
def fbroot():
    tmpdir_name = f"bai-storage-test-{secrets.token_urlsafe(12)}"
    tmpdir = Path(os.environ["BACKEND_STORAGE_TEST_FBMOUNT"]) / tmpdir_name
    tmpdir.mkdir()
    try:
        yield tmpdir
    finally:
        shutil.rmtree(tmpdir)


@pytest.fixture
async def fb_volume(fbroot):
    options = {
        # TODO: mock options
    }
    host = FlashBladeVolume(fbroot, fsprefix=PurePath("fsprefix"), options=options)
    await host.init()
    try:
        yield host
    finally:
        await host.shutdown()


@pytest.fixture
async def empty_vfolder(fb_volume):
    vfid = uuid.uuid4()
    await fb_volume.create_vfolder(vfid)
    yield vfid
    await fb_volume.delete_vfolder(vfid)


def test_dummy():
    # prevent pants error due to when no tests are selected.
    pass


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fb_get_usage(fb_volume, empty_vfolder):
    vfpath = fb_volume._mangle_vfpath(empty_vfolder)
    (vfpath / "test.txt").write_bytes(b"12345")
    (vfpath / "inner").mkdir()
    (vfpath / "inner" / "hello.txt").write_bytes(b"678")
    (vfpath / "inner" / "world.txt").write_bytes(b"901")
    (vfpath / "test2.txt").symlink_to((vfpath / "inner" / "hello.txt"))
    (vfpath / "inner2").symlink_to((vfpath / "inner"))
    usage = await fb_volume.get_usage(empty_vfolder)
    assert usage.file_count == 5  # including symlinks
    assert usage.used_bytes == (
        11 + len(bytes(vfpath / "inner" / "hello.txt")) + len(bytes(vfpath / "inner"))
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_fb_scandir(fb_volume, empty_vfolder):
    vfpath = fb_volume._mangle_vfpath(empty_vfolder)
    (vfpath / "test1.txt").write_bytes(b"12345")
    (vfpath / "inner").mkdir()
    (vfpath / "inner" / "hello.txt").write_bytes(b"abc")
    (vfpath / "inner" / "world.txt").write_bytes(b"def")
    (vfpath / "test2.txt").symlink_to((vfpath / "inner" / "hello.txt"))
    (vfpath / "inner2").symlink_to((vfpath / "inner"))
    entries = [item async for item in fb_volume.scandir(empty_vfolder, PurePosixPath("."))]
    assert len(entries) == 4
    entries.sort(key=lambda entry: entry.name)
    assert entries[0].name == "inner"
    assert entries[0].type == DirEntryType.DIRECTORY
    assert entries[1].name == "inner2"
    assert entries[1].type == DirEntryType.SYMLINK
    assert entries[2].name == "test1.txt"
    assert entries[2].type == DirEntryType.FILE
    assert entries[3].name == "test2.txt"
    assert entries[3].type == DirEntryType.SYMLINK
