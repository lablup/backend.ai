"""Translate a Backend.AI KernelCreationConfig into a containerd container spec (BEP-1058).

Pure translation from kernel-domain concepts to what `OciRuntime` needs
(image ref, command, OCI-ish spec + labels/env). Kept small and testable; the full OCI
spec (krunner entrypoint, resource limits, mounts, cgroup placement) is layered on as the
containerd agent lifecycle matures.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from ai.backend.agent.resources import Mount
from ai.backend.common.types import KernelCreationConfig, MountPermission

KERNEL_ID_LABEL = "ai.backend.kernel-id"
SESSION_ID_LABEL = "ai.backend.session-id"
KRUNNER_ENTRYPOINT = "/opt/kernel/entrypoint.sh"


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
    return AcceleratorSpec(
        devices=devices,
        gpu_device_ids=gpu_ids,
        env=env,
        cpuset_cpus=host_config.get("CpusetCpus") or None,
        cpuset_mems=host_config.get("CpusetMems") or None,
        memory_limit=int(memory) if memory else None,
        memory_swap=int(memory_swap) if memory_swap else None,
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
