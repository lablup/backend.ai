"""배포가 걸린 라우트의 트래픽 상태 바꾸기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.model_deployment.types import RouteTrafficStatus
from ai.backend.common.dto.manager.v2.deployment.response import RouteNode
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
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

type Answer = RouteNode
type RouteStep = Scenario[
    TestSeedingSession, ARoutedDeploymentAndACaller, DeploymentAdapter, Answer
]


@dataclass(frozen=True)
class OpeningTheTrafficOfTheRoute(
    When[ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]
):
    """심은 라우트 하나의 id 와 트래픽 상태를 준다."""

    @override
    def operation(self) -> str:
        return "update_route_traffic"

    @override
    def describe(self, laid: ARoutedDeploymentAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 {laid.deployment.metadata.name}의 라우트 트래픽을 "
            f"{RouteTrafficStatus.ACTIVE.value} 로 바꿉니다",
            english=(
                f"{laid.caller.username} turns the traffic of a route of "
                f"{laid.deployment.metadata.name} to {RouteTrafficStatus.ACTIVE.value}"
            ),
        )

    @override
    async def call(
        self, adapter: DeploymentAdapter, laid: ARoutedDeploymentAndACaller
    ) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.update_route_traffic(
                laid.routes[0].id, RouteTrafficStatus.ACTIVE
            )


@dataclass(frozen=True)
class TheRouteWithTrafficOpenComesBack(Then[ARoutedDeploymentAndACaller, Answer]):
    """트래픽을 연 라우트가 통째로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "트래픽을 연 라우트가 전체가 응답으로 옵니다",
            english="the route with its traffic turned on comes back whole",
        )

    @override
    def look(
        self, laid: ARoutedDeploymentAndACaller, answered: Answered[Answer]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [MissingResponse(answered.raised)]
        return TheRouteNode(
            self.started,
            revision_id=laid.revision_id,
            traffic_status=RouteTrafficStatus.ACTIVE.value,
        ).verdicts(node, laid.routes[0])


@dataclass(frozen=True)
class AUserGrantedDeploymentUpdateOpensTheTraffic(
    Scenario[TestSeedingSession, ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-deployment-update-opens-the-traffic"

    @override
    def describe(self) -> str:
        return Says(
            "배포 조회와 수정 권한을 받은 사용자가 라우트의 트래픽을 열면, 트래픽을 연 "
            "라우트가 옵니다. 트래픽 바꾸기는 라우트가 걸린 배포를 먼저 찾는 호출이라 "
            "조회 권한도 필요합니다",
            english=(
                "when a user granted deployment read and update turns the traffic of a "
                "route on, the route with its traffic turned on comes back. The traffic "
                "change reads the deployment first, so read is also required"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARoutedDeploymentAndACaller]:
        return ADeploymentWithRoutes(granted=(Permission.READ, Permission.UPDATE))

    @override
    def when(self) -> When[ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]:
        return OpeningTheTrafficOfTheRoute()

    @override
    def then(self) -> Then[ARoutedDeploymentAndACaller, Answer]:
        return TheRouteWithTrafficOpenComesBack(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingChangesNoTraffic(
    Scenario[TestSeedingSession, ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-changes-no-traffic"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 라우트의 트래픽을 바꾸려 하면, 라우트가 걸린 "
            "배포를 찾는 조회가 거부됩니다",
            english=(
                "when a user granted nothing tries to turn the traffic of a route, "
                "the lookup that finds the deployment holding the route is rejected"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARoutedDeploymentAndACaller]:
        return ADeploymentWithRoutes()

    @override
    def when(self) -> When[ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]:
        return OpeningTheTrafficOfTheRoute()

    @override
    def then(self) -> Then[ARoutedDeploymentAndACaller, Answer]:
        return TheCallIsRefused(GenericBadRequest)


STARTED = datetime.now(UTC)

SCENARIOS: list[RouteStep] = [
    AUserGrantedDeploymentUpdateOpensTheTraffic(started=STARTED),
    AUserGrantedNothingChangesNoTraffic(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing_route_traffic(
    scenario: RouteStep,
    adapter: DeploymentAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
