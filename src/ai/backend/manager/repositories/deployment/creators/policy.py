"""CreatorSpec for deployment policy creation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.manager.models.deployment_policy import (
    BlueGreenSpec,
    DeploymentPolicyRow,
    RollingUpdateSpec,
)
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class DeploymentPolicyCreatorSpec(CreatorSpec[DeploymentPolicyRow]):
    """CreatorSpec for deployment policy creation.

    Each deployment can have at most one deployment policy (1:1 relationship).
    The policy defines the deployment strategy and its configuration.
    """

    deployment_id: DeploymentID
    strategy: DeploymentStrategy
    strategy_spec: RollingUpdateSpec | BlueGreenSpec

    @classmethod
    def build_default(cls, deployment_id: DeploymentID) -> DeploymentPolicyCreatorSpec:
        """Create a default rolling deployment policy spec."""
        return cls(
            deployment_id=deployment_id,
            strategy=DeploymentStrategy.ROLLING,
            strategy_spec=RollingUpdateSpec(),
        )

    @override
    def build_row(self) -> DeploymentPolicyRow:
        return DeploymentPolicyRow(
            endpoint=self.deployment_id,
            strategy=self.strategy,
            strategy_spec=self.strategy_spec.model_dump(),
        )
