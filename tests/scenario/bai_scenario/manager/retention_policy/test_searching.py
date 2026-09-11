"""보존 정책 검색 — 필터가 무엇을 좁히고, 누가 검색할 수 있는가.

카테고리가 여덟뿐이라 정책도 여덟을 넘지 못한다. 열 건을 넘겨 다음 페이지를 확인하는 시나리오는
없다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.retention_policy import (
    AnActiveAndAnInactivePolicy,
    ManyPoliciesAndACaller,
    OnlyTheNamedPolicyIsLeft,
    TheLaidPoliciesAreLeft,
    TwoPoliciesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.retention_policy.request import (
    RetentionPolicyFilter,
    SearchRetentionPoliciesInput,
)
from ai.backend.common.dto.manager.v2.retention_policy.response import (
    SearchRetentionPoliciesPayload,
)
from ai.backend.manager.api.adapters.retention_policy.adapter import RetentionPolicyAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

type Searched = SearchRetentionPoliciesPayload
type SearchingStep = Scenario[
    SeedingSession, ManyPoliciesAndACaller, RetentionPolicyAdapter, Searched
]


@dataclass(frozen=True)
class SearchingEveryPolicy(When[ManyPoliciesAndACaller, RetentionPolicyAdapter, Searched]):
    """필터 없이 전체를 검색한다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyPoliciesAndACaller) -> str:
        return f"{laid.caller.username}이 필터 없이 전체 조회"

    @override
    async def call(self, adapter: RetentionPolicyAdapter, laid: ManyPoliciesAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search(SearchRetentionPoliciesInput())


@dataclass(frozen=True)
class SearchingByCategory(When[ManyPoliciesAndACaller, RetentionPolicyAdapter, Searched]):
    """골라낸 하나의 카테고리를 필터로 검색한다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyPoliciesAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.named.category.value} 카테고리 필터로 조회"

    @override
    async def call(self, adapter: RetentionPolicyAdapter, laid: ManyPoliciesAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search(
                SearchRetentionPoliciesInput(
                    filter=RetentionPolicyFilter(category=laid.named.category)
                )
            )


@dataclass(frozen=True)
class SearchingTheActiveOnes(When[ManyPoliciesAndACaller, RetentionPolicyAdapter, Searched]):
    """활성인 정책만 필터로 검색한다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyPoliciesAndACaller) -> str:
        return f"{laid.caller.username}이 활성 필터로 조회"

    @override
    async def call(self, adapter: RetentionPolicyAdapter, laid: ManyPoliciesAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search(
                SearchRetentionPoliciesInput(filter=RetentionPolicyFilter(enabled=True))
            )


@dataclass(frozen=True)
class TheSuperadminCountsEveryPolicy(
    Scenario[SeedingSession, ManyPoliciesAndACaller, RetentionPolicyAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-counts-every-policy-laid"

    @override
    def describe(self) -> str:
        return "카테고리가 다른 정책 둘이 있을 때 슈퍼관리자가 필터 없이 조회하면 둘 다 집계된다"

    @override
    def given(self) -> Given[SeedingSession, ManyPoliciesAndACaller]:
        return TwoPoliciesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyPoliciesAndACaller, RetentionPolicyAdapter, Searched]:
        return SearchingEveryPolicy()

    @override
    def then(self) -> Then[ManyPoliciesAndACaller, Searched]:
        return TheLaidPoliciesAreLeft()


@dataclass(frozen=True)
class ACategoryFilterNarrows(
    Scenario[SeedingSession, ManyPoliciesAndACaller, RetentionPolicyAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-category-filter-narrows-the-answer-to-that-category"

    @override
    def describe(self) -> str:
        return "카테고리가 다른 정책 여럿 중 하나의 카테고리를 필터로 조회하면 그 카테고리의 정책 하나만 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyPoliciesAndACaller]:
        return TwoPoliciesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyPoliciesAndACaller, RetentionPolicyAdapter, Searched]:
        return SearchingByCategory()

    @override
    def then(self) -> Then[ManyPoliciesAndACaller, Searched]:
        return OnlyTheNamedPolicyIsLeft()


@dataclass(frozen=True)
class AnEnabledFilterKeepsTheActive(
    Scenario[SeedingSession, ManyPoliciesAndACaller, RetentionPolicyAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "an-enabled-filter-keeps-only-the-active-policies"

    @override
    def describe(self) -> str:
        return "활성과 비활성이 섞여 있을 때 활성 필터로 조회하면 활성인 정책만 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyPoliciesAndACaller]:
        return AnActiveAndAnInactivePolicy(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyPoliciesAndACaller, RetentionPolicyAdapter, Searched]:
        return SearchingTheActiveOnes()

    @override
    def then(self) -> Then[ManyPoliciesAndACaller, Searched]:
        return TheLaidPoliciesAreLeft()


@dataclass(frozen=True)
class TheMonitorSearchesLikeTheSuperadmin(
    Scenario[SeedingSession, ManyPoliciesAndACaller, RetentionPolicyAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-monitor-searches-policies-like-the-superadmin"

    @override
    def describe(self) -> str:
        return "모니터 역할이 필터 없이 조회하면 슈퍼관리자와 같은 응답이 반환된다. 전역 역할 검사는 모니터의 읽기를 허용한다"

    @override
    def given(self) -> Given[SeedingSession, ManyPoliciesAndACaller]:
        return TwoPoliciesAndSomeone(role=UserRole.MONITOR)

    @override
    def when(self) -> When[ManyPoliciesAndACaller, RetentionPolicyAdapter, Searched]:
        return SearchingEveryPolicy()

    @override
    def then(self) -> Then[ManyPoliciesAndACaller, Searched]:
        return TheLaidPoliciesAreLeft()


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotSearch(
    Scenario[SeedingSession, ManyPoliciesAndACaller, RetentionPolicyAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-policies"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 전체 조회를 요청하면 역할 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ManyPoliciesAndACaller]:
        return TwoPoliciesAndSomeone()

    @override
    def when(self) -> When[ManyPoliciesAndACaller, RetentionPolicyAdapter, Searched]:
        return SearchingEveryPolicy()

    @override
    def then(self) -> Then[ManyPoliciesAndACaller, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchingStep] = [
    TheSuperadminCountsEveryPolicy(),
    ACategoryFilterNarrows(),
    AnEnabledFilterKeepsTheActive(),
    TheMonitorSearchesLikeTheSuperadmin(),
    AUserWhoIsNotTheSuperadminMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: RetentionPolicyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
