"""Translate a Backend.AI KernelCreationConfig into a containerd container spec (BEP-1055).

Pure translation from kernel-domain concepts to what `ContainerdRuntimeClient` needs
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
            "mounts": [mount_to_oci(m) for m in mounts],
        },
    )
