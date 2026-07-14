"""Translate a Backend.AI KernelCreationConfig into a containerd container spec (BEP-1062).

Pure translation from kernel-domain concepts to what `OciRuntime` needs
(image ref, command, OCI-ish spec + labels/env). Kept small and testable; the full OCI
spec (krunner entrypoint, resource limits, mounts, cgroup placement) is layered on as the
containerd agent lifecycle matures.
"""

from __future__ import annotations

import grp
import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ai.backend.agent.resources import Mount
from ai.backend.common.types import KernelCreationConfig, MountPermission
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# OCI rlimits are unsigned; Docker's -1 ("unlimited") maps to the max value.
_RLIM_INFINITY = 0xFFFFFFFFFFFFFFFF

KERNEL_ID_LABEL = "ai.backend.kernel-id"
SESSION_ID_LABEL = "ai.backend.session-id"
# Which agent owns the container. A containerd namespace can be shared by two agents on one host,
# and every restart-time scan has to keep to its own kernels (LabelName.OWNER_AGENT, written at
# create time).
OWNER_AGENT_LABEL = "ai.backend.owner"
KRUNNER_ENTRYPOINT = "/opt/kernel/entrypoint.sh"

# RDMA/InfiniBand verbs devices live under this directory; uverbs0 is the sentinel the Docker
# backend keys on (docker/agent.py). See infiniband_devices().
_IB_ROOT = Path("/dev/infiniband")


def mount_to_oci(mount: Mount) -> dict[str, Any]:
    """Convert a Backend.AI Mount into a runtime-neutral bind-mount descriptor
    (source/destination/readonly) that the runtime client maps to its own flags."""
    readonly = mount.permission == MountPermission.READ_ONLY
    return {
        "source": str(mount.source),
        "destination": str(mount.target),
        "readonly": readonly,
    }


@dataclass(frozen=True)
class ContainerSpec:
    container_id: str
    session_id: str
    image_ref: str
    command: list[str] = field(default_factory=list)
    oci_spec: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DevicePassthrough:
    """A host device node exposed into the container (AMD/NPU accelerators, etc.)."""

    source: str
    destination: str
    permissions: str = "rwm"


def infiniband_devices(ib_root: Path = _IB_ROOT) -> list[DevicePassthrough]:
    """The RDMA/InfiniBand character devices to pass through, or [] when the host has no HCA.

    Docker parity (docker/agent.py): if ``/dev/infiniband`` exists and holds ``uverbs0``, the whole
    directory is exposed into every container — an unconditional, unscheduled bulk passthrough (no
    HCA<->GPU topology, no per-tenant isolation). Docker hands dockerd the directory and lets it
    expand to the char nodes; the OCI/containerd path cannot pass a directory, so each node under it
    is enumerated into its own device entry. Same devices reach the container, expressed per-node.
    """
    if not (ib_root.is_dir() and (ib_root / "uverbs0").exists()):
        return []
    devices: list[DevicePassthrough] = []
    for node in sorted(ib_root.iterdir()):
        if node.is_char_device():
            path = str(node)
            devices.append(DevicePassthrough(source=path, destination=path))
    return devices


@dataclass(frozen=True)
class AcceleratorSpec:
    """Runtime-neutral compute wiring translated from a compute plugin's Docker args.

    Accumulated across ALL compute plugins (cpu, mem, accelerators):
    - ``devices``: explicit /dev node passthrough (AMD ROCm, Furiosa/Rebellions/Habana NPUs).
    - ``gpu_device_ids``: NVIDIA device IDs handled by nvidia-container-toolkit (`--gpus`).
    - ``env``: extra environment the plugin injects (e.g. NVIDIA_DRIVER_CAPABILITIES).
    - ``cpuset_cpus`` / ``cpuset_mems``: cgroup CPU/NUMA pinning (from the CPU plugin).
    - ``memory_limit`` / ``memory_swap``: cgroup memory limits in bytes (from the mem plugin).
    """

    devices: list[DevicePassthrough] = field(default_factory=list)
    gpu_device_ids: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    cpuset_cpus: str | None = None
    cpuset_mems: str | None = None
    memory_limit: int | None = None
    memory_swap: int | None = None
    # The rest of the HostConfig the NPU/IPU/ROCm plugins emit. Dropping these does not fail
    # loudly — the container starts and the accelerator then misbehaves (no memlock, no host IPC,
    # no device group), which is far harder to diagnose than a refusal.
    cap_add: list[str] = field(default_factory=list)  # OCI names, e.g. CAP_IPC_LOCK
    sysctls: dict[str, str] = field(default_factory=dict)
    rlimits: list[dict[str, Any]] = field(default_factory=list)  # OCI process.rlimits entries
    additional_gids: list[int] = field(default_factory=list)
    ipc_host: bool = False  # HostConfig.IpcMode/Ipc == "host"
    seccomp_unconfined: bool = False  # HostConfig.SecurityOpt contains seccomp=unconfined


def _to_oci_cap(name: str) -> str:
    """Docker's CapAdd names are bare ('IPC_LOCK'); the OCI spec wants 'CAP_' prefixed."""
    upper = name.upper()
    return upper if upper.startswith("CAP_") else f"CAP_{upper}"


def _to_oci_rlimits(raw: Any) -> list[dict[str, Any]]:
    """Docker Ulimits ([{Name, Soft, Hard}]) -> OCI process.rlimits.

    Docker's -1 means "unlimited"; OCI rlimits are unsigned, where unlimited is the max value.
    """
    rlimits: list[dict[str, Any]] = []
    for item in raw or []:
        name = str(item.get("Name") or "").upper()
        if not name:
            continue
        soft = int(item.get("Soft", 0))
        hard = int(item.get("Hard", 0))
        rlimits.append({
            "type": name if name.startswith("RLIMIT_") else f"RLIMIT_{name}",
            "soft": _RLIM_INFINITY if soft < 0 else soft,
            "hard": _RLIM_INFINITY if hard < 0 else hard,
        })
    return rlimits


