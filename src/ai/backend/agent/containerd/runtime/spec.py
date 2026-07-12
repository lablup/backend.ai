"""Build a containerd/runc OCI *runtime* spec from our runtime-neutral oci_spec (BEP-1062).

There is no CLI to assemble the OCI runtime spec for us: ``Containers.Create`` takes the full OCI
runtime spec (the runc ``config.json`` structure) directly, so we build it here.

Pure and testable: input is the runtime-neutral ``oci_spec`` (mounts/env/labels/devices/
gpus as produced by ``oci.translate_creation_config`` + accelerator injection) plus the
container command and rootfs path; output is the OCI runtime spec dict that goes into the
``Container.spec`` Any. Snapshot/rootfs preparation and the gRPC calls live in the
runtime client; this module only shapes the spec.
"""

from __future__ import annotations

import logging
import os
import stat
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ai.backend.agent.containerd.runtime.cdi import CDI_DEFAULT_DIRS, inject_cdi_devices
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

OCI_VERSION = "1.1.0"
_TYPE_URL = "types.containerd.io/opencontainers/runtime-spec/1/Spec"

# nvidia-container-toolkit's OCI hook: injects the requested GPU device nodes + driver
# libraries at container start, driven by the NVIDIA_VISIBLE_DEVICES env it reads from the
# spec. This is what nerdctl/docker's `--gpus` ultimately wires up.
_NVIDIA_HOOK_PATH = "/usr/bin/nvidia-container-runtime-hook"

# We set each container's cgroup path explicitly (``linux.cgroupsPath`` below), so the cgroup
# lives at a deterministic location we control instead of the runtime's driver-specific default
# (``system.slice/containerd-<id>.scope`` for systemd, ``/<id>`` for cgroupfs). Both the spec
# writer and the stats reader (agent.get_cgroup_path) derive from this one constant so they can
# never drift apart. Assumes the cgroup v2 unified hierarchy.
_CGROUP_PARENT = "backend-ai"
_CGROUP_ROOT = "/sys/fs/cgroup"


def container_cgroup_fs_path(kernel_id: str) -> Path:
    """On-disk cgroup path for a container, matching the ``cgroupsPath`` set in the OCI spec."""
    return Path(_CGROUP_ROOT) / _CGROUP_PARENT / kernel_id


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


