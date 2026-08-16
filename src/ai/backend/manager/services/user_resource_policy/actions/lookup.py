from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.resource_policy import (
    USER_RESOURCE_POLICY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.actions.v2.ops.base import LookupEntityOpsAction
from ai.backend.manager.data.resource.types import UserResourcePolicyData
from ai.backend.manager.models.resource_policy.row import UserResourcePolicyRow
from ai.backend.manager.repositories.user_resource_policy.lookups import (
    UserResourcePolicyLookup,
)


@dataclass(frozen=True)
class UserResourcePolicyUserKey(LookupKey):
    """The user a caller passes instead of the policy's name."""

    user_id: UserID

    @override
    def kind(self) -> str:
        return "user_resource_policy_user"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"user_id": str(self.user_id)}


@dataclass
class LookupUserResourcePolicyAction(
    LookupEntityOpsAction[UserResourcePolicyRow, UserResourcePolicyData]
):
    """Resolve a user into the policy they are subject to."""

    user_id: UserID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return USER_RESOURCE_POLICY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_user_resource_policy"

    @override
    def lookup_key(self) -> UserResourcePolicyUserKey:
        return UserResourcePolicyUserKey(user_id=self.user_id)

    @override
    def to_lookup(self) -> UserResourcePolicyLookup:
        return UserResourcePolicyLookup(user_id=self.user_id)
