from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import BulkGetOwnedFieldOpsAction
from ai.backend.manager.data.deployment.types import DeploymentPolicyData
from ai.backend.manager.models.deployment_policy.queriers import (
    DeploymentPolicyByDeploymentQuerier,
)
from ai.backend.manager.models.deployment_policy.row import DeploymentPolicyRow


@dataclass
class BulkGetDeploymentPoliciesAction(
    BulkGetOwnedFieldOpsAction[DeploymentID, DeploymentPolicyRow, DeploymentPolicyData]
):
    """Read the policy each named deployment carries."""

    deployment_ids: Sequence[DeploymentID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_deployment_policies"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.deployment_ids)

    @override
    def owner_ids(self) -> Sequence[DeploymentID]:
        return tuple(self.deployment_ids)

    @override
    def to_querier(self) -> DeploymentPolicyByDeploymentQuerier:
        return DeploymentPolicyByDeploymentQuerier()
