"""마스킹 정책 검색 — 누가 검색할 수 있는가.

필터가 무엇을 좁히는지는 시나리오로 두지 않는다. 대상이 `default`, `login_history`, `audit_logs`
셋뿐이라 정책도 셋을 넘지 못하고, 10건을 넘겨 다음 페이지를 확인하는 시나리오도 없다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.client_ip_masking.request import (
    AdminSearchClientIPMaskingPoliciesInput,
)
from ai.backend.common.dto.manager.v2.client_ip_masking.response import (
    AdminSearchClientIPMaskingPoliciesPayload,
)
from ai.backend.manager.api.adapters.client_ip_masking.adapter import ClientIPMaskingAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.client_ip_masking import (
    ManyMaskingPoliciesAndACaller,
    TheLaidMaskingPoliciesAreLeft,
    TwoMaskingPoliciesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type Searched = AdminSearchClientIPMaskingPoliciesPayload
type SearchingStep = Scenario[
    SeedingSession, ManyMaskingPoliciesAndACaller, ClientIPMaskingAdapter, Searched
]


@dataclass(frozen=True)
class SearchingEveryPolicy(When[ManyMaskingPoliciesAndACaller, ClientIPMaskingAdapter, Searched]):
    """필터 없이 전체를 검색한다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyMaskingPoliciesAndACaller) -> str:
        return f"{laid.caller.username}이 필터 없이 전체 조회"

    @override
    async def call(
        self, adapter: ClientIPMaskingAdapter, laid: ManyMaskingPoliciesAndACaller
    ) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(AdminSearchClientIPMaskingPoliciesInput())


@dataclass(frozen=True)
class TheSuperadminCountsEveryPolicy(
    Scenario[SeedingSession, ManyMaskingPoliciesAndACaller, ClientIPMaskingAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-counts-every-masking-policy-laid"

    @override
    def describe(self) -> str:
        return "대상이 다른 정책 둘이 있을 때 슈퍼관리자가 필터 없이 조회하면 둘 다 집계된다"

    @override
    def given(self) -> Given[SeedingSession, ManyMaskingPoliciesAndACaller]:
        return TwoMaskingPoliciesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyMaskingPoliciesAndACaller, ClientIPMaskingAdapter, Searched]:
        return SearchingEveryPolicy()

    @override
    def then(self) -> Then[ManyMaskingPoliciesAndACaller, Searched]:
        return TheLaidMaskingPoliciesAreLeft()


@dataclass(frozen=True)
class TheMonitorSearchesLikeTheSuperadmin(
    Scenario[SeedingSession, ManyMaskingPoliciesAndACaller, ClientIPMaskingAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-monitor-searches-masking-policies-like-the-superadmin"

    @override
    def describe(self) -> str:
        return "모니터 역할이 필터 없이 조회하면 슈퍼관리자와 같은 응답이 반환된다. 슈퍼관리자 검사는 모니터의 읽기를 허용한다"

    @override
    def given(self) -> Given[SeedingSession, ManyMaskingPoliciesAndACaller]:
        return TwoMaskingPoliciesAndSomeone(role=UserRole.MONITOR)

    @override
    def when(self) -> When[ManyMaskingPoliciesAndACaller, ClientIPMaskingAdapter, Searched]:
        return SearchingEveryPolicy()

    @override
    def then(self) -> Then[ManyMaskingPoliciesAndACaller, Searched]:
        return TheLaidMaskingPoliciesAreLeft()


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotSearch(
    Scenario[SeedingSession, ManyMaskingPoliciesAndACaller, ClientIPMaskingAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-masking-policies"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 전체 조회를 요청하면 역할 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ManyMaskingPoliciesAndACaller]:
        return TwoMaskingPoliciesAndSomeone()

    @override
    def when(self) -> When[ManyMaskingPoliciesAndACaller, ClientIPMaskingAdapter, Searched]:
        return SearchingEveryPolicy()

    @override
    def then(self) -> Then[ManyMaskingPoliciesAndACaller, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchingStep] = [
    TheSuperadminCountsEveryPolicy(),
    TheMonitorSearchesLikeTheSuperadmin(),
    AUserWhoIsNotTheSuperadminMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: ClientIPMaskingAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
