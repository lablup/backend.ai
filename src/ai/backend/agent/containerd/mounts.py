"""Translate the agent's mount list into the bind mounts of the kernel spec."""

from __future__ import annotations

import platform
from collections.abc import Sequence
from pathlib import Path

from ai.backend.agent.containerd.spec import BindMount
from ai.backend.agent.errors.containerd import KernelVerbNotSupported
from ai.backend.agent.resources import Mount
from ai.backend.common.types import MountPermission, MountTypes

_LXCFS_ROOT = Path("/var/lib/lxcfs")
_HOST_FILES = (
    Path("/etc/resolv.conf"),
    Path("/etc/localtime"),
    Path("/etc/timezone"),
)


def to_bind_mounts(mounts: Sequence[Mount]) -> list[BindMount]:
    """Bind mounts and krunner volumes (host directories) only; anything else is refused."""
    bind_mounts: list[BindMount] = []
    for mount in mounts:
        if mount.type not in (MountTypes.BIND, MountTypes.VOLUME):
            raise KernelVerbNotSupported(f"mount type {mount.type} ({mount.target})")
        if mount.source is None or not mount.source.is_absolute():
            raise KernelVerbNotSupported(f"mount source {mount.source} ({mount.target})")
        bind_mounts.append(
            BindMount(
                source=mount.source,
                target=str(mount.target),
                read_only=mount.permission == MountPermission.READ_ONLY,
            )
        )
    return bind_mounts


def host_system_mounts(hosts_file: Path) -> list[Mount]:
    """The kernel's hosts file, the host's resolver and timezone files and lxcfs views."""
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
