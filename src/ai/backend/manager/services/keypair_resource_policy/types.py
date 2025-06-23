from dataclasses import dataclass
from typing import Any, Optional

from ai.backend.common.types import DefaultForUnspecified, ResourceSlot
from ai.backend.manager.types import Creator


@dataclass
class KeyPairResourcePolicyCreator(Creator):
    name: Optional[str]
    allowed_vfolder_hosts: Optional[dict[str, Any]]
    default_for_unspecified: Optional[DefaultForUnspecified]
    idle_timeout: Optional[int]
    max_concurrent_sessions: Optional[int]
    max_containers_per_session: Optional[int]
    max_pending_session_count: Optional[int]
    max_pending_session_resource_slots: Optional[ResourceSlot]
    max_quota_scope_size: Optional[int]
    max_vfolder_count: Optional[int]
    max_vfolder_size: Optional[int]
    max_concurrent_sftp_sessions: Optional[int]
    max_session_lifetime: Optional[int]
    total_resource_slots: Optional[ResourceSlot]

    def fields_to_store(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "allowed_vfolder_hosts": self.allowed_vfolder_hosts,
            "default_for_unspecified": self.default_for_unspecified,
            "idle_timeout": self.idle_timeout,
            "max_concurrent_sessions": self.max_concurrent_sessions,
            "max_containers_per_session": self.max_containers_per_session,
            "max_pending_session_count": self.max_pending_session_count,
            "max_pending_session_resource_slots": self.max_pending_session_resource_slots,
            # "max_quota_scope_size": self.max_quota_scope_size, # Deprecated
            # "max_vfolder_count": self.max_vfolder_count, # Deprecated
            # "max_vfolder_size": self.max_vfolder_size, # Deprecated
            "max_concurrent_sftp_sessions": self.max_concurrent_sftp_sessions,
            "max_session_lifetime": self.max_session_lifetime,
            "total_resource_slots": self.total_resource_slots,
        }
