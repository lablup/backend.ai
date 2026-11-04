from __future__ import annotations

import uuid
from pathlib import Path, PurePosixPath

import pytest

from ai.backend.agent.errors.agent import InvalidVFolderMountSourceError
from ai.backend.agent.vfolder_mount import resolve_vfolder_mount_source
from ai.backend.common.types import (
    MountPermission,
    QuotaScopeID,
    QuotaScopeType,
    VFolderID,
    VFolderMount,
    VFolderUsageMode,
)


def _make_mount(host_path: Path, vfsubpath: str) -> VFolderMount:
    return VFolderMount(
        name="data",
        vfid=VFolderID(QuotaScopeID(QuotaScopeType.USER, uuid.uuid4()), uuid.uuid4()),
        vfsubpath=PurePosixPath(vfsubpath),
        host_path=PurePosixPath(host_path),
        kernel_path=PurePosixPath("/home/work/data"),
        mount_perm=MountPermission.READ_WRITE,
        usage_mode=VFolderUsageMode.GENERAL,
    )


@pytest.fixture
def vfolder_base(tmp_path: Path) -> Path:
    base = tmp_path / "vfroot" / "vfolder"
    (base / "sub" / "nested").mkdir(parents=True)
    return base


@pytest.fixture
def outside_dir(tmp_path: Path) -> Path:
    outside = tmp_path / "outside"
    outside.mkdir()
    return outside


class TestResolveVFolderMountSource:
    def test_whole_folder_mount_returns_host_path(self, vfolder_base: Path) -> None:
        mount = _make_mount(vfolder_base, ".")

        assert resolve_vfolder_mount_source(mount) == vfolder_base

    def test_subpath_mount_returns_resolved_path(self, vfolder_base: Path) -> None:
        mount = _make_mount(vfolder_base / "sub" / "nested", "sub/nested")

        assert resolve_vfolder_mount_source(mount) == (vfolder_base / "sub" / "nested").resolve()

    def test_symlink_inside_vfolder_returns_target(self, vfolder_base: Path) -> None:
        (vfolder_base / "link").symlink_to(vfolder_base / "sub" / "nested")
        mount = _make_mount(vfolder_base / "link", "link")

        assert resolve_vfolder_mount_source(mount) == (vfolder_base / "sub" / "nested").resolve()

    def test_symlink_to_outside_is_rejected(self, vfolder_base: Path, outside_dir: Path) -> None:
        (vfolder_base / "link").symlink_to(outside_dir)
        mount = _make_mount(vfolder_base / "link", "link")

        with pytest.raises(InvalidVFolderMountSourceError):
            resolve_vfolder_mount_source(mount)

    def test_nested_symlink_to_outside_is_rejected(
        self, vfolder_base: Path, outside_dir: Path
    ) -> None:
        (vfolder_base / "sub" / "link").symlink_to(outside_dir)
        mount = _make_mount(vfolder_base / "sub" / "link", "sub/link")

        with pytest.raises(InvalidVFolderMountSourceError):
            resolve_vfolder_mount_source(mount)

    def test_parent_reference_escaping_vfolder_is_rejected(self, vfolder_base: Path) -> None:
        mount = _make_mount(vfolder_base / ".." / "..", "../..")

        with pytest.raises(InvalidVFolderMountSourceError):
            resolve_vfolder_mount_source(mount)

    def test_missing_subpath_is_rejected(self, vfolder_base: Path) -> None:
        mount = _make_mount(vfolder_base / "missing", "missing")

        with pytest.raises(InvalidVFolderMountSourceError):
            resolve_vfolder_mount_source(mount)

    def test_host_path_not_ending_with_subpath_is_rejected(self, vfolder_base: Path) -> None:
        mount = _make_mount(vfolder_base / "sub", "nested")

        with pytest.raises(InvalidVFolderMountSourceError):
            resolve_vfolder_mount_source(mount)
