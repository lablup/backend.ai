"""CreatorSpec for deployment policy creation."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from typing_extensions import override

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.manager.models.deployment_policy import (
    BlueGreenSpec,
    DeploymentPolicyRow,
    RollingUpdateSpec,
)
from ai.backend.manager.repositories.base import CreatorSpec


@dataclass
class DeploymentPolicyCreatorSpec(CreatorSpec[DeploymentPolicyRow]):
    """CreatorSpec for deployment policy creation.

    Each endpoint can have at most one deployment policy (1:1 relationship).
    The policy defines the deployment strategy and its configuration.
    """

    endpoint_id: uuid.UUID
    strategy: DeploymentStrategy
    strategy_spec: RollingUpdateSpec | BlueGreenSpec
    rollback_on_failure: bool

    @override
    def build_row(self) -> DeploymentPolicyRow:
        return DeploymentPolicyRow(
            endpoint=self.endpoint_id,
            strategy=self.strategy,
            strategy_spec=self.strategy_spec.model_dump(),
            rollback_on_failure=self.rollback_on_failure,
        )
