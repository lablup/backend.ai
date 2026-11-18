"""배포가 걸린 복제본 훑기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.model_deployment.types import RouteTrafficStatus
from ai.backend.common.dto.manager.v2.deployment.request import (
    ReplicaFilter,
    ReplicaOrder,
    ReplicaTrafficStatusFilter,
    SearchReplicasInput,
)
from ai.backend.common.dto.manager.v2.deployment.response import SearchReplicasPayload
from ai.backend.common.dto.manager.v2.deployment.types import OrderDirection, ReplicaOrderField
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.data.deployment.types import ReplicaOperationScope
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Same,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.deployment_route import (
    ADeploymentWithRoutes,
    ARoutedDeploymentAndACaller,
    TheReplicaNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = SearchReplicasPayload
type ReplicaStep = Scenario[
    TestSeedingSession, ARoutedDeploymentAndACaller, DeploymentAdapter, Answer
]


@dataclass(frozen=True)
class SearchingTheReplicasOfTheDeployment(
    When[ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]
):
    """트래픽이 꺼진 복제본만 남기고, 생성 시각순으로 한 페이지를 훑는다."""

    @override
    def operation(self) -> str:
        return "search_replicas"

    @override
    def describe(self, laid: ARoutedDeploymentAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 {laid.deployment.metadata.name}의 복제본을 하나의 "
            f"기준으로 걸러 순서와 함께 조회합니다",
            english=(
                f"{laid.caller.username} searches the replicas of "
                f"{laid.deployment.metadata.name} with one filter, one order and pagination"
            ),
        )

    @override
    async def call(self, adapter: DeploymentAdapter, laid: ARoutedDeploymentAndACaller) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.search_replicas(
                ReplicaOperationScope(deployment_id=laid.deployment.id),
                SearchReplicasInput(
                    filter=ReplicaFilter(
                        traffic_status=ReplicaTrafficStatusFilter(
                            equals=RouteTrafficStatus.INACTIVE
                        )
                    ),
                    order=[
                        ReplicaOrder(
                            field=ReplicaOrderField.CREATED_AT, direction=OrderDirection.ASC
                        )
                    ],
                    limit=10,
                    offset=0,
                ),
            )


@dataclass(frozen=True)
class TheReplicaPageComesBack(Then[ARoutedDeploymentAndACaller, Answer]):
    """심은 복제본이 양과 함께 온다."""

    started: datetime
    traffic_status: str = "inactive"

    @override
    def says(self) -> str:
        if self.traffic_status == "active":
            return Says(
                "트래픽이 켜진 심은 복제본이 양과 함께 옵니다",
                english=(
                    "the replica seeded in advance with traffic enabled comes back with its count"
                ),
            )
        return Says(
            "기준이 제외하는 복제본과 다른 배포에 걸린 복제본은 오지 않고, "
            "심은 복제본이 양과 함께 옵니다",
            english=(
                "the replica the filter excludes and the replica on another deployment do "
                "not come back, and the replicas seeded in advance come back with their count"
            ),
        )

    @override
    def look(self, laid: ARoutedDeploymentAndACaller, answered: Answered[Answer]) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [MissingResponse(answered.raised)]
        verdicts: list[Verdict] = [
            Same("total_count", page.total_count, len(laid.routes)),
            Same("items count", len(page.items), len(laid.routes)),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]
        by_id = {route.id: route for route in laid.routes}
        for i, node in enumerate(page.items):
            route = by_id.get(node.id)
            if route is None:
                verdicts.append(Same(f"items[{i}].id", node.id, "a replica the deployment holds"))
            else:
                verdicts += TheReplicaNode(
                    self.started, revision_id=laid.revision_id, traffic_status=self.traffic_status
                ).verdicts(node, route, f"items[{i}].")
        return verdicts


@dataclass(frozen=True)
class AUserGrantedDeploymentReadSearchesTheReplicas(
    Scenario[TestSeedingSession, ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-deployment-read-searches-the-replicas"

    @override
    def describe(self) -> str:
        return Says(
            "배포 조회 권한을 받은 사용자가 배포의 복제본을 기준으로 걸러 조회하면, "
            "심은 복제본이 옵니다",
            english=(
                "when a user granted deployment read searches the replicas of the "
                "deployment with a filter, the replicas seeded in advance come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARoutedDeploymentAndACaller]:
        return ADeploymentWithRoutes(granted=(Permission.READ,), excluded_active=True, outside=True)

    @override
    def when(self) -> When[ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]:
        return SearchingTheReplicasOfTheDeployment()

    @override
    def then(self) -> Then[ARoutedDeploymentAndACaller, Answer]:
        return TheReplicaPageComesBack(started=self.started)


@dataclass(frozen=True)
class SearchingTheReplicaWithTrafficEnabled(
    When[ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]
):
    """아무 조건 없이 한 페이지를 훑는다."""

    @override
    def operation(self) -> str:
        return "search_replicas"

    @override
    def describe(self, laid: ARoutedDeploymentAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 {laid.deployment.metadata.name}의 복제본을 조회합니다",
            english=(
                f"{laid.caller.username} searches the replicas of {laid.deployment.metadata.name}"
            ),
        )

    @override
    async def call(self, adapter: DeploymentAdapter, laid: ARoutedDeploymentAndACaller) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.search_replicas(
                ReplicaOperationScope(deployment_id=laid.deployment.id), SearchReplicasInput()
            )


@dataclass(frozen=True)
class AUserGrantedDeploymentReadSearchesTheReplicaWithTrafficEnabled(
    Scenario[TestSeedingSession, ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-deployment-read-searches-the-replica-with-traffic-enabled"

    @override
    def describe(self) -> str:
        return Says(
            "배포 조회 권한을 받은 사용자가 트래픽이 켜진 라우트의 복제본을 조회하면, "
            "심은 복제본이 옵니다",
            english=(
                "when a user granted deployment read searches the replica of a route with "
                "traffic enabled, the replicas seeded in advance come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARoutedDeploymentAndACaller]:
        return ADeploymentWithRoutes(granted=(Permission.READ,), active_traffic=True)

    @override
    def when(self) -> When[ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]:
        return SearchingTheReplicaWithTrafficEnabled()

    @override
    def then(self) -> Then[ARoutedDeploymentAndACaller, Answer]:
        return TheReplicaPageComesBack(
            started=self.started, traffic_status=RouteTrafficStatus.ACTIVE.value
        )


@dataclass(frozen=True)
class AUserGrantedNothingSearchesNoReplica(
    Scenario[TestSeedingSession, ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-searches-no-replica"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 배포의 복제본을 조회하려 하면, 권한이 없다는 "
            "이유로 거부됩니다",
            english=(
                "when a user granted nothing tries to search the replicas of the "
                "deployment, the search is rejected because the user lacks permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARoutedDeploymentAndACaller]:
        return ADeploymentWithRoutes()

    @override
    def when(self) -> When[ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]:
        return SearchingTheReplicasOfTheDeployment()

    @override
    def then(self) -> Then[ARoutedDeploymentAndACaller, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


STARTED = datetime.now(UTC)

SCENARIOS: list[ReplicaStep] = [
    AUserGrantedDeploymentReadSearchesTheReplicas(started=STARTED),
    AUserGrantedDeploymentReadSearchesTheReplicaWithTrafficEnabled(started=STARTED),
    AUserGrantedNothingSearchesNoReplica(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching_replicas(
    scenario: ReplicaStep,
    adapter: DeploymentAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
