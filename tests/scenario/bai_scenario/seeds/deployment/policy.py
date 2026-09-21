"""Write spec for the policy row a deployment carries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.schema.deployment import IntOrPercent, RollingUpdateSpec
from ai.backend.manager.data.deployment.types import DeploymentInfo, DeploymentPolicyData
from ai.backend.manager.models.deployment_policy.creators import DeploymentPolicyCreator
from bai_scenario.seeds.seeder import SeedField


@dataclass(frozen=True)
class SeedPolicyOf(SeedField[DeploymentInfo, DeploymentPolicyData]):
    """The rolling policy of the deployment; a deployment carries at most one.

    The budgets are absolute counts so a table can state the row it expects back.
    """

    max_surge: int = 2
    max_unavailable: int = 1

    @override
    def kind(self) -> str:
        return (
            f"순차 배포 정책을 갖는다 — 한 번에 {self.max_surge}개까지 더 띄우고 "
            f"{self.max_unavailable}개까지 내린다"
        )

    @override
    def owner_id(self, owner: DeploymentInfo) -> DeploymentID:
        return DeploymentID(owner.id)

    @override
    def seed(self) -> DeploymentPolicyCreator:
        return DeploymentPolicyCreator(
            strategy=DeploymentStrategy.ROLLING,
            strategy_spec=RollingUpdateSpec(
                max_surge=IntOrPercent(count=self.max_surge),
                max_unavailable=IntOrPercent(count=self.max_unavailable),
            ),
        )
