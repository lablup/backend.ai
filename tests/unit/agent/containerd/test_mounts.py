from __future__ import annotations

from pathlib import Path

import pytest

from ai.backend.agent.containerd.mounts import classify_mount, to_generated_mounts
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
