"""배포 정책 훑기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.deployment.request import (
    DeploymentPolicyFilter,
    SearchDeploymentPoliciesInput,
)
from ai.backend.common.dto.manager.v2.deployment.response import (
    SearchDeploymentPoliciesPayload,
)
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
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
from bai_scenario.components.deployment_policy import (
    APolicyAndACaller,
    APolicyOfADeploymentAndACaller,
    ThePolicyNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = SearchDeploymentPoliciesPayload
type PolicyStep = Scenario[
    TestSeedingSession, APolicyOfADeploymentAndACaller, DeploymentAdapter, Answer
]


@dataclass(frozen=True)
class SearchingEveryPolicy(When[APolicyOfADeploymentAndACaller, DeploymentAdapter, Answer]):
    """심은 배포 하나의 정책만 남기고 한 페이지를 훑는다."""

    @override
    def operation(self) -> str:
        return "search_policies"

    @override
    def describe(self, laid: APolicyOfADeploymentAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 배포 정책을 하나의 기준으로 걸러 훑습니다",
            english=(
                f"{laid.caller.username} searches the deployment policies with one filter "
                f"and pagination"
            ),
        )

    @override
    async def call(
        self, adapter: DeploymentAdapter, laid: APolicyOfADeploymentAndACaller
    ) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.search_policies(
                SearchDeploymentPoliciesInput(
                    filter=DeploymentPolicyFilter(deployment_id=laid.deployment.id),
                    limit=10,
                    offset=0,
                )
            )


@dataclass(frozen=True)
class ThePolicyPageComesBack(Then[APolicyOfADeploymentAndACaller, Answer]):
    """심은 정책이 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "기준이 제외하는 다른 배포의 정책은 오지 않고, 심은 정책이 양과 함께 옵니다",
            english=(
                "the policy on another deployment the filter excludes does not come back, "
                "and the policy seeded in advance comes back with its count"
            ),
        )

    @override
    def look(
        self, laid: APolicyOfADeploymentAndACaller, answered: Answered[Answer]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [MissingResponse(answered.raised)]
        verdicts: list[Verdict] = [
            Same("total_count", page.total_count, 1),
            Same("items count", len(page.items), 1),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]
        for i, node in enumerate(page.items):
            verdicts += ThePolicyNode(self.started).verdicts(node, laid.policy, f"items[{i}].")
        return verdicts


@dataclass(frozen=True)
class TheSuperadminSearchesThePolicies(
    Scenario[TestSeedingSession, APolicyOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-searches-the-policies"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 배포 정책을 기준으로 걸러 훑으면, 심은 정책이 옵니다. 정책 훑기는 "
            "전역 권한이 필요한 호출이라 이 행의 요청 사용자는 superadmin 입니다",
            english=(
                "when the superadmin searches the deployment policies with a filter, the "
                "policy seeded in advance comes back. The requesting user of this row is "
                "the superadmin because the search is gated by the global role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyOfADeploymentAndACaller]:
        return APolicyAndACaller(role=UserRole.SUPERADMIN, outside=True)

    @override
    def when(self) -> When[APolicyOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return SearchingEveryPolicy()

    @override
    def then(self) -> Then[APolicyOfADeploymentAndACaller, Answer]:
        return ThePolicyPageComesBack(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingSearchesNoPolicy(
    Scenario[TestSeedingSession, APolicyOfADeploymentAndACaller, DeploymentAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-searches-no-policy"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 배포 정책을 훑으려 하면, 전역 권한이 없다는 "
            "이유로 거부됩니다",
            english=(
                "when a user granted nothing tries to search the deployment policies, the "
                "search is rejected because the user lacks the global role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, APolicyOfADeploymentAndACaller]:
        return APolicyAndACaller(role=UserRole.USER)

    @override
    def when(self) -> When[APolicyOfADeploymentAndACaller, DeploymentAdapter, Answer]:
        return SearchingEveryPolicy()

    @override
    def then(self) -> Then[APolicyOfADeploymentAndACaller, Answer]:
        return TheCallIsRefused(InsufficientPrivilege)


STARTED = datetime.now(UTC)

SCENARIOS: list[PolicyStep] = [
    TheSuperadminSearchesThePolicies(started=STARTED),
    AUserGrantedNothingSearchesNoPolicy(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching_policies(
    scenario: PolicyStep,
    adapter: DeploymentAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
