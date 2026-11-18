"""Write specs for a session group and the replica group holding one."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any, override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.replica_group import ReplicaGroupID
from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.deployment.types import (
    DeploymentInfo,
    ReplicaGroupData,
    ReplicaGroupLifecycle,
)
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
from ai.backend.manager.models.session_group.updaters import SessionGroupRetentionUpdater
from ai.backend.manager.models.specs.updater import DataBatchUpdater
from ai.backend.testutils.scenario_steps import Says
from bai_scenario.seeds.seeder import (
    Naming,
    TestSeedBatchUpdate,
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
        return Says("사용자가 만든 세션 그룹", english="Session group a user made")

    @override
    def detail(self) -> str:
        return Says(
            "멤버를 한 에이전트에 모으고, 반드시 지킵니다",
            english="packs its members onto one agent and enforces it strictly",
        )

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
        return Says("배포의 세션 그룹", english="Session group of a deployment")

    @override
    def detail(self) -> str:
        return Says(
            "배포가 복제본 그룹과 함께 생성하는 세션 그룹입니다",
            english="the session group a deployment creates with its replica group",
        )

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
        return Says(
            "세션 그룹을 가진 복제본 그룹 하나를 갖습니다",
            english="has one replica group holding the session group",
        )

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


@dataclass(frozen=True)
class TestSeedRetiredReplicaGroupOf(TestSeedFieldCreator[DeploymentInfo, ReplicaGroupData]):
    """The deployment's replica group holding the given session group, no longer served.

    The retention boundary is stamped on the session group of a replica group whose
    lifecycle is terminal, so the group is laid drained and holding no replica.
    """

    session_group_id: SessionGroupID

    @override
    def kind(self) -> str:
        return Says(
            "세션 그룹을 가진 복제본 그룹 하나가 서비스를 마쳤습니다",
            english="one replica group holding the session group stopped serving",
        )

    @override
    def owner_id(self, owner: DeploymentInfo) -> DeploymentID:
        return DeploymentID(owner.id)

    @override
    def seed(self) -> ReplicaGroupCreator:
        return replace(
            ReplicaGroupCreator.for_primary(
                session_group_id=self.session_group_id,
                rollout=DeploymentPolicyCreator.build_default().strategy_spec.to_rollout_spec(),
                desired_current_replica_count=0,
            ),
            lifecycle=ReplicaGroupLifecycle.DRAINED,
        )


@dataclass(frozen=True)
class TestSeedRetiredSessionGroupOf(TestSeedBatchUpdate[ReplicaGroupData, SessionGroupData]):
    """The session group the given replica group held, stamped with its deletion time."""

    deleted_at: datetime

    @override
    def kind(self) -> str:
        return Says("삭제 시각이 찍힌 세션 그룹", english="a session group stamped as deleted")

    @override
    def detail(self) -> str:
        return Says(
            "복제본 그룹이 서비스를 마쳐 유지 기간이 시작됐습니다",
            english="its replica group stopped serving, so its retention period has started",
        )

    @override
    def name(self, naming: Naming) -> str:
        return naming("retired-session-group")

    @override
    def updater(self, source: ReplicaGroupData) -> DataBatchUpdater[Any, SessionGroupData]:
        return SessionGroupRetentionUpdater(
            replica_group_ids=[ReplicaGroupID(source.id)],
            deleted_at=self.deleted_at,
        )
