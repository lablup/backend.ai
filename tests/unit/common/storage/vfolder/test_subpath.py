from __future__ import annotations

from pathlib import Path, PurePosixPath

import pytest

from ai.backend.common.exception import InvalidVFolderMountSourceError
from ai.backend.common.storage.vfolder.subpath import VFolderSubpath, resolve_vfolder_subpath


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


class TestResolveVFolderSubpath:
    def test_whole_folder_returns_base_path(self, vfolder_base: Path) -> None:
        target = VFolderSubpath(base_path=vfolder_base, subpath=PurePosixPath("."))

        assert resolve_vfolder_subpath(target) == vfolder_base

    def test_subpath_returns_resolved_path(self, vfolder_base: Path) -> None:
        target = VFolderSubpath(base_path=vfolder_base, subpath=PurePosixPath("sub/nested"))

        assert resolve_vfolder_subpath(target) == (vfolder_base / "sub" / "nested").resolve()

    def test_symlink_inside_vfolder_returns_target(self, vfolder_base: Path) -> None:
        (vfolder_base / "link").symlink_to(vfolder_base / "sub" / "nested")
        target = VFolderSubpath(base_path=vfolder_base, subpath=PurePosixPath("link"))

        assert resolve_vfolder_subpath(target) == (vfolder_base / "sub" / "nested").resolve()

    def test_symlink_to_outside_is_rejected(self, vfolder_base: Path, outside_dir: Path) -> None:
        (vfolder_base / "link").symlink_to(outside_dir)
        target = VFolderSubpath(base_path=vfolder_base, subpath=PurePosixPath("link"))

        with pytest.raises(InvalidVFolderMountSourceError):
            resolve_vfolder_subpath(target)

    def test_nested_symlink_to_outside_is_rejected(
        self, vfolder_base: Path, outside_dir: Path
    ) -> None:
        (vfolder_base / "sub" / "link").symlink_to(outside_dir)
        target = VFolderSubpath(base_path=vfolder_base, subpath=PurePosixPath("sub/link"))

        with pytest.raises(InvalidVFolderMountSourceError):
            resolve_vfolder_subpath(target)

    def test_parent_reference_escaping_vfolder_is_rejected(self, vfolder_base: Path) -> None:
        target = VFolderSubpath(base_path=vfolder_base, subpath=PurePosixPath("../.."))

        with pytest.raises(InvalidVFolderMountSourceError):
            resolve_vfolder_subpath(target)

    def test_missing_subpath_is_rejected(self, vfolder_base: Path) -> None:
        target = VFolderSubpath(base_path=vfolder_base, subpath=PurePosixPath("missing"))

        with pytest.raises(InvalidVFolderMountSourceError):
            resolve_vfolder_subpath(target)
