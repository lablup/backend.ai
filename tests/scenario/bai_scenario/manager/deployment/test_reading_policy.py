"""배포가 걸린 정책 하나 읽기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.deployment.response import GetDeploymentPolicyPayload
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
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
from bai_scenario.components.deployment_policy import (
    APolicyAndACaller,
    APolicyOfADeploymentAndACaller,
    ThePolicyNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = GetDeploymentPolicyPayload
type PolicyStep = Scenario[
    TestSeedingSession, APolicyOfADeploymentAndACaller, DeploymentAdapter, Answer
]


@dataclass(frozen=True)
class ReadingThePolicyOfTheDeployment(
    When[APolicyOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    """심은 배포 하나의 id 만 준다."""

    @override
    def operation(self) -> str:
        return "get_policy"

    @override
    def describe(self, laid: APolicyOfADeploymentAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 배포가 걸린 정책을 읽습니다",
            english=f"{laid.caller.username} reads the policy the deployment holds",
        )

    @override
    async def call(
        self, adapter: DeploymentAdapter, laid: APolicyOfADeploymentAndACaller
    ) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.get_policy(laid.deployment.id)


@dataclass(frozen=True)
class ThePolicyComesBack(Then[APolicyOfADeploymentAndACaller, Answer]):
    """배포가 걸린 정책이 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "배포가 걸린 정책이 전체가 응답으로 옵니다",
            english="the policy the deployment holds comes back whole",
        )

    @override
    def look(
        self, laid: APolicyOfADeploymentAndACaller, answered: Answered[Answer]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return ThePolicyNode(self.started).verdicts(payload.policy, laid.policy)


@dataclass(frozen=True)
class AUserGrantedDeploymentReadReadsThePolicy(
    Scenario[TestSeedingSession, APolicyOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-deployment-read-reads-the-policy"

    @override
    def describe(self) -> str:
        return Says(
            "배포 조회 권한을 받은 사용자가 배포가 걸린 정책을 읽으면, 그 정책이 옵니다",
            english=(
                "when a user granted deployment read reads the policy the deployment "
                "holds, that policy comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyOfADeploymentAndACaller]:
        return APolicyAndACaller(granted=(Permission.READ,))

    @override
    def when(self) -> When[APolicyOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return ReadingThePolicyOfTheDeployment()

    @override
    def then(self) -> Then[APolicyOfADeploymentAndACaller, Answer]:
        return ThePolicyComesBack(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingReadsNoPolicy(
    Scenario[TestSeedingSession, APolicyOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-reads-no-policy"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 배포가 걸린 정책을 읽으려 하면, 권한이 없다는 "
            "이유로 거부됩니다",
            english=(
                "when a user granted nothing tries to read the policy the deployment "
                "holds, the read is rejected because the user lacks permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyOfADeploymentAndACaller]:
        return APolicyAndACaller()

    @override
    def when(self) -> When[APolicyOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return ReadingThePolicyOfTheDeployment()

    @override
    def then(self) -> Then[APolicyOfADeploymentAndACaller, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


STARTED = datetime.now()

SCENARIOS: list[PolicyStep] = [
    AUserGrantedDeploymentReadReadsThePolicy(started=STARTED),
    AUserGrantedNothingReadsNoPolicy(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading_policy(
    scenario: PolicyStep,
    adapter: DeploymentAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
