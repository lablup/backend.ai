from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.services.keypair_resource_policy.actions.base import (
    KeypairResourcePolicyAction,
)


# TODO: Add proper type hints for dict.
@dataclass
class CreateKeyPairResourcePolicyInputData:
    name: Optional[str]
    allowed_vfolder_hosts: Optional[dict[str, Any]]
    default_for_unspecified: Optional[str]
    idle_timeout: Optional[int]
    max_concurrent_sessions: Optional[int]
    max_containers_per_session: Optional[int]
    max_pending_session_count: Optional[int]
    max_pending_session_resource_slots: Optional[dict[str, Any]]
    max_quota_scope_size: Optional[int]
    max_vfolder_count: Optional[int]
    max_vfolder_size: Optional[int]
    max_concurrent_sftp_sessions: Optional[int]
    max_session_lifetime: Optional[int]
    total_resource_slots: Optional[ResourceSlot]


@dataclass
class CreateKeyPairResourcePolicyAction(KeypairResourcePolicyAction):
    props: CreateKeyPairResourcePolicyInputData

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "create"


@dataclass
class CreateKeyPairResourcePolicyActionResult(BaseActionResult):
    keypair_resource_policy: KeyPairResourcePolicyData

    @override
    def entity_id(self) -> Optional[str]:
        return self.keypair_resource_policy.name
