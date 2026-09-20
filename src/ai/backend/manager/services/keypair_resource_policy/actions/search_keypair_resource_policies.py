from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    KeyPairResourcePolicyEntityType,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import ScopedSearchOpsAction
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow


@dataclass(frozen=True)
class SearchKeypairResourcePoliciesAction(
    ScopedSearchOpsAction[KeyPairResourcePolicyRow, KeyPairResourcePolicyData]
):
    """Page through the keypair resource policies the named scopes reach, combined
    with OR.

    Which users those are, is the caller's business: the scopes are an argument.
    """

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return KeyPairResourcePolicyEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_keypair_resource_policies"
