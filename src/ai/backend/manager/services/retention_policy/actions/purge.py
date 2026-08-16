from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PurgeEntityOpsAction
from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.models.retention.purgers import RetentionPolicyPurger
from ai.backend.manager.models.retention.row import RetentionPolicyRow


@dataclass
class PurgeRetentionPolicyAction(PurgeEntityOpsAction[RetentionPolicyRow, RetentionPolicyData]):
    """Remove a retention policy row from the catalog."""

    purger: RetentionPolicyPurger

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_retention_policy"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.to_purger().entity_id()

    @override
    def to_purger(self) -> RetentionPolicyPurger:
        return self.purger
