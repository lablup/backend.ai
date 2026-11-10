from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdateSingleEntityOpsAction
from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.models.retention.row import RetentionPolicyRow
from ai.backend.manager.models.retention.updaters import RetentionPolicyUpdater


@dataclass
class UpdateRetentionPolicyAction(
    UpdateSingleEntityOpsAction[RetentionPolicyRow, RetentionPolicyData]
):
    """Retune one category's cleanup settings; the category itself stays the key."""

    updater: RetentionPolicyUpdater

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_retention_policy"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.policy_id

    @override
    def to_updater(self) -> RetentionPolicyUpdater:
        return self.updater
