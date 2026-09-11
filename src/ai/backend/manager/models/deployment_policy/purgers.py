"""Purge specs for the deployment_policies table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.deployment_policy import DeploymentPolicyID
from ai.backend.manager.data.deployment.types import DeploymentPolicyData
from ai.backend.manager.models.deployment_policy.row import DeploymentPolicyRow
from ai.backend.manager.models.specs.purger import FieldPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class DeploymentPolicyPurger(FieldPurger[DeploymentPolicyRow, DeploymentPolicyData]):
    """Removes the strategy row of one deployment."""

    policy_id: DeploymentPolicyID

    @override
    def row_class(self) -> type[DeploymentPolicyRow]:
        return DeploymentPolicyRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return DeploymentPolicyRow.id

    @override
    def target_id_value(self) -> DeploymentPolicyID:
        return self.policy_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: DeploymentPolicyRow) -> DeploymentPolicyData:
        return row.to_data()
