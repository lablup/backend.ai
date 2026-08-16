from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.retention_policy import (
    RetentionPolicyID,
)
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PurgeEntityOpsAction
from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.models.retention.purgers import RetentionPolicyPurger
from ai.backend.manager.models.retention.row import RetentionPolicyRow


@dataclass
class DeleteRetentionPolicyAction(PurgeEntityOpsAction[RetentionPolicyRow, RetentionPolicyData]):
    """Drop one category's policy, falling the category back to its built-in default.

    Keeps the ``Delete`` name although it purges: :class:`PurgeRetentionPolicyAction`
    holds the other one and both are exposed, so collapsing them is an API change.
    """

    id: RetentionPolicyID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_retention_policy"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.to_purger().entity_id()

    @override
    def to_purger(self) -> RetentionPolicyPurger:
        return RetentionPolicyPurger(policy_id=self.id)
