from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.retention_policy import RETENTION_POLICY_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import UpdateGlobalOpsAction
from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.repositories.retention_policy.updaters import RetentionPolicyUpdater


@dataclass
class UpdateRetentionPolicyAction(UpdateGlobalOpsAction[RetentionPolicyRow, RetentionPolicyData]):
    """Retune one category's cleanup settings; the category itself stays the key."""

    updater: RetentionPolicyUpdater

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RETENTION_POLICY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_retention_policy"

    @override
    def to_updater(self) -> RetentionPolicyUpdater:
        return self.updater
