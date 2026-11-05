"""배포가 걸린 자동 스케일링 규칙 하나 읽기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.deployment.response import GetAutoScalingRulePayload
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
from bai_scenario.components.auto_scaling_rule import (
    RulesOfADeployment,
    RulesOfADeploymentAndACaller,
    TheRuleNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = GetAutoScalingRulePayload
type RuleStep = Scenario[
    TestSeedingSession, RulesOfADeploymentAndACaller, DeploymentAdapter, Answer
]


@dataclass(frozen=True)
class ReadingTheFirstRule(When[RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]):
    """심은 규칙 하나의 id 만 준다."""

    @override
    def operation(self) -> str:
        return "get_rule"

    @override
    def describe(self, laid: RulesOfADeploymentAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 심은 규칙 하나를 id 로 읽습니다",
            english=f"{laid.caller.username} reads one of the rules seeded in advance by id",
        )

    @override
    async def call(
        self, adapter: DeploymentAdapter, laid: RulesOfADeploymentAndACaller
    ) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.get_rule(laid.rules[0].id)


@dataclass(frozen=True)
class TheRuleReadComesBack(Then[RulesOfADeploymentAndACaller, Answer]):
    """읽은 규칙이 통째로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "읽은 규칙이 전체가 응답으로 옵니다", english="the whole rule read comes back"
        )

    @override
    def look(
        self, laid: RulesOfADeploymentAndACaller, answered: Answered[Answer]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return TheRuleNode(self.started).verdicts(payload.rule, laid.rules[0])


@dataclass(frozen=True)
class AUserGrantedDeploymentReadReadsARule(
    Scenario[TestSeedingSession, RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-deployment-read-reads-a-rule"

    @override
    def describe(self) -> str:
        return Says(
            "배포 조회 권한을 받은 사용자가 심은 규칙 하나를 id 로 읽으면, 그 규칙이 옵니다",
            english=(
                "when a user granted deployment read reads one of the rules seeded in "
                "advance by id, that rule comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RulesOfADeploymentAndACaller]:
        return RulesOfADeployment(granted=(Permission.READ,))

    @override
    def when(self) -> When[RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return ReadingTheFirstRule()

    @override
    def then(self) -> Then[RulesOfADeploymentAndACaller, Answer]:
        return TheRuleReadComesBack(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingReadsNoRule(
    Scenario[TestSeedingSession, RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-reads-no-rule"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 심은 규칙 하나를 id 로 읽으려 하면, 규칙이 "
            "걸린 배포를 찾는 조회가 거부됩니다",
            english=(
                "when a user granted nothing tries to read one of the rules seeded in "
                "advance by id, the lookup that finds the deployment holding the rule "
                "is rejected"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RulesOfADeploymentAndACaller]:
        return RulesOfADeployment()

    @override
    def when(self) -> When[RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return ReadingTheFirstRule()

    @override
    def then(self) -> Then[RulesOfADeploymentAndACaller, Answer]:
        return TheCallIsRefused(GenericBadRequest)


STARTED = datetime.now(UTC)

SCENARIOS: list[RuleStep] = [
    AUserGrantedDeploymentReadReadsARule(started=STARTED),
    AUserGrantedNothingReadsNoRule(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading_rules(
    scenario: RuleStep,
    adapter: DeploymentAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
