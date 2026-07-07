"""
Kernel-creation spec model and pure builders for the ``ag kernel`` CLI.

The manager assembles ``KernelCreationConfig`` / ``ClusterInfo`` / ``ImageRef``
inside ``manager/sokovan/scheduler/launcher/launcher.py`` from database-resolved
values. The verification CLI has no database, so this module reconstructs the
same structures from a small user-supplied ``KernelCreateSpec`` plus a locally
inspected image, mirroring the launcher's defaults for a single-node,
single-kernel session.

Everything here is pure (no I/O) so it can be unit-tested without a live docker
daemon; image inspection and RPC live in ``kernel.py``.
"""

from __future__ import annotations

from typing import Any

from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from pydantic import BaseModel, Field

from ai.backend.common.docker import ImageRef, LabelName
from ai.backend.common.types import (
    AutoPullBehavior,
    ClusterInfo,
    ClusterMode,
    ClusterSSHKeyPair,
    ImageConfig,
    KernelCreationConfig,
    SessionTypes,
)

DEFAULT_RESOURCE_SLOTS: dict[str, str] = {"cpu": "1", "mem": str(1 * 2**30)}


class RegistrySpec(BaseModel):
    """Container registry coordinates for the image being created."""

    name: str = "local"
    url: str = ""
    username: str | None = None
    password: str | None = None


class KernelCreateSpec(BaseModel):
    """User-facing spec for ``ag kernel create``.

    Only ``image`` is required; every other field mirrors a launcher default so
    a minimal spec (``{"image": "..."}``) yields a working single-node kernel on
    a local docker agent. ``architecture`` defaults to the inspected image's
    architecture when omitted.
    """

    image: str
    project: str | None = None
    architecture: str | None = None
    registry: RegistrySpec = Field(default_factory=RegistrySpec)
    is_local: bool = True
    auto_pull: AutoPullBehavior = AutoPullBehavior.NONE

    resource_slots: dict[str, str] = Field(default_factory=lambda: dict(DEFAULT_RESOURCE_SLOTS))
    resource_opts: dict[str, Any] = Field(default_factory=dict)
    environ: dict[str, str] = Field(default_factory=dict)

    cluster_mode: ClusterMode = ClusterMode.SINGLE_NODE
    session_type: SessionTypes = SessionTypes.INTERACTIVE
    scaling_group: str = "default"

    mounts: list[dict[str, Any]] = Field(default_factory=list)
    bootstrap_script: str | None = None
    startup_command: str | None = None
    preopen_ports: list[int] = Field(default_factory=list)
    idle_timeout: int = 0

    uid: int | None = None
    main_gid: int | None = None
    supplementary_gids: list[int] = Field(default_factory=list)

    # Optional identity overrides; generated when omitted.
    kernel_id: str | None = None
    session_id: str | None = None
    owner_user_id: str | None = None


def generate_cluster_ssh_keypair() -> ClusterSSHKeyPair:
    """Generate an ephemeral RSA keypair for the cluster SSH slot.

    Mirrors ``manager/models/keypair/row.py:generate_ssh_keypair`` (which lives
    in a manager-only layer the agent cannot import). Single-node kernels do not
    use it, but the manager always sends one, so we do too to keep parity.
    """
    key = rsa.generate_private_key(
        backend=crypto_default_backend(),
        public_exponent=65537,
        key_size=2048,
    )
    private_key = key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.TraditionalOpenSSL,
        crypto_serialization.NoEncryption(),
    ).decode("utf-8")
    public_key = (
        key.public_key()
        .public_bytes(
            crypto_serialization.Encoding.OpenSSH,
            crypto_serialization.PublicFormat.OpenSSH,
        )
        .decode("utf-8")
    )
    return ClusterSSHKeyPair(
        public_key=f"{public_key.rstrip()}\n",
        private_key=f"{private_key.rstrip()}\n",
    )


def build_cluster_info(
    spec: KernelCreateSpec,
    ssh_keypair: ClusterSSHKeyPair,
) -> ClusterInfo:
    """Build a single-node, single-kernel ``ClusterInfo`` (launcher parity)."""
    return ClusterInfo(
        mode=spec.cluster_mode,
        size=1,
        replicas={"main": 1},
        network_config={},
        ssh_keypair=ssh_keypair,
        cluster_ssh_port_mapping=None,
    )


def build_image_ref(image_config: ImageConfig) -> ImageRef:
    """Build the ``ImageRef`` the same way the launcher does per kernel."""
    return ImageRef.from_image_str(
        image_config["canonical"],
        project=image_config["project"],
        registry=image_config["registry"]["name"],
        architecture=image_config["architecture"],
        is_local=image_config["is_local"],
    )


def _build_environ(
    spec: KernelCreateSpec,
    image_config: ImageConfig,
    kernel_id: str,
) -> dict[str, str]:
    """Compose the kernel environ with the BACKENDAI_* cluster/service vars.

    Mirrors the launcher's environ assembly for a single ``main`` kernel.
    """
    environ = dict(spec.environ)
    environ.setdefault("BACKENDAI_KERNEL_ID", kernel_id)
    environ.setdefault("BACKENDAI_KERNEL_IMAGE", image_config["canonical"])
    environ.setdefault("BACKENDAI_CLUSTER_ROLE", "main")
    environ.setdefault("BACKENDAI_CLUSTER_IDX", "1")
    environ.setdefault("BACKENDAI_CLUSTER_LOCAL_RANK", "0")
    environ.setdefault("BACKENDAI_CLUSTER_HOST", "main1")
    service_ports = image_config["labels"].get(LabelName.SERVICE_PORTS, "")
    if service_ports:
        environ.setdefault("BACKENDAI_SERVICE_PORTS", service_ports)
    return environ


def build_kernel_creation_config(
    spec: KernelCreateSpec,
    *,
    image_config: ImageConfig,
    kernel_id: str,
    session_id: str,
    owner_user_id: str,
    agent_addr: str,
) -> KernelCreationConfig:
    """Assemble the full ``KernelCreationConfig`` for one ``main`` kernel.

    Every ``KernelCreationConfig`` key is populated with the same defaults the
    launcher uses, so the agent's create path exercises the identical shape it
    would receive from the manager. ``owner_user_id`` must be a UUID string —
    the agent coerces it into a UUID, so an empty string would raise.
    """
    return KernelCreationConfig(
        image=image_config,
        kernel_id=kernel_id,
        session_id=session_id,
        owner_user_id=owner_user_id,
        owner_project_id=None,
        network_id=session_id,
        auto_pull=spec.auto_pull,
        session_type=spec.session_type,
        cluster_mode=spec.cluster_mode,
        cluster_role="main",
        cluster_idx=1,
        cluster_hostname="main1",
        local_rank=0,
        uid=spec.uid,
        main_gid=spec.main_gid,
        supplementary_gids=list(spec.supplementary_gids),
        resource_slots=dict(spec.resource_slots),
        resource_opts=dict(spec.resource_opts),
        environ=_build_environ(spec, image_config, kernel_id),
        mounts=list(spec.mounts),
        package_directory=(),
        idle_timeout=spec.idle_timeout,
        bootstrap_script=spec.bootstrap_script,
        startup_command=spec.startup_command,
        internal_data=None,
        preopen_ports=list(spec.preopen_ports),
        allocated_host_ports=[],
        scaling_group=spec.scaling_group,
        agent_addr=agent_addr,
        endpoint_id=None,
    )
