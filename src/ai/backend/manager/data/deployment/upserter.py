from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.manager.models.deployment_policy import BlueGreenSpec, RollingUpdateSpec


@dataclass
class DeploymentPolicyUpserter:
    """Domain input for upserting a deployment policy."""

    deployment_id: UUID
    strategy: DeploymentStrategy
    strategy_spec: RollingUpdateSpec | BlueGreenSpec
    rollback_on_failure: bool = False
