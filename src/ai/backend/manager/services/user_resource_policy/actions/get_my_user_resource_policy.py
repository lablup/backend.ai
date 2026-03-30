from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.services.user_resource_policy.actions.base import (
    UserResourcePolicyAction,
)


@dataclass
class GetMyUserResourcePolicyAction(UserResourcePolicyAction):
    user_id: UUID

    @override
    def entity_id(self) -> str | None:
        return str(self.user_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetMyUserResourcePolicyActionResult(BaseActionResult):
    data: UserResourcePolicyData

    @override
    def entity_id(self) -> str | None:
        return self.data.name
