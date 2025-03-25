from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.resource_policy import (
    UserResourcePolicyRow,
)
from ai.backend.manager.services.user_resource_policy.base import UserResourcePolicyAction


@dataclass
class DeleteUserResourcePolicyAction(UserResourcePolicyAction):
    name: str

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "delete_user_resource_policy"


@dataclass
class DeleteUserResourcePolicyActionResult(BaseActionResult):
    # TODO: 리턴 타입 만들 것.
    user_resource_policy: UserResourcePolicyRow

    @override
    def entity_id(self) -> Optional[str]:
        return self.user_resource_policy.name
