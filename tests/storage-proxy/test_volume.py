import secrets
import uuid
from collections.abc import AsyncIterator
from pathlib import Path, PurePath, PurePosixPath
from typing import Any

import pytest

from ai.backend.common.exception import ConfigurationError
from ai.backend.storage.abc import AbstractVolume
from ai.backend.storage.config import load_local_config
from ai.backend.storage.types import VFolderID


def has_backend(backend_name: str) -> dict[str, Any] | None:
    try:
        local_config = load_local_config(None, debug=True)
    except ConfigurationError:
        return None
    for _, info in local_config["volume"].items():
        if info["backend"] == backend_name:
            return info
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
async def volume(request, local_volume) -> AsyncIterator[AbstractVolume]:
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
            from ai.backend.storage.cephfs import CephFSVolume

            volume_cls = CephFSVolume
        case "gpfs":
            from ai.backend.storage.gpfs import GPFSVolume

            volume_cls = GPFSVolume
        case "netapp":
            from ai.backend.storage.netapp import NetAppVolume

            volume_cls = NetAppVolume
        case "purestorage":
            from ai.backend.storage.purestorage import FlashBladeVolume

            volume_cls = FlashBladeVolume
        case "vfs":
            from ai.backend.storage.vfs import BaseVolume

            volume_cls = BaseVolume
        case "weka":
            from ai.backend.storage.weka import WekaVolume

            volume_cls = WekaVolume
        case "xfs":
            from ai.backend.storage.xfs import XfsVolume

            volume_cls = XfsVolume
        case _:
            raise RuntimeError(f"Unknown volume backend: {request.param}")
    volume = volume_cls(
        {
            "storage-proxy": {
                "scandir-limit": 1000,
            },
        },
        volume_path,
        fsprefix=PurePath("fsprefix"),
        options=backend_options,
    )
    await volume.init()
    try:
        yield volume
    finally:
        await volume.shutdown()


@pytest.fixture
async def empty_vfolder(volume: AbstractVolume) -> AsyncIterator[VFolderID]:
    qsid = f"qs-{secrets.token_hex(16)}-0"
    vfid = VFolderID(qsid, uuid.uuid4())
    await volume.quota_model.create_quota_scope(qsid)
    await volume.create_vfolder(vfid)
    yield vfid
    await volume.delete_vfolder(vfid)
    await volume.quota_model.delete_quota_scope(qsid)


@pytest.mark.asyncio
async def test_volume_vfolder_prefix_handling(volume: AbstractVolume) -> None:
    qsid = f"qs-{secrets.token_hex(16)}-0"
    vfid = VFolderID(qsid, uuid.uuid4())
    await volume.quota_model.create_quota_scope(qsid)
    await volume.create_vfolder(vfid)
    assert vfid.quota_scope_id is not None
    vfpath = (
        volume.mount_path
        / vfid.quota_scope_id
        / vfid.folder_id.hex[0:2]
        / vfid.folder_id.hex[2:4]
        / vfid.folder_id.hex[4:]
    )
    assert vfpath.is_dir()
    await volume.delete_vfolder(vfid)
    assert not vfpath.exists()
    assert not vfpath.parent.exists()
    assert not vfpath.parent.parent.exists()

    vfid1 = VFolderID(qsid, uuid.UUID(hex="82a6ba2b7b8e41deb5ee2c909c00000b"))
    vfid2 = VFolderID(qsid, uuid.UUID(hex="82a6ba2b7b8e41deb5ee2c909c00000c"))
    await volume.create_vfolder(vfid1)
    await volume.create_vfolder(vfid2)
    vfpath1 = (
        volume.mount_path
        / qsid
        / vfid1.folder_id.hex[0:2]
        / vfid1.folder_id.hex[2:4]
        / vfid1.folder_id.hex[4:]
    )
    vfpath2 = (
        volume.mount_path
        / qsid
        / vfid2.folder_id.hex[0:2]
        / vfid2.folder_id.hex[2:4]
        / vfid2.folder_id.hex[4:]
    )
    assert vfpath2.relative_to(vfpath1.parent).name == vfpath2.name
    assert vfpath1.is_dir()
    await volume.delete_vfolder(vfid1)
    assert not vfpath1.exists()
    # if the prefix dirs are not empty, they shouldn't be deleted
    assert vfpath1.parent.exists()
    assert vfpath1.parent.parent.exists()
    await volume.delete_vfolder(vfid2)
    assert not vfpath2.exists()
    # if the prefix dirs become empty, they should be deleted
    assert not vfpath2.parent.exists()
    assert not vfpath2.parent.parent.exists()

    await volume.quota_model.delete_quota_scope(qsid)
    assert not volume.quota_model.mangle_qspath(qsid).exists()


@pytest.mark.asyncio
async def test_volume_get_usage(volume: AbstractVolume, empty_vfolder: VFolderID) -> None:
    vfpath = volume.mangle_vfpath(empty_vfolder)
    (vfpath / "test.txt").write_bytes(b"12345")
    (vfpath / "inner").mkdir()
    (vfpath / "inner" / "hello.txt").write_bytes(b"678")
    (vfpath / "inner" / "world.txt").write_bytes(b"901")
    (vfpath / "test2.txt").symlink_to((vfpath / "inner" / "hello.txt"))
    (vfpath / "inner2").symlink_to((vfpath / "inner"))
    usage = await volume.get_usage(empty_vfolder)
    # Depending on the backend, the top directory may be included or not.
    assert usage.file_count in (6, 7)  # including directories
    # This may vary depending on the device block size.
    assert 11 <= usage.used_bytes <= 4096 * 4