def _to_gids(raw: Any) -> list[int]:
    """Docker GroupAdd entries are group names or numeric ids; the OCI spec needs numeric gids.

    Resolving against the *host* group database is the right lookup here, not a mistake: these
    groups (ROCm's ``video``/``render``) exist to match the ownership of the host device nodes we
    are passing through, so the numeric gid the container needs is the host's.
    """
    gids: list[int] = []
    for entry in raw or []:
        text = str(entry)
        if text.lstrip("-").isdigit():
            gids.append(int(text))
            continue
        try:
            gids.append(grp.getgrnam(text).gr_gid)
        except KeyError:
            log.warning(
                "compute plugin asked for group {!r}, which does not exist on this host;"
                " the container will not get it",
                text,
            )
    return gids


def _normalize_env(raw: Any) -> dict[str, str]:
    if isinstance(raw, Mapping):
        return {str(k): str(v) for k, v in raw.items()}
    env: dict[str, str] = {}
    for item in raw or []:  # docker-style ["KEY=value", ...]
        key, _, value = str(item).partition("=")
        env[key] = value
    return env


def translate_accelerator_args(docker_args: Mapping[str, Any]) -> AcceleratorSpec:
    """Translate a compute plugin's ``generate_docker_args`` output (a Docker HostConfig)
    into runtime-neutral accelerator wiring for the containerd (OCI) path.

    Reuses the per-vendor logic the plugins already encode — only the transport differs:
    NVIDIA rides DeviceRequests/Runtime=nvidia -> nvidia-container-toolkit; every other
    accelerator is plain /dev node passthrough (HostConfig.Devices)."""
    host_config = docker_args.get("HostConfig") or {}
    devices = [
        DevicePassthrough(
            source=d["PathOnHost"],
            destination=d.get("PathInContainer") or d["PathOnHost"],
            permissions=d.get("CgroupPermissions") or "rwm",
        )
        for d in host_config.get("Devices") or []
    ]
    gpu_ids: list[str] = []
    for req in host_config.get("DeviceRequests") or []:
        if req.get("Driver") == "nvidia":
            gpu_ids.extend(str(i) for i in (req.get("DeviceIDs") or []))
    env = _normalize_env(docker_args.get("Env") or host_config.get("Env") or {})
    if not gpu_ids and host_config.get("Runtime") == "nvidia":
        visible = env.get("NVIDIA_VISIBLE_DEVICES", "")
        gpu_ids.extend(d for d in visible.split(",") if d and d != "void")
    memory = host_config.get("Memory")
    memory_swap = host_config.get("MemorySwap")
    security_opts = [str(o) for o in host_config.get("SecurityOpt") or []]
    if host_config.get("Privileged"):
        # Deliberately not honored: a privileged container is a security decision, not a device
        # detail, and no in-tree plugin asks for it. Say so rather than pretend.
        log.warning(
            "compute plugin requested a privileged container; the containerd backend does not"
            " grant it (the requested devices and capabilities are still applied)"
        )
    # Habana emits `Ipc`, everyone else `IpcMode` — both are the Docker host-IPC switch.
    ipc = host_config.get("IpcMode") or host_config.get("Ipc")
    return AcceleratorSpec(
        devices=devices,
        gpu_device_ids=gpu_ids,
        env=env,
        cpuset_cpus=host_config.get("CpusetCpus") or None,
        cpuset_mems=host_config.get("CpusetMems") or None,
        memory_limit=int(memory) if memory else None,
        memory_swap=int(memory_swap) if memory_swap else None,
        cap_add=[_to_oci_cap(str(c)) for c in host_config.get("CapAdd") or []],
        sysctls={str(k): str(v) for k, v in (host_config.get("Sysctls") or {}).items()},
        rlimits=_to_oci_rlimits(host_config.get("Ulimits")),
        additional_gids=_to_gids(host_config.get("GroupAdd")),
        ipc_host=str(ipc) == "host",
        seccomp_unconfined=any(o.replace(" ", "") == "seccomp=unconfined" for o in security_opts),
    )


def translate_creation_config(
    kernel_config: KernelCreationConfig,
    *,
    environ: Mapping[str, str],
    command: list[str] | None = None,
    mounts: Sequence[Mount] = (),
) -> ContainerSpec:
    """Derive the containerd container spec for a kernel.

    ``container_id`` = the kernel id (unique per kernel); ``image_ref`` = the image's
    canonical reference. ``command`` defaults to the krunner entrypoint (mounted by the
    inherited mount_krunner). ``mounts`` are the krunner + vfolder mounts, injected as
    bind-mount descriptors the runtime client maps to its own flags.
    """
    image = kernel_config["image"]
    kernel_id = str(kernel_config["kernel_id"])
    session_id = str(kernel_config["session_id"])
    return ContainerSpec(
        container_id=kernel_id,
        session_id=session_id,
        image_ref=str(image["canonical"]),
        command=list(command) if command is not None else [KRUNNER_ENTRYPOINT],
        oci_spec={
            "env": dict(environ),
            "labels": {
                KERNEL_ID_LABEL: kernel_id,
                SESSION_ID_LABEL: session_id,
            },
            # Sort by destination depth so parent mounts (e.g. the krunner volume at
            # /opt/backend.ai) are applied before nested mounts (/opt/backend.ai/lib/...);
            # otherwise runc cannot create the nested mountpoint on the read-only rootfs.
            "mounts": [
                mount_to_oci(m) for m in sorted(mounts, key=lambda m: len(str(m.target).split("/")))
            ],
        },
    )
