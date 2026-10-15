from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.auto_scaling_rule import AutoScalingRuleID
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.field.bulk_base import BasePartialBulkFieldAction
from ai.backend.manager.services.deployment.actions.lookup_owner import (
    LookupBulkAutoScalingRuleOwnerAction,
)


@dataclass
class PartialBulkPurgeAutoScalingRulesAction(
    BasePartialBulkFieldAction[AutoScalingRuleID, DeploymentID]
):
    """Remove the named auto-scaling rules, each authorized against the deployment it belongs to.

    Declares ``PURGE``: removing the rows asks for the deployment's hard-delete right.
    """

    rule_ids: Sequence[AutoScalingRuleID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_purge_auto_scaling_rules"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.PURGE

    @override
    def field_ids(self) -> Sequence[AutoScalingRuleID]:
        return tuple(self.rule_ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkAutoScalingRuleOwnerAction:
        return LookupBulkAutoScalingRuleOwnerAction(rule_ids=self.rule_ids)

    @override
    def narrowed_to(self, field_ids: Sequence[AutoScalingRuleID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(self, rule_ids=[rule_id for rule_id in self.rule_ids if rule_id in allowed])
