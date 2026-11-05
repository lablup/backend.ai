"""배포가 걸린 복제본 라우트 id 로 한꺼번에 읽기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.deployment.response import RouteNode
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.deployment_route import (
    ADeploymentWithRoutes,
    ARoutedDeploymentAndACaller,
    TheRouteNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = list[RouteNode | Exception | None]
type RouteStep = Scenario[
    TestSeedingSession, ARoutedDeploymentAndACaller, DeploymentAdapter, Answer
]


@dataclass(frozen=True)
class LoadingTheSeededRoutes(When[ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]):
    """심은 라우트의 id 만 준다."""

    @override
    def operation(self) -> str:
        return "batch_load_routes_by_ids"

    @override
    def describe(self, laid: ARoutedDeploymentAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 심은 라우트를 id 로 한꺼번에 읽습니다",
            english=f"{laid.caller.username} batch loads the routes seeded in advance by id",
        )

    @override
    async def call(
        self, adapter: DeploymentAdapter, laid: ARoutedDeploymentAndACaller
    ) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.batch_load_routes_by_ids(
                [route.id for route in laid.routes]
            )


@dataclass(frozen=True)
class TheRoutesComeBackInOrder(Then[ARoutedDeploymentAndACaller, Answer]):
    """라우트가 요청에 넣은 순서대로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "라우트가 요청에 넣은 순서대로 옵니다",
            english="the routes come back in the order they were put in the request",
        )

    @override
    def look(
        self, laid: ARoutedDeploymentAndACaller, answered: Answered[Answer]
    ) -> list[Verdict]:
        routes = answered.response
        if routes is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = []
        for i, entry in enumerate(routes):
            if isinstance(entry, RouteNode):
                verdicts += TheRouteNode(
                    self.started, revision_id=laid.revision_id
                ).verdicts(entry, laid.routes[i], f"[{i}].")
            else:
                verdicts.append(Same(f"[{i}]", type(entry).__name__, "RouteNode"))
        return verdicts


@dataclass(frozen=True)
class EveryEntryIsRefused(Then[ARoutedDeploymentAndACaller, Answer]):
    """라우트 없이, 모든 항목이 같은 이유로 거부된 예외로 온다."""

    @override
    def says(self) -> str:
        return Says(
            "라우트 없이 모든 항목이 거부된 예외로 옵니다",
            english="no route comes back and every entry is the exception the check raised",
        )

    @override
    def look(
        self, laid: ARoutedDeploymentAndACaller, answered: Answered[Answer]
    ) -> list[Verdict]:
        routes = answered.response
        if routes is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Refused(NotEnoughPermission, entry if isinstance(entry, Exception) else None)
            if entry is not None
            else Same(f"[{i}]", type(entry).__name__, "exception")
            for i, entry in enumerate(routes)
        ]


@dataclass(frozen=True)
class AUserGrantedDeploymentReadLoadsTheRoutesById(
    Scenario[TestSeedingSession, ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-deployment-read-loads-the-routes-by-id"

    @override
    def describe(self) -> str:
        return Says(
            "배포 조회 권한을 받은 사용자가 배포가 걸린 라우트를 id 로 한꺼번에 읽으면, "
            "그 라우트들이 옵니다",
            english=(
                "when a user granted deployment read batch loads the routes the deployment "
                "holds by id, those routes come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARoutedDeploymentAndACaller]:
        return ADeploymentWithRoutes(granted=(Permission.READ,))

    @override
    def when(self) -> When[ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]:
        return LoadingTheSeededRoutes()

    @override
    def then(self) -> Then[ARoutedDeploymentAndACaller, Answer]:
        return TheRoutesComeBackInOrder(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingGetsARefusalForTheRoutes(
    Scenario[TestSeedingSession, ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-gets-a-refusal-for-the-routes"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 배포가 걸린 라우트를 id 로 한꺼번에 읽으려 하면, "
            "모든 항목이 권한이 없다는 이유로 거부됩니다",
            english=(
                "when a user granted nothing tries to batch load the routes the deployment "
                "holds by id, every entry is rejected because the user lacks permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARoutedDeploymentAndACaller]:
        return ADeploymentWithRoutes()

    @override
    def when(self) -> When[ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]:
        return LoadingTheSeededRoutes()

    @override
    def then(self) -> Then[ARoutedDeploymentAndACaller, Answer]:
        return EveryEntryIsRefused()


STARTED = datetime.now(UTC)

SCENARIOS: list[RouteStep] = [
    AUserGrantedDeploymentReadLoadsTheRoutesById(started=STARTED),
    AUserGrantedNothingGetsARefusalForTheRoutes(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_batch_loading_routes(
    scenario: RouteStep,
    adapter: DeploymentAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
