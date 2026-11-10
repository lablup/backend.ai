from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.retention_policy import RetentionPolicyEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.models.retention.row import RetentionPolicyRow


@dataclass(frozen=True)
class SearchRetentionPoliciesAction(
    GlobalSearcherOpsAction[RetentionPolicyRow, RetentionPolicyData]
):
    """Page through the retention policy catalog."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RetentionPolicyEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_retention_policies"
