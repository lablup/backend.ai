from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path
from typing import Any, cast

import pytest

from ai.backend.agent import utils


def test_read_sysfs() -> None:
    with tempfile.NamedTemporaryFile("w") as f:
        f.write("10")
        f.flush()
        int_val = utils.read_sysfs(f.name, int)
        assert isinstance(int_val, int)
        assert int_val == 10
        str_val = utils.read_sysfs(f.name, str)
        assert isinstance(str_val, str)
        assert str_val == "10"
        float_val = utils.read_sysfs(f.name, float)
        assert isinstance(float_val, float)
        assert float_val == 10.0

    with tempfile.NamedTemporaryFile("w") as f:
        f.write("1")
        f.flush()
        bool_val = utils.read_sysfs(f.name, bool)
        assert isinstance(bool_val, bool)
        assert bool_val is True
        f.seek(0, 0)
        f.write("0")
        f.flush()
        bool_val = utils.read_sysfs(f.name, bool)
        assert isinstance(bool_val, bool)
        assert bool_val is False

    default_val = utils.read_sysfs("/tmp/xxxxx-non-existent-file", int)
    assert isinstance(default_val, int)
    assert default_val == 0

    custom_default_val = utils.read_sysfs("/tmp/xxxxx-non-existent-file", int, -1)
    assert isinstance(custom_default_val, int)
    assert custom_default_val == -1

    with pytest.raises(TypeError):
        utils.read_sysfs("/tmp/xxxxx-non-existent-file", object)  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        utils.read_sysfs("/tmp/xxxxx-non-existent-file", object, -1)  # type: ignore[arg-type]


def test_update_nested_dict() -> None:
    o1: dict[str, Any] = {
        "a": 1,
        "b": 2,
    }
    utils.update_nested_dict(o1, {"a": 3, "c": 4})
    assert o1 == {
        "a": 3,
        "b": 2,
        "c": 4,
    }

    o2: dict[str, Any] = {
        "a": {
            "x": 1,
        },
        "b": 2,
    }
    with pytest.raises(TypeError):
        utils.update_nested_dict(o2, {"a": 3})

    o3: dict[str, Any] = {
        "a": {
            "x": 1,
        },
        "b": 2,
    }
    utils.update_nested_dict(o3, {"a": {"x": 3, "y": 4}, "b": 5})
    assert cast(dict[str, Any], o3["a"]) == {
        "x": 3,
        "y": 4,
    }
    assert o3["b"] == 5

    o4: dict[str, Any] = {
        "a": [1, 2],
        "b": 3,
    }
    utils.update_nested_dict(o4, {"a": [4, 5], "b": 6})
    assert cast(list[Any], o4["a"]) == [1, 2, 4, 5]
    assert o4["b"] == 6


