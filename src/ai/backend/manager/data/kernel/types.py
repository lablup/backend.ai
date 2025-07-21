import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from ai.backend.common.types import (
    ClusterMode,
    ResourceSlot,
    SessionResult,
    SessionTypes,
    VFolderMount,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.kernel import KernelStatus


@dataclass
class KernelData:
    # --- identity & session ---
    id: uuid.UUID
    session_id: uuid.UUID
    session_creation_id: Optional[str]
    session_name: Optional[str]
    session_type: SessionTypes

    # --- cluster info ---
    cluster_mode: ClusterMode
    cluster_size: int
    cluster_role: str
    cluster_idx: int
    local_rank: int
    cluster_hostname: str

    # --- uid / gid ---
    uid: Optional[int]
    main_gid: Optional[int]
    gids: Optional[list[int]]

    # --- ownership / auth ---
    scaling_group: Optional[str]
    agent: Optional[str]
    agent_addr: Optional[str]
    domain_name: str
    group_id: uuid.UUID
    user_uuid: uuid.UUID
    access_key: Optional[str]

    # --- image & registry ---
    image: Optional[str]
    architecture: str
    registry: Optional[str]
    tag: Optional[str]
    container_id: Optional[str]

    # --- resources ---
    occupied_slots: ResourceSlot
    requested_slots: ResourceSlot
    occupied_shares: dict
    environ: Optional[list[str]]
    mounts: Optional[list[str]]
    mount_map: dict
    vfolder_mounts: Optional[list[VFolderMount]]
    attached_devices: dict
    resource_opts: dict
    bootstrap_script: Optional[str]

    # --- networking ---
    kernel_host: Optional[str]
    repl_in_port: int
    repl_out_port: int
    stdin_port: int
    stdout_port: int
    service_ports: Optional[dict]
    preopen_ports: Optional[list[int]]
    use_host_network: bool

    # --- lifecycle timestamps ---
    created_at: datetime
    terminated_at: Optional[datetime]
    starts_at: Optional[datetime]

    # --- runtime status ---
    status: "KernelStatus"
    status_changed: Optional[datetime]
    status_info: Optional[str]
    status_data: Optional[dict]
    status_history: Optional[dict]

    # --- callbacks & commands ---
    callback_url: Optional[str]
    startup_command: Optional[str]

    # --- result & logs ---
    result: SessionResult
    internal_data: Optional[dict]
    container_log: Optional[bytes]

    # --- metrics ---
    num_queries: int
    last_stat: Optional[dict]
