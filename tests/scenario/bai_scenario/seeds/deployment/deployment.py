"""Write specs for a deployment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.deployment.types import DeploymentInfo, DeploymentOptions
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.data.session.options import AgentSelectionPolicy
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.endpoint.creators import (
    DeploymentCreator,
    DeploymentMetadataFields,
    DeploymentNetworkFields,
    DeploymentReplicaFields,
)
from ai.backend.testutils.scenario_steps import Says
from bai_scenario.seeds.seeder import Naming, TestSeedRowFromThree, joined


@dataclass(frozen=True)
class TestSeedDeployment(
    TestSeedRowFromThree[ProjectData, ResourceGroupData, UserData, DeploymentInfo]
):
    """A deployment of the given project, on the given group, owned by the given user.

    It is laid without a revision: the row a scenario needs to read, edit or retire does
    not need one, and laying one belongs to the revision scenarios.
    """

    name_hint: str = "deployment"
    replica_count: int = 1
    open_to_public: bool = False
    tag: str | None = None
    agent_selection_policy: AgentSelectionPolicy = AgentSelectionPolicy.PREFERRED

    @override
    def kind(self) -> str:
        return Says("배포", english="Deployment")

    @override
    def detail(self) -> str:
        says = [
            Says(
                f"복제본 {self.replica_count}개를 두려 한다",
                english=f"replica count {self.replica_count}",
            ),
            Says("아직 리비전이 없다", english="has no revision yet"),
        ]
        if self.open_to_public:
            says.append(Says("외부에 열려 있다", english="open to the public"))
        if self.tag is not None:
            says.append(Says(f"{self.tag} 태그가 붙어 있다", english=f"tagged {self.tag}"))
        if self.agent_selection_policy != AgentSelectionPolicy.PREFERRED:
            says.append(
                Says(
                    f"선택 정책은 {self.agent_selection_policy.value} 입니다",
                    english=f"the selection policy is {self.agent_selection_policy.value}",
                )
            )
        return joined(says, ", ")

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(
        self,
        name: str,
        first: ProjectData,
        second: ResourceGroupData,
        third: UserData,
    ) -> DeploymentCreator:
        return DeploymentCreator(
            metadata=DeploymentMetadataFields(
                name=name,
                domain=first.domain_name,
                project_id=ProjectID(first.id),
                resource_group=second.name,
                created_user_id=third.id,
                session_owner_id=UserID(third.id),
                tag=self.tag,
            ),
            replica=DeploymentReplicaFields(replica_count=self.replica_count),
            network=DeploymentNetworkFields(open_to_public=self.open_to_public),
            options=DeploymentOptions(agent_selection_policy=self.agent_selection_policy),
        )
