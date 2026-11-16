"""배포가 걸린 정책 id 로 한꺼번에 읽기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.entity.deployment_policy import DeploymentPolicyID
from ai.backend.common.dto.manager.v2.deployment.response import DeploymentPolicyNode
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
from bai_scenario.components.deployment_policy import (
    APolicyAndACaller,
    APolicyOfADeploymentAndACaller,
    ThePolicyNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = list[DeploymentPolicyNode | Exception | None]
type PolicyStep = Scenario[
    TestSeedingSession, APolicyOfADeploymentAndACaller, DeploymentAdapter, Answer
]


@dataclass(frozen=True)
class LoadingTheSeededPolicies(When[APolicyOfADeploymentAndACaller, DeploymentAdapter, Answer]):
    """심은 정책 하나의 id 만 준다."""

    @override
    def operation(self) -> str:
        return "batch_load_policies_by_ids"

    @override
    def describe(self, laid: APolicyOfADeploymentAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 심은 정책 하나를 id 로 한꺼번에 읽습니다",
            english=f"{laid.caller.username} batch loads the policy seeded in advance by id",
        )

    @override
    async def call(
        self, adapter: DeploymentAdapter, laid: APolicyOfADeploymentAndACaller
    ) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.batch_load_policies_by_ids([DeploymentPolicyID(laid.policy.id)])


@dataclass(frozen=True)
class ThePolicyComesBackInOrder(Then[APolicyOfADeploymentAndACaller, Answer]):
    """정책이 요청에 넣은 순서대로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "정책이 요청에 넣은 순서대로 옵니다",
            english="the policy comes back in the order it was put in the request",
        )

    @override
    def look(
        self, laid: APolicyOfADeploymentAndACaller, answered: Answered[Answer]
    ) -> list[Verdict]:
        policies = answered.response
        if policies is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        if len(policies) == 1 and isinstance(policies[0], DeploymentPolicyNode):
            return ThePolicyNode(self.started).verdicts(policies[0], laid.policy, "[0].")
        return [Same("[0]", type(policies[0]).__name__, "DeploymentPolicyNode")]


@dataclass(frozen=True)
class EveryEntryIsRefused(Then[APolicyOfADeploymentAndACaller, Answer]):
    """정책 없이, 모든 항목이 같은 이유로 거부된 예외로 온다."""

    @override
    def says(self) -> str:
        return Says(
            "정책 없이 모든 항목이 거부된 예외로 옵니다",
            english="no policy comes back and every entry is the exception the check raised",
        )

    @override
    def look(
        self, laid: APolicyOfADeploymentAndACaller, answered: Answered[Answer]
    ) -> list[Verdict]:
        policies = answered.response
        if policies is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Refused(NotEnoughPermission, entry if isinstance(entry, Exception) else None)
            if entry is not None
            else Same("[0]", type(entry).__name__, "exception")
            for entry in policies
        ]


@dataclass(frozen=True)
class AUserGrantedDeploymentReadLoadsThePolicyById(
    Scenario[TestSeedingSession, APolicyOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-deployment-read-loads-the-policy-by-id"

    @override
    def describe(self) -> str:
        return Says(
            "배포 조회 권한을 받은 사용자가 배포가 걸린 정책을 id 로 한꺼번에 읽으면, "
            "그 정책이 옵니다",
            english=(
                "when a user granted deployment read batch loads the policy the deployment "
                "holds by id, that policy comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyOfADeploymentAndACaller]:
        return APolicyAndACaller(granted=(Permission.READ,))

    @override
    def when(self) -> When[APolicyOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return LoadingTheSeededPolicies()

    @override
    def then(self) -> Then[APolicyOfADeploymentAndACaller, Answer]:
        return ThePolicyComesBackInOrder(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingGetsARefusalForThePolicy(
    Scenario[TestSeedingSession, APolicyOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-gets-a-refusal-for-the-policy"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 배포가 걸린 정책을 id 로 한꺼번에 읽으려 하면, "
            "모든 항목이 권한이 없다는 이유로 거부됩니다",
            english=(
                "when a user granted nothing tries to batch load the policy the deployment "
                "holds by id, every entry is rejected because the user lacks permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyOfADeploymentAndACaller]:
        return APolicyAndACaller()

    @override
    def when(self) -> When[APolicyOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return LoadingTheSeededPolicies()

    @override
    def then(self) -> Then[APolicyOfADeploymentAndACaller, Answer]:
        return EveryEntryIsRefused()


STARTED = datetime.now(UTC)

SCENARIOS: list[PolicyStep] = [
    AUserGrantedDeploymentReadLoadsThePolicyById(started=STARTED),
    AUserGrantedNothingGetsARefusalForThePolicy(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_batch_loading_policies(
    scenario: PolicyStep,
    adapter: DeploymentAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
