"""Write specs for one scheduling history row and the replica a route history is read through."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.common.data.entity.replica import ReplicaID
from ai.backend.common.data.entity.replica_group import ReplicaGroupID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.types import KernelId
from ai.backend.manager.data.deployment.types import (
    DeploymentHandlerCategory,
    DeploymentHistoryData,
    DeploymentInfo,
    ReplicaGroupHandlerCategory,
    ReplicaGroupHistoryData,
    RouteHandlerCategory,
    RouteHistoryData,
    RouteStatus,
    RouteSubStatus,
)
from ai.backend.manager.data.kernel.types import (
    KernelSchedulingHistoryData,
    KernelSchedulingPhase,
)
from ai.backend.manager.data.model_serving.types import RoutingData
from ai.backend.manager.data.session.types import (
    SchedulingResult,
    SessionEntityData,
    SessionSchedulingHistoryData,
    SessionStatus,
)
from ai.backend.manager.models.replica_group_history.creators import ReplicaGroupHistoryCreator
from ai.backend.manager.models.routing.creators import ReplicaCreator
from ai.backend.manager.models.scheduling_history.creators import (
    DeploymentHistoryCreator,
    KernelSchedulingHistoryCreator,
    RouteHistoryCreator,
    SessionSchedulingHistoryCreator,
)
from ai.backend.testutils.scenario_steps import Says
from bai_scenario.seeds.seeder import TestSeedFieldCreator

MESSAGE = "the transition finished"
"""이력 행이 남기는 설명."""


@dataclass(frozen=True)
class TestSeedSessionHistory(
    TestSeedFieldCreator[SessionEntityData, SessionSchedulingHistoryData]
):
    """One transition the session went through."""

    @override
    def kind(self) -> str:
        return Says(
            "스케줄링 시도 하나를 남깁니다",
            english="has one scheduling attempt recorded",
        )

    @override
    def detail(self) -> str:
        return Says(
            "PENDING 에서 SCHEDULED 로 성공한 전이 하나",
            english="one transition from PENDING to SCHEDULED that succeeded",
        )

    @override
    def owner_id(self, owner: SessionEntityData) -> SessionID:
        return SessionID(owner.id)

    @override
    def seed(self) -> SessionSchedulingHistoryCreator:
        return SessionSchedulingHistoryCreator(
            phase="scheduling",
            result=SchedulingResult.SUCCESS,
            message=MESSAGE,
            from_status=SessionStatus.PENDING,
            to_status=SessionStatus.SCHEDULED,
        )


@dataclass(frozen=True)
class TestSeedKernelHistory(TestSeedFieldCreator[SessionEntityData, KernelSchedulingHistoryData]):
    """One transition the kernel of the session went through."""

    kernel_id: KernelId

    @override
    def kind(self) -> str:
        return Says(
            "커널의 스케줄링 시도 하나를 남깁니다",
            english="has one scheduling attempt of a kernel recorded",
        )

    @override
    def detail(self) -> str:
        return Says(
            "PREPARING 에서 PULLING 으로 성공한 전이 하나",
            english="one transition from PREPARING to PULLING that succeeded",
        )

    @override
    def owner_id(self, owner: SessionEntityData) -> SessionID:
        return SessionID(owner.id)

    @override
    def seed(self) -> KernelSchedulingHistoryCreator:
        return KernelSchedulingHistoryCreator(
            kernel_id=self.kernel_id,
            phase="scheduling",
            result=SchedulingResult.SUCCESS,
            message=MESSAGE,
            from_status=KernelSchedulingPhase.PREPARING,
            to_status=KernelSchedulingPhase.PULLING,
        )


@dataclass(frozen=True)
class TestSeedDeploymentHistory(TestSeedFieldCreator[DeploymentInfo, DeploymentHistoryData]):
    """One transition the deployment went through."""

    @override
    def kind(self) -> str:
        return Says(
            "배포의 스케줄링 시도 하나를 남깁니다",
            english="has one scheduling attempt of the deployment recorded",
        )

    @override
    def detail(self) -> str:
        return Says(
            "lifecycle 처리기가 남긴 성공한 전이 하나",
            english="one transition recorded by a lifecycle handler that succeeded",
        )

    @override
    def owner_id(self, owner: DeploymentInfo) -> DeploymentID:
        return DeploymentID(owner.id)

    @override
    def seed(self) -> DeploymentHistoryCreator:
        return DeploymentHistoryCreator(
            phase="lifecycle",
            result=SchedulingResult.SUCCESS,
            message=MESSAGE,
            handler_category=DeploymentHandlerCategory.LIFECYCLE,
        )


@dataclass(frozen=True)
class TestSeedReplicaOf(TestSeedFieldCreator[DeploymentInfo, RoutingData]):
    """One replica the deployment serves traffic with.

    The session owner, the domain and the project are values earlier rows answered.
    """

    replica_group_id: ReplicaGroupID
    session_owner_id: uuid.UUID
    domain_name: str
    project_id: uuid.UUID

    @override
    def kind(self) -> str:
        return Says("복제본 하나를 갖습니다", english="has one replica")

    @override
    def detail(self) -> str:
        return Says(
            "아직 트래픽을 받지 않는, 배포의 기본 복제본 그룹에 속한 복제본",
            english="a replica of the deployment's primary replica group taking no traffic yet",
        )

    @override
    def owner_id(self, owner: DeploymentInfo) -> DeploymentID:
        return DeploymentID(owner.id)

    @override
    def seed(self) -> ReplicaCreator:
        return ReplicaCreator(
            session_owner_id=self.session_owner_id,
            domain=self.domain_name,
            project_id=self.project_id,
            revision_id=DeploymentRevisionID(uuid.uuid4()),
            health_check=None,
            termination_grace_period=0,
            replica_group_id=self.replica_group_id,
        )


@dataclass(frozen=True)
class TestSeedRouteHistory(TestSeedFieldCreator[DeploymentInfo, RouteHistoryData]):
    """One transition a replica of the deployment went through."""

    route_id: ReplicaID

    @override
    def kind(self) -> str:
        return Says(
            "라우트의 스케줄링 시도 하나를 남깁니다",
            english="has one scheduling attempt of a route recorded",
        )

    @override
    def detail(self) -> str:
        return Says(
            "PROVISIONING 에서 RUNNING 으로 가는 lifecycle 전이 하나",
            english="one lifecycle transition from PROVISIONING to RUNNING",
        )

    @override
    def owner_id(self, owner: DeploymentInfo) -> DeploymentID:
        return DeploymentID(owner.id)

    @override
    def seed(self) -> RouteHistoryCreator:
        return RouteHistoryCreator(
            route_id=self.route_id,
            category=RouteHandlerCategory.LIFECYCLE,
            phase="lifecycle",
            result=SchedulingResult.SUCCESS,
            message=MESSAGE,
            from_status=RouteStatus.PROVISIONING,
            to_status=RouteStatus.RUNNING,
            from_sub_status=RouteSubStatus.PENDING,
            to_sub_status=RouteSubStatus.WARMING_UP,
        )


@dataclass(frozen=True)
class TestSeedReplicaGroupHistory(
    TestSeedFieldCreator[DeploymentInfo, ReplicaGroupHistoryData]
):
    """One transition the replica group of the deployment went through."""

    replica_group_id: ReplicaGroupID

    @override
    def kind(self) -> str:
        return Says(
            "복제본 그룹의 스케줄링 시도 하나를 남깁니다",
            english="has one scheduling attempt of the replica group recorded",
        )

    @override
    def detail(self) -> str:
        return Says(
            "lifecycle 처리기가 남긴 성공한 전이 하나",
            english="one transition recorded by a lifecycle handler that succeeded",
        )

    @override
    def owner_id(self, owner: DeploymentInfo) -> DeploymentID:
        return DeploymentID(owner.id)

    @override
    def seed(self) -> ReplicaGroupHistoryCreator:
        return ReplicaGroupHistoryCreator(
            replica_group_id=self.replica_group_id,
            category=ReplicaGroupHandlerCategory.LIFECYCLE,
            phase="lifecycle",
            result=SchedulingResult.SUCCESS,
            message=MESSAGE,
        )
