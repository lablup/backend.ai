from __future__ import annotations

import platform
from pathlib import Path

import pytest

from ai.backend.agent.containerd import mounts as mounts_module
from ai.backend.agent.containerd.mounts import host_system_mounts, to_bind_mounts
from ai.backend.agent.errors.containerd import KernelVerbNotSupported
from ai.backend.agent.resources import Mount
from ai.backend.common.types import MountPermission, MountTypes


class TestToBindMounts:
    def test_bind_and_host_path_volume_become_bind_mounts(self) -> None:
        mounts = [
            Mount(
                MountTypes.BIND, Path("/h/config"), Path("/home/config"), MountPermission.READ_ONLY
            ),
            Mount(MountTypes.VOLUME, Path("/var/krunner/v1"), Path("/opt/backend.ai")),
            Mount(
                MountTypes.BIND, Path("/h/data"), Path("/home/work/data"), MountPermission.RW_DELETE
            ),
        ]

        bind_mounts = to_bind_mounts(mounts)

        assert [(str(m.source), m.target, m.read_only) for m in bind_mounts] == [
            ("/h/config", "/home/config", True),
            ("/var/krunner/v1", "/opt/backend.ai", True),
            ("/h/data", "/home/work/data", False),
        ]

    def test_named_docker_volume_is_refused(self) -> None:
        with pytest.raises(KernelVerbNotSupported, match="mount source"):
            to_bind_mounts([Mount(MountTypes.VOLUME, Path("krunner-vol"), Path("/opt/backend.ai"))])

    def test_tmpfs_is_refused(self) -> None:
        with pytest.raises(KernelVerbNotSupported, match="mount type"):
            to_bind_mounts([Mount(MountTypes.TMPFS, None, Path("/tmp"))])


class TestHostSystemMounts:
    @pytest.fixture
    def host_files(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> list[Path]:
        names = ("timezone", "localtime")
        paths = [tmp_path / n for n in names]
        for p in paths[:1]:
            p.write_text("x\n")
        monkeypatch.setattr(mounts_module, "_HOST_FILES", tuple(paths))
        monkeypatch.setattr(mounts_module, "_LXCFS_ROOT", tmp_path / "no-lxcfs")
        monkeypatch.setattr(platform, "system", lambda: "Linux")
        return paths

    def test_existing_host_files_are_bound_read_only(self, host_files: list[Path]) -> None:
        mounts = host_system_mounts(Path("/scratch/k/hosts"))

        assert [(m.source, m.target, m.permission) for m in mounts] == [
            (Path("/scratch/k/hosts"), Path("/etc/hosts"), MountPermission.READ_ONLY),
            *[(p, p, MountPermission.READ_ONLY) for p in host_files[:1]],
        ]

    def test_nothing_on_a_non_linux_host(
        self, host_files: list[Path], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(platform, "system", lambda: "Darwin")

        assert host_system_mounts(Path("/scratch/k/hosts")) == []
