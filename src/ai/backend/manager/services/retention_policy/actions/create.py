from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.retention_policy import RETENTION_POLICY_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import CreateGlobalOpsAction
from ai.backend.manager.data.retention.types import RetentionPolicyData
from ai.backend.manager.models.retention.creators import RetentionPolicyCreator
from ai.backend.manager.models.retention.row import RetentionPolicyRow


@dataclass
class CreateRetentionPolicyAction(CreateGlobalOpsAction[RetentionPolicyRow, RetentionPolicyData]):
    """Register the cleanup settings for one retention category."""

    creator: RetentionPolicyCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RETENTION_POLICY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_retention_policy"

    @override
    def to_creator(self) -> RetentionPolicyCreator:
        return self.creator
