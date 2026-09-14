"""컨테이너 레지스트리 검색 권한, 필터, 페이지네이션."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
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
from ai.backend.manager.api.adapter_options.pagination.pagination import (
    DEFAULT_PAGINATION_LIMIT,
)
from ai.backend.manager.api.adapters.container_registry.adapter import ContainerRegistryAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
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

type SearchScenario = Scenario[
    SeedingSession,
    ManyRegistriesAndACaller,
    ContainerRegistryAdapter,
    AdminSearchContainerRegistriesPayload,
]


@dataclass(frozen=True)
class Searching(
    When[ManyRegistriesAndACaller, ContainerRegistryAdapter, AdminSearchContainerRegistriesPayload]
):
    filter_by_name: bool = False
    limit: int | None = None

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyRegistriesAndACaller) -> str:
        who = laid.caller.username
        if self.filter_by_name:
            return f"{who}이 {laid.matching_registry.registry_name} 이름으로 걸러 검색함"
        if self.limit is None:
            return f"{who}이 크기를 생략하고 검색함"
        return f"{who}이 조건 없이 검색함"

    @override
    async def call(
        self, adapter: ContainerRegistryAdapter, laid: ManyRegistriesAndACaller
    ) -> AdminSearchContainerRegistriesPayload:
        registry_filter = (
            ContainerRegistryFilter(
                registry_name=StringFilter(equals=laid.matching_registry.registry_name)
            )
            if self.filter_by_name
            else None
        )
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                AdminSearchContainerRegistriesInput(filter=registry_filter, limit=self.limit)
            )


@dataclass(frozen=True)
class AllSeededRegistriesAreReturned(
    Then[ManyRegistriesAndACaller, AdminSearchContainerRegistriesPayload]
):
    @override
    def says(self) -> str:
        return "심은 레지스트리가 모두 세어진다"

    @override
    def look(
        self,
        laid: ManyRegistriesAndACaller,
        answered: Answered[AdminSearchContainerRegistriesPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            Same(
                "items",
                sorted(one.registry_name for one in payload.items),
                sorted(one.registry_name for one in laid.registries),
            ),
            Same("total_count", payload.total_count, len(laid.registries)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class OnlyTheMatchingRegistryIsReturned(
    Then[ManyRegistriesAndACaller, AdminSearchContainerRegistriesPayload]
):
    @override
    def says(self) -> str:
        return "걸러낸 그 레지스트리 하나만 남는다"

    @override
    def look(
        self,
        laid: ManyRegistriesAndACaller,
        answered: Answered[AdminSearchContainerRegistriesPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            Same(
                "items",
                [one.registry_name for one in payload.items],
                [laid.matching_registry.registry_name],
            ),
            Same("total_count", payload.total_count, 1),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class DefaultPageIsReturned(Then[ManyRegistriesAndACaller, AdminSearchContainerRegistriesPayload]):
    @override
    def says(self) -> str:
        return "한 쪽만 오고 다음 쪽이 있다고 답한다"

    @override
    def look(
        self,
        laid: ManyRegistriesAndACaller,
        answered: Answered[AdminSearchContainerRegistriesPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            Same("items", len(payload.items), DEFAULT_PAGINATION_LIMIT),
            Same("total_count", payload.total_count, len(laid.registries)),
            Same("has_next_page", payload.has_next_page, True),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class SearchingWithoutAFilterCountsEvery(
    Scenario[
        SeedingSession,
        ManyRegistriesAndACaller,
        ContainerRegistryAdapter,
        AdminSearchContainerRegistriesPayload,
    ]
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
    def when(
        self,
    ) -> When[
        ManyRegistriesAndACaller, ContainerRegistryAdapter, AdminSearchContainerRegistriesPayload
    ]:
        return Searching(limit=100)

    @override
    def then(self) -> Then[ManyRegistriesAndACaller, AdminSearchContainerRegistriesPayload]:
        return AllSeededRegistriesAreReturned()


@dataclass(frozen=True)
class ANameNarrowsTheSearch(
    Scenario[
        SeedingSession,
        ManyRegistriesAndACaller,
        ContainerRegistryAdapter,
        AdminSearchContainerRegistriesPayload,
    ]
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
    def when(
        self,
    ) -> When[
        ManyRegistriesAndACaller, ContainerRegistryAdapter, AdminSearchContainerRegistriesPayload
    ]:
        return Searching(filter_by_name=True)

    @override
    def then(self) -> Then[ManyRegistriesAndACaller, AdminSearchContainerRegistriesPayload]:
        return OnlyTheMatchingRegistryIsReturned()


@dataclass(frozen=True)
class ThePageSizeDefaultsToTen(
    Scenario[
        SeedingSession,
        ManyRegistriesAndACaller,
        ContainerRegistryAdapter,
        AdminSearchContainerRegistriesPayload,
    ]
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
        return ManyRegistriesAndSomeone(besides=DEFAULT_PAGINATION_LIMIT)

    @override
    def when(
        self,
    ) -> When[
        ManyRegistriesAndACaller, ContainerRegistryAdapter, AdminSearchContainerRegistriesPayload
    ]:
        return Searching()

    @override
    def then(self) -> Then[ManyRegistriesAndACaller, AdminSearchContainerRegistriesPayload]:
        return DefaultPageIsReturned()


@dataclass(frozen=True)
class APlainUserMayNotSearch(
    Scenario[
        SeedingSession,
        ManyRegistriesAndACaller,
        ContainerRegistryAdapter,
        AdminSearchContainerRegistriesPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-registries"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 아닌 사용자가 레지스트리를 검색하려 하면 권한 부족으로 거부된다. "
            "이 호출은 부른 사람이 슈퍼관리자인지만 보고, 어떤 권한을 받았는지는 보지 않는다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyRegistriesAndACaller]:
        return ManyRegistriesAndSomeone(role=UserRole.USER)

    @override
    def when(
        self,
    ) -> When[
        ManyRegistriesAndACaller, ContainerRegistryAdapter, AdminSearchContainerRegistriesPayload
    ]:
        return Searching(limit=100)

    @override
    def then(self) -> Then[ManyRegistriesAndACaller, AdminSearchContainerRegistriesPayload]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchScenario] = [
    SearchingWithoutAFilterCountsEvery(),
    ANameNarrowsTheSearch(),
    ThePageSizeDefaultsToTen(),
    APlainUserMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchScenario,
    adapter: ContainerRegistryAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
