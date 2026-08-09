from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.retention_policy import RETENTION_POLICY_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.identifier.retention_policy import RetentionPolicyID
from ai.backend.manager.actions.v2.ops.base import PurgeGlobalOpsAction
from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.models.retention.purgers import RetentionPolicyPurger
from ai.backend.manager.models.retention.row import RetentionPolicyRow


@dataclass
class DeleteRetentionPolicyAction(PurgeGlobalOpsAction[RetentionPolicyRow, RetentionPolicyData]):
    """Drop one category's policy, falling the category back to its built-in default.

    Purge-shaped: a retention policy carries no lifecycle column, so removing one has
    always been the row leaving the table. The separate ``purge`` path stays because
    both are exposed; the two differ only in the name they record.
    """

    id: RetentionPolicyID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RETENTION_POLICY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_retention_policy"

    @override
    def to_purger(self) -> RetentionPolicyPurger:
        return RetentionPolicyPurger(policy_id=self.id)
