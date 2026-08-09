from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.retention_policy import RETENTION_POLICY_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.repositories.retention_policy.searchers import RetentionPolicySearcher


@dataclass
class SearchRetentionPoliciesAction(SearchGlobalOpsAction[RetentionPolicyRow, RetentionPolicyData]):
    """Page through the retention policy catalog."""

    searcher: RetentionPolicySearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RETENTION_POLICY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_retention_policies"

    @override
    def to_searcher(self) -> RetentionPolicySearcher:
        return self.searcher
