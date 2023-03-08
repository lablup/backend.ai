import os
import uuid
from pathlib import Path, PurePath

import pytest

from ai.backend.common.types import BinarySize
from ai.backend.storage.vfs import BaseVolume, run
from ai.backend.storage.xfs import XfsVolume

# module-level marker
pytestmark = pytest.mark.integration


def read_etc_projid():
    with open("/etc/projid") as fp:
        content = fp.read()
    project_id_dict = {}
    for line in content.splitlines():
        proj_name, proj_id = line.split(":")[:2]
        project_id_dict[proj_name] = int(proj_id)
    return project_id_dict


def read_etc_projects():
    with open("/etc/projects") as fp:
        content = fp.read()
    vfpath_id_dict = {}
    for line in content.splitlines():
        proj_id, vfpath = line.split(":")[:2]
        vfpath_id_dict[int(proj_id)] = vfpath
    return vfpath_id_dict


def create_sample_dir_tree(vfpath: Path) -> int:
    (vfpath / "test.txt").write_bytes(b"12345")
    (vfpath / "inner").mkdir()
    (vfpath / "inner" / "hello.txt").write_bytes(b"678")
    return 8  # return number of bytes written


def assert_sample_dir_tree(vfpath: Path) -> None:
    assert (vfpath / "test.txt").is_file()
    assert (vfpath / "test.txt").read_bytes() == b"12345"
    assert (vfpath / "inner").is_dir()
    assert (vfpath / "inner" / "hello.txt").is_file()
    assert (vfpath / "inner" / "hello.txt").read_bytes() == b"678"


@pytest.fixture
async def xfs(vfroot):
    xfs = XfsVolume({}, vfroot / "xfs")
    await xfs.init(os.getuid(), os.getgid())
    try:
        yield xfs
    finally:
        await xfs.shutdown()


@pytest.fixture
async def vfs(local_volume):
    vfs = BaseVolume({}, local_volume, fsprefix=PurePath("fsprefix"), options={})
    await vfs.init()
    try:
        yield vfs
    finally:
        await vfs.shutdown()


@pytest.fixture
async def empty_vfolder(xfs):
    vfid = uuid.uuid4()
    await xfs.create_vfolder(vfid, options={"quota": BinarySize.from_str("10m")})
    yield vfid
    await xfs.delete_vfolder(vfid)


def test_dummy():
    # prevent pants error due to when no tests are selected.
    pass


@pytest.mark.integration
@pytest.mark.asyncio
async def test_xfs_single_vfolder_mgmt(xfs):
    vfid = uuid.uuid4()
    options = {"quota": BinarySize.from_str("10m")}
    # vfolder create test
    await xfs.create_vfolder(vfid, options=options)
    vfpath = xfs.mount_path / vfid.hex[0:2] / vfid.hex[2:4] / vfid.hex[4:]
    project_id_dict = read_etc_projid()
    vfpath_id_dict = read_etc_projects()
    assert vfpath.is_dir()
    assert str(vfid) in project_id_dict
    vfid_project_id = project_id_dict[str(vfid)]
    # vfolder delete test
    assert vfpath_id_dict[project_id_dict[str(vfid)]] == str(vfpath)
    await xfs.delete_vfolder(vfid)
    assert not vfpath.exists()
    assert not vfpath.parent.exists() or not (vfpath.parent / vfid.hex[2:4]).exists()
    assert not vfpath.parent.parent.exists() or not (vfpath.parent.parent / vfid.hex[0:2]).exists()
    project_id_dict = read_etc_projid()
    vfpath_id_dict = read_etc_projects()
    assert str(vfid) not in project_id_dict
    assert vfid_project_id not in vfpath_id_dict


@pytest.mark.integration
@pytest.mark.asyncio
async def test_xfs_multiple_vfolder_mgmt(xfs):
    vfid1 = uuid.UUID(hex="83a6ba2b7b8e41deb5ee2c909ce34bcb")
    vfid2 = uuid.UUID(hex="83a6ba2b7b8e41deb5ee2c909ce34bcc")
    options = {"quota": BinarySize.from_str("10m")}
    await xfs.create_vfolder(vfid1, options=options)
    await xfs.create_vfolder(vfid2, options=options)
    vfpath1 = xfs.mount_path / vfid1.hex[0:2] / vfid1.hex[2:4] / vfid1.hex[4:]
    vfpath2 = xfs.mount_path / vfid2.hex[0:2] / vfid2.hex[2:4] / vfid2.hex[4:]
    assert vfpath2.relative_to(vfpath1.parent).name == vfpath2.name
    assert vfpath1.is_dir()
    await xfs.delete_vfolder(vfid1)
    assert not vfpath1.exists()
    # if the prefix dirs are not empty, they shouldn't be deleted
    assert vfpath1.parent.exists()
    assert vfpath1.parent.parent.exists()
    await xfs.delete_vfolder(vfid2)
    # if the prefix dirs become empty, they should be deleted
    assert not vfpath2.parent.exists()
    assert not vfpath2.parent.parent.exists()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_xfs_quota(xfs):
    vfid = uuid.uuid4()
    options = {"quota": BinarySize.from_str("10m")}
    await xfs.create_vfolder(vfid, options=options)
    vfpath = xfs.mount_path / vfid.hex[0:2] / vfid.hex[2:4] / vfid.hex[4:]
    assert vfpath.is_dir()
    assert await xfs.get_quota(vfid) == BinarySize.from_str("10m")
    await xfs.set_quota(vfid, BinarySize.from_str("1m"))
    assert await xfs.get_quota(vfid) == BinarySize.from_str("1m")
    await xfs.delete_vfolder(vfid)
    assert not vfpath.is_dir()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_xfs_get_usage(xfs, empty_vfolder):
    vfpath = xfs.mangle_vfpath(empty_vfolder)
    (vfpath / "test.txt").write_bytes(b"12345")
    (vfpath / "inner").mkdir()
    (vfpath / "inner" / "hello.txt").write_bytes(b"678")
    (vfpath / "inner" / "world.txt").write_bytes(b"901")
    usage = await xfs.get_usage(empty_vfolder)
    assert usage.file_count == 3
    assert usage.used_bytes == 11


