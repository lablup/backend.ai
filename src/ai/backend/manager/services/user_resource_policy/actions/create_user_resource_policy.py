from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.services.user_resource_policy.actions.base import UserResourcePolicyAction
from ai.backend.manager.types import Creator


@dataclass
class UserResourcePolicyCreator(Creator):
    name: str
    max_vfolder_count: Optional[int]
    max_quota_scope_size: Optional[int]
    max_session_count_per_model_session: Optional[int]
    max_vfolder_size: Optional[int]
    max_customized_image_count: Optional[int]

    def fields_to_store(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "max_vfolder_count": self.max_vfolder_count,
            "max_quota_scope_size": self.max_quota_scope_size,
            "max_session_count_per_model_session": self.max_session_count_per_model_session,
            # "max_vfolder_size": self.max_vfolder_size, # Deprecated
            "max_customized_image_count": self.max_customized_image_count,
        }


@dataclass
class CreateUserResourcePolicyAction(UserResourcePolicyAction):
    creator: UserResourcePolicyCreator

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