class TestContainerSSHFileWriter:
    PUBLIC_KEY = b"public-key"
    PRIVATE_KEY = b"private-key"

    @pytest.fixture
    def work_dir(self, tmp_path: Path) -> Path:
        path = tmp_path / "work"
        path.mkdir()
        return path

    @pytest.fixture
    def outside_file(self, tmp_path: Path) -> Path:
        path = tmp_path / "outside-file"
        path.write_bytes(b"outside")
        path.chmod(0o644)
        return path

    @pytest.fixture
    def writer(self, work_dir: Path) -> utils.ContainerSSHFileWriter:
        return utils.ContainerSSHFileWriter(work_dir, self.PUBLIC_KEY, self.PRIVATE_KEY)

    def test_writes_files_in_empty_work_dir(
        self, work_dir: Path, writer: utils.ContainerSSHFileWriter
    ) -> None:
        paths = writer.write()

        ssh_dir = work_dir / ".ssh"
        assert paths == [
            ssh_dir,
            ssh_dir / "authorized_keys",
            ssh_dir / "id_rsa",
            work_dir / "id_container",
        ]
        assert stat.S_IMODE(ssh_dir.stat().st_mode) == 0o700
        assert (ssh_dir / "authorized_keys").read_bytes() == self.PUBLIC_KEY
        assert (ssh_dir / "id_rsa").read_bytes() == self.PRIVATE_KEY
        assert (work_dir / "id_container").read_bytes() == self.PRIVATE_KEY
        for path in paths[1:]:
            assert stat.S_IMODE(path.stat().st_mode) == 0o600

    def test_overwrites_existing_regular_files(
        self, work_dir: Path, writer: utils.ContainerSSHFileWriter
    ) -> None:
        writer.write()
        (work_dir / ".ssh" / "authorized_keys").write_bytes(b"old")
        (work_dir / "id_container").write_bytes(b"old")

        writer.write()

        assert (work_dir / ".ssh" / "authorized_keys").read_bytes() == self.PUBLIC_KEY
        assert (work_dir / "id_container").read_bytes() == self.PRIVATE_KEY

    def test_keeps_existing_regular_id_rsa(
        self, work_dir: Path, writer: utils.ContainerSSHFileWriter
    ) -> None:
        ssh_dir = work_dir / ".ssh"
        ssh_dir.mkdir()
        (ssh_dir / "id_rsa").write_bytes(b"user-key")

        writer.write()

        assert (ssh_dir / "id_rsa").read_bytes() == b"user-key"

    @pytest.mark.parametrize(
        ("relative_path", "expected"),
        [
            (".ssh/authorized_keys", PUBLIC_KEY),
            (".ssh/id_rsa", PRIVATE_KEY),
            ("id_container", PRIVATE_KEY),
        ],
    )
    def test_replaces_file_symlink_and_keeps_its_target(
        self,
        work_dir: Path,
        outside_file: Path,
        writer: utils.ContainerSSHFileWriter,
        relative_path: str,
        expected: bytes,
    ) -> None:
        link = work_dir / relative_path
        link.parent.mkdir(exist_ok=True)
        link.symlink_to(outside_file)

        writer.write()

        assert outside_file.read_bytes() == b"outside"
        assert stat.S_IMODE(outside_file.stat().st_mode) == 0o644
        assert not link.is_symlink()
        assert link.read_bytes() == expected

    def test_replaces_dangling_symlink_without_creating_its_target(
        self, tmp_path: Path, work_dir: Path, writer: utils.ContainerSSHFileWriter
    ) -> None:
        missing = tmp_path / "missing"
        (work_dir / "id_container").symlink_to(missing)

        writer.write()

        assert not missing.exists()
        assert (work_dir / "id_container").read_bytes() == self.PRIVATE_KEY

    def test_replaces_ssh_dir_symlink_and_keeps_its_target(
        self, tmp_path: Path, work_dir: Path, writer: utils.ContainerSSHFileWriter
    ) -> None:
        outside_dir = tmp_path / "outside-dir"
        outside_dir.mkdir()
        outside_dir.chmod(0o755)
        (work_dir / ".ssh").symlink_to(outside_dir)

        paths = writer.write()

        assert list(outside_dir.iterdir()) == []
        assert stat.S_IMODE(outside_dir.stat().st_mode) == 0o755
        assert not (work_dir / ".ssh").is_symlink()
        real_work_dir = work_dir.resolve()
        for path in paths:
            assert path.resolve().is_relative_to(real_work_dir)

    def test_replaces_named_pipe(
        self, work_dir: Path, writer: utils.ContainerSSHFileWriter
    ) -> None:
        os.mkfifo(work_dir / "id_container")

        writer.write()

        assert (work_dir / "id_container").read_bytes() == self.PRIVATE_KEY


class TestWriteFileBeneath:
    @pytest.fixture
    def work_dir(self, tmp_path: Path) -> Path:
        path = tmp_path / "work"
        path.mkdir()
        return path

    @pytest.fixture
    def outside_dir(self, tmp_path: Path) -> Path:
        path = tmp_path / "outside"
        path.mkdir()
        (path / "f.txt").write_bytes(b"outside")
        return path

    @pytest.fixture
    def symlinked_dir(self, work_dir: Path, outside_dir: Path) -> Path:
        link = work_dir / "sub"
        link.symlink_to(outside_dir)
        return link

    @pytest.fixture
    def symlinked_file(self, work_dir: Path, outside_dir: Path) -> Path:
        link = work_dir / "f.txt"
        link.symlink_to(outside_dir / "f.txt")
        return link

    def test_writes_file_creating_parents(self, work_dir: Path) -> None:
        utils.write_file_beneath(work_dir, work_dir / "a" / "b" / "f.txt", b"data")

        assert (work_dir / "a" / "b" / "f.txt").read_bytes() == b"data"

    def test_overwrites_existing_file(self, work_dir: Path) -> None:
        (work_dir / "f.txt").write_bytes(b"old content")

        utils.write_file_beneath(work_dir, work_dir / "f.txt", b"new")

        assert (work_dir / "f.txt").read_bytes() == b"new"

    @pytest.mark.usefixtures("symlinked_dir")
    def test_refuses_symlinked_directory(self, work_dir: Path, outside_dir: Path) -> None:
        with pytest.raises(OSError):
            utils.write_file_beneath(work_dir, work_dir / "sub" / "new.txt", b"evil")

        assert not (outside_dir / "new.txt").exists()

    @pytest.mark.usefixtures("symlinked_file")
    def test_refuses_symlinked_file(self, work_dir: Path, outside_dir: Path) -> None:
        with pytest.raises(OSError):
            utils.write_file_beneath(work_dir, work_dir / "f.txt", b"evil")

        assert (outside_dir / "f.txt").read_bytes() == b"outside"

    def test_refuses_root_as_target(self, work_dir: Path) -> None:
        with pytest.raises(IsADirectoryError):
            utils.write_file_beneath(work_dir, work_dir, b"data")
