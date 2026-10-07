"""리소스 그룹 범위에서 도메인 search — 그 그룹을 쓸 수 있는 도메인만, 그 범위를 읽을 수 있는 사람에게."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.domain.request import ScopedSearchDomainsInput
from ai.backend.common.dto.manager.v2.domain.response import AdminSearchDomainsPayload
from ai.backend.common.dto.manager.v2.domain.types import DomainScope
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Same,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.domain import DomainsOfAGroupAndACaller, DomainsOfAGroupAndSomeone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type Searched = AdminSearchDomainsPayload
type DomainStep = Scenario[SeedingSession, DomainsOfAGroupAndACaller, DomainAdapter, Searched]


@dataclass(frozen=True)
class SearchingInTheGroup(When[DomainsOfAGroupAndACaller, DomainAdapter, Searched]):
    """그 리소스 그룹 범위에서 필터 없이 search 한다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: DomainsOfAGroupAndACaller) -> str:
        return f"{laid.caller.username}이 리소스 그룹 {laid.group.name} 범위에서 조회"

    @override
    async def call(self, adapter: DomainAdapter, laid: DomainsOfAGroupAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchDomainsInput(
                    scope=DomainScope(resource_group=[UUIDScope(value=laid.group.id)])
                )
            )


@dataclass(frozen=True)
class OnlyTheLinkedDomainsAreLeft(Then[DomainsOfAGroupAndACaller, Searched]):
    """그 그룹을 쓸 수 있는 도메인만 남는다."""

    @override
    def says(self) -> str:
        return "그 그룹을 쓸 수 있는 도메인만 남는다"

    @override
    def look(self, laid: DomainsOfAGroupAndACaller, answered: Answered[Searched]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            Same(
                "items",
                sorted(one.basic_info.name for one in payload.items),
                sorted(one.name for one in laid.linked),
            ),
            Same("total_count", payload.total_count, len(laid.linked)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheSuperadminSearchesInAGroup(
    Scenario[SeedingSession, DomainsOfAGroupAndACaller, DomainAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-searches-the-domains-of-a-resource-group"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 리소스 그룹 범위에서 search 하면, 그 그룹을 쓸 수 있는 도메인만 온다"

    @override
    def given(self) -> Given[SeedingSession, DomainsOfAGroupAndACaller]:
        return DomainsOfAGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[DomainsOfAGroupAndACaller, DomainAdapter, Searched]:
        return SearchingInTheGroup()

    @override
    def then(self) -> Then[DomainsOfAGroupAndACaller, Searched]:
        return OnlyTheLinkedDomainsAreLeft()


@dataclass(frozen=True)
class AUserReadingInTheGroupSearches(
    Scenario[SeedingSession, DomainsOfAGroupAndACaller, DomainAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-in-the-group-searches-its-domains"

    @override
    def describe(self) -> str:
        return (
            "리소스 그룹 범위에서 도메인 읽기 역할을 받은 사용자가 그 범위에서 search 하면, "
            "슈퍼관리자와 같은 도메인들이 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, DomainsOfAGroupAndACaller]:
        return DomainsOfAGroupAndSomeone(reading=True)

    @override
    def when(self) -> When[DomainsOfAGroupAndACaller, DomainAdapter, Searched]:
        return SearchingInTheGroup()

    @override
    def then(self) -> Then[DomainsOfAGroupAndACaller, Searched]:
        return OnlyTheLinkedDomainsAreLeft()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearchInTheGroup(
    Scenario[SeedingSession, DomainsOfAGroupAndACaller, DomainAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-the-domains-of-a-resource-group"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 리소스 그룹 범위에서 search 하면 권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, DomainsOfAGroupAndACaller]:
        return DomainsOfAGroupAndSomeone()

    @override
    def when(self) -> When[DomainsOfAGroupAndACaller, DomainAdapter, Searched]:
        return SearchingInTheGroup()

    @override
    def then(self) -> Then[DomainsOfAGroupAndACaller, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[DomainStep] = [
    TheSuperadminSearchesInAGroup(),
    AUserReadingInTheGroupSearches(),
    AUserGrantedNothingMayNotSearchInTheGroup(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_scoped_searching(
    scenario: DomainStep, adapter: DomainAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
