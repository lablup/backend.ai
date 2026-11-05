"""배포에 정책 올리기 (있으면 갈아끼우기)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.dto.manager.v2.deployment.request import UpsertDeploymentPolicyInput
from ai.backend.common.dto.manager.v2.deployment.response import UpsertDeploymentPolicyPayload
from ai.backend.common.schema.deployment import IntOrPercent
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
from bai_scenario.components.deployment import ADeploymentAndACaller, ADeploymentInThatPlace
from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = UpsertDeploymentPolicyPayload
type PolicyStep = Scenario[
    TestSeedingSession, ADeploymentAndACaller, DeploymentAdapter, Answer
]


@dataclass(frozen=True)
class UpsertingThePolicyOfTheDeployment(
    When[ADeploymentAndACaller, DeploymentAdapter, Answer]
):
    """심은 배포 하나의 id 와 정책 값을 준다."""

    @override
    def operation(self) -> str:
        return "upsert_policy"

    @override
    def describe(self, laid: ADeploymentAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 배포에 롤링 업데이트 정책을 올립니다",
            english=f"{laid.caller.username} puts a rolling-update policy on the deployment",
        )

    @override
    async def call(
        self, adapter: DeploymentAdapter, laid: ADeploymentAndACaller
    ) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.upsert_policy(
                UpsertDeploymentPolicyInput(
                    deployment_id=laid.deployment.id,
                    strategy=DeploymentStrategy.ROLLING,
                )
            )


@dataclass(frozen=True)
class ThePolicyPutComesBack(Then[ADeploymentAndACaller, Answer]):
    """올린 정책이 통째로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "올린 정책이 전체가 응답으로 옵니다",
            english="the whole policy put comes back",
        )

    @override
    def look(
        self, laid: ADeploymentAndACaller, answered: Answered[Answer]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        node = payload.policy
        spec = node.strategy_spec
        return [
            Skipped("id", "the database generates it"),
            Skipped("field_id", "the database generates it"),
            Held[UUID](
                "deployment_id",
                node.deployment_id,
                SameAs(
                    laid.deployment.id,
                    Says("정책을 올린 배포의 id", english="the id of the deployment the policy was put on"),
                ),
            ),
            Same("strategy_spec.strategy", spec.strategy, DeploymentStrategy.ROLLING),
            Same("strategy_spec.max_surge", spec.max_surge, IntOrPercent(percent=0.5)),
            Same("strategy_spec.max_unavailable", spec.max_unavailable, IntOrPercent(percent=0.0)),
            Held("created_at", node.created_at, WrittenByThisRun(self.started)),
            Held("updated_at", node.updated_at, WrittenByThisRun(self.started)),
        ]


@dataclass(frozen=True)
class AUserGrantedDeploymentCreatePutsThePolicy(
    Scenario[TestSeedingSession, ADeploymentAndACaller, DeploymentAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-deployment-create-puts-the-policy"

    @override
    def describe(self) -> str:
        return Says(
            "배포 생성 권한을 받은 사용자가 배포에 정책을 올리면, 올린 정책이 옵니다",
            english=(
                "when a user granted deployment create puts a policy on the deployment, "
                "the policy put comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace(granted=(Permission.CREATE,))

    @override
    def when(self) -> When[ADeploymentAndACaller, DeploymentAdapter, Answer]:
        return UpsertingThePolicyOfTheDeployment()

    @override
    def then(self) -> Then[ADeploymentAndACaller, Answer]:
        return ThePolicyPutComesBack(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingPutsNoPolicy(
    Scenario[TestSeedingSession, ADeploymentAndACaller, DeploymentAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-puts-no-policy"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 배포에 정책을 올리려 하면, 권한이 없다는 "
            "이유로 거부됩니다",
            english=(
                "when a user granted nothing tries to put a policy on the deployment, "
                "the upsert is rejected because the user lacks permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADeploymentAndACaller]:
        return ADeploymentInThatPlace()

    @override
    def when(self) -> When[ADeploymentAndACaller, DeploymentAdapter, Answer]:
        return UpsertingThePolicyOfTheDeployment()

    @override
    def then(self) -> Then[ADeploymentAndACaller, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


STARTED = datetime.now()

SCENARIOS: list[PolicyStep] = [
    AUserGrantedDeploymentCreatePutsThePolicy(started=STARTED),
    AUserGrantedNothingPutsNoPolicy(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_upserting_policy(
    scenario: PolicyStep,
    adapter: DeploymentAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
