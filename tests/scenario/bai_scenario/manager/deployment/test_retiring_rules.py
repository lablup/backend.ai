"""배포가 걸린 자동 스케일링 규칙 purge 하기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.dto.manager.v2.deployment.response import DeleteAutoScalingRulePayload
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.auto_scaling_rule import (
    RULE_ID,
    RulesOfADeployment,
    RulesOfADeploymentAndACaller,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = DeleteAutoScalingRulePayload
type RuleStep = Scenario[
    TestSeedingSession, RulesOfADeploymentAndACaller, DeploymentAdapter, Answer
]


@dataclass(frozen=True)
class PurgingTheFirstRule(When[RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]):
    """심은 규칙 하나의 id 만 준다."""

    @override
    def operation(self) -> str:
        return "purge_rule"

    @override
    def describe(self, laid: RulesOfADeploymentAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 심은 규칙 하나를 purge 합니다",
            english=f"{laid.caller.username} purges one of the rules seeded in advance",
        )

    @override
    async def call(
        self, adapter: DeploymentAdapter, laid: RulesOfADeploymentAndACaller
    ) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.purge_rule(laid.rules[0].id)


@dataclass(frozen=True)
class TheRuleIsGone(Then[RulesOfADeploymentAndACaller, Answer]):
    """purge 한 규칙의 id 가 응답으로 온다."""

    @override
    def says(self) -> str:
        return Says(
            "purge 한 규칙의 id 가 응답으로 옵니다",
            english="the id of the purged rule comes back",
        )

    @override
    def look(
        self, laid: RulesOfADeploymentAndACaller, answered: Answered[Answer]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            Held[UUID]("id", payload.id, SameAs(laid.rules[0].id, RULE_ID)),
            Held[UUID]("field_id", payload.field_id, SameAs(laid.rules[0].id, RULE_ID)),
        ]


@dataclass(frozen=True)
class AUserGrantedDeploymentPurgePurgesARule(
    Scenario[TestSeedingSession, RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-deployment-purge-purges-a-rule"

    @override
    def describe(self) -> str:
        return Says(
            "배포 조회와 영구 삭제 권한을 받은 사용자가 배포가 걸린 자동 스케일링 규칙 하나를 "
            "purge 하면, 그 규칙의 id 가 옵니다. 규칙 purge 는 배포를 먼저 찾는 호출이라 "
            "조회 권한도 필요합니다",
            english=(
                "when a user granted deployment read and purge purges one of the "
                "auto-scaling rules the deployment holds, the id of that rule comes back. "
                "The purge reads the deployment first, so read is also required"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RulesOfADeploymentAndACaller]:
        return RulesOfADeployment(granted=(Permission.READ, Permission.HARD_DELETE))

    @override
    def when(self) -> When[RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return PurgingTheFirstRule()

    @override
    def then(self) -> Then[RulesOfADeploymentAndACaller, Answer]:
        return TheRuleIsGone()


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNoRule(
    Scenario[TestSeedingSession, RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purges-no-rule"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 배포가 걸린 자동 스케일링 규칙 하나를 purge 하려 하면, "
            "규칙이 걸린 배포를 찾는 조회가 거부됩니다",
            english=(
                "when a user granted nothing tries to purge one of the auto-scaling rules "
                "the deployment holds, the lookup that finds the deployment holding the "
                "rule is rejected"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RulesOfADeploymentAndACaller]:
        return RulesOfADeployment()

    @override
    def when(self) -> When[RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return PurgingTheFirstRule()

    @override
    def then(self) -> Then[RulesOfADeploymentAndACaller, Answer]:
        return TheCallIsRefused(GenericBadRequest)


SCENARIOS: list[RuleStep] = [
    AUserGrantedDeploymentPurgePurgesARule(),
    AUserGrantedNothingPurgesNoRule(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_retiring_rules(
    scenario: RuleStep,
    adapter: DeploymentAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
