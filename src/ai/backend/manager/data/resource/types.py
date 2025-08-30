from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from ai.backend.common.types import DefaultForUnspecified, ResourceSlot


@dataclass
class UserResourcePolicyData:
    name: str
    max_vfolder_count: int
    max_quota_scope_size: int
    max_session_count_per_model_session: int
    max_customized_image_count: int


@dataclass
class ProjectResourcePolicyData:
    name: str
    max_vfolder_count: int
    max_quota_scope_size: int
    max_network_count: int


@dataclass
class KeyPairResourcePolicyData:
    name: str
    created_at: datetime = field(compare=False)
    default_for_unspecified: DefaultForUnspecified
    total_resource_slots: ResourceSlot
    max_session_lifetime: int
    max_concurrent_sessions: int
    max_pending_session_count: Optional[int]
    max_pending_session_resource_slots: Optional[Any]  # TODO: Use ResourceSlot.
    max_concurrent_sftp_sessions: int
    max_containers_per_session: int
    idle_timeout: int
    allowed_vfolder_hosts: dict[str, Any]


@dataclass
class ScalingGroupProxyTarget:
    addr: str
    api_token: str
