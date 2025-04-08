from dataclasses import dataclass, field
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.services.user_resource_policy.actions.base import UserResourcePolicyAction
from ai.backend.manager.types import OptionalState


@dataclass
class ModifyUserResourcePolicyInputData:
    max_vfolder_count: OptionalState[int] = field(
        default_factory=lambda: OptionalState.nop("max_vfolder_count")
    )
    max_quota_scope_size: OptionalState[int] = field(
        default_factory=lambda: OptionalState.nop("max_quota_scope_size")
    )
    max_session_count_per_model_session: OptionalState[int] = field(
        default_factory=lambda: OptionalState.nop("max_session_count_per_model_session")
    )
    max_customized_image_count: OptionalState[int] = field(
        default_factory=lambda: OptionalState.nop("max_customized_image_count")
    )

    def set_attr(self, obj: Any) -> None:
        self.max_vfolder_count.set_attr(obj)
        self.max_quota_scope_size.set_attr(obj)
        self.max_session_count_per_model_session.set_attr(obj)
        self.max_customized_image_count.set_attr(obj)


@dataclass
class ModifyUserResourcePolicyAction(UserResourcePolicyAction):
    name: str
    props: ModifyUserResourcePolicyInputData

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "modify"


@dataclass
class ModifyUserResourcePolicyActionResult(BaseActionResult):
    user_resource_policy: UserResourcePolicyData

    @override
    def entity_id(self) -> Optional[str]:
        return self.user_resource_policy.name
