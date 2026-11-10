from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.auto_scaling_rule import AutoScalingRuleID
from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.manager.actions.v2.field.ops import PartialBulkGetFieldOpsAction
from ai.backend.manager.data.deployment.types import ModelDeploymentAutoScalingRuleData
from ai.backend.manager.models.endpoint.queriers import BulkAutoScalingRuleQuerier
from ai.backend.manager.models.endpoint.row import EndpointAutoScalingRuleRow
from ai.backend.manager.services.deployment.actions.lookup_owner import (
    LookupBulkAutoScalingRuleOwnerAction,
)


@dataclass
class BulkGetAutoScalingRulesAction(
    PartialBulkGetFieldOpsAction[
        AutoScalingRuleID,
        DeploymentID,
        EndpointAutoScalingRuleRow,
        ModelDeploymentAutoScalingRuleData,
    ]
):
    """Read the auto-scaling rules the caller named, answering for each one."""

    ids: Sequence[AutoScalingRuleID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_auto_scaling_rules"

    @override
    def field_ids(self) -> Sequence[AutoScalingRuleID]:
        return tuple(self.ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkAutoScalingRuleOwnerAction:
        return LookupBulkAutoScalingRuleOwnerAction(rule_ids=self.ids)

    @override
    def to_querier(self) -> BulkAutoScalingRuleQuerier:
        return BulkAutoScalingRuleQuerier()

    @override
    def narrowed_to(self, field_ids: Sequence[AutoScalingRuleID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(self, ids=[field_id for field_id in self.ids if field_id in allowed])
