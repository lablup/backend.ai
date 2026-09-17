"""리소스 그룹 검색 — 전체 검색은 슈퍼관리자 검사를, 스코프 검색은 스코프마다 권한 검사를 거친다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.common.dto.manager.v2.resource_group.request import (
    AdminSearchResourceGroupsInput,
    ResourceGroupFilter,
    ScopedSearchResourceGroupsInput,
)
from ai.backend.common.dto.manager.v2.resource_group.types import ResourceGroupScope
from ai.backend.manager.api.adapters.resource_group.adapter import (
    ResourceGroupAdapter,
    ResourceGroupSearchPayload,
)
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_group import (
    ADomainGroupsAndACaller,
    ADomainGroupsAndSomeone,
    AnActiveAndAnInactiveGroup,
    ManyGroupsAndACaller,
    OnlyTheLinkedGroupIsLeft,
    OnlyTheNamedGroupIsLeft,
    TheFirstGroupPage,
    TheLaidGroupsAreLeft,
    TwoGroupsAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type Searched = ResourceGroupSearchPayload
type SearchingStep = Scenario[SeedingSession, Any, ResourceGroupAdapter, Searched]


@dataclass(frozen=True)
class SearchingEveryGroup(When[ManyGroupsAndACaller, ResourceGroupAdapter, Searched]):
    """필터 없이 전체를 검색한다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyGroupsAndACaller) -> str:
        return f"{laid.caller.username}이 필터 없이 전체 조회"

    @override
    async def call(self, adapter: ResourceGroupAdapter, laid: ManyGroupsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search(AdminSearchResourceGroupsInput())


@dataclass(frozen=True)
class SearchingByName(When[ManyGroupsAndACaller, ResourceGroupAdapter, Searched]):
    """골라낸 하나의 이름을 필터로 검색한다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyGroupsAndACaller) -> str:
        return f"{laid.caller.username}이 이름 {laid.named.name} 필터로 조회"

    @override
    async def call(self, adapter: ResourceGroupAdapter, laid: ManyGroupsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search(
                AdminSearchResourceGroupsInput(
                    filter=ResourceGroupFilter(name=StringFilter(equals=laid.named.name))
                )
            )


@dataclass(frozen=True)
class SearchingTheActiveOnes(When[ManyGroupsAndACaller, ResourceGroupAdapter, Searched]):
    """활성인 그룹만 필터로 검색한다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyGroupsAndACaller) -> str:
        return f"{laid.caller.username}이 활성 필터로 조회"

    @override
    async def call(self, adapter: ResourceGroupAdapter, laid: ManyGroupsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search(
                AdminSearchResourceGroupsInput(filter=ResourceGroupFilter(is_active=True))
            )


@dataclass(frozen=True)
class SearchingTheFirstOne(When[ManyGroupsAndACaller, ResourceGroupAdapter, Searched]):
    """앞에서 한 건만 요청한다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyGroupsAndACaller) -> str:
        return f"{laid.caller.username}이 앞에서 한 건만 조회"

    @override
    async def call(self, adapter: ResourceGroupAdapter, laid: ManyGroupsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search(AdminSearchResourceGroupsInput(first=1))


@dataclass(frozen=True)
class SearchingTheDomainScope(When[ADomainGroupsAndACaller, ResourceGroupAdapter, Searched]):
    """호출자의 도메인을 스코프로 검색한다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: ADomainGroupsAndACaller) -> str:
        return f"{laid.caller.username}이 도메인 {laid.domain.name} 스코프로 조회"

    @override
    async def call(self, adapter: ResourceGroupAdapter, laid: ADomainGroupsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchResourceGroupsInput(
                    scope=ResourceGroupScope(domain=[UUIDScope(value=laid.domain.id)])
                )
            )


