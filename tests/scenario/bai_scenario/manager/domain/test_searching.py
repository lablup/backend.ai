"""도메인 훑기 — 필터가 무엇을 좁히고, 누가 물을 수 있는가."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest
from bai_scenario.components.domain import (
    ManyDomainsAndACaller,
    ManyDomainsAndSomeone,
    TheCallIsRefused,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.domain.request import (
    AdminSearchDomainsInput,
    DomainFilter,
)
from ai.backend.common.dto.manager.v2.domain.response import AdminSearchDomainsPayload
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Scenario,
    Then,
    Verdict,
    When,
)

type Searched = AdminSearchDomainsPayload
type DomainStep = Scenario[SeedingSession, ManyDomainsAndACaller, DomainAdapter, Searched]


@dataclass(frozen=True)
class SearchingEveryDomain(When[ManyDomainsAndACaller, DomainAdapter, Searched]):
    """필터 없이 전체를 훑는다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyDomainsAndACaller) -> str:
        return f"{laid.caller.username}이 필터 없이 전체 조회"

    @override
    async def call(self, adapter: DomainAdapter, laid: ManyDomainsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(AdminSearchDomainsInput())


@dataclass(frozen=True)
class SearchingByName(When[ManyDomainsAndACaller, DomainAdapter, Searched]):
    """심은 것 중 하나의 이름으로 걸러 훑는다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyDomainsAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.named.name}으로 걸러 조회"

    @override
    async def call(self, adapter: DomainAdapter, laid: ManyDomainsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                AdminSearchDomainsInput(
                    filter=DomainFilter(name=StringFilter(equals=laid.named.name))
                )
            )


@dataclass(frozen=True)
class EveryLaidDomainIsCounted(Then[ManyDomainsAndACaller, Searched]):
    """심은 것이 모두 세어진다."""

    @override
    def says(self) -> str:
        return "심은 도메인이 모두 세어진다"

    @override
    def look(self, laid: ManyDomainsAndACaller, answered: Answered[Searched]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(InsufficientPrivilege, answered.raised)]
        return [
            Same(
                "items",
                sorted(one.basic_info.name for one in payload.items),
                sorted(one.name for one in laid.laid),
            ),
            Same("total_count", payload.total_count, len(laid.laid)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class OnlyTheNamedOneIsLeft(Then[ManyDomainsAndACaller, Searched]):
    """걸러낸 그 하나만 남는다."""

    @override
    def says(self) -> str:
        return "걸러낸 그 도메인 하나만 남는다"

    @override
    def look(self, laid: ManyDomainsAndACaller, answered: Answered[Searched]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(InsufficientPrivilege, answered.raised)]
        return [
            Same("items", [one.basic_info.name for one in payload.items], [laid.named.name]),
            Same("total_count", payload.total_count, 1),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheAnswerCountsEveryDomainLaid(
    Scenario[SeedingSession, ManyDomainsAndACaller, DomainAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-answer-counts-every-domain-the-scenario-laid"

    @override
    def describe(self) -> str:
        return "이 시나리오가 심은 도메인이 넷일 때, 필터 없는 조회는 그 넷을 모두 센다"

    @override
    def given(self) -> Given[SeedingSession, ManyDomainsAndACaller]:
        return ManyDomainsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyDomainsAndACaller, DomainAdapter, Searched]:
        return SearchingEveryDomain()

    @override
    def then(self) -> Then[ManyDomainsAndACaller, Searched]:
        return EveryLaidDomainIsCounted()


@dataclass(frozen=True)
class ANameFilterNarrows(Scenario[SeedingSession, ManyDomainsAndACaller, DomainAdapter, Searched]):
    @override
    def summary(self) -> str:
        return "a-name-filter-narrows-the-answer-to-the-domain-it-names"

    @override
    def describe(self) -> str:
        return "도메인 여럿 중 하나의 이름으로 걸러 조회하면, 답에는 그 이름의 도메인만 남는다"

    @override
    def given(self) -> Given[SeedingSession, ManyDomainsAndACaller]:
        return ManyDomainsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyDomainsAndACaller, DomainAdapter, Searched]:
        return SearchingByName()

    @override
    def then(self) -> Then[ManyDomainsAndACaller, Searched]:
        return OnlyTheNamedOneIsLeft()


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotSearch(
    Scenario[SeedingSession, ManyDomainsAndACaller, DomainAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-every-domain"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 전체 도메인 조회를 요청하면 역할로 막힌다"

    @override
    def given(self) -> Given[SeedingSession, ManyDomainsAndACaller]:
        return ManyDomainsAndSomeone()

    @override
    def when(self) -> When[ManyDomainsAndACaller, DomainAdapter, Searched]:
        return SearchingEveryDomain()

    @override
    def then(self) -> Then[ManyDomainsAndACaller, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[DomainStep] = [
    TheAnswerCountsEveryDomainLaid(),
    ANameFilterNarrows(),
    AUserWhoIsNotTheSuperadminMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: DomainStep, adapter: DomainAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
