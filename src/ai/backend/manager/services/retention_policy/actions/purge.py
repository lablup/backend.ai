from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.retention_policy import RETENTION_POLICY_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.identifier.entity import EntityID
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
    def entity_type(cls) -> EntityType:
        return RETENTION_POLICY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_retention_policy"

    @override
    def entity_id(self) -> EntityID:
        return self.to_purger().entity_id()

    @override
    def to_purger(self) -> RetentionPolicyPurger:
        return self.purger