@dataclass(frozen=True)
class TheSuperadminCountsEveryGroup(
    Scenario[SeedingSession, ManyGroupsAndACaller, ResourceGroupAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-counts-every-resource-group-laid"

    @override
    def describe(self) -> str:
        return "리소스 그룹 둘이 있을 때 슈퍼관리자가 필터 없이 조회하면 둘 다 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyGroupsAndACaller]:
        return TwoGroupsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyGroupsAndACaller, ResourceGroupAdapter, Searched]:
        return SearchingEveryGroup()

    @override
    def then(self) -> Then[ManyGroupsAndACaller, Searched]:
        return TheLaidGroupsAreLeft()


@dataclass(frozen=True)
class ANameFilterNarrows(
    Scenario[SeedingSession, ManyGroupsAndACaller, ResourceGroupAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-name-filter-narrows-the-answer-to-that-resource-group"

    @override
    def describe(self) -> str:
        return "리소스 그룹 둘 중 한쪽 이름을 필터로 조회하면 그 그룹 하나만 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyGroupsAndACaller]:
        return TwoGroupsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyGroupsAndACaller, ResourceGroupAdapter, Searched]:
        return SearchingByName()

    @override
    def then(self) -> Then[ManyGroupsAndACaller, Searched]:
        return OnlyTheNamedGroupIsLeft()


@dataclass(frozen=True)
class AnActiveFilterNarrows(
    Scenario[SeedingSession, ManyGroupsAndACaller, ResourceGroupAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "an-active-filter-leaves-only-the-active-resource-groups"

    @override
    def describe(self) -> str:
        return "활성 그룹과 비활성 그룹이 섞여 있을 때 활성 필터로 조회하면 활성인 것만 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyGroupsAndACaller]:
        return AnActiveAndAnInactiveGroup(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyGroupsAndACaller, ResourceGroupAdapter, Searched]:
        return SearchingTheActiveOnes()

    @override
    def then(self) -> Then[ManyGroupsAndACaller, Searched]:
        return TheLaidGroupsAreLeft()


@dataclass(frozen=True)
class TheFirstPageSaysThereIsMore(
    Scenario[SeedingSession, ManyGroupsAndACaller, ResourceGroupAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "asking-for-the-first-resource-group-only-says-there-is-a-next-page"

    @override
    def describe(self) -> str:
        return "리소스 그룹 둘이 있을 때 앞에서 한 건만 요청하면 한 건이 반환되고 다음 페이지가 있다고 응답한다"

    @override
    def given(self) -> Given[SeedingSession, ManyGroupsAndACaller]:
        return TwoGroupsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyGroupsAndACaller, ResourceGroupAdapter, Searched]:
        return SearchingTheFirstOne()

    @override
    def then(self) -> Then[ManyGroupsAndACaller, Searched]:
        return TheFirstGroupPage()


@dataclass(frozen=True)
class TheMonitorSearchesLikeTheSuperadmin(
    Scenario[SeedingSession, ManyGroupsAndACaller, ResourceGroupAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-monitor-searches-resource-groups-like-the-superadmin"

    @override
    def describe(self) -> str:
        return "모니터가 필터 없이 조회하면 슈퍼관리자와 같은 응답을 받는다"

    @override
    def given(self) -> Given[SeedingSession, ManyGroupsAndACaller]:
        return TwoGroupsAndSomeone(role=UserRole.MONITOR)

    @override
    def when(self) -> When[ManyGroupsAndACaller, ResourceGroupAdapter, Searched]:
        return SearchingEveryGroup()

    @override
    def then(self) -> Then[ManyGroupsAndACaller, Searched]:
        return TheLaidGroupsAreLeft()


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotSearch(
    Scenario[SeedingSession, ManyGroupsAndACaller, ResourceGroupAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-every-resource-group"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 필터 없이 전체를 조회하면 역할 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ManyGroupsAndACaller]:
        return TwoGroupsAndSomeone()

    @override
    def when(self) -> When[ManyGroupsAndACaller, ResourceGroupAdapter, Searched]:
        return SearchingEveryGroup()

    @override
    def then(self) -> Then[ManyGroupsAndACaller, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class AUserReadingInTheDomainSearchesItsScope(
    Scenario[SeedingSession, ADomainGroupsAndACaller, ResourceGroupAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-in-the-domain-searches-the-groups-linked-to-it"

    @override
    def describe(self) -> str:
        return (
            "도메인 범위에서 리소스 그룹 읽기 역할을 받은 사용자가 그 도메인 스코프로 조회하면, "
            "도메인에 건 그룹 하나만 반환되고 걸지 않은 그룹은 나오지 않는다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADomainGroupsAndACaller]:
        return ADomainGroupsAndSomeone(reading=True)

    @override
    def when(self) -> When[ADomainGroupsAndACaller, ResourceGroupAdapter, Searched]:
        return SearchingTheDomainScope()

    @override
    def then(self) -> Then[ADomainGroupsAndACaller, Searched]:
        return OnlyTheLinkedGroupIsLeft()


@dataclass(frozen=True)
class TheSuperadminSearchesTheDomainScope(
    Scenario[SeedingSession, ADomainGroupsAndACaller, ResourceGroupAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-searching-a-domain-scope-sees-only-the-groups-linked-to-it"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 도메인 스코프로 조회해도 그 도메인에 건 그룹 하나만 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ADomainGroupsAndACaller]:
        return ADomainGroupsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADomainGroupsAndACaller, ResourceGroupAdapter, Searched]:
        return SearchingTheDomainScope()

    @override
    def then(self) -> Then[ADomainGroupsAndACaller, Searched]:
        return OnlyTheLinkedGroupIsLeft()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearchTheDomainScope(
    Scenario[SeedingSession, ADomainGroupsAndACaller, ResourceGroupAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-a-domain-scope"

    @override
    def describe(self) -> str:
        return "아무 권한도 없는 사용자가 자기 도메인 스코프로 조회하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ADomainGroupsAndACaller]:
        return ADomainGroupsAndSomeone()

    @override
    def when(self) -> When[ADomainGroupsAndACaller, ResourceGroupAdapter, Searched]:
        return SearchingTheDomainScope()

    @override
    def then(self) -> Then[ADomainGroupsAndACaller, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[SearchingStep] = [
    TheSuperadminCountsEveryGroup(),
    ANameFilterNarrows(),
    AnActiveFilterNarrows(),
    TheFirstPageSaysThereIsMore(),
    TheMonitorSearchesLikeTheSuperadmin(),
    AUserWhoIsNotTheSuperadminMayNotSearch(),
    AUserReadingInTheDomainSearchesItsScope(),
    TheSuperadminSearchesTheDomainScope(),
    AUserGrantedNothingMayNotSearchTheDomainScope(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: ResourceGroupAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
