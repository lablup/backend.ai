from dataclasses import dataclass, field
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.models.resource_policy import KeyPairResourcePolicyRow
from ai.backend.manager.services.keypair_resource_policy.base import KeypairResourcePolicyAction
from ai.backend.manager.types import OptionalState, TriState


# TODO: Add proper type hints for dict.
@dataclass
class CreateKeyPairResourcePolicyInputData:
    name: OptionalState[str] = field(default_factory=lambda: OptionalState.nop("name"))
    allowed_vfolder_hosts: OptionalState[dict[str, Any]] = field(
        default_factory=lambda: OptionalState.nop("allowed_vfolder_hosts")
    )
    default_for_unspecified: OptionalState[str] = field(
        default_factory=lambda: OptionalState.nop("default_for_unspecified")
    )
    idle_timeout: OptionalState[int] = field(
        default_factory=lambda: OptionalState.nop("idle_timeout")
    )
    max_concurrent_sessions: OptionalState[int] = field(
        default_factory=lambda: OptionalState.nop("max_concurrent_sessions")
    )
    max_containers_per_session: OptionalState[int] = field(
        default_factory=lambda: OptionalState.nop("max_containers_per_session")
    )
    max_pending_session_count: OptionalState[int] = field(
        default_factory=lambda: OptionalState.nop("max_pending_session_count")
    )
    max_pending_session_resource_slots: TriState[dict[str, Any]] = field(
        default_factory=lambda: TriState.nop("max_pending_session_resource_slots")
    )
    max_quota_scope_size: OptionalState[int] = field(
        default_factory=lambda: OptionalState.nop("max_quota_scope_size")
    )
    max_vfolder_count: OptionalState[int] = field(
        default_factory=lambda: OptionalState.nop("max_vfolder_count")
    )
    max_vfolder_size: OptionalState[int] = field(
        default_factory=lambda: OptionalState.nop("max_vfolder_size")
    )
    max_concurrent_sftp_sessions: OptionalState[int] = field(
        default_factory=lambda: OptionalState.nop("max_concurrent_sftp_sessions")
    )
    max_session_lifetime: OptionalState[int] = field(
        default_factory=lambda: OptionalState.nop("max_session_lifetime")
    )
    total_resource_slots: OptionalState[dict[str, Any]] = field(
        default_factory=lambda: OptionalState.nop("total_resource_slots")
    )

    def to_db_row(self) -> KeyPairResourcePolicyRow:
        policy_row = KeyPairResourcePolicyRow()

        self.name.set_attr(policy_row)
        self.allowed_vfolder_hosts.set_attr(policy_row)
        self.default_for_unspecified.set_attr(policy_row)
        self.idle_timeout.set_attr(policy_row)
        self.max_concurrent_sessions.set_attr(policy_row)
        self.max_containers_per_session.set_attr(policy_row)
        self.max_pending_session_count.set_attr(policy_row)
        self.max_pending_session_resource_slots.set_attr(policy_row)
        self.max_quota_scope_size.set_attr(policy_row)
        self.max_vfolder_count.set_attr(policy_row)
        self.max_vfolder_size.set_attr(policy_row)
        self.max_concurrent_sftp_sessions.set_attr(policy_row)
        self.max_session_lifetime.set_attr(policy_row)
        self.total_resource_slots.set_attr(policy_row)

        return policy_row


@dataclass
class CreateKeyPairResourcePolicyAction(KeypairResourcePolicyAction):
    props: CreateKeyPairResourcePolicyInputData

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "create_keypair_resource_policy"


@dataclass
class CreateKeyPairResourcePolicyActionResult(BaseActionResult):
    keypair_resource_policy: KeyPairResourcePolicyData

    @override
    def entity_id(self) -> Optional[str]:
        return self.keypair_resource_policy.name
