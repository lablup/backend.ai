from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.retention_policy import (
    RetentionPolicyID,
)
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import GetSingleEntityOpsAction
from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.repositories.retention_policy.queriers import RetentionPolicyQuerier


@dataclass
class GetRetentionPolicyAction(GetSingleEntityOpsAction[RetentionPolicyRow, RetentionPolicyData]):
    """Read one retention policy."""

    policy_id: RetentionPolicyID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_retention_policy"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.policy_id

    @override
    def to_querier(self) -> RetentionPolicyQuerier:
        return RetentionPolicyQuerier(policy_id=self.policy_id)