@pytest.mark.asyncio
async def test_volume_scandir(volume: AbstractVolume, empty_vfolder: VFolderID) -> None:
    vfpath = volume.mangle_vfpath(empty_vfolder)
    (vfpath / "test.txt").write_bytes(b"12345")
    (vfpath / "inner").mkdir()
    (vfpath / "inner" / "hello.txt").write_bytes(b"678")
    (vfpath / "inner" / "world.txt").write_bytes(b"901")
    (vfpath / "test2.txt").symlink_to((vfpath / "inner" / "hello.txt"))
    (vfpath / "inner2").symlink_to((vfpath / "inner"))
    entries = []
    async for entry in volume.scandir(empty_vfolder, PurePosixPath(".")):
        entries.append(entry)
    assert len(entries) == 6
    merged_output = [str(entry.path) for entry in entries]
    assert "inner/hello.txt" in merged_output
    assert "inner/world.txt" in merged_output
    assert "test.txt" in merged_output
    assert "test2.txt" in merged_output
    assert "inner" in merged_output
    assert "inner2" in merged_output


@pytest.mark.asyncio
async def test_volume_clone(volume: AbstractVolume) -> None:
    qsid_base = secrets.token_hex(16)
    qsid1 = f"qs-{qsid_base}-0"
    qsid2 = f"qs-{qsid_base}-1"
    await volume.quota_model.create_quota_scope(qsid1)
    await volume.quota_model.create_quota_scope(qsid2)
    vfid1 = VFolderID(qsid1, uuid.uuid4())
    vfid2 = VFolderID(qsid2, uuid.uuid4())
    assert vfid1.quota_scope_id is not None
    assert vfid2.quota_scope_id is not None
    vfpath1 = volume.mangle_vfpath(vfid1)
    vfpath2 = volume.mangle_vfpath(vfid2)
    await volume.create_vfolder(vfid1)
    assert vfpath1.is_dir()
    (vfpath1 / "test.txt").write_bytes(b"12345")
    (vfpath1 / "inner").mkdir()
    (vfpath1 / "inner" / "hello.txt").write_bytes(b"678")
    await volume.clone_vfolder(vfid1, vfid2)
    assert vfpath2.is_dir()
    assert (vfpath2 / "test.txt").is_file()
    assert (vfpath2 / "inner").is_dir()
    assert (vfpath2 / "inner" / "hello.txt").is_file()
    await volume.delete_vfolder(vfid1)
    await volume.delete_vfolder(vfid2)
    await volume.quota_model.delete_quota_scope(qsid1)
    await volume.quota_model.delete_quota_scope(qsid2)
    assert not volume.quota_model.mangle_qspath(qsid1).exists()
    assert not volume.quota_model.mangle_qspath(qsid2).exists()


@pytest.mark.asyncio
async def test_volume_fsop(volume: AbstractVolume, empty_vfolder: VFolderID) -> None:
    vfpath = volume.mangle_vfpath(empty_vfolder)
    (vfpath / "test0").mkdir()
    (vfpath / "test0" / "test.txt").write_bytes(b"12345")
    with pytest.raises(FileNotFoundError):
        await volume.move_file(
            empty_vfolder, PurePosixPath("test0/test.txt"), PurePosixPath("test1/test.txt")
        )
    (vfpath / "test1").mkdir()
    await volume.move_file(
        empty_vfolder, PurePosixPath("test0/test.txt"), PurePosixPath("test1/test.txt")
    )
    assert (vfpath / "test1" / "test.txt").is_file()
    assert (vfpath / "test1" / "test.txt").read_bytes() == b"12345"
    assert not (vfpath / "test0" / "test.txt").is_file()

    # rename directory from test1 to test2
    await volume.move_tree(empty_vfolder, PurePosixPath("test1"), PurePosixPath("test2"))
    assert (vfpath / "test2").is_dir()
    assert (vfpath / "test2" / "test.txt").read_bytes() == b"12345"

    # move directory into another directory that not exists
    await volume.move_tree(
        empty_vfolder, PurePosixPath("test2"), PurePosixPath("test0/inner/test2/test3")
    )
    assert (vfpath / "test0" / "inner").is_dir()
    assert (vfpath / "test0" / "inner" / "test2" / "test3").is_dir()
    assert (vfpath / "test0" / "inner" / "test2" / "test3" / "test.txt").read_bytes() == b"12345"

    # move directory into another directory that already exists
    await volume.move_tree(
        empty_vfolder, PurePosixPath("test0/inner/test2/"), PurePosixPath("test0/")
    )
    assert (vfpath / "test0" / "test2" / "test3").is_dir()

    # do not let move directory to non-relative directory
    with pytest.raises(Exception):
        await volume.move_tree(empty_vfolder, PurePosixPath("test0"), PurePosixPath("../"))
        await volume.move_tree(empty_vfolder, PurePosixPath("/"), PurePosixPath("./"))
