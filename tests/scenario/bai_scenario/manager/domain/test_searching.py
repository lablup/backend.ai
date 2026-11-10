"""도메인 search — 필터가 무엇을 좁히고, 누가 물을 수 있는가."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

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
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.domain import (
    ManyDomainsAndACaller,
    ManyDomainsAndSomeone,
    TheCallIsRefused,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Searched = AdminSearchDomainsPayload
type DomainStep = Scenario[TestSeedingSession, ManyDomainsAndACaller, DomainAdapter, Searched]


@dataclass(frozen=True)
class SearchingEveryDomain(When[ManyDomainsAndACaller, DomainAdapter, Searched]):
    """필터 없이 전체를 search 한다."""

    @override
    def operation(self) -> str:
        return "global_search"

    @override
    def describe(self, laid: ManyDomainsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 필터 없이 전체를 조회합니다",
            english=f"{laid.caller.username} searches every domain without a filter",
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: ManyDomainsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.global_search(AdminSearchDomainsInput())


@dataclass(frozen=True)
class SearchingByName(When[ManyDomainsAndACaller, DomainAdapter, Searched]):
    """미리 만든 것 중 하나의 이름으로 걸러 search 한다."""

    @override
    def operation(self) -> str:
        return "global_search"

    @override
    def describe(self, laid: ManyDomainsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.named.name}으로 필터 기반 조회합니다",
            english=f"{laid.caller.username} searches with a filter on {laid.named.name}",
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: ManyDomainsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.global_search(
                AdminSearchDomainsInput(
                    filter=DomainFilter(name=StringFilter(equals=laid.named.name))
                )
            )


@dataclass(frozen=True)
class SoftDeletingOneThenSearching(When[ManyDomainsAndACaller, DomainAdapter, Searched]):
    """미리 만든 것 중 하나를 soft delete 한 뒤 필터 없이 전체를 search 한다."""

    @override
    def operation(self) -> str:
        return "global_search"

    @override
    def describe(self, laid: ManyDomainsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.named.name}을 soft delete 한 뒤 필터 없이 전체를 "
            "조회합니다",
            english=(
                f"{laid.caller.username} soft deletes {laid.named.name} and then searches "
                "every domain without a filter"
            ),
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: ManyDomainsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            await adapter.delete(await adapter.lookup_name(laid.named.name))
            return await adapter.global_search(AdminSearchDomainsInput())


@dataclass(frozen=True)
class EveryLaidDomainIsCounted(Then[ManyDomainsAndACaller, Searched]):
    """미리 만든 것이 모두 나온다."""

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 도메인이 모두 나옵니다",
            english="every domain seeded in advance comes back",
        )

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
        return Says(
            "필터로 걸러낸 그 도메인 하나만 남습니다",
            english="only the domain that the filter named is left",
        )

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
    Scenario[TestSeedingSession, ManyDomainsAndACaller, DomainAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-answer-counts-every-domain-the-scenario-laid"

    @override
    def describe(self) -> str:
        return Says(
            "이 시나리오가 미리 저장한 도메인이 넷일 때, 필터 없는 조회는 그 넷이 모두 나옵니다",
            english=(
                "when this scenario seeded four domains, "
                "a search without a filter brings back all four"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyDomainsAndACaller]:
        return ManyDomainsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyDomainsAndACaller, DomainAdapter, Searched]:
        return SearchingEveryDomain()

    @override
    def then(self) -> Then[ManyDomainsAndACaller, Searched]:
        return EveryLaidDomainIsCounted()


@dataclass(frozen=True)
class ANameFilterNarrows(
    Scenario[TestSeedingSession, ManyDomainsAndACaller, DomainAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-name-filter-narrows-the-answer-to-the-domain-it-names"

    @override
    def describe(self) -> str:
        return Says(
            "도메인 여럿 중 하나의 이름으로 필터 기반 조회하면, "
            "응답에는 그 이름의 도메인만 남습니다",
            english=(
                "when several domains are searched with a filter on the name of one, "
                "only the domain of that name is left in the answer"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyDomainsAndACaller]:
        return ManyDomainsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyDomainsAndACaller, DomainAdapter, Searched]:
        return SearchingByName()

    @override
    def then(self) -> Then[ManyDomainsAndACaller, Searched]:
        return OnlyTheNamedOneIsLeft()


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotSearch(
    Scenario[TestSeedingSession, ManyDomainsAndACaller, DomainAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-every-domain"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 전체 도메인 조회를 요청하면 역할로 거부됩니다",
            english=(
                "when a user who is not the superadmin asks to search every domain, "
                "the role rejects it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyDomainsAndACaller]:
        return ManyDomainsAndSomeone()

    @override
    def when(self) -> When[ManyDomainsAndACaller, DomainAdapter, Searched]:
        return SearchingEveryDomain()

    @override
    def then(self) -> Then[ManyDomainsAndACaller, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class SoftDeletedDomainsAreCountedToo(
    Scenario[TestSeedingSession, ManyDomainsAndACaller, DomainAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-answer-includes-soft-deleted-domains-too"

    @override
    def describe(self) -> str:
        return Says(
            "미리 저장한 도메인 중 하나를 soft delete 한 뒤 필터 없이 search 하면, "
            "그것까지 모두 나옵니다",
            english=(
                "when one of the domains seeded in advance is soft-deleted and every "
                "domain is searched without a filter, that one comes back too"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyDomainsAndACaller]:
        return ManyDomainsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyDomainsAndACaller, DomainAdapter, Searched]:
        return SoftDeletingOneThenSearching()

    @override
    def then(self) -> Then[ManyDomainsAndACaller, Searched]:
        return EveryLaidDomainIsCounted()


SCENARIOS: list[DomainStep] = [
    TheAnswerCountsEveryDomainLaid(),
    ANameFilterNarrows(),
    AUserWhoIsNotTheSuperadminMayNotSearch(),
    SoftDeletedDomainsAreCountedToo(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: DomainStep, adapter: DomainAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
