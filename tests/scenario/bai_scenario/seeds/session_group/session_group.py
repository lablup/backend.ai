"""Write specs for a session group and the replica group holding one."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.deployment.types import DeploymentInfo, ReplicaGroupData
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.session_group.types import (
    SessionGroupData,
    SessionGroupPlacementDirection,
    SessionGroupPlacementEnforcement,
)
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.deployment_policy.creators import DeploymentPolicyCreator
from ai.backend.manager.models.replica_group.creators import ReplicaGroupCreator
from ai.backend.manager.models.session_group.creators import SessionGroupCreator
from bai_scenario.seeds.seeder import (
    Naming,
    TestSeedFieldCreator,
    TestSeedRowFrom,
    TestSeedRowFromTwo,
)


@dataclass(frozen=True)
class TestSeedSessionGroup(TestSeedRowFromTwo[ProjectData, UserData, SessionGroupData]):
    """A group a user made in the given project, owned by the given user.

    It packs and holds its members, apart from a deployment's spread-and-prefer default.
    """

    @override
    def kind(self) -> str:
        return "사용자가 만든 세션 그룹"

    @override
    def detail(self) -> str:
        return "멤버를 한 에이전트에 모으고, 반드시 지킨다"

    @override
    def name(self, naming: Naming) -> str:
        return naming("session-group")

    @override
    def seed(self, name: str, first: ProjectData, second: UserData) -> SessionGroupCreator:
        return SessionGroupCreator(
            project_id=ProjectID(first.id),
            owner_user_id=UserID(second.id),
            placement_direction=SessionGroupPlacementDirection.PACK,
            placement_enforcement=SessionGroupPlacementEnforcement.STRICT,
        )


@dataclass(frozen=True)
class TestSeedDeploymentSessionGroup(TestSeedRowFrom[DeploymentInfo, SessionGroupData]):
    """The group a replica group of the given deployment holds.

    Built the way the deployment builds it, under the deployment's project and owner.
    """

    @override
    def kind(self) -> str:
        return "배포의 세션 그룹"

    @override
    def detail(self) -> str:
        return "배포가 replica group과 함께 만드는 세션 그룹이다"

    @override
    def name(self, naming: Naming) -> str:
        return naming("deployment-session-group")

    @override
    def seed(self, name: str, source: DeploymentInfo) -> SessionGroupCreator:
        return SessionGroupCreator.for_replica_group(
            project_id=ProjectID(source.metadata.project),
            owner_user_id=UserID(source.metadata.session_owner),
        )


@dataclass(frozen=True)
class TestSeedPrimaryReplicaGroupOf(TestSeedFieldCreator[DeploymentInfo, ReplicaGroupData]):
    """The deployment's primary replica group, holding the given session group.

    The session group is a value an earlier row answered.
    """

    session_group_id: SessionGroupID

    @override
    def kind(self) -> str:
        return "세션 그룹을 가진 replica group 하나를 갖는다"

    @override
    def owner_id(self, owner: DeploymentInfo) -> DeploymentID:
        return DeploymentID(owner.id)

    @override
    def seed(self) -> ReplicaGroupCreator:
        return ReplicaGroupCreator.for_primary(
            session_group_id=self.session_group_id,
            rollout=DeploymentPolicyCreator.build_default().strategy_spec.to_rollout_spec(),
            desired_current_replica_count=1,
        )
