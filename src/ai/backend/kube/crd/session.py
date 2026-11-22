from __future__ import annotations

import enum
from typing import Any, ClassVar

from pydantic import Field

from ai.backend.kube.crd.base import (
    BACKEND_AI_GROUP,
    CRDInfo,
    CRDModel,
    CRDScope,
    CustomResource,
    PrinterColumn,
)


class SessionPhase(enum.StrEnum):
    """Session phases reported by the session controller (suggestion 13.4)."""

    PENDING = "Pending"
    SCHEDULED = "Scheduled"
    PREPARING = "Preparing"
    PULLING = "Pulling"
    CREATING = "Creating"
    RUNNING = "Running"
    TERMINATING = "Terminating"
    TERMINATED = "Terminated"
    ERROR = "Error"


class ImagePullPolicy(enum.StrEnum):
    ALWAYS = "Always"
    IF_NOT_PRESENT = "IfNotPresent"
    NEVER = "Never"


class MountPermission(enum.StrEnum):
    RO = "ro"
    RW = "rw"
    WD = "wd"


class KernelImage(CRDModel):
    canonical: str
    architecture: str = "x86_64"
    digest: str | None = None
    pull_policy: ImagePullPolicy = ImagePullPolicy.IF_NOT_PRESENT
    pull_secret_name: str | None = None
    labels: dict[str, str] = Field(default_factory=dict)


class VFolderVolumeMount(CRDModel):
    name: str
    vfid: str
    host_path: str = Field(
        description="Path of the vfolder as the storage-proxy mounts it; a StorageBinding maps it"
    )
    kernel_path: str
    mount_perm: MountPermission = MountPermission.RW
    usage_mode: str = "general"


class ServicePortSpec(CRDModel):
    name: str
    protocol: str
    container_ports: list[int]
    is_inference: bool = False


class KernelSpec(CRDModel):
    kernel_id: str
    cluster_role: str = "main"
    cluster_idx: int = 1
    cluster_hostname: str = "main1"
    local_rank: int = 0
    image: KernelImage
    resource_slots: dict[str, str] = Field(default_factory=dict)
    resource_opts: dict[str, Any] = Field(default_factory=dict)
    environ: dict[str, str] = Field(default_factory=dict)
    mounts: list[VFolderVolumeMount] = Field(default_factory=list)
    service_ports: list[ServicePortSpec] = Field(default_factory=list)
    preopen_ports: list[int] = Field(default_factory=list)
    uid: int | None = None
    main_gid: int | None = None
    supplementary_gids: list[int] = Field(default_factory=list)
    startup_command: str | None = None


class SessionWorkloadSpec(CRDModel):
    session_id: str
    session_name: str
    session_type: str = "interactive"
    owner_user_id: str
    owner_project_id: str | None = None
    access_key: str | None = None
    domain_name: str | None = None
    resource_group: str
    queue: str | None = None
    priority: int = 0
    cluster_mode: str = "single-node"
    cluster_size: int = Field(default=1, ge=1)
    network_id: str | None = None
    idle_timeout: int = 0
    scheduler_name: str = "sokovan"
    secret_name: str | None = Field(
        default=None,
        description=(
            "Secret holding the cluster SSH keypair (key `cluster-ssh-keypair`) and each kernel's"
            " internal data and bootstrap script (key `kernel-<kernel id>`), as JSON"
        ),
    )
    kernels: list[KernelSpec] = Field(min_length=1)


class KernelStatus(CRDModel):
    kernel_id: str
    phase: SessionPhase = SessionPhase.PENDING
    reported_phase: SessionPhase | None = Field(
        default=None, description="The last phase sent to the Manager as a kernel event"
    )
    pod_name: str | None = None
    pod_uid: str | None = None
    node_name: str | None = None
    pod_ip: str | None = None
    container_id: str | None = None
    exit_code: int | None = None
    reason: str | None = None
    message: str | None = None


class Condition(CRDModel):
    type: str
    status: str
    reason: str | None = None
    message: str | None = None
    last_transition_time: str | None = None


class SessionWorkloadStatus(CRDModel):
    phase: SessionPhase = SessionPhase.PENDING
    reason: str | None = None
    message: str | None = None
    observed_generation: int | None = None
    kernels: list[KernelStatus] = Field(default_factory=list)
    conditions: list[Condition] = Field(default_factory=list)


class SessionWorkload(CustomResource):
    crd: ClassVar[CRDInfo] = CRDInfo(
        group=BACKEND_AI_GROUP,
        kind="SessionWorkload",
        plural="sessionworkloads",
        scope=CRDScope.NAMESPACED,
        short_names=("sw",),
        printer_columns=(
            PrinterColumn("Session", ".spec.sessionName"),
            PrinterColumn("Phase", ".status.phase"),
            PrinterColumn("Size", ".spec.clusterSize", "integer"),
            PrinterColumn("Age", ".metadata.creationTimestamp", "date"),
        ),
    )

    spec: SessionWorkloadSpec
    status: SessionWorkloadStatus | None = None
