"""레지스트리 검색 — 누가 볼 수 있고, 무엇으로 걸러지는가."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.container_registry import (
    ManyRegistriesAndACaller,
    ManyRegistriesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.container_registry.request import (
    AdminSearchContainerRegistriesInput,
    ContainerRegistryFilter,
)
from ai.backend.common.dto.manager.v2.container_registry.response import (
    AdminSearchContainerRegistriesPayload,
)
from ai.backend.manager.api.adapters.container_registry.adapter import ContainerRegistryAdapter
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

DEFAULT_PAGE = 10
"""요청이 크기를 생략했을 때 어댑터가 채우는 한 쪽의 크기."""

type Searched = AdminSearchContainerRegistriesPayload
type SearchingStep = Scenario[
    SeedingSession, ManyRegistriesAndACaller, ContainerRegistryAdapter, Searched
]


@dataclass(frozen=True)
class Searching(When[ManyRegistriesAndACaller, ContainerRegistryAdapter, Searched]):
    """레지스트리를 검색한다. 이름을 주면 그 이름으로 거른다."""

    narrowed_by_name: bool = False
    limit: int | None = None

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyRegistriesAndACaller) -> str:
        who = laid.caller.username
        if self.narrowed_by_name:
            return f"{who}이 {laid.named.registry_name} 이름으로 걸러 검색함"
        if self.limit is None:
            return f"{who}이 크기를 생략하고 검색함"
        return f"{who}이 조건 없이 검색함"

    @override
    async def call(
        self, adapter: ContainerRegistryAdapter, laid: ManyRegistriesAndACaller
    ) -> Searched:
        named = (
            ContainerRegistryFilter(registry_name=StringFilter(equals=laid.named.registry_name))
            if self.narrowed_by_name
            else None
        )
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                AdminSearchContainerRegistriesInput(filter=named, limit=self.limit)
            )


@dataclass(frozen=True)
class EveryLaidRegistryIsCounted(Then[ManyRegistriesAndACaller, Searched]):
    """심은 것이 모두 세어진다."""

    @override
    def says(self) -> str:
        return "심은 레지스트리가 모두 세어진다"

    @override
    def look(self, laid: ManyRegistriesAndACaller, answered: Answered[Searched]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [
                Refused(type(answered.raised) if answered.raised else Exception, answered.raised)
            ]
        return [
            Same(
                "items",
                sorted(one.registry_name for one in payload.items),
                sorted(one.registry_name for one in laid.laid),
            ),
            Same("total_count", payload.total_count, len(laid.laid)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class OnlyTheNamedOneIsLeft(Then[ManyRegistriesAndACaller, Searched]):
    """걸러낸 그 하나만 남는다."""

    @override
    def says(self) -> str:
        return "걸러낸 그 레지스트리 하나만 남는다"

    @override
    def look(self, laid: ManyRegistriesAndACaller, answered: Answered[Searched]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [
                Refused(type(answered.raised) if answered.raised else Exception, answered.raised)
            ]
        return [
            Same(
                "items",
                [one.registry_name for one in payload.items],
                [laid.named.registry_name],
            ),
            Same("total_count", payload.total_count, 1),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class OnePageComesBack(Then[ManyRegistriesAndACaller, Searched]):
    """한 쪽만 오고, 다음 쪽이 있다고 답한다."""

    @override
    def says(self) -> str:
        return "한 쪽만 오고 다음 쪽이 있다고 답한다"

    @override
    def look(self, laid: ManyRegistriesAndACaller, answered: Answered[Searched]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [
                Refused(type(answered.raised) if answered.raised else Exception, answered.raised)
            ]
        return [
            Same("items", len(payload.items), DEFAULT_PAGE),
            Same("total_count", payload.total_count, len(laid.laid)),
            Same("has_next_page", payload.has_next_page, True),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class SearchingWithoutAFilterCountsEvery(
    Scenario[SeedingSession, ManyRegistriesAndACaller, ContainerRegistryAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "searching-without-a-filter-counts-every-registry"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 조건 없이 검색하면 심어둔 레지스트리가 모두 답으로 온다"

    @override
    def given(self) -> Given[SeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone()

    @override
    def when(self) -> When[ManyRegistriesAndACaller, ContainerRegistryAdapter, Searched]:
        return Searching(limit=DEFAULT_PAGE)

    @override
    def then(self) -> Then[ManyRegistriesAndACaller, Searched]:
        return EveryLaidRegistryIsCounted()


@dataclass(frozen=True)
class ANameNarrowsTheSearch(
    Scenario[SeedingSession, ManyRegistriesAndACaller, ContainerRegistryAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "filtering-by-name-leaves-only-the-registry-that-holds-it"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 이름으로 걸러 검색하면 그 이름을 가진 레지스트리만 남는다"

    @override
    def given(self) -> Given[SeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone()

    @override
    def when(self) -> When[ManyRegistriesAndACaller, ContainerRegistryAdapter, Searched]:
        return Searching(narrowed_by_name=True)

    @override
    def then(self) -> Then[ManyRegistriesAndACaller, Searched]:
        return OnlyTheNamedOneIsLeft()


@dataclass(frozen=True)
class ThePageSizeDefaultsToTen(
    Scenario[SeedingSession, ManyRegistriesAndACaller, ContainerRegistryAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "omitting-the-page-size-answers-with-ten-and-says-there-is-more"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 페이지 크기를 생략하고 검색하면, 열 건까지만 오고 다음 쪽이 있다고 답한다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone(besides=DEFAULT_PAGE)

    @override
    def when(self) -> When[ManyRegistriesAndACaller, ContainerRegistryAdapter, Searched]:
        return Searching()

    @override
    def then(self) -> Then[ManyRegistriesAndACaller, Searched]:
        return OnePageComesBack()


@dataclass(frozen=True)
class APlainUserMayNotSearch(
    Scenario[SeedingSession, ManyRegistriesAndACaller, ContainerRegistryAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-registries"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 레지스트리를 검색하려 하면 역할로 막힌다"

    @override
    def given(self) -> Given[SeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[ManyRegistriesAndACaller, ContainerRegistryAdapter, Searched]:
        return Searching(limit=DEFAULT_PAGE)

    @override
    def then(self) -> Then[ManyRegistriesAndACaller, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchingStep] = [
    SearchingWithoutAFilterCountsEvery(),
    ANameNarrowsTheSearch(),
    ThePageSizeDefaultsToTen(),
    APlainUserMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep,
    adapter: ContainerRegistryAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
