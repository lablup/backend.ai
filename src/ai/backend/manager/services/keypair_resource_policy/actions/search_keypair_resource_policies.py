from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_policy import (
    KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow
from ai.backend.manager.repositories.keypair_resource_policy.searchers import (
    KeyPairResourcePolicySearcher,
)


@dataclass
class SearchKeypairResourcePoliciesAction(
    SearchGlobalOpsAction[KeyPairResourcePolicyRow, KeyPairResourcePolicyData]
):
    """Page through the keypair resource policy catalog."""

    searcher: KeyPairResourcePolicySearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return KEYPAIR_RESOURCE_POLICY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "admin_search_keypair_resource_policies"

    @override
    def to_searcher(self) -> KeyPairResourcePolicySearcher:
        return self.searcher
