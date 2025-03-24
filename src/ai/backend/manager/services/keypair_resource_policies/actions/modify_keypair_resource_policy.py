from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.resource_policy import KeyPairResourcePolicyRow
from ai.backend.manager.services.keypair_resource_policies.base import KeypairResourcePolicyAction


@dataclass
class ModifyKeyPairResourcePolicyInput:
    allowed_vfolder_hosts: Optional[dict[str, Any]] = None
    default_for_unspecified: Optional[str] = None
    idle_timeout: Optional[int] = None
    max_containers_per_session: Optional[int] = None
    max_concurrent_sessions: Optional[int] = None
    max_concurrent_sftp_sessions: Optional[int] = None
    max_pending_session_count: Optional[int] = None
    max_pending_session_resource_slots: Optional[dict[str, Any]] = None
    max_quota_scope_size: Optional[int] = None
    max_session_lifetime: Optional[int] = None
    max_vfolder_count: Optional[int] = None
    max_vfolder_size: Optional[int] = None
    total_resource_slots: Optional[dict[str, Any]] = None


@dataclass
class ModifyKeyPairResourcePolicyAction(KeypairResourcePolicyAction):
    name: str
    props: ModifyKeyPairResourcePolicyInput

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "modify_keypair_resource_policy"


@dataclass
class ModifyKeyPairResourcePolicyActionResult(BaseActionResult):
    # TODO: 리턴 타입 만들 것.
    keypair_resource_policy: KeyPairResourcePolicyRow

    @override
    def entity_id(self) -> Optional[str]:
        return self.keypair_resource_policy.name
