"""The generic OCI runtime spec of a kernel container, and the profile patch merged over it."""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

from ai.backend.agent.containerd.profile.base import GeneratedMount, GeneratedMountKind
from ai.backend.agent.utils import get_safe_ulimit

OCI_VERSION: Final = "1.1.0"
CPU_PERIOD_US: Final = 100_000
_RLIM_INFINITY: Final = 2**64 - 1

# Docker's default capability set minus NET_RAW and NET_BIND_SERVICE (the kernel shares the
# host network) plus the two the Docker agent adds (IPC_LOCK, SYS_NICE).
DEFAULT_CAPABILITIES: Final = (
    "CAP_CHOWN",
    "CAP_DAC_OVERRIDE",
    "CAP_FSETID",
    "CAP_FOWNER",
    "CAP_MKNOD",
    "CAP_SETGID",
    "CAP_SETUID",
    "CAP_SETFCAP",
    "CAP_SETPCAP",
    "CAP_SYS_CHROOT",
    "CAP_KILL",
    "CAP_AUDIT_WRITE",
    "CAP_IPC_LOCK",
    "CAP_SYS_NICE",
)

# No network namespace: the kernel shares the host network.
_NAMESPACES: Final = ("pid", "ipc", "uts", "mount", "cgroup")

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
    cwd: str
    hostname: str
    cpu_cores: Sequence[int]  # the cpuset; its length is the CPU quota
    memory_bytes: int
    shm_bytes: int
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


def build_base_spec(inp: SpecInput) -> dict[str, Any]:
    """The kernel-independent spec: no process args, no kernel mounts, no profile patch."""
    caps = [*DEFAULT_CAPABILITIES, *inp.extra_caps]
    mounts: list[dict[str, Any]] = copy.deepcopy(list(_DEFAULT_MOUNTS))
    mounts.insert(
        3,
        {
            "destination": "/dev/shm",
            "type": "tmpfs",
            "source": "shm",
            "options": ["nosuid", "noexec", "nodev", "mode=1777", f"size={inp.shm_bytes}"],
        },
    )
    return {
        "ociVersion": OCI_VERSION,
        "process": {
            "terminal": False,
            "user": {"uid": 0, "gid": 0},
            "args": [],
            "env": [],
            "cwd": inp.cwd,
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
            "namespaces": [{"type": ns} for ns in _NAMESPACES],
            "resources": _resources(inp),
            "maskedPaths": list(_MASKED_PATHS),
            "readonlyPaths": list(_READONLY_PATHS),
        },
    }


def _bind_mount(mount: GeneratedMount) -> dict[str, Any]:
    return {
        "destination": mount.target,
        "type": "bind",
        "source": str(mount.source),
        "options": ["rbind", "rprivate", "ro" if mount.read_only else "rw"],
    }


def merge_patch(base: Mapping[str, Any], patch: Mapping[str, Any]) -> dict[str, Any]:
    """RFC 7386 JSON merge patch: dicts merge, lists and scalars replace, null deletes."""
    merged = copy.deepcopy(dict(base))
    for key, value in patch.items():
        if value is None:
            merged.pop(key, None)
        elif isinstance(value, Mapping) and isinstance(merged.get(key), dict):
            merged[key] = merge_patch(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def build_launch_spec(
    base_spec: Mapping[str, Any],
    *,
    args: Sequence[str],
    env: Sequence[str],
    mounts: Sequence[GeneratedMount],
    allowed_mount_kinds: frozenset[GeneratedMountKind],
    spec_patch: Mapping[str, Any],
    cgroups_path: str,
) -> dict[str, Any]:
    """Add the process args, env, cgroup path and the allowed kernel mounts, then the patch."""
    spec = copy.deepcopy(dict(base_spec))
    spec["linux"]["cgroupsPath"] = cgroups_path
    spec["process"]["args"] = list(args)
    spec["process"]["env"] = list(env)
    # Shallower destinations first, so a mount is never hidden by one made before its parent.
    ordered = sorted(
        (m for m in mounts if m.kind in allowed_mount_kinds),
        key=lambda m: m.target.rstrip("/").count("/"),
    )
    spec["mounts"] = [*spec["mounts"], *(_bind_mount(m) for m in ordered)]
    return merge_patch(spec, spec_patch)


def merge_env(image_env: Sequence[str], kernel_env: Mapping[str, str]) -> list[str]:
    """The image's environment overlaid with the kernel's; the kernel wins on a clash."""
    merged: dict[str, str] = {}
    for entry in image_env:
        name, _, value = entry.partition("=")
        merged[name] = value
    merged.update(kernel_env)
    return [f"{name}={value}" for name, value in merged.items()]
