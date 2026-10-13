from __future__ import annotations

import platform
from pathlib import Path

import pytest

from ai.backend.agent.containerd import mounts as mounts_module
from ai.backend.agent.containerd.mounts import (
    classify_mount,
    host_system_mounts,
    to_generated_mounts,
)
from ai.backend.agent.containerd.profile.base import GeneratedMountKind
from ai.backend.agent.errors.containerd import KernelVerbNotSupported
from ai.backend.agent.resources import Mount
from ai.backend.common.types import MountPermission, MountTypes


@pytest.mark.parametrize(
    ("target", "kind"),
    [
        ("/home/config", GeneratedMountKind.CONFIG_DIR),
        ("/home/work", GeneratedMountKind.SCRATCH),
        ("/tmp", GeneratedMountKind.SCRATCH),
        ("/opt/kernel/entrypoint.sh", GeneratedMountKind.KRUNNER),
        ("/opt/backend.ai", GeneratedMountKind.KRUNNER),
        ("/usr/local/bin/bssh", GeneratedMountKind.KRUNNER),
        ("/home/work/.terminfo", GeneratedMountKind.KRUNNER),
        ("/home/work/data", GeneratedMountKind.VFOLDER),
        ("/etc/localtime", GeneratedMountKind.VFOLDER),
    ],
)
def test_classify_mount(target: str, kind: GeneratedMountKind) -> None:
    assert classify_mount(target) == kind


class TestToGeneratedMounts:
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

        generated = to_generated_mounts(mounts)

        assert [(m.kind, str(m.source), m.target, m.read_only) for m in generated] == [
            (GeneratedMountKind.CONFIG_DIR, "/h/config", "/home/config", True),
            (GeneratedMountKind.KRUNNER, "/var/krunner/v1", "/opt/backend.ai", True),
            (GeneratedMountKind.VFOLDER, "/h/data", "/home/work/data", False),
        ]

    def test_named_docker_volume_is_refused(self) -> None:
        with pytest.raises(KernelVerbNotSupported, match="mount source"):
            to_generated_mounts([
                Mount(MountTypes.VOLUME, Path("krunner-vol"), Path("/opt/backend.ai"))
            ])

    def test_tmpfs_is_refused(self) -> None:
        with pytest.raises(KernelVerbNotSupported, match="mount type"):
            to_generated_mounts([Mount(MountTypes.TMPFS, None, Path("/tmp"))])


class TestHostSystemMounts:
    @pytest.fixture
    def host_files(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> list[Path]:
        names = ("resolv.conf", "hosts", "localtime")
        paths = [tmp_path / n for n in names]
        for p in paths[:2]:
            p.write_text("x\n")
        monkeypatch.setattr(mounts_module, "_HOST_FILES", tuple(paths))
        monkeypatch.setattr(mounts_module, "_LXCFS_ROOT", tmp_path / "no-lxcfs")
        monkeypatch.setattr(platform, "system", lambda: "Linux")
        return paths

    def test_existing_host_files_are_bound_read_only(self, host_files: list[Path]) -> None:
        mounts = host_system_mounts()

        assert [(m.source, m.target, m.permission) for m in mounts] == [
            (p, p, MountPermission.READ_ONLY) for p in host_files[:2]
        ]

    def test_resolver_files_are_part_of_the_default_set(self) -> None:
        assert {Path("/etc/resolv.conf"), Path("/etc/hosts")} <= set(mounts_module._HOST_FILES)

    def test_nothing_on_a_non_linux_host(
        self, host_files: list[Path], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(platform, "system", lambda: "Darwin")

        assert host_system_mounts() == []
