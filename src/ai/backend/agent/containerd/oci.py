"""OCI runtime spec construction for the containerd backend.

containerd stores a container's OCI runtime spec
(https://github.com/opencontainers/runtime-spec) in ``Container.spec`` as
a typeurl-wrapped JSON blob and hands it to the runc shim when a task is
created. This module builds that spec.

This is currently a minimal Linux spec sufficient to run a workload
container. Per-kernel concerns — vfolder bind-mounts, accelerator
devices, resource limits, the krunner mounts, the CNI-provided network
namespace path — are layered on as the agent lifecycle integration grows.
"""

from __future__ import annotations

from typing import Any

# runtime-spec version this builder targets.
OCI_VERSION = "1.2.0"

# typeurl under which containerd stores the OCI spec in Container.spec.
# containerd registers specs.Spec as
# `types.containerd.io/opencontainers/runtime-spec/1/Spec`; the Any value
# is the JSON encoding of the spec (it is NOT a protobuf message).
OCI_SPEC_TYPE_URL = "types.containerd.io/opencontainers/runtime-spec/1/Spec"

_DEFAULT_ENV = ("PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",)

# Conservative Linux capability set, matching what `runc spec` grants an
# unprivileged container by default.
_DEFAULT_CAPABILITIES = (
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
)

# Namespaces with no `path` — runc creates a fresh one for each. The
# network namespace will gain an explicit path once the NetworkProvider
# hands the agent a CNI-prepared netns.
_DEFAULT_NAMESPACES = ("pid", "ipc", "uts", "mount", "network")

_DEFAULT_MOUNTS: tuple[dict[str, Any], ...] = (
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
        "destination": "/dev/shm",
        "type": "tmpfs",
        "source": "shm",
        "options": ["nosuid", "noexec", "nodev", "mode=1777", "size=65536k"],
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

_MASKED_PATHS = (
    "/proc/asound",
    "/proc/acpi",
    "/proc/kcore",
    "/proc/keys",
    "/proc/latency_stats",
    "/proc/timer_list",
    "/proc/timer_stats",
    "/proc/sched_debug",
    "/proc/scsi",
    "/sys/firmware",
)
_READONLY_PATHS = (
    "/proc/bus",
    "/proc/fs",
    "/proc/irq",
    "/proc/sys",
    "/proc/sysrq-trigger",
)


def build_oci_spec(
    *,
    container_id: str,
    args: list[str],
    env: list[str] | None = None,
    cwd: str = "/",
    hostname: str | None = None,
    terminal: bool = False,
    cgroups_path: str | None = None,
) -> dict[str, Any]:
    """Build a minimal Linux OCI runtime spec for a workload container.

    The rootfs itself is supplied separately, via the snapshot mounts on
    the task-create request; ``root.path`` is the conventional ``rootfs``
    that containerd's runc shim resolves inside the container bundle.
    """
    full_env = list(_DEFAULT_ENV)
    if env:
        full_env.extend(env)
    capabilities = list(_DEFAULT_CAPABILITIES)
    return {
        "ociVersion": OCI_VERSION,
        "process": {
            "terminal": terminal,
            "user": {"uid": 0, "gid": 0},
            "args": list(args),
            "env": full_env,
            "cwd": cwd,
            "capabilities": {
                "bounding": capabilities,
                "effective": capabilities,
                "permitted": capabilities,
            },
            "rlimits": [{"type": "RLIMIT_NOFILE", "hard": 1024, "soft": 1024}],
            "noNewPrivileges": True,
        },
        "root": {"path": "rootfs", "readonly": False},
        "hostname": hostname or container_id,
        "mounts": [dict(mount) for mount in _DEFAULT_MOUNTS],
        "linux": {
            "namespaces": [{"type": ns} for ns in _DEFAULT_NAMESPACES],
            "maskedPaths": list(_MASKED_PATHS),
            "readonlyPaths": list(_READONLY_PATHS),
            "cgroupsPath": cgroups_path or f"/backendai/{container_id}",
            "resources": {"devices": [{"allow": False, "access": "rwm"}]},
        },
    }
