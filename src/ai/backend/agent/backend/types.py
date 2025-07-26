from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from ai.backend.common.docker import ImageRef, LabelName
from ai.backend.common.types import (
    AutoPullBehavior,
    ClusterMode,
    ClusterRole,
    ClusterSSHKeyPair,
    ClusterSSHPortMapping,
    ContainerSSHKeyPair,
    ImageRegistry,
    KernelCreationConfig,
    KernelId,
    ResourceSlot,
    VFolderMount,
)

from ..proxy import DomainSocketProxy
from ..types import KernelOwnershipData


@dataclass
class CGroupInfo:
    cgroup_path: Path
    version: str


@dataclass
class DotfileInfo:
    path: str
    data: str
    perm: str  # Octal permission string like "644"


@dataclass
class ClusterInfo:
    network_id: str
    cluster_mode: ClusterMode
    cluster_size: int
    cluster_role: ClusterRole  # the kernel's role in the cluster
    cluster_idx: int  # the kernel's index in the cluster
    cluster_hostname: str  # the kernel's hostname in the cluster

    replicas: Mapping[str, int]  # per-role kernel counts
    ssh_keypair: ClusterSSHKeyPair
    cluster_ssh_port_mapping: Optional[ClusterSSHPortMapping]


@dataclass
class KernelCreationInfo:
    kernel_id: KernelId
    kernel_creation_config: KernelCreationConfig  # TODO: Remove this field after refactoring

    ownership: KernelOwnershipData

    image_ref: ImageRef
    image_labels: Mapping[LabelName, str]
    image_registry: ImageRegistry
    image_digest: str
    image_auto_pull: AutoPullBehavior

    uid: Optional[int]
    main_gid: Optional[int]
    supplementary_gids: list[int]

    vfolder_mounts: list[VFolderMount]
    dotfiles: list[DotfileInfo]

    cluster_info: ClusterInfo
    resource_slots: ResourceSlot
    resource_opts: dict[str, Any]

    environ: dict[str, str]
    bootstrap_script: Optional[str]
    startup_command: Optional[str]
    internal_data: dict[str, Any]
    preopen_ports: list[int]
    allocated_host_ports: list[int]
    block_service_ports: bool

    docker_credentials: Optional[dict[str, Any]]
    container_ssh_keypair: ContainerSSHKeyPair

    # Is this field used in real?
    prevent_vfolder_mount: bool = False
    domain_socket_proxies: list[DomainSocketProxy] = field(default_factory=list)
