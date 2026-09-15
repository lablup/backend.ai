from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override
from uuid import UUID

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.bulk.base import BasePartialBulkAction


@dataclass
class BulkDeleteAutoScalingRulesAction(BasePartialBulkAction):
    """Delete the named auto-scaling rules, answered for by the deployment each belongs to."""

    rule_deployments: Mapping[UUID, DeploymentID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_delete_auto_scaling_rules"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(dict.fromkeys(self.rule_deployments.values()))

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self,
            rule_deployments={
                rule_id: deployment_id
                for rule_id, deployment_id in self.rule_deployments.items()
                if deployment_id in allowed
            },
        )
