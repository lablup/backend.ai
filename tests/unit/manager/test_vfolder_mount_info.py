from __future__ import annotations

import uuid
from pathlib import PurePosixPath

from ai.backend.common.data.vfolder.types import VFolderMountData
from ai.backend.common.types import (
    MountPermission,
    VFolderID,
    VFolderMount,
    VFolderUsageMode,
)
from ai.backend.manager.api.gql_legacy.session import (
    VFolderMountInfo,
    _vfolder_mount_info_from_mount,
    _vfolder_mount_infos,
)


def _make_mount(
    *,
    vfsubpath: str,
    kernel_path: str = "/home/work/data",
    name: str = "data",
    mount_perm: MountPermission = MountPermission.READ_WRITE,
    usage_mode: VFolderUsageMode = VFolderUsageMode.GENERAL,
) -> VFolderMount:
    folder_id = uuid.uuid4()
    return VFolderMount(
        name=name,
        vfid=VFolderID(quota_scope_id=None, folder_id=folder_id),
        vfsubpath=PurePosixPath(vfsubpath),
        host_path=PurePosixPath("/vfroot/data"),
        kernel_path=PurePosixPath(kernel_path),
        mount_perm=mount_perm,
        usage_mode=usage_mode,
    )


def test_mapping_with_custom_subpath_and_destination() -> None:
    mount = _make_mount(
        vfsubpath="sub/dir",
        kernel_path="/home/work/alias",
        name="myfolder",
        mount_perm=MountPermission.READ_ONLY,
    )
    info = _vfolder_mount_info_from_mount(mount)

    assert isinstance(info, VFolderMountInfo)
    assert info.vfolder_id == str(mount.vfid.folder_id)
    assert info.name == "myfolder"
    assert info.subpath == "sub/dir"
    assert info.mount_destination == "/home/work/alias"
    assert info.permission == MountPermission.READ_ONLY.value
    assert info.usage_mode == VFolderUsageMode.GENERAL.value


def test_mapping_root_subpath_is_none() -> None:
    mount = _make_mount(vfsubpath=".")
    info = _vfolder_mount_info_from_mount(mount)

    assert info.subpath is None
    assert info.mount_destination == "/home/work/data"


def test_mapping_from_dataclass() -> None:
    folder_id = uuid.uuid4()
    data = VFolderMountData(
        name="data",
        vfid=VFolderID(quota_scope_id=None, folder_id=folder_id),
        vfsubpath=PurePosixPath("nested"),
        host_path=PurePosixPath("/vfroot/data"),
        kernel_path=PurePosixPath("/home/work/data"),
        mount_perm=MountPermission.READ_WRITE,
        usage_mode=VFolderUsageMode.GENERAL,
    )
    info = _vfolder_mount_info_from_mount(data)

    assert info.vfolder_id == str(folder_id)
    assert info.subpath == "nested"
    assert info.mount_destination == "/home/work/data"
    assert info.permission == MountPermission.READ_WRITE.value


def test_mapping_list_preserves_order() -> None:
    mounts = [
        _make_mount(vfsubpath=".", name="first"),
        _make_mount(vfsubpath="x", name="second"),
    ]
    infos = _vfolder_mount_infos(mounts)

    assert [i.name for i in infos] == ["first", "second"]
    assert infos[0].subpath is None
    assert infos[1].subpath == "x"
