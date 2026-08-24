"""Applying a container's overlay onto the base rootfs when committing.

A plain copy of the upperdir is wrong in a way that reaches the registry: overlayfs records a
deletion as a character device, so `rm /etc/hostname` inside a session republished that path as an
unopenable `c--------- 0,0` node instead of removing it. That was measured in the pushed OCI layer,
not theorised, so both overlay conventions are pinned here.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from ai.backend.agent.singularity.runtime import SingularityRuntime


def _whiteout(path: Path) -> None:
    """How overlayfs marks a path deleted: a char device with rdev 0:0."""
    os.mknod(path, stat.S_IFCHR | 0o000, os.makedev(0, 0))


@pytest.fixture
def trees(tmp_path: Path) -> tuple[Path, Path]:
    """(upper, target) — `target` starts as a copy of the base image rootfs."""
    upper, target = tmp_path / "upper", tmp_path / "target"
    for d in (upper, target):
        d.mkdir()
    return upper, target


def _merge(upper: Path, target: Path) -> None:
    SingularityRuntime._merge_overlay(upper, target)


class TestWhiteouts:
    def test_a_deleted_file_is_removed_not_republished(self, trees: tuple[Path, Path]) -> None:
        upper, target = trees
        (target / "etc").mkdir()
        (target / "etc" / "hostname").write_text("from-the-base-image")
        (upper / "etc").mkdir()
        _whiteout(upper / "etc" / "hostname")

        _merge(upper, target)

        assert not (target / "etc" / "hostname").exists()

    def test_a_deleted_directory_is_removed_whole(self, trees: tuple[Path, Path]) -> None:
        upper, target = trees
        (target / "opt" / "gone").mkdir(parents=True)
        (target / "opt" / "gone" / "inner").write_text("x")
        (upper / "opt").mkdir()
        _whiteout(upper / "opt" / "gone")

        _merge(upper, target)

        assert not (target / "opt" / "gone").exists()

    def test_the_marker_itself_never_survives(self, trees: tuple[Path, Path]) -> None:
        """Even with nothing to delete in the base — a stray marker in the image is worse than a
        missing file, because it is a device node nothing can open."""
        upper, target = trees
        _whiteout(upper / "never-existed")

        _merge(upper, target)

        assert not (target / "never-existed").exists()


class TestOpaqueDirectories:
    def test_an_opaque_directory_replaces_the_base_one(self, trees: tuple[Path, Path]) -> None:
        """`overlay.opaque` means the upper directory *replaces* the lower, so what the base had
        there must not show through."""
        upper, target = trees
        (target / "cache").mkdir()
        (target / "cache" / "stale").write_text("from-the-base-image")
        (upper / "cache").mkdir()
        (upper / "cache" / "fresh").write_text("written-by-the-kernel")
        try:
            os.setxattr(upper / "cache", "user.overlay.opaque", b"y")
        except OSError:
            pytest.skip("this filesystem does not carry user xattrs")

        _merge(upper, target)

        assert (target / "cache" / "fresh").read_text() == "written-by-the-kernel"
        assert not (target / "cache" / "stale").exists()

    def test_a_plain_directory_merges_instead(self, trees: tuple[Path, Path]) -> None:
        upper, target = trees
        (target / "cache").mkdir()
        (target / "cache" / "kept").write_text("from-the-base-image")
        (upper / "cache").mkdir()
        (upper / "cache" / "added").write_text("new")

        _merge(upper, target)

        assert (target / "cache" / "kept").exists()
        assert (target / "cache" / "added").exists()


class TestOrdinaryWrites:
    def test_a_new_file_is_carried_over(self, trees: tuple[Path, Path]) -> None:
        upper, target = trees
        (upper / "opt").mkdir()
        (upper / "opt" / "added.txt").write_text("COMMITTED-BY-BAI")

        _merge(upper, target)

        assert (target / "opt" / "added.txt").read_text() == "COMMITTED-BY-BAI"

    def test_a_modified_file_wins_over_the_base(self, trees: tuple[Path, Path]) -> None:
        upper, target = trees
        (target / "f").write_text("base")
        (upper / "f").write_text("modified")

        _merge(upper, target)

        assert (target / "f").read_text() == "modified"

    def test_a_symlink_stays_a_symlink(self, trees: tuple[Path, Path]) -> None:
        """copy2 without follow_symlinks would otherwise inline the target, quietly turning a
        relative link in the image into a fixed copy."""
        upper, target = trees
        (upper / "link").symlink_to("/etc/passwd")

        _merge(upper, target)

        assert (target / "link").is_symlink()
        assert os.readlink(target / "link") == "/etc/passwd"

    def test_the_overlays_bookkeeping_xattrs_are_not_published(
        self, trees: tuple[Path, Path]
    ) -> None:
        """`user.overlay.origin`/`.impure` describe this container's overlay, not the image."""
        upper, target = trees
        (upper / "f").write_text("x")
        try:
            os.setxattr(upper / "f", "user.overlay.origin", b"junk")
        except OSError:
            pytest.skip("this filesystem does not carry user xattrs")

        _merge(upper, target)

        assert not [x for x in os.listxattr(target / "f") if "overlay" in x]
