"""What a route scenario table says besides the call.

A route and a replica are the same row (``routings``) read two ways: the searcher
answers one row as a route for the route family and as a replica for the replica
family. One nest given serves both.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.model_deployment.types import (
    ActivenessStatus,
    LivenessStatus,
    ReadinessStatus,
)
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.deployment.response import ReplicaNode, RouteNode
from ai.backend.manager.data.deployment.types import DeploymentInfo
from ai.backend.manager.data.model_serving.types import RoutingData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData
from ai.backend.testutils.scenario_steps import (
    Given,
    Held,
    Same,
    SameAs,
    Says,
    Verdict,
)
from bai_scenario.components.deployment import LaidPlace, lay_a_deployment, lay_a_place
from bai_scenario.components.deployment_revision import (
    WhatARevisionStandsOn,
    lay_revisions,
)
from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.seeds.deployment.route import TestSeedRouteOf
from bai_scenario.seeds.session_group.session_group import (
    TestSeedDeploymentSessionGroup,
    TestSeedPrimaryReplicaGroupOf,
)

ROUTE_ID = Says("미리 저장한 라우트의 id", english="the id of the route seeded in advance")
REVISION_ID = Says("미리 저장한 리비전의 id", english="the id of the revision seeded in advance")


@dataclass(frozen=True)
class ARoutedDeploymentAndACaller:
    """리비전과 복제본 라우트가 딸린 배포, 그것을 부를 사람."""

    place: LaidPlace
    deployment: DeploymentInfo
    revision_id: UUID
    routes: tuple[RoutingData, ...]
    caller: UserData


@dataclass(frozen=True)
class ADeploymentWithRoutes(Given[Any, ARoutedDeploymentAndACaller]):
    """리비전 하나와 복제본 라우트가 딸린 배포 하나와, 그 프로젝트 안의 사용자 한 명."""

    granted: tuple[Permission, ...] = ()
    role: UserRole = UserRole.USER
    routes: int = 1

    @override
    def describe(self) -> str:
        if self.role is UserRole.SUPERADMIN:
            who_ko = "superadmin"
            who_en = "the superadmin"
        elif not self.granted:
            who_ko = "아무 배포 권한도 받지 않은 사용자"
            who_en = "a user with no deployment permission"
        else:
            names = ", ".join(p.name or "" for p in self.granted)
            who_ko = f"배포에 {names} 권한을 받은 사용자"
            who_en = f"a user granted the {names} permission on deployments"
        return Says(
            f"리비전과 복제본 라우트 {self.routes}개가 딸린 배포 하나와, {who_ko} 한 명",
            english=(
                f"one deployment holding one revision and {self.routes} replica routes, "
                f"and {who_en}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> ARoutedDeploymentAndACaller:
        place = await lay_a_place(seeding, granted=self.granted, role=self.role)
        deployment = await lay_a_deployment(seeding, place)
        materials = await seeding.within(WhatARevisionStandsOn(place.caller))
        revisions = await lay_revisions(seeding, place, deployment, materials, 1)
        made = seeding.made(deployment)
        session_group = await seeding.creating_from(TestSeedDeploymentSessionGroup(), deployment)
        replica_group = await seeding.adding(
            TestSeedPrimaryReplicaGroupOf(session_group_id=seeding.made(session_group).id),
            deployment,
        )
        routes: list[RoutingData] = []
        for _ in range(self.routes):
            route = await seeding.adding(
                TestSeedRouteOf(
                    revision_id=revisions[0].id,
                    replica_group_id=seeding.made(replica_group).id,
                    session_owner_id=made.metadata.session_owner,
                    domain=made.metadata.domain,
                    project_id=made.metadata.project,
                ),
                deployment,
            )
            routes.append(seeding.made(route))
        return ARoutedDeploymentAndACaller(
            place=place,
            deployment=made,
            revision_id=revisions[0].id,
            routes=tuple(routes),
            caller=seeding.made(place.caller),
        )


@dataclass(frozen=True)
class TheRouteNode:
    """미리 저장한 라우트의 노드가 어떤 값으로 와야 하는지. 값은 심은 것에서 읽는다.

    리비전은 라우트 행이 가리키는 것이고 트래픽 상태는 심을 때 두는 것이므로 검사가
    받는다. 트래픽 상태는 심은 것의 값이다.
    """

    started: datetime
    revision_id: UUID
    traffic_status: str = "inactive"

    def verdicts(self, node: RouteNode, laid: RoutingData, at: str = "") -> list[Verdict]:
        return [
            Held[UUID](f"{at}id", node.id, SameAs(laid.id, ROUTE_ID)),
            Held[UUID](f"{at}field_id", node.field_id, SameAs(laid.id, ROUTE_ID)),
            Held[UUID](
                f"{at}deployment_id",
                node.deployment_id,
                SameAs(
                    laid.endpoint,
                    Says(
                        "라우트가 받쳐주는 배포의 id",
                        english="the id of the deployment the route serves",
                    ),
                ),
            ),
            Same(f"{at}session_id", node.session_id, None),
            Same(f"{at}status", node.status.value, laid.status.value),
            Same(f"{at}health_status", node.health_status.value, laid.health_status.value),
            Same(f"{at}traffic_ratio", node.traffic_ratio, laid.traffic_ratio),
            Held(f"{at}created_at", node.created_at, WrittenByThisRun(self.started)),
            Held[UUID | None](
                f"{at}revision_id",
                node.revision_id,
                SameAs[UUID | None](self.revision_id, REVISION_ID),
            ),
            Same(f"{at}traffic_status", node.traffic_status.value, self.traffic_status),
            Same(f"{at}error_data", node.error_data, laid.error_data),
        ]


@dataclass(frozen=True)
class TheReplicaNode:
    """미리 저장한 라우트를 복제본으로 읽은 노드가 어떤 값으로 와야 하는지.

    대기 상태, 생존 상태, 활성 상태는 칼럼이 없고 심은 행의 상태 검사 상태와 트래픽
    상태에서 접힌다. 접는 규칙은 검색기가 문서로 둔다.
    """

    started: datetime
    revision_id: UUID
    traffic_status: str = "inactive"

    def verdicts(self, node: ReplicaNode, laid: RoutingData, at: str = "") -> list[Verdict]:
        readiness = self._readiness(laid)
        liveness = LivenessStatus(laid.health_status.value)
        activeness = self._activeness(readiness, liveness)
        return [
            Held[UUID](f"{at}id", node.id, SameAs(laid.id, ROUTE_ID)),
            Held[UUID](f"{at}field_id", node.field_id, SameAs(laid.id, ROUTE_ID)),
            Held[UUID](
                f"{at}deployment_id",
                node.deployment_id,
                SameAs(
                    laid.endpoint,
                    Says(
                        "복제본이 받쳐주는 배포의 id",
                        english="the id of the deployment the replica serves",
                    ),
                ),
            ),
            Held[UUID](f"{at}revision_id", node.revision_id, SameAs(self.revision_id, REVISION_ID)),
            Same(f"{at}session_id", node.session_id, None),
            Same(f"{at}readiness_status", node.readiness_status.value, readiness.value),
            Same(f"{at}liveness_status", node.liveness_status.value, liveness.value),
            Same(f"{at}activeness_status", node.activeness_status.value, activeness.value),
            Same(f"{at}status", node.status.value, laid.status.value),
            Same(f"{at}traffic_status", node.traffic_status.value, self.traffic_status),
            Same(f"{at}health_status", node.health_status.value, laid.health_status.value),
            Held(f"{at}created_at", node.created_at, WrittenByThisRun(self.started)),
        ]

    def _readiness(self, laid: RoutingData) -> ReadinessStatus:
        if laid.health_status.value == "unhealthy":
            return ReadinessStatus.UNHEALTHY
        return ReadinessStatus(laid.health_status.value)

    def _activeness(self, readiness: ReadinessStatus, liveness: LivenessStatus) -> ActivenessStatus:
        if self.traffic_status == "inactive":
            return ActivenessStatus.INACTIVE
        if readiness != ReadinessStatus.HEALTHY:
            return ActivenessStatus.INACTIVE
        if liveness != LivenessStatus.HEALTHY:
            return ActivenessStatus.INACTIVE
        return ActivenessStatus.ACTIVE
