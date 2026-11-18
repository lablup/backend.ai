from __future__ import annotations

import errno
import os
import stat
from collections.abc import Iterator
from pathlib import Path

import pytest

from ai.backend.common.files import open_dir_beneath

_SYMLINK_REFUSED_ERRNOS = {errno.ELOOP, errno.ENOTDIR}


def _same_inode(fd: int, path: Path) -> bool:
    fd_stat = os.fstat(fd)
    path_stat = path.stat()
    return (fd_stat.st_dev, fd_stat.st_ino) == (path_stat.st_dev, path_stat.st_ino)


class TestOpenDirBeneath:
    @pytest.fixture
    def root(self, tmp_path: Path) -> Path:
        root = tmp_path / "root"
        root.mkdir()
        return root

    @pytest.fixture
    def outside(self, tmp_path: Path) -> Path:
        outside = tmp_path / "outside"
        outside.mkdir()
        return outside

    @pytest.fixture
    def nested_dir(self, root: Path) -> Path:
        nested = root / "a" / "b"
        nested.mkdir(parents=True)
        return nested

    @pytest.fixture
    def symlinked_dir(self, root: Path, outside: Path) -> Path:
        link = root / "a"
        link.symlink_to(outside)
        return link

    @pytest.fixture
    def outside_child_dir(self, outside: Path) -> Path:
        child = outside / "b"
        child.mkdir()
        return child

    @pytest.fixture
    def regular_file(self, root: Path) -> Path:
        path = root / "a"
        path.write_bytes(b"")
        return path

    @pytest.fixture
    def private_dir(self, root: Path) -> Path:
        path = root / "a"
        path.mkdir()
        path.chmod(0o700)
        return path

    @pytest.fixture
    def strict_umask(self) -> Iterator[None]:
        old = os.umask(0o077)
        try:
            yield
        finally:
            os.umask(old)

    def test_opens_nested_directory(self, root: Path, nested_dir: Path) -> None:
        with open_dir_beneath(root, ["a", "b"]) as fd:
            assert _same_inode(fd, nested_dir)

    def test_empty_parts_opens_root(self, root: Path) -> None:
        with open_dir_beneath(root, []) as fd:
            assert _same_inode(fd, root)

    def test_closes_fd_on_exit(self, root: Path) -> None:
        with open_dir_beneath(root, []) as fd:
            pass

        with pytest.raises(OSError) as exc_info:
            os.fstat(fd)
        assert exc_info.value.errno == errno.EBADF

    @pytest.mark.usefixtures("symlinked_dir")
    def test_refuses_symlinked_directory(self, root: Path) -> None:
        with pytest.raises(OSError) as exc_info:
            with open_dir_beneath(root, ["a"]):
                pass
        assert exc_info.value.errno in _SYMLINK_REFUSED_ERRNOS

    @pytest.mark.usefixtures("symlinked_dir", "outside_child_dir")
    def test_refuses_symlinked_intermediate_directory(self, root: Path, outside: Path) -> None:
        with pytest.raises(OSError) as exc_info:
            with open_dir_beneath(root, ["a", "b", "c"], mkdir_mode=0o755):
                pass
        assert exc_info.value.errno in _SYMLINK_REFUSED_ERRNOS
        assert os.listdir(outside) == ["b"]
        assert os.listdir(outside / "b") == []

    @pytest.mark.usefixtures("regular_file")
    def test_refuses_regular_file_as_directory(self, root: Path) -> None:
        with pytest.raises(NotADirectoryError):
            with open_dir_beneath(root, ["a"]):
                pass

    def test_missing_directory_without_mkdir_mode_raises(self, root: Path) -> None:
        with pytest.raises(FileNotFoundError):
            with open_dir_beneath(root, ["a"]):
                pass
        assert not (root / "a").exists()

    @pytest.mark.usefixtures("strict_umask")
    def test_mkdir_mode_creates_missing_directories_under_umask(self, root: Path) -> None:
        with open_dir_beneath(root, ["a", "b"], mkdir_mode=0o755) as fd:
            assert _same_inode(fd, root / "a" / "b")

        assert stat.S_IMODE((root / "a").stat().st_mode) == 0o700
        assert stat.S_IMODE((root / "a" / "b").stat().st_mode) == 0o700

    @pytest.mark.usefixtures("strict_umask")
    def test_chmod_created_sets_mode_past_umask(self, root: Path) -> None:
        with open_dir_beneath(root, ["a", "b"], mkdir_mode=0o755, chmod_created=True):
            pass

        assert stat.S_IMODE((root / "a").stat().st_mode) == 0o755
        assert stat.S_IMODE((root / "a" / "b").stat().st_mode) == 0o755

    def test_chmod_created_keeps_mode_of_existing_directory(
        self, root: Path, private_dir: Path
    ) -> None:
        with open_dir_beneath(root, ["a", "b"], mkdir_mode=0o755, chmod_created=True):
            pass

        assert stat.S_IMODE(private_dir.stat().st_mode) == 0o700
        assert stat.S_IMODE((private_dir / "b").stat().st_mode) == 0o755
