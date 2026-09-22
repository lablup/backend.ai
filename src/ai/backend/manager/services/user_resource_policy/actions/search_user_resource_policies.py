from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    UserResourcePolicyEntityType,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import ScopedSearchOpsAction
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow


@dataclass(frozen=True)
class SearchUserResourcePoliciesAction(
    ScopedSearchOpsAction[UserResourcePolicyRow, UserResourcePolicyData]
):
    """Page through the user resource policies the named scopes reach, combined with
    OR.

    Which users those are, is the caller's business: the scopes are an argument.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return UserResourcePolicyEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_user_resource_policies"
