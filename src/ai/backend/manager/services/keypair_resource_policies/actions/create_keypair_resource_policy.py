from dataclasses import dataclass, field
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.resource_policy import KeyPairResourcePolicyRow
from ai.backend.manager.services.keypair_resource_policies.base import KeypairResourcePolicyAction


@dataclass
class CreateKeyPairResourcePolicyInput:
    # TODO: 타입 주기.
    allowed_vfolder_hosts: dict[str, Any]
    default_for_unspecified: str
    idle_timeout: int
    max_concurrent_sessions: int
    max_containers_per_session: int
    max_pending_session_count: int
    # TODO: 타입 주기.
    max_pending_session_resource_slots: dict[str, Any]
    max_quota_scope_size: int
    max_vfolder_count: int
    max_vfolder_size: int
    max_concurrent_sftp_sessions: int = 1
    max_session_lifetime: int = 0
    # TODO: 타입 주기. (ResourceSlot)
    total_resource_slots: dict[str, Any] = field(default_factory=dict)


@dataclass
class CreateKeyPairResourcePolicyAction(KeypairResourcePolicyAction):
    name: str
    props: CreateKeyPairResourcePolicyInput

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "create_keypair_resource_policy"


@dataclass
class CreateKeyPairResourcePolicyActionResult(BaseActionResult):
    # TODO: 리턴 타입 만들 것.
    keypair_resource_policy: KeyPairResourcePolicyRow

    @override
    def entity_id(self) -> Optional[str]:
        return self.keypair_resource_policy.name
