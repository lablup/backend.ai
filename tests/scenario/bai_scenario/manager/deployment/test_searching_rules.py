"""배포가 걸린 자동 스케일링 규칙 훑기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.deployment.request import SearchAutoScalingRulesInput
from ai.backend.common.dto.manager.v2.deployment.response import SearchAutoScalingRulesPayload
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.data.deployment.types import AutoScalingRuleOperationScope
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
from bai_scenario.components.auto_scaling_rule import (
    RulesOfADeployment,
    RulesOfADeploymentAndACaller,
    TheRuleNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = SearchAutoScalingRulesPayload
type RuleStep = Scenario[
    TestSeedingSession, RulesOfADeploymentAndACaller, DeploymentAdapter, Answer
]


@dataclass(frozen=True)
class SearchingTheRulesOfTheDeployment(
    When[RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    """심은 배포 하나의 id 만 준다."""

    @override
    def operation(self) -> str:
        return "search_rules"

    @override
    def describe(self, laid: RulesOfADeploymentAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 배포가 걸린 자동 스케일링 규칙을 훑습니다",
            english=f"{laid.caller.username} searches the auto-scaling rules the deployment holds",
        )

    @override
    async def call(self, adapter: DeploymentAdapter, laid: RulesOfADeploymentAndACaller) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.search_rules(
                AutoScalingRuleOperationScope(deployment_id=laid.deployment.id),
                SearchAutoScalingRulesInput(),
            )


@dataclass(frozen=True)
class TheRulePageComesBack(Then[RulesOfADeploymentAndACaller, Answer]):
    """배포가 걸린 규칙이 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "배포가 걸린 규칙이 양과 함께 옵니다",
            english="the auto-scaling rules the deployment holds come back with their count",
        )

    @override
    def look(self, laid: RulesOfADeploymentAndACaller, answered: Answered[Answer]) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [MissingResponse(answered.raised)]
        verdicts: list[Verdict] = [
            Same("total_count", page.total_count, len(laid.rules)),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]
        by_id = {rule.id: rule for rule in laid.rules}
        for i, node in enumerate(page.items):
            rule = by_id.get(node.id)
            if rule is None:
                verdicts.append(Same(f"items[{i}].id", node.id, "a rule the deployment holds"))
            else:
                verdicts += TheRuleNode(self.started).verdicts(node, rule, f"items[{i}].")
        return verdicts


@dataclass(frozen=True)
class AUserGrantedDeploymentReadSearchesTheRules(
    Scenario[TestSeedingSession, RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-deployment-read-searches-the-rules"

    @override
    def describe(self) -> str:
        return Says(
            "배포 조회 권한을 받은 사용자가 배포가 걸린 자동 스케일링 규칙을 훑으면, "
            "그 규칙들이 옵니다",
            english=(
                "when a user granted deployment read searches the auto-scaling rules the "
                "deployment holds, those rules come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RulesOfADeploymentAndACaller]:
        return RulesOfADeployment(granted=(Permission.READ,))

    @override
    def when(self) -> When[RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return SearchingTheRulesOfTheDeployment()

    @override
    def then(self) -> Then[RulesOfADeploymentAndACaller, Answer]:
        return TheRulePageComesBack(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingSearchesNoRule(
    Scenario[TestSeedingSession, RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-searches-no-rule"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 배포가 걸린 자동 스케일링 규칙을 훑으려 하면, "
            "권한이 없다는 이유로 거부됩니다",
            english=(
                "when a user granted nothing tries to search the auto-scaling rules the "
                "deployment holds, the search is rejected because the user lacks permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RulesOfADeploymentAndACaller]:
        return RulesOfADeployment()

    @override
    def when(self) -> When[RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return SearchingTheRulesOfTheDeployment()

    @override
    def then(self) -> Then[RulesOfADeploymentAndACaller, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


STARTED = datetime.now(UTC)

SCENARIOS: list[RuleStep] = [
    AUserGrantedDeploymentReadSearchesTheRules(started=STARTED),
    AUserGrantedNothingSearchesNoRule(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching_rules(
    scenario: RuleStep,
    adapter: DeploymentAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
