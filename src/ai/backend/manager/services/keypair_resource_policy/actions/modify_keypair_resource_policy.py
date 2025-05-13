from dataclasses import dataclass, field
from typing import Any, Optional, override

from ai.backend.common.types import DefaultForUnspecified, ResourceSlot
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.services.keypair_resource_policy.actions.base import (
    KeypairResourcePolicyAction,
)
from ai.backend.manager.types import OptionalState, PartialModifier, TriState


@dataclass
class KeyPairResourcePolicyModifier(PartialModifier):
    allowed_vfolder_hosts: OptionalState[dict[str, Any]] = field(default_factory=OptionalState.nop)
    default_for_unspecified: OptionalState[DefaultForUnspecified] = field(
        default_factory=OptionalState.nop
    )
    idle_timeout: OptionalState[int] = field(default_factory=OptionalState.nop)
    max_concurrent_sessions: OptionalState[int] = field(default_factory=OptionalState.nop)
    max_containers_per_session: OptionalState[int] = field(default_factory=OptionalState.nop)
    max_pending_session_count: TriState[int] = field(default_factory=TriState.nop)
    max_pending_session_resource_slots: TriState[dict[str, Any]] = field(
        default_factory=TriState.nop
    )
    max_quota_scope_size: OptionalState[int] = field(default_factory=OptionalState.nop)
    max_vfolder_count: OptionalState[int] = field(default_factory=OptionalState.nop)
    max_vfolder_size: OptionalState[int] = field(default_factory=OptionalState.nop)
    max_concurrent_sftp_sessions: OptionalState[int] = field(default_factory=OptionalState.nop)
    max_session_lifetime: OptionalState[int] = field(default_factory=OptionalState.nop)
    total_resource_slots: OptionalState[ResourceSlot] = field(default_factory=OptionalState.nop)

    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.allowed_vfolder_hosts.update_dict(to_update, "allowed_vfolder_hosts")
        self.default_for_unspecified.update_dict(to_update, "default_for_unspecified")
        self.idle_timeout.update_dict(to_update, "idle_timeout")
        self.max_concurrent_sessions.update_dict(to_update, "max_concurrent_sessions")
        self.max_containers_per_session.update_dict(to_update, "max_containers_per_session")
        self.max_pending_session_count.update_dict(to_update, "max_pending_session_count")
        self.max_pending_session_resource_slots.update_dict(
            to_update, "max_pending_session_resource_slots"
        )
        self.max_quota_scope_size.update_dict(to_update, "max_quota_scope_size")
        self.max_vfolder_count.update_dict(to_update, "max_vfolder_count")
        self.max_vfolder_size.update_dict(to_update, "max_vfolder_size")
        self.max_concurrent_sftp_sessions.update_dict(to_update, "max_concurrent_sftp_sessions")
        self.max_session_lifetime.update_dict(to_update, "max_session_lifetime")
        self.total_resource_slots.update_dict(to_update, "total_resource_slots")
        return to_update


@dataclass
class ModifyKeyPairResourcePolicyAction(KeypairResourcePolicyAction):
    name: str
    modifier: KeyPairResourcePolicyModifier

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "modify"


@dataclass
class ModifyKeyPairResourcePolicyActionResult(BaseActionResult):
    keypair_resource_policy: KeyPairResourcePolicyData

    @override
    def entity_id(self) -> Optional[str]:
        return self.keypair_resource_policy.name