def _tmp_mounts(oci_spec: Mapping[str, Any]) -> list[dict[str, Any]]:
    """A tmpfs /tmp for the MEMORY scratch type (in-memory scratch); empty otherwise."""
    if not oci_spec.get("tmpfs_tmp"):
        return []
    return [
        {
            "destination": "/tmp",
            "type": "tmpfs",
            "source": "tmpfs",
            "options": ["nosuid", "nodev", "mode=1777"],
        }
    ]


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
    explicit ``devices`` (AMD/NPU /dev nodes) become runtime-spec devices + cgroup rules.

    Each node is stat()ed on the host: runc needs the real major/minor to mknod the device inside
    the container, and the cgroup rule needs them to be *specific*. A rule with no major/minor is
    an OCI wildcard — allowing one NPU would have allowed every character device on the box, which
    is strictly weaker than what Docker grants.
    """
    devices: list[dict[str, Any]] = []
    rules: list[dict[str, Any]] = [{"allow": False, "access": "rwm"}]
    for dev in oci_spec.get("devices", []):
        # The plugin may remap the path (e.g. /dev/rngd/npu3 -> npu0), so stat the SOURCE.
        source = Path(dev.get("source") or dev["destination"])
        try:
            st = source.stat()
        except OSError:
            log.warning("skipping device {}: cannot stat it on the host", source)
            continue
        if stat.S_ISBLK(st.st_mode):
            dev_type = "b"
        elif stat.S_ISCHR(st.st_mode):
            dev_type = "c"
        else:
            log.warning("skipping device {}: not a block or character device", source)
            continue
        major, minor = os.major(st.st_rdev), os.minor(st.st_rdev)
        access = dev.get("permissions") or "rwm"
        devices.append({
            "path": dev["destination"],
            "type": dev_type,
            "major": major,
            "minor": minor,
            "fileMode": stat.S_IMODE(st.st_mode),
            "uid": st.st_uid,
            "gid": st.st_gid,
        })
        rules.append({
            "allow": True,
            "type": dev_type,
            "major": major,
            "minor": minor,
            "access": access,
        })
    return devices, rules


def _nvidia_hooks(oci_spec: Mapping[str, Any], env: list[str]) -> dict[str, Any] | None:
    """If NVIDIA GPUs are requested, register the nvidia-container-toolkit prestart hook and
    ensure the env it consumes is present. Returns the OCI ``hooks`` dict (or None)."""
    gpus = oci_spec.get("gpus")
    if not gpus:
        return None
    # The allocation is authoritative: override any NVIDIA_VISIBLE_DEVICES the image baked in
    # (commonly ``all``) so the hook injects ONLY the allocated GPUs. Otherwise a session that
    # requested one GPU would see every GPU on a multi-GPU node — the Docker backend avoids this
    # because its DeviceRequests select devices at the daemon level, so we must enforce it here
    # to keep per-device isolation on par across backends.
    env[:] = [e for e in env if not e.startswith("NVIDIA_VISIBLE_DEVICES=")]
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
    cdi_dirs: Sequence[str] = CDI_DEFAULT_DIRS,
) -> dict[str, Any]:
    """Assemble the OCI runtime spec (runc config.json) for ``Container.spec``.

    ``network_ns_path`` pins the container to an existing netns (the BEP-1055 layer creates
    it and attaches CNI); when None a fresh network namespace is created.
    """
    env = [f"{k}={v}" for k, v in (oci_spec.get("env") or {}).items()]
    devices, device_rules = _linux_devices(oci_spec)
    resources = _linux_resources(oci_spec, device_rules)
    # Backend-requested extra capabilities (e.g. CAP_SYS_PTRACE for the jail sandbox), appended to
    # the default set without duplicating.
    caps = [*_DEFAULT_CAPS, *(c for c in oci_spec.get("extra_caps", []) if c not in _DEFAULT_CAPS)]
    seccomp = oci_spec.get("seccomp")
    namespaces: list[dict[str, Any]] = [
        {"type": "pid"},
        {"type": "uts"},
        {"type": "mount"},
    ]
    # Host IPC (HostConfig.IpcMode=host): several NPU plugins need it to share the vendor
    # runtime's shared memory with the host daemon. Omitting the ipc namespace entry — rather
    # than adding one — is how the OCI spec says "stay in the host's".
    if not oci_spec.get("ipc_host"):
        namespaces.append({"type": "ipc"})
    net_ns: dict[str, Any] = {"type": "network"}
    if network_ns_path is not None:
        net_ns["path"] = network_ns_path
    namespaces.append(net_ns)

    user: dict[str, Any] = {"uid": 0, "gid": 0}
    # Supplementary groups the compute plugins asked for (ROCm's video/render): without them the
    # container's processes cannot open the device nodes they were just given.
    if additional_gids := oci_spec.get("additional_gids"):
        user["additionalGids"] = list(additional_gids)
    # Plugin rlimits override the defaults of the same type (e.g. an NPU raising memlock).
    plugin_rlimits = oci_spec.get("rlimits") or []
    overridden = {r["type"] for r in plugin_rlimits}
    rlimits = [*(r for r in _DEFAULT_RLIMITS if r["type"] not in overridden), *plugin_rlimits]

    spec: dict[str, Any] = {
        "ociVersion": OCI_VERSION,
        "process": {
            "terminal": False,
            "user": user,
            "args": list(command),
            "env": env,
            "cwd": cwd,
            "capabilities": {
                "bounding": caps,
                "effective": caps,
                "permitted": caps,
            },
            "noNewPrivileges": False,
            "rlimits": rlimits,
        },
        "root": {"path": rootfs_path, "readonly": False},
        "hostname": hostname,
        "mounts": [
            *_DEFAULT_MOUNTS,
            _shm_mount(oci_spec),
            *_tmp_mounts(oci_spec),
            *_bind_mounts(oci_spec),
        ],
        "linux": {
            "namespaces": namespaces,
            "devices": devices,
            "resources": resources,
            "cgroupsPath": f"/{_CGROUP_PARENT}/{oci_spec.get('labels', {}).get('ai.backend.kernel-id', '')}",
        },
    }
    if seccomp is not None:
        spec["linux"]["seccomp"] = seccomp
    if sysctls := oci_spec.get("sysctls"):
        spec["linux"]["sysctl"] = dict(sysctls)
    _inject_gpus(spec, oci_spec, cdi_dirs)
    return spec


def _inject_gpus(
    spec: dict[str, Any], oci_spec: Mapping[str, Any], cdi_dirs: Sequence[str]
) -> None:
    """Wire requested NVIDIA GPUs into the assembled runtime spec. Prefer CDI (declarative,
    vendor-neutral; per-device isolation comes from the injected device nodes, not an env var);
    fall back to the nvidia-container-toolkit prestart hook + NVIDIA_VISIBLE_DEVICES when the host
    has no CDI spec for the requested devices."""
    gpus = oci_spec.get("gpus")
    if not gpus:
        return
    if inject_cdi_devices(spec, [f"nvidia.com/gpu={g}" for g in gpus], dirs=cdi_dirs):
        return
    hooks = _nvidia_hooks(oci_spec, spec["process"]["env"])
    if hooks is not None:
        for name, entries in hooks.items():
            spec.setdefault("hooks", {}).setdefault(name, []).extend(entries)
