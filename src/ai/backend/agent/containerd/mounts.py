"""Translate the agent's mount list into the generated mounts a runtime profile sees."""

from __future__ import annotations

import platform
from collections.abc import Sequence
from pathlib import Path

from ai.backend.agent.containerd.profile.base import GeneratedMount, GeneratedMountKind
from ai.backend.agent.errors.containerd import KernelVerbNotSupported
from ai.backend.agent.resources import Mount
from ai.backend.common.types import MountPermission, MountTypes

_KRUNNER_PREFIXES = ("/opt/kernel", "/opt/backend.ai", "/usr/local/bin/", "/usr/local/share/man/")
_LXCFS_ROOT = Path("/var/lib/lxcfs")
_HOST_FILES = (
    Path("/etc/resolv.conf"),
    Path("/etc/localtime"),
    Path("/etc/timezone"),
)


def classify_mount(target: str) -> GeneratedMountKind:
    if target == "/home/config":
        return GeneratedMountKind.CONFIG_DIR
    if target in ("/home/work", "/tmp"):
        return GeneratedMountKind.SCRATCH
    if target == "/home/work/.terminfo" or target.startswith(_KRUNNER_PREFIXES):
        return GeneratedMountKind.KRUNNER
    return GeneratedMountKind.VFOLDER


def to_generated_mounts(mounts: Sequence[Mount]) -> list[GeneratedMount]:
    """Bind mounts and krunner volumes (host directories) only; anything else is refused."""
    generated: list[GeneratedMount] = []
    for mount in mounts:
        if mount.type not in (MountTypes.BIND, MountTypes.VOLUME):
            raise KernelVerbNotSupported(f"mount type {mount.type} ({mount.target})")
        if mount.source is None or not mount.source.is_absolute():
            raise KernelVerbNotSupported(f"mount source {mount.source} ({mount.target})")
        generated.append(
            GeneratedMount(
                kind=classify_mount(str(mount.target)),
                source=mount.source,
                target=str(mount.target),
                read_only=mount.permission == MountPermission.READ_ONLY,
            )
        )
    return generated


def host_system_mounts(hosts_file: Path) -> list[Mount]:
    """The kernel's hosts file, the host's resolver and timezone files and lxcfs views.

    The kernel shares the host network, so the host's resolver config is the right one.
    """
    if platform.system() != "Linux":
        return []
    mounts = [Mount(MountTypes.BIND, hosts_file, Path("/etc/hosts"), MountPermission.READ_ONLY)]
    mounts.extend(
        Mount(MountTypes.BIND, path, path, MountPermission.READ_ONLY)
        for path in _HOST_FILES
        if path.exists()
    )
    if _LXCFS_ROOT.is_dir():
        mounts.extend(
            Mount(
                MountTypes.BIND,
                proc_path,
                "/" / proc_path.relative_to(_LXCFS_ROOT),
                MountPermission.READ_WRITE,
            )
            for proc_path in (_LXCFS_ROOT / "proc").iterdir()
            if proc_path.stat().st_size > 0
        )
        mounts.extend(
            Mount(MountTypes.BIND, _LXCFS_ROOT / rel, "/" / Path(rel), MountPermission.READ_WRITE)
            for rel in ("sys/devices/system/cpu", "sys/devices/system/cpu/online")
            if (_LXCFS_ROOT / rel).exists()
        )
    return mounts
