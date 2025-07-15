from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from ai.backend.common.types import DefaultForUnspecified, ResourceSlot
from ai.backend.manager.data.utils import OptionalState, PartialModifier


@dataclass
class UserResourcePolicyModifier(PartialModifier):
    max_vfolder_count: OptionalState[int]
    max_quota_scope_size: OptionalState[int]
    max_session_count_per_model_session: OptionalState[int]
    max_customized_image_count: OptionalState[int]

    def fields_to_update(self) -> dict[str, Any]:
        data = {}
        if self.max_vfolder_count.is_set:
            data["max_vfolder_count"] = self.max_vfolder_count.value
        if self.max_quota_scope_size.is_set:
            data["max_quota_scope_size"] = self.max_quota_scope_size.value
        if self.max_session_count_per_model_session.is_set:
            data["max_session_count_per_model_session"] = self.max_session_count_per_model_session.value
        if self.max_customized_image_count.is_set:
            data["max_customized_image_count"] = self.max_customized_image_count.value
        return data


@dataclass
class ProjectResourcePolicyModifier(PartialModifier):
    max_vfolder_count: OptionalState[int]
    max_quota_scope_size: OptionalState[int]
    max_network_count: OptionalState[int]

    def fields_to_update(self) -> dict[str, Any]:
        data = {}
        if self.max_vfolder_count.is_set:
            data["max_vfolder_count"] = self.max_vfolder_count.value
        if self.max_quota_scope_size.is_set:
            data["max_quota_scope_size"] = self.max_quota_scope_size.value
        if self.max_network_count.is_set:
            data["max_network_count"] = self.max_network_count.value
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
        data = {}
        if self.default_for_unspecified.is_set:
            data["default_for_unspecified"] = self.default_for_unspecified.value
        if self.total_resource_slots.is_set:
            data["total_resource_slots"] = self.total_resource_slots.value
        if self.max_session_lifetime.is_set:
            data["max_session_lifetime"] = self.max_session_lifetime.value
        if self.max_concurrent_sessions.is_set:
            data["max_concurrent_sessions"] = self.max_concurrent_sessions.value
        if self.max_pending_session_count.is_set:
            data["max_pending_session_count"] = self.max_pending_session_count.value
        if self.max_pending_session_resource_slots.is_set:
            data["max_pending_session_resource_slots"] = self.max_pending_session_resource_slots.value
        if self.max_concurrent_sftp_sessions.is_set:
            data["max_concurrent_sftp_sessions"] = self.max_concurrent_sftp_sessions.value
        if self.max_containers_per_session.is_set:
            data["max_containers_per_session"] = self.max_containers_per_session.value
        if self.idle_timeout.is_set:
            data["idle_timeout"] = self.idle_timeout.value
        if self.allowed_vfolder_hosts.is_set:
            data["allowed_vfolder_hosts"] = self.allowed_vfolder_hosts.value
        return data