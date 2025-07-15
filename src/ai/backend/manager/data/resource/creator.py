from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from ai.backend.common.types import DefaultForUnspecified, ResourceSlot
from ai.backend.manager.types import Creator


@dataclass
class UserResourcePolicyCreator(Creator):
    name: str
    max_vfolder_count: int
    max_quota_scope_size: int
    max_session_count_per_model_session: int
    max_customized_image_count: int

    def fields_to_store(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "max_vfolder_count": self.max_vfolder_count,
            "max_quota_scope_size": self.max_quota_scope_size,
            "max_session_count_per_model_session": self.max_session_count_per_model_session,
            "max_customized_image_count": self.max_customized_image_count,
        }


@dataclass
class ProjectResourcePolicyCreator(Creator):
    name: str
    max_vfolder_count: int
    max_quota_scope_size: int
    max_network_count: int

    def fields_to_store(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "max_vfolder_count": self.max_vfolder_count,
            "max_quota_scope_size": self.max_quota_scope_size,
            "max_network_count": self.max_network_count,
        }


@dataclass
class KeyPairResourcePolicyCreator(Creator):
    name: str
    created_at: datetime
    default_for_unspecified: DefaultForUnspecified
    total_resource_slots: ResourceSlot
    max_session_lifetime: int
    max_concurrent_sessions: int
    max_pending_session_count: Optional[int]
    max_pending_session_resource_slots: Optional[Any]
    max_concurrent_sftp_sessions: int
    max_containers_per_session: int
    idle_timeout: int
    allowed_vfolder_hosts: dict[str, Any]

    def fields_to_store(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "created_at": self.created_at,
            "default_for_unspecified": self.default_for_unspecified,
            "total_resource_slots": self.total_resource_slots,
            "max_session_lifetime": self.max_session_lifetime,
            "max_concurrent_sessions": self.max_concurrent_sessions,
            "max_pending_session_count": self.max_pending_session_count,
            "max_pending_session_resource_slots": self.max_pending_session_resource_slots,
            "max_concurrent_sftp_sessions": self.max_concurrent_sftp_sessions,
            "max_containers_per_session": self.max_containers_per_session,
            "idle_timeout": self.idle_timeout,
            "allowed_vfolder_hosts": self.allowed_vfolder_hosts,
        }
