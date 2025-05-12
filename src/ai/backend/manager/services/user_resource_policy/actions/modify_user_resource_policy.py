from dataclasses import dataclass, field
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.services.user_resource_policy.actions.base import UserResourcePolicyAction
from ai.backend.manager.types import OptionalState, PartialModifier


@dataclass
class UserResourcePolicyModifier(PartialModifier):
    max_vfolder_count: OptionalState[int] = field(default_factory=OptionalState.nop)
    max_quota_scope_size: OptionalState[int] = field(default_factory=OptionalState.nop)
    max_session_count_per_model_session: OptionalState[int] = field(
        default_factory=OptionalState.nop
    )
    max_customized_image_count: OptionalState[int] = field(default_factory=OptionalState.nop)

    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.max_vfolder_count.update_dict(to_update, "max_vfolder_count")
        self.max_quota_scope_size.update_dict(to_update, "max_quota_scope_size")
        self.max_session_count_per_model_session.update_dict(
            to_update, "max_session_count_per_model_session"
        )
        self.max_customized_image_count.update_dict(to_update, "max_customized_image_count")
        return to_update


@dataclass
class ModifyUserResourcePolicyAction(UserResourcePolicyAction):
    name: str
    modifier: UserResourcePolicyModifier

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "modify"


@dataclass
class ModifyUserResourcePolicyActionResult(BaseActionResult):
    user_resource_policy: UserResourcePolicyData

    @override
    def entity_id(self) -> Optional[str]:
        return self.user_resource_policy.name
