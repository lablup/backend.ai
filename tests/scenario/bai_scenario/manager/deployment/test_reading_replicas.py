"""배포가 걸린 복제본 하나 읽기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.deployment.response import ReplicaNode
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
    TheReplicaNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = ReplicaNode | None
type ReplicaStep = Scenario[
    TestSeedingSession, ARoutedDeploymentAndACaller, DeploymentAdapter, Answer
]


@dataclass(frozen=True)
class ReadingTheReplicaOfTheDeployment(
    When[ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]
):
    """심은 라우트 하나의 id 만 준다."""

    @override
    def operation(self) -> str:
        return "get_replica"

    @override
    def describe(self, laid: ARoutedDeploymentAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 심은 복제본 하나를 읽습니다",
            english=f"{laid.caller.username} reads one replica seeded in advance",
        )

    @override
    async def call(self, adapter: DeploymentAdapter, laid: ARoutedDeploymentAndACaller) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.get_replica(laid.routes[0].id)


@dataclass(frozen=True)
class TheReplicaComesBack(Then[ARoutedDeploymentAndACaller, Answer]):
    """심은 복제본이 전체가 응답으로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "심은 복제본이 전체가 응답으로 옵니다",
            english="the replica seeded in advance comes back whole",
        )

    @override
    def look(self, laid: ARoutedDeploymentAndACaller, answered: Answered[Answer]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [MissingResponse(answered.raised)]
        return TheReplicaNode(self.started, revision_id=laid.revision_id).verdicts(
            node, laid.routes[0]
        )


@dataclass(frozen=True)
class AUserGrantedDeploymentReadReadsTheReplica(
    Scenario[TestSeedingSession, ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-deployment-read-reads-the-replica"

    @override
    def describe(self) -> str:
        return Says(
            "배포 조회 권한을 받은 사용자가 배포의 복제본을 읽으면, 그 복제본이 옵니다",
            english=(
                "when a user granted deployment read reads a replica of the deployment, "
                "that replica comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARoutedDeploymentAndACaller]:
        return ADeploymentWithRoutes(granted=(Permission.READ,))

    @override
    def when(self) -> When[ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]:
        return ReadingTheReplicaOfTheDeployment()

    @override
    def then(self) -> Then[ARoutedDeploymentAndACaller, Answer]:
        return TheReplicaComesBack(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingReadsNoReplica(
    Scenario[TestSeedingSession, ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-reads-no-replica"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 배포의 복제본을 읽으려 하면, 복제본이 걸린 "
            "배포를 찾는 조회가 거부됩니다",
            english=(
                "when a user granted nothing tries to read a replica of the deployment, "
                "the lookup that finds the deployment holding the replica is rejected"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ARoutedDeploymentAndACaller]:
        return ADeploymentWithRoutes()

    @override
    def when(self) -> When[ARoutedDeploymentAndACaller, DeploymentAdapter, Answer]:
        return ReadingTheReplicaOfTheDeployment()

    @override
    def then(self) -> Then[ARoutedDeploymentAndACaller, Answer]:
        return TheCallIsRefused(GenericBadRequest)


STARTED = datetime.now(UTC)

SCENARIOS: list[ReplicaStep] = [
    AUserGrantedDeploymentReadReadsTheReplica(started=STARTED),
    AUserGrantedNothingReadsNoReplica(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading_replicas(
    scenario: ReplicaStep,
    adapter: DeploymentAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
