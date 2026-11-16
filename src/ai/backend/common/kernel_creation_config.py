from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, TypedDict

from ai.backend.common.types import AutoPullBehavior, ClusterMode, ImageConfig, SessionTypes


class KernelCreationConfig(TypedDict):
    image: ImageConfig
    kernel_id: str  # the kernel's ID
    session_id: str  # the session's ID
    session_name: str  # the session's name
    owner_user_id: str  # the owner user's ID
    owner_project_id: str | None  # the owner project's ID (for project-owned sessions)
    network_id: str
    auto_pull: AutoPullBehavior
    session_type: SessionTypes
    cluster_mode: ClusterMode
    cluster_role: str  # the kernel's role in the cluster
    cluster_idx: int  # the kernel's index in the cluster
    cluster_hostname: str  # the kernel's hostname in the cluster
    local_rank: int  # the kernel's local rank in the cluster
    uid: int | None
    main_gid: int | None
    supplementary_gids: list[int]
    resource_slots: Mapping[str, str]  # json form of ResourceSlot
    resource_opts: Mapping[str, Any]  # json form of resource options
    environ: Mapping[str, str]
    mounts: Sequence[Mapping[str, Any]]  # list of serialized VFolderMount
    package_directory: Sequence[str]
    idle_timeout: int
    bootstrap_script: str | None
    startup_command: str | None
    internal_data: Mapping[str, Any] | None
    preopen_ports: list[int]
    allocated_host_ports: list[int]
    scaling_group: str
    agent_addr: str
    endpoint_id: str | None
