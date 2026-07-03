"""Translate a Backend.AI KernelCreationConfig into a containerd container spec (BEP-1055).

Pure translation from kernel-domain concepts to what `ContainerdRuntimeClient` needs
(image ref, command, OCI-ish spec + labels/env). Kept small and testable; the full OCI
spec (krunner entrypoint, resource limits, mounts, cgroup placement) is layered on as the
containerd agent lifecycle matures.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ai.backend.common.types import KernelCreationConfig

KERNEL_ID_LABEL = "ai.backend.kernel-id"
SESSION_ID_LABEL = "ai.backend.session-id"


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
) -> ContainerSpec:
    """Derive the containerd container spec for a kernel.

    ``container_id`` = the kernel id (unique per kernel); ``image_ref`` = the image's
    canonical reference. ``command`` defaults to empty (use the image's entrypoint/CMD);
    the krunner entrypoint is injected by later lifecycle work.
    """
    image = kernel_config["image"]
    kernel_id = str(kernel_config["kernel_id"])
    session_id = str(kernel_config["session_id"])
    return ContainerSpec(
        container_id=kernel_id,
        session_id=session_id,
        image_ref=str(image["canonical"]),
        command=list(command or []),
        oci_spec={
            "env": dict(environ),
            "labels": {
                KERNEL_ID_LABEL: kernel_id,
                SESSION_ID_LABEL: session_id,
            },
        },
    )
