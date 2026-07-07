"""Build a containerd/runc OCI *runtime* spec from our runtime-neutral oci_spec (BEP-1058).

The nerdctl runtime lets nerdctl assemble the OCI runtime spec from ``-v/-e/--device``
flags. The gRPC runtime has no such helper: ``Containers.Create`` takes the full OCI
runtime spec (the runc ``config.json`` structure) directly, so we build it here.

Pure and testable: input is the runtime-neutral ``oci_spec`` (mounts/env/labels/devices/
gpus as produced by ``oci.translate_creation_config`` + accelerator injection) plus the
container command and rootfs path; output is the OCI runtime spec dict that goes into the
``Container.spec`` Any. Snapshot/rootfs preparation and the gRPC calls live in the
runtime client; this module only shapes the spec.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

OCI_VERSION = "1.1.0"
_TYPE_URL = "types.containerd.io/opencontainers/runtime-spec/1/Spec"

# Minimal default capability set (runc's default bounded set for non-privileged).
_DEFAULT_CAPS = [
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
]

# Mounts every Linux container needs (runc does not add these implicitly).
_DEFAULT_MOUNTS: list[dict[str, Any]] = [
    {"destination": "/proc", "type": "proc", "source": "proc",
     "options": ["nosuid", "noexec", "nodev"]},
    {"destination": "/dev", "type": "tmpfs", "source": "tmpfs",
     "options": ["nosuid", "strictatime", "mode=755", "size=65536k"]},
    {"destination": "/dev/pts", "type": "devpts", "source": "devpts",
     "options": ["nosuid", "noexec", "newinstance", "ptmxmode=0666", "mode=0620", "gid=5"]},
    {"destination": "/dev/shm", "type": "tmpfs", "source": "shm",
     "options": ["nosuid", "noexec", "nodev", "mode=1777", "size=65536k"]},
    {"destination": "/dev/mqueue", "type": "mqueue", "source": "mqueue",
     "options": ["nosuid", "noexec", "nodev"]},
    {"destination": "/sys", "type": "sysfs", "source": "sysfs",
     "options": ["nosuid", "noexec", "nodev", "ro"]},
]  # fmt: skip


def _bind_mounts(oci_spec: Mapping[str, Any]) -> list[dict[str, Any]]:
    binds = []
    for m in oci_spec.get("mounts", []):
        opts = ["rbind", "rprivate"]
        opts.append("ro" if m.get("readonly") else "rw")
        binds.append({
            "destination": m["destination"],
            "type": "bind",
            "source": m["source"],
            "options": opts,
        })
    return binds


def _linux_devices(
    oci_spec: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (linux.devices, cgroup device rules) for host-device passthrough.

    NVIDIA GPUs are injected by the nvidia OCI hook (from ``gpus``), not here; only the
    explicit ``devices`` (AMD/NPU /dev nodes) become runtime-spec devices + cgroup rules."""
    devices: list[dict[str, Any]] = []
    rules: list[dict[str, Any]] = [{"allow": False, "access": "rwm"}]
    for dev in oci_spec.get("devices", []):
        path = dev["destination"]
        devices.append({"path": path, "type": "c", "major": -1, "minor": -1})
        rules.append({"allow": True, "type": "c", "access": dev.get("permissions", "rwm")})
    return devices, rules


def build_oci_runtime_spec(
    oci_spec: Mapping[str, Any],
    *,
    command: Sequence[str],
    rootfs_path: str,
    cwd: str = "/",
    hostname: str = "",
    network_ns_path: str | None = None,
) -> dict[str, Any]:
    """Assemble the OCI runtime spec (runc config.json) for ``Container.spec``.

    ``network_ns_path`` pins the container to an existing netns (the BEP-1055 layer creates
    it and attaches CNI); when None a fresh network namespace is created.
    """
    env = [f"{k}={v}" for k, v in (oci_spec.get("env") or {}).items()]
    devices, device_rules = _linux_devices(oci_spec)
    namespaces: list[dict[str, Any]] = [
        {"type": "pid"},
        {"type": "ipc"},
        {"type": "uts"},
        {"type": "mount"},
    ]
    net_ns: dict[str, Any] = {"type": "network"}
    if network_ns_path is not None:
        net_ns["path"] = network_ns_path
    namespaces.append(net_ns)

    return {
        "ociVersion": OCI_VERSION,
        "process": {
            "terminal": False,
            "user": {"uid": 0, "gid": 0},
            "args": list(command),
            "env": env,
            "cwd": cwd,
            "capabilities": {
                "bounding": _DEFAULT_CAPS,
                "effective": _DEFAULT_CAPS,
                "permitted": _DEFAULT_CAPS,
            },
            "noNewPrivileges": False,
        },
        "root": {"path": rootfs_path, "readonly": False},
        "hostname": hostname,
        "mounts": [*_DEFAULT_MOUNTS, *_bind_mounts(oci_spec)],
        "linux": {
            "namespaces": namespaces,
            "devices": devices,
            "resources": {"devices": device_rules},
            "cgroupsPath": f"/backend-ai/{oci_spec.get('labels', {}).get('ai.backend.kernel-id', '')}",
        },
    }
