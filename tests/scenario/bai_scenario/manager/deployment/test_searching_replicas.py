"""배포가 걸린 복제본 훑기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.deployment.request import SearchReplicasInput
from ai.backend.common.dto.manager.v2.deployment.response import SearchReplicasPayload
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
    """심은 배포 하나를 스코프로 주고 아무 조건도 주지 않는다."""

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
class TheReplicaPageComesBack(Then[ARoutedDeploymentAndACaller, Answer]):
    """심은 복제본이 양과 함께 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "심은 복제본이 양과 함께 옵니다",
            english="the replicas seeded in advance come back with their count",
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
            verdicts += TheReplicaNode(self.started, revision_id=laid.revision_id).verdicts(
                node, laid.routes[i], f"items[{i}]."
            )
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
            "배포 조회 권한을 받은 사용자가 배포의 복제본을 조회하면, 심은 복제본이 옵니다",
            english=(
                "when a user granted deployment read searches the replicas of the "
                "deployment, the replicas seeded in advance come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARoutedDeploymentAndACaller]:
        return ADeploymentWithRoutes(granted=(Permission.READ,))

    @override
    def when(self) -> When[ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]:
        return SearchingTheReplicasOfTheDeployment()

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
    AUserGrantedNothingSearchesNoReplica(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching_replicas(
    scenario: ReplicaStep,
    adapter: DeploymentAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
