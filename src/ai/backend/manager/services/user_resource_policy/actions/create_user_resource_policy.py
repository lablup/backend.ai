from dataclasses import dataclass, field
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.resource_policy import (
    UserResourcePolicyRow,
)
from ai.backend.manager.services.user_resource_policy.base import UserResourcePolicyAction
from ai.backend.manager.types import OptionalState


@dataclass
class CreateUserResourcePolicyInputData:
    max_vfolder_count: OptionalState[int] = field(
        default_factory=lambda: OptionalState.nop("max_vfolder_count")
    )
    max_quota_scope_size: OptionalState[int] = field(
        default_factory=lambda: OptionalState.nop("max_quota_scope_size")
    )
    max_session_count_per_model_session: OptionalState[int] = field(
        default_factory=lambda: OptionalState.nop("max_session_count_per_model_session")
    )
    max_vfolder_size: OptionalState[int] = field(
        default_factory=lambda: OptionalState.nop("max_vfolder_size")
    )
    max_customized_image_count: OptionalState[int] = field(
        default_factory=lambda: OptionalState.nop("max_customized_image_count")
    )

    def to_db_row(self, name: str) -> UserResourcePolicyRow:
        # TODO: Improve this,
        policy_row = UserResourcePolicyRow(
            name,
            0,
            0,
            0,
            0,
        )

        self.max_vfolder_count.set_attr(policy_row)
        self.max_quota_scope_size.set_attr(policy_row)
        self.max_session_count_per_model_session.set_attr(policy_row)
        self.max_vfolder_size.set_attr(policy_row)
        self.max_customized_image_count.set_attr(policy_row)

        return policy_row


@dataclass
class CreateUserResourcePolicyAction(UserResourcePolicyAction):
    name: str
    props: CreateUserResourcePolicyInputData

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "create_user_resource_policy"


@dataclass
class CreateUserResourcePolicyActionResult(BaseActionResult):
    user_resource_policy: UserResourcePolicyData

    @override
    def entity_id(self) -> Optional[str]:
        return self.user_resource_policy.name
