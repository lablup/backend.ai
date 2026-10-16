from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.auto_scaling_rule import AutoScalingRuleID
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.field.bulk_base import BasePartialBulkFieldAction
from ai.backend.manager.data.deployment.scale_modifier import ModelDeploymentAutoScalingRuleModifier
from ai.backend.manager.services.deployment.actions.lookup_owner import (
    LookupBulkAutoScalingRuleOwnerAction,
)


@dataclass
class PartialBulkUpdateAutoScalingRulesAction(
    BasePartialBulkFieldAction[AutoScalingRuleID, DeploymentID]
):
    """Update the named auto-scaling rules, each authorized against the deployment it belongs to."""

    modifiers: Mapping[AutoScalingRuleID, ModelDeploymentAutoScalingRuleModifier]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_update_auto_scaling_rules"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def field_ids(self) -> Sequence[AutoScalingRuleID]:
        return tuple(self.modifiers)

    @override
    def to_owner_lookup_action(self) -> LookupBulkAutoScalingRuleOwnerAction:
        return LookupBulkAutoScalingRuleOwnerAction(rule_ids=tuple(self.modifiers))

    @override
    def narrowed_to(self, field_ids: Sequence[AutoScalingRuleID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(
            self,
            modifiers={
                rule_id: modifier
                for rule_id, modifier in self.modifiers.items()
                if rule_id in allowed
            },
        )
