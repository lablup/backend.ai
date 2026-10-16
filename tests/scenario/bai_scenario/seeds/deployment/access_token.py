"""Write specs for an access token of a deployment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    ModelDeploymentAccessTokenData,
)
from ai.backend.manager.models.endpoint.creators import EndpointTokenCreator
from bai_scenario.seeds.seeder import TestSeedFieldCreator


@dataclass(frozen=True)
class TestSeedAccessTokenOf(TestSeedFieldCreator[DeploymentInfo, ModelDeploymentAccessTokenData]):
    """A token granting access to the deployment, with no expiry.

    The domain, project and owner are values earlier rows answered. The token string is
    a placeholder: nothing here presents it to a worker.
    """

    domain: str
    project_id: ProjectID
    session_owner_id: UserID
    token: str = "scenario-token"

    @override
    def kind(self) -> str:
        return "접근 토큰 하나를 갖는다"

    @override
    def owner_id(self, owner: DeploymentInfo) -> DeploymentID:
        return DeploymentID(owner.id)

    @override
    def seed(self) -> EndpointTokenCreator:
        return EndpointTokenCreator(
            domain=self.domain,
            project_id=self.project_id,
            session_owner_id=self.session_owner_id,
            token=self.token,
        )
