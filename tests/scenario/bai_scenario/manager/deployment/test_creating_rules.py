"""배포가 걸린 자동 스케일링 규칙 만들기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.dto.manager.v2.auto_scaling_rule.request import CreateAutoScalingRuleInput
from ai.backend.common.dto.manager.v2.deployment.response import CreateAutoScalingRulePayload
from ai.backend.common.types import AutoScalingMetricSource
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    SameAs,
    Says,
    Scenario,
    Skipped,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.auto_scaling_rule import (
    RulesOfADeployment,
    RulesOfADeploymentAndACaller,
)
from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = CreateAutoScalingRulePayload
type RuleStep = Scenario[
    TestSeedingSession, RulesOfADeploymentAndACaller, DeploymentAdapter, Answer
]


@dataclass(frozen=True)
class MakingARuleOfTheDeployment(
    When[RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    """심은 배포 하나의 id 와 규칙 값을 준다."""

    @override
    def operation(self) -> str:
        return "create_rule"

    @override
    def describe(self, laid: RulesOfADeploymentAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 배포에 자동 스케일링 규칙 하나를 만듭니다",
            english=f"{laid.caller.username} makes one auto-scaling rule of the deployment",
        )

    @override
    async def call(
        self, adapter: DeploymentAdapter, laid: RulesOfADeploymentAndACaller
    ) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.create_rule(
                CreateAutoScalingRuleInput(
                    model_deployment_id=laid.deployment.id,
                    metric_source=AutoScalingMetricSource.KERNEL,
                    metric_name="made-rule",
                    step_size=1,
                    time_window=60,
                )
            )


@dataclass(frozen=True)
class TheMadeRuleComesBack(Then[RulesOfADeploymentAndACaller, Answer]):
    """만든 규칙이 통째로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "만든 규칙이 전체가 응답으로 옵니다", english="the whole rule made comes back"
        )

    @override
    def look(
        self, laid: RulesOfADeploymentAndACaller, answered: Answered[Answer]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        node = payload.rule
        return [
            Skipped("id", "the database generates it"),
            Skipped("field_id", "the database generates it"),
            Held[UUID](
                "deployment_id",
                node.deployment_id,
                SameAs(
                    laid.deployment.id,
                    Says("규칙이 걸린 배포의 id", english="the id of the deployment the rule scales"),
                ),
            ),
            Same("metric_source", node.metric_source, "kernel"),
            Same("metric_name", node.metric_name, "made-rule"),
            Same("min_threshold", node.min_threshold, None),
            Same("max_threshold", node.max_threshold, None),
            Same("step_size", node.step_size, 1),
            Same("time_window", node.time_window, 60),
            Same("min_replicas", node.min_replicas, None),
            Same("max_replicas", node.max_replicas, None),
            Same("prometheus_query_preset_id", node.prometheus_query_preset_id, None),
            Held("created_at", node.created_at, WrittenByThisRun(self.started)),
            Same("last_triggered_at", node.last_triggered_at, None),
        ]


@dataclass(frozen=True)
class AUserGrantedDeploymentCreateMakesARule(
    Scenario[TestSeedingSession, RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-deployment-create-makes-a-rule"

    @override
    def describe(self) -> str:
        return Says(
            "배포 생성 권한을 받은 사용자가 배포에 자동 스케일링 규칙을 만들면, "
            "만든 규칙이 옵니다",
            english=(
                "when a user granted deployment create makes an auto-scaling rule of the "
                "deployment, the rule made comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RulesOfADeploymentAndACaller]:
        return RulesOfADeployment(granted=(Permission.CREATE,))

    @override
    def when(self) -> When[RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return MakingARuleOfTheDeployment()

    @override
    def then(self) -> Then[RulesOfADeploymentAndACaller, Answer]:
        return TheMadeRuleComesBack(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMakesNoRule(
    Scenario[TestSeedingSession, RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-makes-no-rule"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 배포에 자동 스케일링 규칙을 만들려 하면, "
            "권한이 없다는 이유로 거부됩니다",
            english=(
                "when a user granted nothing tries to make an auto-scaling rule of the "
                "deployment, the create is rejected because the user lacks permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RulesOfADeploymentAndACaller]:
        return RulesOfADeployment()

    @override
    def when(self) -> When[RulesOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return MakingARuleOfTheDeployment()

    @override
    def then(self) -> Then[RulesOfADeploymentAndACaller, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


STARTED = datetime.now(UTC)

SCENARIOS: list[RuleStep] = [
    AUserGrantedDeploymentCreateMakesARule(started=STARTED),
    AUserGrantedNothingMakesNoRule(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_creating_rules(
    scenario: RuleStep,
    adapter: DeploymentAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
