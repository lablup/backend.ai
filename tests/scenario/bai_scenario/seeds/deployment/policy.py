"""Write specs for a deployment policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.schema.deployment import IntOrPercent, RollingUpdateSpec
from ai.backend.manager.data.deployment.types import DeploymentInfo, DeploymentPolicyData
from ai.backend.manager.models.deployment_policy.upserters import DeploymentPolicyUpserter
from ai.backend.testutils.scenario_steps import Says
from bai_scenario.seeds.seeder import TestSeedFieldUpserter


@dataclass(frozen=True)
class TestSeedDeploymentPolicyOf(
    TestSeedFieldUpserter[DeploymentInfo, DeploymentPolicyData]
):
    """A rolling-update policy with a surge of one replica and nothing unavailable."""

    @override
    def kind(self) -> str:
        return Says("배포 정책 하나를 갖는다", english="has one deployment policy")

    @override
    def owner_id(self, owner: DeploymentInfo) -> DeploymentID:
        return DeploymentID(owner.id)

    @override
    def seed(self) -> DeploymentPolicyUpserter:
        return DeploymentPolicyUpserter(
            strategy=DeploymentStrategy.ROLLING,
            strategy_spec=RollingUpdateSpec(
                max_surge=IntOrPercent(count=1),
                max_unavailable=IntOrPercent(count=0),
            ),
        )
