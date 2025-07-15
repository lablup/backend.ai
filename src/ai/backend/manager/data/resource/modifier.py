from dataclasses import dataclass
from typing import Any, Optional

from ai.backend.common.types import DefaultForUnspecified, ResourceSlot
from ai.backend.manager.types import OptionalState, PartialModifier


@dataclass
class UserResourcePolicyModifier(PartialModifier):
    max_vfolder_count: OptionalState[int]
    max_quota_scope_size: OptionalState[int]
    max_session_count_per_model_session: OptionalState[int]
    max_customized_image_count: OptionalState[int]

    def fields_to_update(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        self.max_vfolder_count.update_dict(data, "max_vfolder_count")
        self.max_quota_scope_size.update_dict(data, "max_quota_scope_size")
        self.max_session_count_per_model_session.update_dict(
            data, "max_session_count_per_model_session"
        )
        self.max_customized_image_count.update_dict(data, "max_customized_image_count")
        return data


@dataclass
class ProjectResourcePolicyModifier(PartialModifier):
    max_vfolder_count: OptionalState[int]
    max_quota_scope_size: OptionalState[int]
    max_network_count: OptionalState[int]

    def fields_to_update(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        self.max_vfolder_count.update_dict(data, "max_vfolder_count")
        self.max_quota_scope_size.update_dict(data, "max_quota_scope_size")
        self.max_network_count.update_dict(data, "max_network_count")
        return data


@dataclass
class KeyPairResourcePolicyModifier(PartialModifier):
    default_for_unspecified: OptionalState[DefaultForUnspecified]
    total_resource_slots: OptionalState[ResourceSlot]
    max_session_lifetime: OptionalState[int]
    max_concurrent_sessions: OptionalState[int]
    max_pending_session_count: OptionalState[Optional[int]]
    max_pending_session_resource_slots: OptionalState[Optional[Any]]
    max_concurrent_sftp_sessions: OptionalState[int]
    max_containers_per_session: OptionalState[int]
    idle_timeout: OptionalState[int]
    allowed_vfolder_hosts: OptionalState[dict[str, Any]]

    def fields_to_update(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        self.default_for_unspecified.update_dict(data, "default_for_unspecified")
        self.total_resource_slots.update_dict(data, "total_resource_slots")
        self.max_session_lifetime.update_dict(data, "max_session_lifetime")
        self.max_concurrent_sessions.update_dict(data, "max_concurrent_sessions")
        self.max_pending_session_count.update_dict(data, "max_pending_session_count")
        self.max_pending_session_resource_slots.update_dict(
            data, "max_pending_session_resource_slots"
        )
        self.max_concurrent_sftp_sessions.update_dict(data, "max_concurrent_sftp_sessions")
        self.max_containers_per_session.update_dict(data, "max_containers_per_session")
        self.idle_timeout.update_dict(data, "idle_timeout")
        self.allowed_vfolder_hosts.update_dict(data, "allowed_vfolder_hosts")
        return data
