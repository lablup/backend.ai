"""정책 검색 — 전역 superadmin 역할이 필요하지만, 읽기 연산이라 모니터 역할도 통과한다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.api.adapters.resource_policy.adapter import ResourcePolicyAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Language,
    Refused,
    Same,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
    in_language,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_policy import (
    FAMILIES,
    KEYPAIR,
    EveryLaidPolicyIsFound,
    Family,
    ManyPoliciesAndACaller,
    ManyPoliciesAndSomeone,
    OnlyTheNamedOneIsFound,
    Searched,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type SearchingStep = Scenario[
    TestSeedingSession, ManyPoliciesAndACaller[Any], ResourcePolicyAdapter, Searched
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
        return Says(
            f"{laid.caller.username}이 필터 없이 전체를 검색합니다",
            english=f"{laid.caller.username} searches everything without a filter",
        )

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
        return Says(
            f"{laid.caller.username}이 {laid.named.name} 이름 필터로 검색합니다",
            english=(f"{laid.caller.username} searches with the name {laid.named.name} filter"),
        )

    @override
    async def call(
        self, adapter: ResourcePolicyAdapter, laid: ManyPoliciesAndACaller[Any]
    ) -> Searched:
        with ActingAs(laid.caller):
            return await self.family.search(adapter, named=laid.named.name)


@dataclass(frozen=True)
class SearchingByHolder(When[ManyPoliciesAndACaller[Any], ResourcePolicyAdapter, Searched]):
    """호출자 자신의 키페어에 할당된 정책을 필터로 검색한다."""

    @override
    def operation(self) -> str:
        return KEYPAIR.calls.search

    @override
    def describe(self, laid: ManyPoliciesAndACaller[Any]) -> str:
        return Says(
            f"{laid.caller.username}이 자기 키페어 필터로 검색합니다",
            english=f"{laid.caller.username} searches with their own keypair filter",
        )

    @override
    async def call(
        self, adapter: ResourcePolicyAdapter, laid: ManyPoliciesAndACaller[Any]
    ) -> Searched:
        with ActingAs(laid.caller):
            return await KEYPAIR.search_held_by(adapter, laid.caller.id)


@dataclass(frozen=True)
class OnlyTheHeldOneIsFound(Then[ManyPoliciesAndACaller[Any], Searched]):
    """호출자의 키페어에 할당된 정책 하나만 반환된다."""

    @override
    def says(self) -> str:
        return Says(
            "호출자의 키페어에 할당된 키페어 정책 하나만 반환됩니다",
            english="only the one keypair policy assigned to the caller's keypair comes back",
        )

    @override
    def look(
        self, laid: ManyPoliciesAndACaller[Any], answered: Answered[Searched]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(InsufficientPrivilege, answered.raised)]
        return [
            Same("items", [one.name for one in payload.items], [laid.held.name]),
            Same("total_count", payload.total_count, 1),
        ]


@dataclass(frozen=True)
class TheSuperadminFindsEveryOne(
    Scenario[TestSeedingSession, ManyPoliciesAndACaller[Any], ResourcePolicyAdapter, Searched]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"the-superadmin-finds-every-{self.family.label}"

    @override
    def describe(self) -> str:
        kind = self.family.kind
        kind_en = in_language(kind, Language.ENGLISH)
        return Says(
            f"{kind} 여럿이 있고 superadmin 이 필터 없이 전체를 검색하면, 미리 저장한 정책이 "
            "모두, 그리고 그것만 반환됩니다",
            english=(
                f"when several {kind_en} policies exist and the superadmin searches everything "
                "without a filter, every policy seeded in advance comes back and only those"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPoliciesAndACaller[Any]]:
        return ManyPoliciesAndSomeone(self.family, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyPoliciesAndACaller[Any], ResourcePolicyAdapter, Searched]:
        return SearchingEverything(self.family)

    @override
    def then(self) -> Then[ManyPoliciesAndACaller[Any], Searched]:
        return EveryLaidPolicyIsFound(self.family)


@dataclass(frozen=True)
class FilteringByNameLeavesThatOne(
    Scenario[TestSeedingSession, ManyPoliciesAndACaller[Any], ResourcePolicyAdapter, Searched]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"filtering-{self.family.label}-search-by-name-leaves-that-one"

    @override
    def describe(self) -> str:
        kind = self.family.kind
        kind_en = in_language(kind, Language.ENGLISH)
        return Says(
            f"이름이 다른 {kind} 여럿이 있고 superadmin 이 그중 한 이름을 필터로 검색하면, 그 "
            "이름의 정책만 반환됩니다",
            english=(
                f"when several policies of the {kind_en} kind with different names exist and "
                "the superadmin searches with one of those names as the filter, only the policy "
                "of that name comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPoliciesAndACaller[Any]]:
        return ManyPoliciesAndSomeone(self.family, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyPoliciesAndACaller[Any], ResourcePolicyAdapter, Searched]:
        return SearchingByName(self.family)

    @override
    def then(self) -> Then[ManyPoliciesAndACaller[Any], Searched]:
        return OnlyTheNamedOneIsFound(self.family)


@dataclass(frozen=True)
class FilteringByHolderLeavesTheirs(
    Scenario[TestSeedingSession, ManyPoliciesAndACaller[Any], ResourcePolicyAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "filtering-keypair-policy-search-by-a-user-leaves-the-one-their-keypair-holds"

    @override
    def describe(self) -> str:
        return Says(
            "키페어 정책 여럿이 있고 superadmin 이 특정 사용자의 키페어를 필터로 검색하면, 그 "
            "사용자의 키페어에 할당된 정책만 반환됩니다",
            english=(
                "when several keypair policies exist and the superadmin searches with the "
                "keypair of a user as the filter, only the policy assigned to that user's "
                "keypair comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPoliciesAndACaller[Any]]:
        return ManyPoliciesAndSomeone(KEYPAIR, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyPoliciesAndACaller[Any], ResourcePolicyAdapter, Searched]:
        return SearchingByHolder()

    @override
    def then(self) -> Then[ManyPoliciesAndACaller[Any], Searched]:
        return OnlyTheHeldOneIsFound()


@dataclass(frozen=True)
class AMonitorFindsEveryOne(
    Scenario[TestSeedingSession, ManyPoliciesAndACaller[Any], ResourcePolicyAdapter, Searched]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"a-monitor-finds-every-{self.family.label}-like-the-superadmin"

    @override
    def describe(self) -> str:
        kind = self.family.kind
        kind_en = in_language(kind, Language.ENGLISH)
        return Says(
            f"모니터 역할 사용자가 {kind} 전체를 검색하면 superadmin 과 같은 응답이 반환됩니다. "
            "superadmin 검사가 읽기는 모니터에게도 허용하기 때문입니다",
            english=(
                f"when a user with the monitor role searches every policy of the {kind_en} kind, "
                "the same response comes back as for the superadmin, because the superadmin "
                "check allows the monitor reads too"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPoliciesAndACaller[Any]]:
        return ManyPoliciesAndSomeone(self.family, role=UserRole.MONITOR)

    @override
    def when(self) -> When[ManyPoliciesAndACaller[Any], ResourcePolicyAdapter, Searched]:
        return SearchingEverything(self.family)

    @override
    def then(self) -> Then[ManyPoliciesAndACaller[Any], Searched]:
        return EveryLaidPolicyIsFound(self.family)


@dataclass(frozen=True)
class APlainUserMayNotSearch(
    Scenario[TestSeedingSession, ManyPoliciesAndACaller[Any], ResourcePolicyAdapter, Searched]
):
    family: Family[Any, Any]

    @override
    def summary(self) -> str:
        return f"a-user-who-is-not-the-superadmin-may-not-search-{self.family.label}"

    @override
    def describe(self) -> str:
        kind = self.family.kind
        kind_en = in_language(kind, Language.ENGLISH)
        return Says(
            f"superadmin 이 아닌 사용자가 {kind} 전체를 검색하려 하면 역할 부족으로 거부됩니다",
            english=(
                f"when a user who is not the superadmin tries to search every policy of the "
                f"{kind_en} kind, the call is rejected for lacking the role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPoliciesAndACaller[Any]]:
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
    FilteringByHolderLeavesTheirs(),
    *(AMonitorFindsEveryOne(family) for family in FAMILIES),
    *(APlainUserMayNotSearch(family) for family in FAMILIES),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: ResourcePolicyAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
