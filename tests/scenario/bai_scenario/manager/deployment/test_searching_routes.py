"""배포가 걸린 복제본 라우트 훑기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.deployment.request import SearchRoutesInput
from ai.backend.common.dto.manager.v2.deployment.response import SearchRoutesPayload
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.data.deployment.types import RouteOperationScope
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
    TheRouteNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = SearchRoutesPayload
type RouteStep = Scenario[
    TestSeedingSession, ARoutedDeploymentAndACaller, DeploymentAdapter, Answer
]


@dataclass(frozen=True)
class SearchingTheRoutesOfTheDeployment(
    When[ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]
):
    """심은 배포 하나를 스코프로 주고 아무 조건도 주지 않는다."""

    @override
    def operation(self) -> str:
        return "search_routes"

    @override
    def describe(self, laid: ARoutedDeploymentAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 {laid.deployment.metadata.name}의 라우트를 조회합니다",
            english=(
                f"{laid.caller.username} searches the routes of {laid.deployment.metadata.name}"
            ),
        )

    @override
    async def call(self, adapter: DeploymentAdapter, laid: ARoutedDeploymentAndACaller) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.search_routes(
                RouteOperationScope(deployment_id=laid.deployment.id), SearchRoutesInput()
            )


@dataclass(frozen=True)
class TheRoutePageComesBack(Then[ARoutedDeploymentAndACaller, Answer]):
    """심은 라우트가 양과 함께 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "심은 라우트가 양과 함께 옵니다",
            english="the routes seeded in advance come back with their count",
        )

    @override
    def look(self, laid: ARoutedDeploymentAndACaller, answered: Answered[Answer]) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [MissingResponse(answered.raised)]
        verdicts: list[Verdict] = [
            Same("total_count", page.total_count, len(laid.routes)),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]
        for i, node in enumerate(page.items):
            verdicts += TheRouteNode(self.started, revision_id=laid.revision_id).verdicts(
                node, laid.routes[i], f"items[{i}]."
            )
        return verdicts


@dataclass(frozen=True)
class AUserGrantedDeploymentReadSearchesTheRoutes(
    Scenario[TestSeedingSession, ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-deployment-read-searches-the-routes"

    @override
    def describe(self) -> str:
        return Says(
            "배포 조회 권한을 받은 사용자가 배포의 라우트를 조회하면, 심은 라우트가 옵니다",
            english=(
                "when a user granted deployment read searches the routes of the deployment, "
                "the routes seeded in advance come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARoutedDeploymentAndACaller]:
        return ADeploymentWithRoutes(granted=(Permission.READ,))

    @override
    def when(self) -> When[ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]:
        return SearchingTheRoutesOfTheDeployment()

    @override
    def then(self) -> Then[ARoutedDeploymentAndACaller, Answer]:
        return TheRoutePageComesBack(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingSearchesNoRoute(
    Scenario[TestSeedingSession, ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-searches-no-route"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 배포의 라우트를 조회하려 하면, 권한이 없다는 "
            "이유로 거부됩니다",
            english=(
                "when a user granted nothing tries to search the routes of the deployment, "
                "the search is rejected because the user lacks permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARoutedDeploymentAndACaller]:
        return ADeploymentWithRoutes()

    @override
    def when(self) -> When[ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]:
        return SearchingTheRoutesOfTheDeployment()

    @override
    def then(self) -> Then[ARoutedDeploymentAndACaller, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


STARTED = datetime.now(UTC)

SCENARIOS: list[RouteStep] = [
    AUserGrantedDeploymentReadSearchesTheRoutes(started=STARTED),
    AUserGrantedNothingSearchesNoRoute(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching_routes(
    scenario: RouteStep,
    adapter: DeploymentAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
