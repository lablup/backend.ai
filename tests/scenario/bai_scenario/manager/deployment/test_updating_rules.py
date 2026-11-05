"""배포가 걸린 자동 스케일링 규칙 고치기."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.auto_scaling_rule.request import UpdateAutoScalingRuleInput
from ai.backend.common.dto.manager.v2.deployment.response import UpdateAutoScalingRulePayload
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

EDITED_STEP_SIZE = 2
EDITED_TIME_WINDOW = 120

type Answer = UpdateAutoScalingRulePayload
type RuleStep = Scenario[
    TestSeedingSession, RulesOfADeploymentAndACaller, DeploymentAdapter, Answer
]


@dataclass(frozen=True)
class EditingTheFirstRule(When[RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]):
    """심은 규칙 하나의 id 와 고칠 값을 준다. id 는 REST 핸들러처럼 응답 모양에 얹는다."""

    @override
    def operation(self) -> str:
        return "update_rule"

    @override
    def describe(self, laid: RulesOfADeploymentAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 심은 규칙 하나의 단계 크기와 시간 창을 고칩니다",
            english=f"{laid.caller.username} edits the step size and time window of one of the rules seeded in advance",
        )

    @override
    async def call(
        self, adapter: DeploymentAdapter, laid: RulesOfADeploymentAndACaller
    ) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.update_rule(
                UpdateAutoScalingRuleInput(
                    step_size=EDITED_STEP_SIZE,
                    time_window=EDITED_TIME_WINDOW,
                ).model_copy(update={"id": laid.rules[0].id})
            )


@dataclass(frozen=True)
class TheEditedRuleComesBack(Then[RulesOfADeploymentAndACaller, Answer]):
    """고친 규칙이 통째로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "고친 규칙이 전체가 응답으로 옵니다", english="the whole rule edited comes back"
        )

    @override
    def look(
        self, laid: RulesOfADeploymentAndACaller, answered: Answered[Answer]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        edited = replace(laid.rules[0], step_size=EDITED_STEP_SIZE, time_window=EDITED_TIME_WINDOW)
        return TheRuleNode(self.started).verdicts(payload.rule, edited)


@dataclass(frozen=True)
class AUserGrantedDeploymentUpdateEditsARule(
    Scenario[TestSeedingSession, RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-deployment-update-edits-a-rule"

    @override
    def describe(self) -> str:
        return Says(
            "배포 조회와 수정 권한을 받은 사용자가 심은 규칙 하나를 고치면, 고친 규칙이 "
            "옵니다. 규칙 읽기와 고치기는 배포를 먼저 찾는 호출이라 조회 권한도 필요합니다",
            english=(
                "when a user granted deployment read and update edits one of the rules "
                "seeded in advance, the rule edited comes back. The edit reads the "
                "deployment first, so read is also required"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RulesOfADeploymentAndACaller]:
        return RulesOfADeployment(granted=(Permission.READ, Permission.UPDATE))

    @override
    def when(self) -> When[RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return EditingTheFirstRule()

    @override
    def then(self) -> Then[RulesOfADeploymentAndACaller, Answer]:
        return TheEditedRuleComesBack(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingEditsNoRule(
    Scenario[TestSeedingSession, RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-edits-no-rule"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 심은 규칙 하나를 고치려 하면, 규칙이 걸린 "
            "배포를 찾는 조회가 거부됩니다",
            english=(
                "when a user granted nothing tries to edit one of the rules seeded in "
                "advance, the lookup that finds the deployment holding the rule is rejected"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RulesOfADeploymentAndACaller]:
        return RulesOfADeployment()

    @override
    def when(self) -> When[RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return EditingTheFirstRule()

    @override
    def then(self) -> Then[RulesOfADeploymentAndACaller, Answer]:
        return TheCallIsRefused(GenericBadRequest)


STARTED = datetime.now(UTC)

SCENARIOS: list[RuleStep] = [
    AUserGrantedDeploymentUpdateEditsARule(started=STARTED),
    AUserGrantedNothingEditsNoRule(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_updating_rules(
    scenario: RuleStep,
    adapter: DeploymentAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
