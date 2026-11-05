"""배포가 걸린 자동 스케일링 규칙 id 로 한꺼번에 읽기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.deployment.response import AutoScalingRuleNode
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
from bai_scenario.components.auto_scaling_rule import (
    RulesOfADeployment,
    RulesOfADeploymentAndACaller,
    TheRuleNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = list[AutoScalingRuleNode | Exception | None]
type RuleStep = Scenario[
    TestSeedingSession, RulesOfADeploymentAndACaller, DeploymentAdapter, Answer
]


@dataclass(frozen=True)
class LoadingTheSeededRules(When[RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]):
    """심은 규칙들의 id 만 준다."""

    @override
    def operation(self) -> str:
        return "batch_load_auto_scaling_rules_by_ids"

    @override
    def describe(self, laid: RulesOfADeploymentAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 심은 규칙 {len(laid.rules)}개를 id 로 한꺼번에 읽습니다",
            english=f"{laid.caller.username} batch loads {len(laid.rules)} rules by id",
        )

    @override
    async def call(self, adapter: DeploymentAdapter, laid: RulesOfADeploymentAndACaller) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.batch_load_auto_scaling_rules_by_ids([
                rule.id for rule in laid.rules
            ])


@dataclass(frozen=True)
class TheRulesComeBackInOrder(Then[RulesOfADeploymentAndACaller, Answer]):
    """규칙이 요청에 넣은 순서대로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "규칙이 요청에 넣은 순서대로 옵니다",
            english="the rules come back in the order they were put in the request",
        )

    @override
    def look(self, laid: RulesOfADeploymentAndACaller, answered: Answered[Answer]) -> list[Verdict]:
        rules = answered.response
        if rules is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [Same("loaded count", len(rules), len(laid.rules))]
        for i, (node, rule) in enumerate(zip(rules, laid.rules, strict=False)):
            if isinstance(node, AutoScalingRuleNode):
                verdicts += TheRuleNode(self.started).verdicts(node, rule, f"[{i}].")
            else:
                verdicts.append(Same(f"[{i}]", type(node).__name__, "AutoScalingRuleNode"))
        return verdicts


@dataclass(frozen=True)
class EveryEntryIsRefused(Then[RulesOfADeploymentAndACaller, Answer]):
    """규칙 없이, 모든 항목이 같은 이유로 거부된 예외로 온다."""

    @override
    def says(self) -> str:
        return Says(
            "규칙 없이 모든 항목이 거부된 예외로 옵니다",
            english="no rule comes back and every entry is the exception the check raised",
        )

    @override
    def look(self, laid: RulesOfADeploymentAndACaller, answered: Answered[Answer]) -> list[Verdict]:
        rules = answered.response
        if rules is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [Same("loaded count", len(rules), len(laid.rules))]
        for i, entry in enumerate(rules):
            verdicts.append(
                Refused(NotEnoughPermission, entry if isinstance(entry, Exception) else None)
                if entry is not None
                else Same(f"[{i}]", type(entry).__name__, "exception")
            )
        return verdicts


@dataclass(frozen=True)
class AUserGrantedDeploymentReadLoadsTheRulesById(
    Scenario[TestSeedingSession, RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-deployment-read-loads-the-rules-by-id"

    @override
    def describe(self) -> str:
        return Says(
            "배포 조회 권한을 받은 사용자가 배포가 걸린 자동 스케일링 규칙을 id 로 한꺼번에 "
            "읽으면, 그 규칙들이 옵니다",
            english=(
                "when a user granted deployment read batch loads the auto-scaling rules the "
                "deployment holds by id, those rules come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RulesOfADeploymentAndACaller]:
        return RulesOfADeployment(granted=(Permission.READ,))

    @override
    def when(self) -> When[RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return LoadingTheSeededRules()

    @override
    def then(self) -> Then[RulesOfADeploymentAndACaller, Answer]:
        return TheRulesComeBackInOrder(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingGetsARefusalForEachRule(
    Scenario[TestSeedingSession, RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-gets-a-refusal-for-each-rule"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 배포가 걸린 자동 스케일링 규칙을 id 로 한꺼번에 "
            "읽으려 하면, 모든 항목이 권한이 없다는 이유로 거부됩니다",
            english=(
                "when a user granted nothing tries to batch load the auto-scaling rules the "
                "deployment holds by id, every entry is rejected because the user lacks permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RulesOfADeploymentAndACaller]:
        return RulesOfADeployment()

    @override
    def when(self) -> When[RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return LoadingTheSeededRules()

    @override
    def then(self) -> Then[RulesOfADeploymentAndACaller, Answer]:
        return EveryEntryIsRefused()


STARTED = datetime.now(UTC)

SCENARIOS: list[RuleStep] = [
    AUserGrantedDeploymentReadLoadsTheRulesById(started=STARTED),
    AUserGrantedNothingGetsARefusalForEachRule(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_batch_loading_rules(
    scenario: RuleStep,
    adapter: DeploymentAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
