"""The OCI runtime spec of a kernel container."""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

from ai.backend.agent.utils import get_safe_ulimit

OCI_VERSION: Final = "1.1.0"
CPU_PERIOD_US: Final = 100_000
_RLIM_INFINITY: Final = 2**64 - 1
DEFAULT_SHM_BYTES: Final = 64 * 2**20  # Docker's default /dev/shm size

# Docker's default capability set plus the two the Docker agent adds (IPC_LOCK, SYS_NICE).
DEFAULT_CAPABILITIES: Final = (
    "CAP_CHOWN",
    "CAP_DAC_OVERRIDE",
    "CAP_FSETID",
    "CAP_FOWNER",
    "CAP_MKNOD",
    "CAP_NET_RAW",
    "CAP_SETGID",
    "CAP_SETUID",
    "CAP_SETFCAP",
    "CAP_SETPCAP",
    "CAP_NET_BIND_SERVICE",
    "CAP_SYS_CHROOT",
    "CAP_KILL",
    "CAP_AUDIT_WRITE",
    "CAP_IPC_LOCK",
    "CAP_SYS_NICE",
)

_DEFAULT_MOUNTS: Final = (
    {
        "destination": "/proc",
        "type": "proc",
        "source": "proc",
        "options": ["nosuid", "noexec", "nodev"],
    },
    {
        "destination": "/dev",
        "type": "tmpfs",
        "source": "tmpfs",
        "options": ["nosuid", "strictatime", "mode=755", "size=65536k"],
    },
    {
        "destination": "/dev/pts",
        "type": "devpts",
        "source": "devpts",
        "options": ["nosuid", "noexec", "newinstance", "ptmxmode=0666", "mode=0620", "gid=5"],
    },
    {
        "destination": "/dev/mqueue",
        "type": "mqueue",
        "source": "mqueue",
        "options": ["nosuid", "noexec", "nodev"],
    },
    {
        "destination": "/sys",
        "type": "sysfs",
        "source": "sysfs",
        "options": ["nosuid", "noexec", "nodev", "ro"],
    },
    {
        "destination": "/sys/fs/cgroup",
        "type": "cgroup",
        "source": "cgroup",
        "options": ["nosuid", "noexec", "nodev", "relatime", "ro"],
    },
)

# Same lists and order as containerd's `oci.WithDefaultSpec`.
_MASKED_PATHS: Final = (
    "/proc/acpi",
    "/proc/asound",
    "/proc/kcore",
    "/proc/keys",
    "/proc/latency_stats",
    "/proc/timer_list",
    "/proc/timer_stats",
    "/proc/sched_debug",
    "/sys/firmware",
    "/sys/devices/virtual/powercap",
    "/proc/scsi",
)
_READONLY_PATHS: Final = (
    "/proc/bus",
    "/proc/fs",
    "/proc/irq",
    "/proc/sys",
    "/proc/sysrq-trigger",
)


@dataclass(frozen=True)
class SpecInput:
    hostname: str
    cpu_cores: Sequence[int]  # the cpuset; its length is the CPU quota
    memory_bytes: int
    shm_bytes: int  # 0 or less means DEFAULT_SHM_BYTES
    extra_caps: Sequence[str] = ()


def _rlimit(name: str, soft: int, hard: int) -> dict[str, Any]:
    safe = get_safe_ulimit(name, soft, hard)
    return {
        "type": f"RLIMIT_{name.upper()}",
        "soft": _RLIM_INFINITY if safe["Soft"] < 0 else safe["Soft"],
        "hard": _RLIM_INFINITY if safe["Hard"] < 0 else safe["Hard"],
    }


def _resources(inp: SpecInput) -> dict[str, Any]:
    resources: dict[str, Any] = {"devices": [{"allow": False, "access": "rwm"}]}
    if inp.cpu_cores:
        cores = sorted(inp.cpu_cores)
        resources["cpu"] = {
            "quota": len(cores) * CPU_PERIOD_US,
            "period": CPU_PERIOD_US,
            "cpus": ",".join(map(str, cores)),
        }
    if inp.memory_bytes > 0:
        # swap equals the limit, which disables swap (as the Docker agent does).
        resources["memory"] = {"limit": inp.memory_bytes, "swap": inp.memory_bytes}
    return resources


def _capabilities(extra_caps: Sequence[str]) -> list[str]:
    """The default capabilities plus `extra_caps`, with the CAP_ prefix and no duplicates."""
    names = (
        c if c.startswith("CAP_") else f"CAP_{c}" for c in (*DEFAULT_CAPABILITIES, *extra_caps)
    )
    return list(dict.fromkeys(names))


def build_base_spec(inp: SpecInput) -> dict[str, Any]:
    """The kernel-independent spec: no process args."""
    caps = _capabilities(inp.extra_caps)
    shm_bytes = inp.shm_bytes if inp.shm_bytes > 0 else DEFAULT_SHM_BYTES
    mounts: list[dict[str, Any]] = copy.deepcopy(list(_DEFAULT_MOUNTS))
    mounts.insert(
        3,
        {
            "destination": "/dev/shm",
            "type": "tmpfs",
            "source": "shm",
            "options": ["nosuid", "noexec", "nodev", "mode=1777", f"size={shm_bytes}"],
        },
    )
    return {
        "ociVersion": OCI_VERSION,
        "process": {
            "terminal": False,
            "user": {"uid": 0, "gid": 0},
            "args": [],
            "env": [],
            "cwd": "/",
            "capabilities": {
                "bounding": caps,
                "effective": caps,
                "permitted": caps,
            },
            "rlimits": [_rlimit("nofile", 1048576, 1048576), _rlimit("memlock", -1, -1)],
        },
        "root": {"path": "rootfs", "readonly": False},
        "hostname": inp.hostname,
        "mounts": mounts,
        "linux": {
            # containerd's default order, then cgroup.
            "namespaces": [
                {"type": "pid"},
                {"type": "ipc"},
                {"type": "uts"},
                {"type": "mount"},
                {"type": "network"},
                {"type": "cgroup"},
            ],
            "resources": _resources(inp),
            "maskedPaths": list(_MASKED_PATHS),
            "readonlyPaths": list(_READONLY_PATHS),
        },
    }


def build_launch_spec(
    base_spec: Mapping[str, Any],
    *,
    args: Sequence[str],
    env: Sequence[str],
    cwd: str,
    cgroups_path: str,
) -> dict[str, Any]:
    """Add the process args, env, working directory and cgroup path."""
    spec = copy.deepcopy(dict(base_spec))
    spec["linux"]["cgroupsPath"] = cgroups_path
    spec["process"]["args"] = list(args)
    spec["process"]["env"] = list(env)
    spec["process"]["cwd"] = cwd
    return spec


def merge_env(image_env: Sequence[str], kernel_env: Mapping[str, str]) -> list[str]:
    """The image's environment overlaid with the kernel's; the kernel wins on a clash.

    An image entry without "=" sets nothing.
    """
    merged: dict[str, str] = {}
    for entry in image_env:
        name, sep, value = entry.partition("=")
        if sep:
            merged[name] = value
    merged.update(kernel_env)
    return [f"{name}={value}" for name, value in merged.items()]
