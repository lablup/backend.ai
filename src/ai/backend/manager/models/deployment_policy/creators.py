"""Creator specs for the deployment_policies table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_policy import DeploymentPolicyID
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.schema.deployment import BlueGreenSpec, RollingUpdateSpec
from ai.backend.manager.data.deployment.types import DeploymentPolicyData
from ai.backend.manager.models.deployment_policy.row import DeploymentPolicyRow
from ai.backend.manager.models.specs.creator import FieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class DeploymentPolicyCreator(
    FieldCreator[DeploymentID, DeploymentPolicyRow, DeploymentPolicyData]
):
    """Writes the deployment's strategy row; a deployment has at most one."""

    strategy: DeploymentStrategy
    strategy_spec: RollingUpdateSpec | BlueGreenSpec

    @classmethod
    def build_default(cls) -> DeploymentPolicyCreator:
        """The rolling strategy every deployment starts with."""
        return cls(strategy=DeploymentStrategy.ROLLING, strategy_spec=RollingUpdateSpec())

    @override
    def field_id(self, row: DeploymentPolicyRow) -> DeploymentPolicyID:
        return DeploymentPolicyID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: DeploymentID) -> DeploymentPolicyRow:
        return DeploymentPolicyRow(
            endpoint=owner_id,
            strategy=self.strategy,
            strategy_spec=self.strategy_spec.model_dump(),
        )

    @override
    def to_data(self, row: DeploymentPolicyRow) -> DeploymentPolicyData:
        return row.to_data()
