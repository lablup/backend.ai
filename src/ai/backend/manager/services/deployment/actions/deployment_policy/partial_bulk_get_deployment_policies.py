from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_policy import DeploymentPolicyID
from ai.backend.manager.actions.v2.field.ops import PartialBulkGetFieldOpsAction
from ai.backend.manager.data.deployment.types import DeploymentPolicyData
from ai.backend.manager.models.deployment_policy.queriers import BulkDeploymentPolicyQuerier
from ai.backend.manager.models.deployment_policy.row import DeploymentPolicyRow
from ai.backend.manager.services.deployment.actions.lookup_owner import (
    LookupBulkDeploymentPolicyOwnerAction,
)


@dataclass
class PartialBulkGetDeploymentPoliciesAction(
    PartialBulkGetFieldOpsAction[
        DeploymentPolicyID,
        DeploymentID,
        DeploymentPolicyRow,
        DeploymentPolicyData,
    ]
):
    """Read the deployment policies the caller named, answering for each one."""

    ids: Sequence[DeploymentPolicyID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_get_deployment_policies"

    @override
    def field_ids(self) -> Sequence[DeploymentPolicyID]:
        return tuple(self.ids)

    @override
    def to_owner_lookup_action(self) -> LookupBulkDeploymentPolicyOwnerAction:
        return LookupBulkDeploymentPolicyOwnerAction(policy_ids=self.ids)

    @override
    def to_querier(self) -> BulkDeploymentPolicyQuerier:
        return BulkDeploymentPolicyQuerier()

    @override
    def narrowed_to(self, field_ids: Sequence[DeploymentPolicyID]) -> Self:
        allowed = frozenset(field_ids)
        return replace(self, ids=[field_id for field_id in self.ids if field_id in allowed])
