from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.resource_policy import (
    UserResourcePolicyRow,
)
from ai.backend.manager.services.user_resource_policy.base import UserResourcePolicyAction


@dataclass
class ModifyUserResourcePolicyInput:
    max_vfolder_count: Optional[int] = None
    max_quota_scope_size: Optional[int] = None
    max_session_count_per_model_session: Optional[int] = None
    max_customized_image_count: Optional[int] = None


@dataclass
class ModifyUserResourcePolicyAction(UserResourcePolicyAction):
    name: str
    props: ModifyUserResourcePolicyInput

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "modify_user_resource_policy"


@dataclass
class ModifyUserResourcePolicyActionResult(BaseActionResult):
    # TODO: 리턴 타입 만들 것.
    user_resource_policy: UserResourcePolicyRow

    @override
    def entity_id(self) -> Optional[str]:
        return self.user_resource_policy.name
