import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from ai.backend.common.data.vfolder.types import VFolderMountData
from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    SessionResult,
    SessionTypes,
)
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.network import NetworkType

if TYPE_CHECKING:
    from ai.backend.manager.models.session import SessionStatus


# TODO: Add proper types
@dataclass
class SessionData:
    id: uuid.UUID
    session_type: SessionTypes
    priority: int
    cluster_mode: ClusterMode
    cluster_size: int
    domain_name: str
    group_id: uuid.UUID
    user_uuid: uuid.UUID
    occupying_slots: Any  # TODO: ResourceSlot?
    requested_slots: Any
    use_host_network: bool
    created_at: datetime = field(compare=False)
    status: "SessionStatus"
    result: SessionResult
    num_queries: int
    creation_id: Optional[str]
    name: Optional[str]
    access_key: Optional[AccessKey]
    agent_ids: Optional[list[str]]
    images: Optional[list[str]]
    tag: Optional[str]
    vfolder_mounts: Optional[list[VFolderMountData]]
    environ: Optional[dict[str, Any]]
    bootstrap_script: Optional[str]
    target_sgroup_names: Optional[list[str]]
    timeout: Optional[int]
    batch_timeout: Optional[int]
    terminated_at: Optional[datetime] = field(compare=False)
    scaling_group_name: Optional[str]
    starts_at: Optional[datetime] = field(compare=False)
    status_info: Optional[str] = field(compare=False)
    status_data: Optional[dict[str, Any]] = field(compare=False)
    status_history: Optional[dict[str, Any]] = field(compare=False)
    callback_url: Optional[str]
    startup_command: Optional[str]
    last_stat: Optional[dict[str, Any]] = field(compare=False)
    network_type: Optional[NetworkType]
    network_id: Optional[str]
    owner: Optional[UserData] = field(compare=False)

    # Loaded from relationship
    service_ports: Optional[str]
