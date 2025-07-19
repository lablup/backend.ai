from dataclasses import dataclass
from pathlib import Path
from typing import Optional,Any
from collections.abc import Mapping, Iterable, AsyncIterator

from ai.backend.common.docker import ImageRef
from ai.backend.common.types import ImageRegistry,AutoPullBehavior,ClusterMode, ResourceSlot,VFolderMount

from ..types import KernelOwnershipData


@dataclass
class CGroupInfo:
    cgroup_path: Path
    version: str


@dataclass
class ClusterInfo:
    network_id: str
    cluster_mode: ClusterMode
    cluster_role: str  # the kernel's role in the cluster
    cluster_idx: int  # the kernel's index in the cluster
    cluster_hostname: str  # the kernel's hostname in the cluster


@dataclass
class KernelCreationInfo:
    ownership: KernelOwnershipData

    image_ref: ImageRef
    image_registry: ImageRegistry
    image_auto_pull: AutoPullBehavior

    uid: Optional[int]
    main_gid: Optional[int]
    supplementary_gids: list[int]

    vfolder_mounts: list[VFolderMount]

    cluster_info: ClusterInfo
    resource_slots: ResourceSlot
    resource_opts: dict[str, Any]

    environ: dict[str, str]
    bootstrap_script: Optional[str]
    startup_command: Optional[str]
    internal_data: dict[str, Any]
    preopen_ports: list[int]
    allocated_host_ports: list[int]
