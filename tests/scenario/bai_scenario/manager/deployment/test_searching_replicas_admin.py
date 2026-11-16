"""복제본 전체 훑기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.model_deployment.types import RouteTrafficStatus
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.deployment.request import (
    ReplicaFilter,
    ReplicaOrder,
    ReplicaTrafficStatusFilter,
    SearchReplicasInput,
)
from ai.backend.common.dto.manager.v2.deployment.response import SearchReplicasPayload
from ai.backend.common.dto.manager.v2.deployment.types import OrderDirection, ReplicaOrderField
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
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
class SearchingEveryReplica(When[ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]):
    """트래픽이 꺼진 복제본만 남기고, 생성 시각순으로 한 페이지를 훑는다."""

    @override
    def operation(self) -> str:
        return "admin_search_replicas"

    @override
    def describe(self, laid: ARoutedDeploymentAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 복제본 전체를 하나의 기준으로 걸러 순서와 함께 조회합니다",
            english=(
                f"{laid.caller.username} searches every replica with one filter, one order "
                f"and pagination"
            ),
        )

    @override
    async def call(self, adapter: DeploymentAdapter, laid: ARoutedDeploymentAndACaller) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.admin_search_replicas(
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
                )
            )


@dataclass(frozen=True)
class TheReplicaPageComesBack(Then[ARoutedDeploymentAndACaller, Answer]):
    """심은 복제본이 양과 함께 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "기준이 제외하는 복제본은 오지 않고, 심은 복제본이 양과 함께 옵니다",
            english=(
                "the replica the filter excludes does not come back, and the replicas "
                "seeded in advance come back with their count"
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
                verdicts += TheReplicaNode(self.started, revision_id=laid.revision_id).verdicts(
                    node, route, f"items[{i}]."
                )
        return verdicts


@dataclass(frozen=True)
class TheSuperadminSearchesTheReplicas(
    Scenario[TestSeedingSession, ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-searches-the-replicas"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 복제본 전체를 기준으로 걸러 조회하면, 심은 복제본이 옵니다. "
            "복제본 전체 훑기는 전역 권한이 필요한 호출이라 이 행의 요청 사용자는 "
            "superadmin 입니다",
            english=(
                "when the superadmin searches every replica with a filter, the replicas "
                "seeded in advance come back. The requesting user of this row is the "
                "superadmin because the search is gated by the global role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARoutedDeploymentAndACaller]:
        return ADeploymentWithRoutes(role=UserRole.SUPERADMIN, excluded_active=True)

    @override
    def when(self) -> When[ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]:
        return SearchingEveryReplica()

    @override
    def then(self) -> Then[ARoutedDeploymentAndACaller, Answer]:
        return TheReplicaPageComesBack(started=self.started)


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
            "아무 권한도 받지 않은 사용자가 복제본 전체를 조회하려 하면, 전역 권한이 없다는 "
            "이유로 거부됩니다",
            english=(
                "when a user granted nothing tries to search every replica, the search is "
                "rejected because the user lacks the global role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARoutedDeploymentAndACaller]:
        return ADeploymentWithRoutes(role=UserRole.USER)

    @override
    def when(self) -> When[ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]:
        return SearchingEveryReplica()

    @override
    def then(self) -> Then[ARoutedDeploymentAndACaller, Answer]:
        return TheCallIsRefused(InsufficientPrivilege)


STARTED = datetime.now(UTC)

SCENARIOS: list[ReplicaStep] = [
    TheSuperadminSearchesTheReplicas(started=STARTED),
    AUserGrantedNothingSearchesNoReplica(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching_replicas_admin(
    scenario: ReplicaStep,
    adapter: DeploymentAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
