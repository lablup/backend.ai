import enum
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Any, Optional

from ai.backend.common.types import (
    ClusterMode,
    MountPermission,
    SessionResult,
    SessionTypes,
    VFolderID,
    VFolderUsageMode,
)
from ai.backend.manager.models.network import NetworkType

if TYPE_CHECKING:
    from ai.backend.manager.models.session import SessionStatus


class CustomizedImageVisibilityScope(str, enum.Enum):
    USER = "user"
    PROJECT = "project"


@dataclass
class VFolderMountData:
    name: str
    vfid: VFolderID
    vfsubpath: PurePosixPath
    host_path: PurePosixPath
    kernel_path: PurePosixPath
    mount_perm: MountPermission
    usage_mode: VFolderUsageMode


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
    created_at: datetime
    status: "SessionStatus"
    result: SessionResult

    creation_id: Optional[str] = None
    name: Optional[str] = None
    access_key: Optional[str] = None
    agent_ids: Optional[list[str]] = None
    images: Optional[list[str]] = None
    tag: Optional[str] = None
    vfolder_mounts: Optional[list[VFolderMountData]] = None
    environ: Optional[dict[str, Any]] = None
    bootstrap_script: Optional[str] = None
    target_sgroup_names: Optional[list[str]] = None
    timeout: Optional[int] = None
    batch_timeout: Optional[int] = None
    terminated_at: Optional[datetime] = None
    scaling_group_name: Optional[str] = None
    starts_at: Optional[datetime] = None
    status_info: Optional[str] = None
    status_data: Optional[dict[str, Any]] = None
    status_history: Optional[dict[str, Any]] = None
    callback_url: Optional[str] = None
    startup_command: Optional[str] = None
    num_queries: Optional[int] = None
    last_stat: Optional[dict[str, Any]] = None
    network_type: Optional[NetworkType] = None
    network_id: Optional[str] = None