@pytest.mark.integration
@pytest.mark.asyncio
async def test_xfs_get_used_bytes(xfs):
    vfid = uuid.uuid4()
    options = {"quota": BinarySize.from_str("10m")}
    await xfs.create_vfolder(vfid, options=options)
    vfpath = xfs.mount_path / vfid.hex[0:2] / vfid.hex[2:4] / vfid.hex[4:]
    (vfpath / "test.txt").write_bytes(b"12345")
    (vfpath / "inner").mkdir()
    (vfpath / "inner" / "hello.txt").write_bytes(b"678")
    (vfpath / "inner" / "world.txt").write_bytes(b"901")

    used_bytes = await xfs.get_used_bytes(vfid)
    full_report = await run(
        ["sudo", "xfs_quota", "-x", "-c", "report -h", xfs.mount_path],
    )
    report = ""
    for line in full_report.split("\n"):
        if str(vfid) in line:
            report = line
            break
    assert len(report.split()) == 6
    proj_name, xfs_used, _, _, _, _ = report.split()
    assert str(vfid)[:-5] == proj_name
    assert used_bytes == BinarySize.from_str(xfs_used)
    await xfs.delete_vfolder(vfid)
    assert not vfpath.is_dir()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_xfs_mkdir_rmdir(xfs, empty_vfolder):
    vfpath = xfs.mangle_vfpath(empty_vfolder)
    test_rel_path = "test/abc"
    await xfs.mkdir(empty_vfolder, Path(test_rel_path), parents=True)
    assert Path(vfpath, test_rel_path).is_dir()
    await xfs.rmdir(empty_vfolder, Path(test_rel_path), recursive=True)
    assert not Path(vfpath, test_rel_path).is_dir()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_xfs_vfolder_operations(xfs, empty_vfolder):
    vfpath = xfs.mangle_vfpath(empty_vfolder)
    (vfpath / "test0").mkdir()
    (vfpath / "test0" / "test.txt").write_bytes(b"12345")
    await xfs.move_file(empty_vfolder, Path("test0/test.txt"), Path("test1/test.txt"))
    assert (vfpath / "test1" / "test.txt").is_file()
    assert (vfpath / "test1" / "test.txt").read_bytes() == b"12345"
    assert not (vfpath / "test0" / "test.txt").is_file()

    await xfs.copy_file(empty_vfolder, Path("test1/test.txt"), Path("test2/test.txt"))
    assert (vfpath / "test1" / "test.txt").is_file()
    assert (vfpath / "test2" / "test.txt").is_file()
    assert (vfpath / "test2" / "test.txt").read_bytes() == b"12345"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_xfs_clone_to_vfs(xfs, vfs):
    vfid_src = uuid.uuid4()
    vfid_dst = uuid.uuid4()
    vfpath_src = xfs.mangle_vfpath(vfid_src)
    vfpath_dst = vfs.mangle_vfpath(vfid_dst)
    await xfs.create_vfolder(vfid_src)
    assert vfpath_src.is_dir()
    create_sample_dir_tree(vfpath_src)

    await xfs.clone_vfolder(vfid_src, vfs, vfid_dst)
    assert_sample_dir_tree(vfpath_dst)

    await xfs.delete_vfolder(vfid_src)
    await vfs.delete_vfolder(vfid_dst)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_vfs_clone_to_xfs(xfs, vfs):
    vfid_src = uuid.uuid4()
    vfid_dst = uuid.uuid4()
    vfpath_src = vfs.mangle_vfpath(vfid_src)
    vfpath_dst = xfs.mangle_vfpath(vfid_dst)
    await vfs.create_vfolder(vfid_src)
    assert vfpath_src.is_dir()
    create_sample_dir_tree(vfpath_src)

    await vfs.clone_vfolder(vfid_src, xfs, vfid_dst)
    assert_sample_dir_tree(vfpath_dst)

    await vfs.delete_vfolder(vfid_src)
    await xfs.delete_vfolder(vfid_dst)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_xfs_clone_to_xfs(xfs, vfs):
    vfid_src = uuid.uuid4()
    vfid_dst = uuid.uuid4()
    vfpath_src = xfs.mangle_vfpath(vfid_src)
    vfpath_dst = xfs.mangle_vfpath(vfid_dst)
    await xfs.create_vfolder(vfid_src)
    assert vfpath_src.is_dir()
    create_sample_dir_tree(vfpath_src)

    await xfs.clone_vfolder(vfid_src, xfs, vfid_dst)
    assert_sample_dir_tree(vfpath_dst)

    await xfs.delete_vfolder(vfid_src)
    await xfs.delete_vfolder(vfid_dst)
