from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.services.user_resource_policy.actions.base import UserResourcePolicyAction


@dataclass
class CreateUserResourcePolicyInputData:
    max_vfolder_count: Optional[int]
    max_quota_scope_size: Optional[int]
    max_session_count_per_model_session: Optional[int]
    max_vfolder_size: Optional[int]
    max_customized_image_count: Optional[int]


@dataclass
class CreateUserResourcePolicyAction(UserResourcePolicyAction):
    name: str
    props: CreateUserResourcePolicyInputData

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "create"


@dataclass
class CreateUserResourcePolicyActionResult(BaseActionResult):
    user_resource_policy: UserResourcePolicyData

    @override
    def entity_id(self) -> Optional[str]:
        return self.user_resource_policy.name
