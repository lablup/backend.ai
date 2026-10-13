from __future__ import annotations

import io
import tarfile
from pathlib import Path

import pytest

from ai.backend.agent.containerd import krunner
from ai.backend.agent.containerd.krunner import (
    VERSION_FILE,
    extract_krunner_env,
    krunner_dir,
)
from ai.backend.agent.utils import get_arch_name


def _make_archive(path: Path, files: dict[str, bytes]) -> None:
    with tarfile.open(path, "w:xz") as tar:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o755
            tar.addfile(info, io.BytesIO(data))


@pytest.fixture
def archive(tmp_path: Path) -> Path:
    path = tmp_path / "krunner-env.tar.xz"
    _make_archive(path, {"bin/python": b"#!python", "lib/python3.13/x.py": b"x = 1"})
    return path


def test_directory_name_carries_version_arch_and_distro(tmp_path: Path) -> None:
    assert krunner_dir(tmp_path, 7, "aarch64", "ubuntu22.04") == tmp_path / "v7.aarch64.ubuntu22.04"


class TestExtractKrunnerEnv:
    def test_extracts_the_archive_and_stamps_the_version(
        self, tmp_path: Path, archive: Path
    ) -> None:
        dest = tmp_path / "krunner" / "v3.x86_64.static-gnu"

        extract_krunner_env(archive, dest, 3)

        assert (dest / "bin" / "python").read_bytes() == b"#!python"
        assert (dest / "lib" / "python3.13" / "x.py").read_text() == "x = 1"
        assert (dest / VERSION_FILE).read_text().strip() == "3"
        assert (dest / "bin" / "python").stat().st_mode & 0o111

    def test_no_temporary_directory_is_left_behind(self, tmp_path: Path, archive: Path) -> None:
        dest = tmp_path / "krunner" / "v3.x86_64.static-gnu"

        extract_krunner_env(archive, dest, 3)

        assert [p.name for p in dest.parent.iterdir()] == [dest.name]

    def test_complete_directory_is_left_alone(self, tmp_path: Path, archive: Path) -> None:
        dest = tmp_path / "krunner" / "v3.x86_64.static-gnu"
        extract_krunner_env(archive, dest, 3)
        (dest / "marker").write_text("keep")

        extract_krunner_env(archive, dest, 3)

        assert (dest / "marker").read_text() == "keep"

    def test_corrupt_archive_leaves_nothing(self, tmp_path: Path) -> None:
        broken = tmp_path / "broken.tar.xz"
        broken.write_bytes(b"not an archive")
        dest = tmp_path / "krunner" / "v3.x86_64.static-gnu"

        with pytest.raises(tarfile.TarError):
            extract_krunner_env(broken, dest, 3)

        assert not dest.exists()
        assert list(dest.parent.iterdir()) == []

    def test_extracted_root_is_traversable_by_the_kernel_user(
        self, tmp_path: Path, archive: Path
    ) -> None:
        dest = tmp_path / "krunner" / "v3.x86_64.static-gnu"

        extract_krunner_env(archive, dest, 3)

        assert oct(dest.stat().st_mode & 0o777) == "0o755"


class _FakePlugin:
    async def init(self, config: dict[str, object]) -> None:
        return None


class _FakeEntrypoint:
    name = "fakepkg"
    module = "ai.backend.krunner.fakepkg"

    def load(self) -> _FakePlugin:
        return _FakePlugin()


class TestPrepareKrunnerEnv:
    @pytest.fixture
    def package(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        arch = get_arch_name()
        (pkg / "versions.txt").write_text("good1.0\nbad2.0\nnoarch3.0\n")
        (pkg / "krunner-version.good1.0.txt").write_text("4\n")
        _make_archive(pkg / f"krunner-env.good1.0.{arch}.tar.xz", {"bin/python": b"py"})
        (pkg / "krunner-version.bad2.0.txt").write_text("1\n")
        (pkg / f"krunner-env.bad2.0.{arch}.tar.xz").write_bytes(b"corrupt")
        (pkg / "krunner-version.noarch3.0.txt").write_text("1\n")
        monkeypatch.setattr(krunner, "files", lambda _name: pkg)
        monkeypatch.setattr(krunner, "scan_entrypoints", lambda _prefix: [_FakeEntrypoint()])
        return pkg

    async def test_maps_distro_to_host_directory(self, tmp_path: Path, package: Path) -> None:
        config = {"agent": {"var-base-path": str(tmp_path / "var")}}

        volumes = await krunner.prepare_krunner_env(config)

        expected = tmp_path / "var" / "krunner" / f"v4.{get_arch_name()}.good1.0"
        assert volumes == {"good1.0": str(expected)}
        assert (expected / "bin" / "python").read_bytes() == b"py"
        assert (expected / VERSION_FILE).read_text().strip() == "4"

    async def test_second_run_reuses_the_directory(self, tmp_path: Path, package: Path) -> None:
        config = {"agent": {"var-base-path": str(tmp_path / "var")}}
        first = await krunner.prepare_krunner_env(config)
        marker = Path(first["good1.0"]) / "marker"
        marker.write_text("keep")

        second = await krunner.prepare_krunner_env(config)

        assert second == first
        assert marker.read_text() == "keep"
