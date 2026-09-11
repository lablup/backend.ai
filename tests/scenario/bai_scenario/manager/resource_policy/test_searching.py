"""정책 검색 — 전역 superadmin 역할이 필요하지만, 읽기 연산이라 모니터 역할도 통과한다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_policy import (
    FAMILIES,
    EveryLaidPolicyIsFound,
    Family,
    ManyPoliciesAndACaller,
    ManyPoliciesAndSomeone,
    OnlyTheNamedOneIsFound,
    Searched,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.api.adapters.resource_policy.adapter import ResourcePolicyAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

type SearchingStep = Scenario[
    SeedingSession, ManyPoliciesAndACaller[Any], ResourcePolicyAdapter, Searched
]


@dataclass(frozen=True)
class SearchingEverything(When[ManyPoliciesAndACaller[Any], ResourcePolicyAdapter, Searched]):
    """필터 없이 전체를 검색한다."""

    family: Family[Any, Any]

    @override
    def operation(self) -> str:
        return self.family.calls.search

    @override
    def describe(self, laid: ManyPoliciesAndACaller[Any]) -> str:
        return f"{laid.caller.username}이 필터 없이 전체 검색"

    @override
    async def call(
        self, adapter: ResourcePolicyAdapter, laid: ManyPoliciesAndACaller[Any]
    ) -> Searched:
        with ActingAs(laid.caller):
            return await self.family.search(adapter)


@dataclass(frozen=True)
class SearchingByName(When[ManyPoliciesAndACaller[Any], ResourcePolicyAdapter, Searched]):
    """미리 만들어 둔 정책 중 하나의 이름을 필터로 검색한다."""

    family: Family[Any, Any]

    @override
    def operation(self) -> str:
        return self.family.calls.search

    @override
    def describe(self, laid: ManyPoliciesAndACaller[Any]) -> str:
        return f"{laid.caller.username}이 {laid.named.name} 이름 필터로 검색"

    @override
    async def call(
        self, adapter: ResourcePolicyAdapter, laid: ManyPoliciesAndACaller[Any]
    ) -> Searched:
        with ActingAs(laid.caller):
            return await self.family.search(adapter, named=laid.named.name)


@dataclass(frozen=True)
class TheSuperadminFindsEveryOne(
    Scenario[SeedingSession, ManyPoliciesAndACaller[Any], ResourcePolicyAdapter, Searched]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"the-superadmin-finds-every-{self.family.label}"

    @override
    def describe(self) -> str:
        return (
            f"{self.family.kind} 여럿이 있고 슈퍼관리자가 필터 없이 전체를 검색하면, "
            "미리 만들어 둔 정책이 모두, 그리고 그것만 반환된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyPoliciesAndACaller[Any]]:
        return ManyPoliciesAndSomeone(self.family, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyPoliciesAndACaller[Any], ResourcePolicyAdapter, Searched]:
        return SearchingEverything(self.family)

    @override
    def then(self) -> Then[ManyPoliciesAndACaller[Any], Searched]:
        return EveryLaidPolicyIsFound(self.family)


@dataclass(frozen=True)
class FilteringByNameLeavesThatOne(
    Scenario[SeedingSession, ManyPoliciesAndACaller[Any], ResourcePolicyAdapter, Searched]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"filtering-{self.family.label}-search-by-name-leaves-that-one"

    @override
    def describe(self) -> str:
        return (
            f"이름이 다른 {self.family.kind} 여럿이 있고 슈퍼관리자가 그중 한 이름을 필터로 "
            "검색하면, 그 이름의 정책만 반환된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyPoliciesAndACaller[Any]]:
        return ManyPoliciesAndSomeone(self.family, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyPoliciesAndACaller[Any], ResourcePolicyAdapter, Searched]:
        return SearchingByName(self.family)

    @override
    def then(self) -> Then[ManyPoliciesAndACaller[Any], Searched]:
        return OnlyTheNamedOneIsFound(self.family)


@dataclass(frozen=True)
class AMonitorFindsEveryOne(
    Scenario[SeedingSession, ManyPoliciesAndACaller[Any], ResourcePolicyAdapter, Searched]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"a-monitor-finds-every-{self.family.label}-like-the-superadmin"

    @override
    def describe(self) -> str:
        return (
            f"모니터 역할 사용자가 {self.family.kind} 전체를 검색하면 슈퍼관리자와 같은 응답이 "
            "반환된다. 역할 검사가 읽기는 모니터에게도 허용하기 때문이다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyPoliciesAndACaller[Any]]:
        return ManyPoliciesAndSomeone(self.family, role=UserRole.MONITOR)

    @override
    def when(self) -> When[ManyPoliciesAndACaller[Any], ResourcePolicyAdapter, Searched]:
        return SearchingEverything(self.family)

    @override
    def then(self) -> Then[ManyPoliciesAndACaller[Any], Searched]:
        return EveryLaidPolicyIsFound(self.family)


@dataclass(frozen=True)
class APlainUserMayNotSearch(
    Scenario[SeedingSession, ManyPoliciesAndACaller[Any], ResourcePolicyAdapter, Searched]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"a-user-who-is-not-the-superadmin-may-not-search-{self.family.label}"

    @override
    def describe(self) -> str:
        return f"슈퍼관리자가 아닌 사용자가 {self.family.kind} 전체를 검색하려 하면 역할 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ManyPoliciesAndACaller[Any]]:
        return ManyPoliciesAndSomeone(self.family)

    @override
    def when(self) -> When[ManyPoliciesAndACaller[Any], ResourcePolicyAdapter, Searched]:
        return SearchingEverything(self.family)

    @override
    def then(self) -> Then[ManyPoliciesAndACaller[Any], Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchingStep] = [
    *(TheSuperadminFindsEveryOne(family) for family in FAMILIES),
    *(FilteringByNameLeavesThatOne(family) for family in FAMILIES),
    *(AMonitorFindsEveryOne(family) for family in FAMILIES),
    *(APlainUserMayNotSearch(family) for family in FAMILIES),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: ResourcePolicyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
