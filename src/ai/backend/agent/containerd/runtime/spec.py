"""Build a containerd/runc OCI *runtime* spec from our runtime-neutral oci_spec (BEP-1058).

There is no CLI to assemble the OCI runtime spec for us: ``Containers.Create`` takes the full OCI
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

# nvidia-container-toolkit's OCI hook: injects the requested GPU device nodes + driver
# libraries at container start, driven by the NVIDIA_VISIBLE_DEVICES env it reads from the
# spec. This is what nerdctl/docker's `--gpus` ultimately wires up.
_NVIDIA_HOOK_PATH = "/usr/bin/nvidia-container-runtime-hook"

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
    "CAP_IPC_LOCK",  # hugepages + RDMA (parity with DockerAgent CapAdd)
    "CAP_SYS_NICE",  # NFS-based GPUDirect Storage
]

# rlimits matching the Docker backend's Ulimits (nofile bumped high; memlock unlimited).
_DEFAULT_RLIMITS: list[dict[str, Any]] = [
    {"type": "RLIMIT_NOFILE", "hard": 1048576, "soft": 1048576},
    {"type": "RLIMIT_MEMLOCK", "hard": 0xFFFFFFFFFFFFFFFF, "soft": 0xFFFFFFFFFFFFFFFF},
]
_DEFAULT_SHM_SIZE = 64 * 1024 * 1024  # 64 MiB, containerd/runc default

# Mounts every Linux container needs (runc does not add these implicitly).
_DEFAULT_MOUNTS: list[dict[str, Any]] = [
    {"destination": "/proc", "type": "proc", "source": "proc",
     "options": ["nosuid", "noexec", "nodev"]},
    {"destination": "/dev", "type": "tmpfs", "source": "tmpfs",
     "options": ["nosuid", "strictatime", "mode=755", "size=65536k"]},
    {"destination": "/dev/pts", "type": "devpts", "source": "devpts",
     "options": ["nosuid", "noexec", "newinstance", "ptmxmode=0666", "mode=0620", "gid=5"]},
    {"destination": "/dev/mqueue", "type": "mqueue", "source": "mqueue",
     "options": ["nosuid", "noexec", "nodev"]},
    {"destination": "/sys", "type": "sysfs", "source": "sysfs",
     "options": ["nosuid", "noexec", "nodev", "ro"]},
]  # fmt: skip


def _shm_mount(oci_spec: Mapping[str, Any]) -> dict[str, Any]:
    size = int(oci_spec.get("shmem") or _DEFAULT_SHM_SIZE)
    return {
        "destination": "/dev/shm",
        "type": "tmpfs",
        "source": "shm",
        "options": ["nosuid", "noexec", "nodev", "mode=1777", f"size={size}"],
    }


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


def _nvidia_hooks(oci_spec: Mapping[str, Any], env: list[str]) -> dict[str, Any] | None:
    """If NVIDIA GPUs are requested, register the nvidia-container-toolkit prestart hook and
    ensure the env it consumes is present. Returns the OCI ``hooks`` dict (or None)."""
    gpus = oci_spec.get("gpus")
    if not gpus:
        return None
    if not any(e.startswith("NVIDIA_VISIBLE_DEVICES=") for e in env):
        env.append("NVIDIA_VISIBLE_DEVICES=" + ",".join(str(g) for g in gpus))
    if not any(e.startswith("NVIDIA_DRIVER_CAPABILITIES=") for e in env):
        env.append("NVIDIA_DRIVER_CAPABILITIES=all")
    return {
        "prestart": [
            {"path": _NVIDIA_HOOK_PATH, "args": ["nvidia-container-runtime-hook", "prestart"]}
        ]
    }


def _linux_resources(
    oci_spec: Mapping[str, Any], device_rules: list[dict[str, Any]]
) -> dict[str, Any]:
    """Assemble linux.resources: the device cgroup rules plus CPU pinning and memory
    limits (the cgroup enforcement the CPU/memory compute plugins allocate)."""
    resources: dict[str, Any] = {"devices": device_rules}
    cpu: dict[str, Any] = {}
    if oci_spec.get("cpuset_cpus"):
        cpu["cpus"] = oci_spec["cpuset_cpus"]
    if oci_spec.get("cpuset_mems"):
        cpu["mems"] = oci_spec["cpuset_mems"]
    if cpu:
        resources["cpu"] = cpu
    memory: dict[str, Any] = {}
    if oci_spec.get("memory_limit") is not None:
        memory["limit"] = int(oci_spec["memory_limit"])
    if oci_spec.get("memory_swap") is not None:
        memory["swap"] = int(oci_spec["memory_swap"])
    if memory:
        resources["memory"] = memory
    return resources


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
    resources = _linux_resources(oci_spec, device_rules)
    hooks = _nvidia_hooks(oci_spec, env)  # mutates env with the NVIDIA_* vars the hook needs
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

    spec: dict[str, Any] = {
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
            "rlimits": _DEFAULT_RLIMITS,
        },
        "root": {"path": rootfs_path, "readonly": False},
        "hostname": hostname,
        "mounts": [*_DEFAULT_MOUNTS, _shm_mount(oci_spec), *_bind_mounts(oci_spec)],
        "linux": {
            "namespaces": namespaces,
            "devices": devices,
            "resources": resources,
            "cgroupsPath": f"/backend-ai/{oci_spec.get('labels', {}).get('ai.backend.kernel-id', '')}",
        },
    }
    if hooks is not None:
        spec["hooks"] = hooks
    return spec
