"""Write specs for a route of a deployment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.common.data.entity.replica_group import ReplicaGroupID
from ai.backend.manager.data.deployment.types import DeploymentInfo, RouteTrafficStatus
from ai.backend.manager.data.model_serving.types import RoutingData
from ai.backend.manager.models.routing.creators import ReplicaCreator
from ai.backend.testutils.scenario_steps import Says
from bai_scenario.seeds.seeder import TestSeedFieldCreator


@dataclass(frozen=True)
class TestSeedRouteOf(TestSeedFieldCreator[DeploymentInfo, RoutingData]):
    """One route of the deployment, in the replica group and revision earlier rows
    answered.

    The route serves no session yet: it is laid provisioning and its traffic is
    inactive.
    """

    revision_id: DeploymentRevisionID
    replica_group_id: ReplicaGroupID
    session_owner_id: UUID
    domain: str
    project_id: UUID
    traffic_status: RouteTrafficStatus = RouteTrafficStatus.INACTIVE

    @override
    def kind(self) -> str:
        return Says("복제본 라우트 하나를 갖는다", english="has one replica route")

    @override
    def owner_id(self, owner: DeploymentInfo) -> DeploymentID:
        return DeploymentID(owner.id)

    @override
    def seed(self) -> ReplicaCreator:
        return ReplicaCreator(
            session_owner_id=self.session_owner_id,
            domain=self.domain,
            project_id=self.project_id,
            revision_id=self.revision_id,
            health_check=None,
            termination_grace_period=0.0,
            replica_group_id=self.replica_group_id,
            traffic_status=self.traffic_status,
        )
