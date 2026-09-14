"""컨테이너 레지스트리 검색 권한, 필터, 페이지네이션."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
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

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.container_registry.request import (
    AdminSearchContainerRegistriesInput,
    ContainerRegistryFilter,
    ContainerRegistryOrder,
)
from ai.backend.common.dto.manager.v2.container_registry.response import (
    AdminSearchContainerRegistriesPayload,
    ContainerRegistryNode,
)
from ai.backend.common.dto.manager.v2.container_registry.types import (
    ContainerRegistryOrderField,
    ContainerRegistryTypeFilter,
    OrderDirection,
)
from ai.backend.manager.api.adapter_options.cursor.cursor import encode_cursor
from ai.backend.manager.api.adapter_options.pagination.pagination import (
    DEFAULT_PAGINATION_LIMIT,
)
from ai.backend.manager.api.adapters.container_registry.adapter import ContainerRegistryAdapter
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.errors.api import InvalidGraphQLParameters
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
type SearchGiven = Given[SeedingSession, ManyRegistriesAndACaller]
type SearchThen = Then[ManyRegistriesAndACaller, AdminSearchContainerRegistriesPayload]


class ContainerRegistrySearchScenario(
    Scenario[
        SeedingSession,
        ManyRegistriesAndACaller,
        ContainerRegistryAdapter,
        AdminSearchContainerRegistriesPayload,
    ]
):
    """Common scenario signature for container registry searches."""


class FilterKind(StrEnum):
    NONE = "none"
    NAME = "name"
    TYPE = "type"
    NON_GLOBAL = "non-global"
    AND = "and"
    OR = "or"
    NOT = "not"


def registry_snapshot(
    registry: ContainerRegistryData | ContainerRegistryNode,
) -> tuple[object, ...]:
    return (
        registry.id,
        registry.url,
        registry.registry_name,
        registry.type,
        registry.project,
        registry.username,
        registry.ssl_verify,
        registry.is_global,
        registry.extra,
    )


@dataclass(frozen=True)
class Searching(
    When[ManyRegistriesAndACaller, ContainerRegistryAdapter, AdminSearchContainerRegistriesPayload]
):
    filter_kind: FilterKind = FilterKind.NONE
    order_direction: OrderDirection | None = None
    limit: int | None = None
    offset: int | None = None
    first: int | None = None
    after_first: bool = False
    last: int | None = None
    before_last: bool = False

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyRegistriesAndACaller) -> str:
        who = laid.caller.username
        if self.filter_kind is FilterKind.NAME:
            return f"{who}이 {laid.matching_registry.registry_name} 이름으로 걸러 검색함"
        if self.filter_kind is not FilterKind.NONE:
            return f"{who}이 {self.filter_kind.value} 조건으로 걸러 검색함"
        if self.after_first:
            return f"{who}이 첫 레지스트리 뒤를 커서로 검색함"
        if self.before_last:
            return f"{who}이 마지막 레지스트리 앞을 커서로 검색함"
        if self.offset is not None:
            return f"{who}이 이름순으로 {self.offset}건을 건너뛰고 검색함"
        if self.order_direction is not None:
            return f"{who}이 이름을 {self.order_direction.value} 순서로 검색함"
        if self.limit is None:
            return f"{who}이 크기를 생략하고 검색함"
        return f"{who}이 조건 없이 검색함"

    def _filter(self, laid: ManyRegistriesAndACaller) -> ContainerRegistryFilter | None:
        match self.filter_kind:
            case FilterKind.NONE:
                return None
            case FilterKind.NAME:
                return ContainerRegistryFilter(
                    registry_name=StringFilter(equals=laid.matching_registry.registry_name)
                )
            case FilterKind.TYPE:
                return ContainerRegistryFilter(
                    type=ContainerRegistryTypeFilter(equals=ContainerRegistryType.DOCKER)
                )
            case FilterKind.NON_GLOBAL:
                return ContainerRegistryFilter(is_global=False)
            case FilterKind.AND:
                return ContainerRegistryFilter(
                    AND=[
                        ContainerRegistryFilter(
                            type=ContainerRegistryTypeFilter(equals=ContainerRegistryType.DOCKER)
                        ),
                        ContainerRegistryFilter(is_global=True),
                    ]
                )
            case FilterKind.OR:
                return ContainerRegistryFilter(
                    OR=[
                        ContainerRegistryFilter(
                            type=ContainerRegistryTypeFilter(equals=ContainerRegistryType.DOCKER)
                        ),
                        ContainerRegistryFilter(is_global=False),
                    ]
                )
            case FilterKind.NOT:
                return ContainerRegistryFilter(NOT=[ContainerRegistryFilter(is_global=False)])

    @override
    async def call(
        self, adapter: ContainerRegistryAdapter, laid: ManyRegistriesAndACaller
    ) -> AdminSearchContainerRegistriesPayload:
        registry_order = (
            [
                ContainerRegistryOrder(
                    field=ContainerRegistryOrderField.REGISTRY_NAME,
                    direction=self.order_direction,
                )
            ]
            if self.order_direction is not None
            else None
        )
        after = None
        if self.after_first:
            first_registry = max(laid.registries, key=lambda registry: registry.id)
            after = encode_cursor(first_registry.id)
        before = None
        if self.before_last:
            last_registry = min(laid.registries, key=lambda registry: registry.id)
            before = encode_cursor(last_registry.id)
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                AdminSearchContainerRegistriesInput(
                    filter=self._filter(laid),
                    order=registry_order,
                    limit=self.limit,
                    offset=self.offset,
                    first=self.first,
                    after=after,
                    last=self.last,
                    before=before,
                )
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
                [registry_snapshot(one) for one in sorted(payload.items, key=lambda r: r.id)],
                [registry_snapshot(one) for one in sorted(laid.registries, key=lambda r: r.id)],
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
                [registry_snapshot(one) for one in payload.items],
                [registry_snapshot(laid.matching_registry)],
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
        ordered = sorted(laid.registries, key=lambda registry: registry.id, reverse=True)
        return [
            Same(
                "items",
                [registry_snapshot(one) for one in payload.items],
                [registry_snapshot(one) for one in ordered[:DEFAULT_PAGINATION_LIMIT]],
            ),
            Same("total_count", payload.total_count, len(laid.registries)),
            Same("has_next_page", payload.has_next_page, True),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class OnlyNonGlobalRegistriesAreReturned(
    Then[ManyRegistriesAndACaller, AdminSearchContainerRegistriesPayload]
):
    @override
    def says(self) -> str:
        return "전역이 아닌 레지스트리만 온다"

    @override
    def look(
        self,
        laid: ManyRegistriesAndACaller,
        answered: Answered[AdminSearchContainerRegistriesPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        expected = sorted(
            (registry for registry in laid.registries if not registry.is_global),
            key=lambda registry: registry.id,
        )
        return [
            Same(
                "items",
                [registry_snapshot(one) for one in sorted(payload.items, key=lambda r: r.id)],
                [registry_snapshot(one) for one in expected],
            ),
            Same("total_count", payload.total_count, len(expected)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class RegistriesAreOrderedByName(
    Then[ManyRegistriesAndACaller, AdminSearchContainerRegistriesPayload]
):
    direction: OrderDirection

    @override
    def says(self) -> str:
        return "요청한 이름 순서로 온다"

    @override
    def look(
        self,
        laid: ManyRegistriesAndACaller,
        answered: Answered[AdminSearchContainerRegistriesPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        expected = sorted(
            laid.registries,
            key=lambda registry: registry.registry_name,
            reverse=self.direction is OrderDirection.DESC,
        )
        return [
            Same(
                "items",
                [registry_snapshot(one) for one in payload.items],
                [registry_snapshot(one) for one in expected],
            ),
            Same("total_count", payload.total_count, len(laid.registries)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class OffsetPageIsReturned(Then[ManyRegistriesAndACaller, AdminSearchContainerRegistriesPayload]):
    offset: int
    limit: int

    @override
    def says(self) -> str:
        return "건너뛴 위치의 한 쪽이 온다"

    @override
    def look(
        self,
        laid: ManyRegistriesAndACaller,
        answered: Answered[AdminSearchContainerRegistriesPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        ordered = sorted(laid.registries, key=lambda registry: registry.registry_name)
        expected = ordered[self.offset : self.offset + self.limit]
        return [
            Same(
                "items",
                [registry_snapshot(one) for one in payload.items],
                [registry_snapshot(one) for one in expected],
            ),
            Same("total_count", payload.total_count, len(laid.registries)),
            Same(
                "has_next_page",
                payload.has_next_page,
                self.offset + len(expected) < len(laid.registries),
            ),
            Same("has_previous_page", payload.has_previous_page, self.offset > 0),
        ]


@dataclass(frozen=True)
class ForwardCursorPageIsReturned(
    Then[ManyRegistriesAndACaller, AdminSearchContainerRegistriesPayload]
):
    @override
    def says(self) -> str:
        return "커서 다음 레지스트리와 양쪽 페이지 표시가 온다"

    @override
    def look(
        self,
        laid: ManyRegistriesAndACaller,
        answered: Answered[AdminSearchContainerRegistriesPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        ordered = sorted(laid.registries, key=lambda registry: registry.id, reverse=True)
        return [
            Same(
                "items",
                [registry_snapshot(one) for one in payload.items],
                [registry_snapshot(ordered[1])],
            ),
            Same("total_count", payload.total_count, len(laid.registries)),
            Same("has_next_page", payload.has_next_page, True),
            Same("has_previous_page", payload.has_previous_page, True),
        ]


@dataclass(frozen=True)
class BackwardCursorPageIsReturned(
    Then[ManyRegistriesAndACaller, AdminSearchContainerRegistriesPayload]
):
    @override
    def says(self) -> str:
        return "커서 이전 레지스트리와 양쪽 페이지 표시가 온다"

    @override
    def look(
        self,
        laid: ManyRegistriesAndACaller,
        answered: Answered[AdminSearchContainerRegistriesPayload],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        ordered = sorted(laid.registries, key=lambda registry: registry.id)
        return [
            Same(
                "items",
                [registry_snapshot(one) for one in payload.items],
                [registry_snapshot(ordered[1])],
            ),
            Same("total_count", payload.total_count, len(laid.registries)),
            Same("has_next_page", payload.has_next_page, True),
            Same("has_previous_page", payload.has_previous_page, True),
        ]


@dataclass(frozen=True)
class SearchingWithoutAFilterCountsEvery(ContainerRegistrySearchScenario):
    @override
    def summary(self) -> str:
        return "searching-without-a-filter-counts-every-registry"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 조건 없이 검색하면 심어둔 레지스트리가 모두 답으로 온다"

    @override
    def given(self) -> SearchGiven:
        return ManyRegistriesAndSomeone()

    @override
    def when(
        self,
    ) -> When[
        ManyRegistriesAndACaller, ContainerRegistryAdapter, AdminSearchContainerRegistriesPayload
    ]:
        return Searching(limit=100)

    @override
    def then(self) -> SearchThen:
        return AllSeededRegistriesAreReturned()


@dataclass(frozen=True)
class ANameNarrowsTheSearch(ContainerRegistrySearchScenario):
    @override
    def summary(self) -> str:
        return "filtering-by-name-leaves-only-the-registry-that-holds-it"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 이름으로 걸러 검색하면 그 이름을 가진 레지스트리만 남는다"

    @override
    def given(self) -> SearchGiven:
        return ManyRegistriesAndSomeone()

    @override
    def when(
        self,
    ) -> When[
        ManyRegistriesAndACaller, ContainerRegistryAdapter, AdminSearchContainerRegistriesPayload
    ]:
        return Searching(filter_kind=FilterKind.NAME)

    @override
    def then(self) -> SearchThen:
        return OnlyTheMatchingRegistryIsReturned()


@dataclass(frozen=True)
class ATypeNarrowsTheSearch(ContainerRegistrySearchScenario):
    @override
    def summary(self) -> str:
        return "filtering-by-type-leaves-only-matching-registries"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 종류로 걸러 검색하면 그 종류를 가진 레지스트리만 남는다"

    @override
    def given(self) -> SearchGiven:
        return ManyRegistriesAndSomeone()

    @override
    def when(self) -> Searching:
        return Searching(filter_kind=FilterKind.TYPE)

    @override
    def then(self) -> SearchThen:
        return OnlyTheMatchingRegistryIsReturned()


@dataclass(frozen=True)
class GlobalVisibilityNarrowsTheSearch(ContainerRegistrySearchScenario):
    @override
    def summary(self) -> str:
        return "filtering-by-global-visibility-leaves-only-non-global-registries"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 전역 여부로 걸러 검색하면 전역이 아닌 레지스트리만 남는다"

    @override
    def given(self) -> SearchGiven:
        return ManyRegistriesAndSomeone()

    @override
    def when(self) -> Searching:
        return Searching(filter_kind=FilterKind.NON_GLOBAL)

    @override
    def then(self) -> SearchThen:
        return OnlyNonGlobalRegistriesAreReturned()


@dataclass(frozen=True)
class AndCombinesFilters(ContainerRegistrySearchScenario):
    @override
    def summary(self) -> str:
        return "and-combines-container-registry-filters"

    @override
    def describe(self) -> str:
        return "AND로 종류와 전역 여부를 묶으면 두 조건을 모두 만족하는 레지스트리만 남는다"

    @override
    def given(self) -> SearchGiven:
        return ManyRegistriesAndSomeone()

    @override
    def when(self) -> Searching:
        return Searching(filter_kind=FilterKind.AND)

    @override
    def then(self) -> SearchThen:
        return OnlyTheMatchingRegistryIsReturned()


@dataclass(frozen=True)
class OrCombinesFilters(ContainerRegistrySearchScenario):
    @override
    def summary(self) -> str:
        return "or-combines-container-registry-filters"

    @override
    def describe(self) -> str:
        return "OR로 종류와 전역 여부를 묶으면 어느 한 조건을 만족하는 레지스트리가 모두 남는다"

    @override
    def given(self) -> SearchGiven:
        return ManyRegistriesAndSomeone()

    @override
    def when(self) -> Searching:
        return Searching(filter_kind=FilterKind.OR, limit=100)

    @override
    def then(self) -> SearchThen:
        return AllSeededRegistriesAreReturned()


@dataclass(frozen=True)
class NotNegatesAFilter(ContainerRegistrySearchScenario):
    @override
    def summary(self) -> str:
        return "not-negates-a-container-registry-filter"

    @override
    def describe(self) -> str:
        return "NOT으로 전역이 아닌 조건을 뒤집으면 전역 레지스트리만 남는다"

    @override
    def given(self) -> SearchGiven:
        return ManyRegistriesAndSomeone()

    @override
    def when(self) -> Searching:
        return Searching(filter_kind=FilterKind.NOT)

    @override
    def then(self) -> SearchThen:
        return OnlyTheMatchingRegistryIsReturned()


@dataclass(frozen=True)
class ThePageSizeDefaultsToTen(ContainerRegistrySearchScenario):
    @override
    def summary(self) -> str:
        return "omitting-the-page-size-answers-with-ten-and-says-there-is-more"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 페이지 크기를 생략하고 검색하면, 열 건까지만 오고 다음 쪽이 있다고 답한다"
        )

    @override
    def given(self) -> SearchGiven:
        return ManyRegistriesAndSomeone(besides=DEFAULT_PAGINATION_LIMIT)

    @override
    def when(
        self,
    ) -> When[
        ManyRegistriesAndACaller, ContainerRegistryAdapter, AdminSearchContainerRegistriesPayload
    ]:
        return Searching()

    @override
    def then(self) -> SearchThen:
        return DefaultPageIsReturned()


@dataclass(frozen=True)
class OrderingByNameIsApplied(ContainerRegistrySearchScenario):
    @override
    def summary(self) -> str:
        return "ordering-by-name-returns-registries-in-the-requested-direction"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 이름 오름차순을 요청하면 레지스트리가 그 순서로 온다"

    @override
    def given(self) -> SearchGiven:
        return ManyRegistriesAndSomeone(besides=2)

    @override
    def when(self) -> Searching:
        return Searching(order_direction=OrderDirection.ASC, limit=100)

    @override
    def then(self) -> SearchThen:
        return RegistriesAreOrderedByName(OrderDirection.ASC)


@dataclass(frozen=True)
class OffsetSelectsAMiddlePage(ContainerRegistrySearchScenario):
    @override
    def summary(self) -> str:
        return "offset-pagination-selects-a-middle-page"

    @override
    def describe(self) -> str:
        return "이름순 검색에서 한 건을 건너뛰면 가운데 레지스트리와 양쪽 페이지 표시가 온다"

    @override
    def given(self) -> SearchGiven:
        return ManyRegistriesAndSomeone(besides=2)

    @override
    def when(self) -> Searching:
        return Searching(order_direction=OrderDirection.ASC, limit=1, offset=1)

    @override
    def then(self) -> SearchThen:
        return OffsetPageIsReturned(offset=1, limit=1)


@dataclass(frozen=True)
class OffsetPastTheEndReturnsNothing(ContainerRegistrySearchScenario):
    @override
    def summary(self) -> str:
        return "offset-past-the-end-returns-an-empty-page"

    @override
    def describe(self) -> str:
        return "전체 개수만큼 건너뛰면 빈 목록과 이전 페이지 표시가 온다"

    @override
    def given(self) -> SearchGiven:
        return ManyRegistriesAndSomeone(besides=2)

    @override
    def when(self) -> Searching:
        return Searching(order_direction=OrderDirection.ASC, limit=1, offset=3)

    @override
    def then(self) -> SearchThen:
        return OffsetPageIsReturned(offset=3, limit=1)


@dataclass(frozen=True)
class ForwardCursorSelectsTheNextPage(ContainerRegistrySearchScenario):
    @override
    def summary(self) -> str:
        return "a-forward-cursor-selects-the-next-page"

    @override
    def describe(self) -> str:
        return (
            "첫 레지스트리 뒤의 커서로 한 건을 요청하면 다음 레지스트리와 양쪽 페이지 표시가 온다"
        )

    @override
    def given(self) -> SearchGiven:
        return ManyRegistriesAndSomeone(besides=2)

    @override
    def when(self) -> Searching:
        return Searching(first=1, after_first=True)

    @override
    def then(self) -> SearchThen:
        return ForwardCursorPageIsReturned()


@dataclass(frozen=True)
class BackwardCursorSelectsThePreviousPage(ContainerRegistrySearchScenario):
    @override
    def summary(self) -> str:
        return "a-backward-cursor-selects-the-previous-page"

    @override
    def describe(self) -> str:
        return "마지막 레지스트리 앞의 커서로 한 건을 요청하면 이전 레지스트리와 양쪽 페이지 표시가 온다"

    @override
    def given(self) -> SearchGiven:
        return ManyRegistriesAndSomeone(besides=2)

    @override
    def when(self) -> Searching:
        return Searching(last=1, before_last=True)

    @override
    def then(self) -> SearchThen:
        return BackwardCursorPageIsReturned()


@dataclass(frozen=True)
class MixingPaginationModesIsRefused(ContainerRegistrySearchScenario):
    @override
    def summary(self) -> str:
        return "mixing-cursor-and-offset-pagination-is-refused"

    @override
    def describe(self) -> str:
        return "커서와 오프셋 페이지네이션을 한 요청에 함께 지정하면 잘못된 인자로 거부된다"

    @override
    def given(self) -> SearchGiven:
        return ManyRegistriesAndSomeone()

    @override
    def when(self) -> Searching:
        return Searching(first=1, limit=1)

    @override
    def then(self) -> SearchThen:
        return TheCallIsRefused(InvalidGraphQLParameters)


@dataclass(frozen=True)
class APlainUserMayNotSearch(ContainerRegistrySearchScenario):
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
    def given(self) -> SearchGiven:
        return ManyRegistriesAndSomeone(role=UserRole.USER)

    @override
    def when(
        self,
    ) -> When[
        ManyRegistriesAndACaller, ContainerRegistryAdapter, AdminSearchContainerRegistriesPayload
    ]:
        return Searching(limit=100)

    @override
    def then(self) -> SearchThen:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchScenario] = [
    SearchingWithoutAFilterCountsEvery(),
    ANameNarrowsTheSearch(),
    ATypeNarrowsTheSearch(),
    GlobalVisibilityNarrowsTheSearch(),
    AndCombinesFilters(),
    OrCombinesFilters(),
    NotNegatesAFilter(),
    ThePageSizeDefaultsToTen(),
    OrderingByNameIsApplied(),
    OffsetSelectsAMiddlePage(),
    OffsetPastTheEndReturnsNothing(),
    ForwardCursorSelectsTheNextPage(),
    BackwardCursorSelectsThePreviousPage(),
    MixingPaginationModesIsRefused(),
    APlainUserMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchScenario,
    adapter: ContainerRegistryAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
