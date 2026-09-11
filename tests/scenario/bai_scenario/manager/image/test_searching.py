"""이미지 검색 — 오프셋만 읽는 검색과, 커서를 읽는 검색."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.image import (
    ByABrokenCursor,
    ByCursor,
    ByOffset,
    ByTwoModesAtOnce,
    ManyImagesAndACaller,
    ManyImagesAndSomeone,
    Paging,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.image.request import (
    AdminSearchImageAliasesInput,
    AdminSearchImagesInput,
)
from ai.backend.common.dto.manager.v2.image.response import (
    AdminSearchImageAliasesPayload,
    AdminSearchImagesPayload,
)
from ai.backend.manager.api.adapters.image.adapter import ImageAdapter
from ai.backend.manager.errors.api import InvalidCursor, InvalidGraphQLParameters
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.image.conditions import ImageConditions
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

DEFAULT_PAGE = 50
"""요청이 크기를 생략했을 때 어댑터가 채우는 한 쪽의 크기."""


@dataclass(frozen=True)
class Searching(When[ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]):
    """오프셋만 읽는 검색."""

    paging: Paging = field(default_factory=ByOffset)

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyImagesAndACaller) -> str:
        return f"{laid.caller.username}이 {self.paging.says()} 검색함"

    @override
    async def call(
        self, adapter: ImageAdapter, laid: ManyImagesAndACaller
    ) -> AdminSearchImagesPayload:
        with ActingAs(laid.caller):
            return await adapter.admin_search(AdminSearchImagesInput(**self.paging.asked()))


@dataclass(frozen=True)
class SearchingWithACursor(When[ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]):
    """커서를 읽는 검색. 바깥에서 준 조건도 이 경로에만 있다."""

    paging: Paging = field(default_factory=ByOffset)
    narrowed: bool = False

    @override
    def operation(self) -> str:
        return "admin_search_images_gql"

    @override
    def describe(self, laid: ManyImagesAndACaller) -> str:
        who = laid.caller.username
        narrowing = "한 레지스트리로 좁혀 " if self.narrowed else ""
        return f"{who}이 {narrowing}{self.paging.says()} 검색함"

    @override
    async def call(
        self, adapter: ImageAdapter, laid: ManyImagesAndACaller
    ) -> AdminSearchImagesPayload:
        narrowing = [ImageConditions.by_registry_id(laid.registry.id)] if self.narrowed else None
        with ActingAs(laid.caller):
            return await adapter.admin_search_images_gql(
                AdminSearchImagesInput(**self.paging.asked()), base_conditions=narrowing
            )


@dataclass(frozen=True)
class SearchingAliases(When[ManyImagesAndACaller, ImageAdapter, AdminSearchImageAliasesPayload]):
    """별칭을 검색한다."""

    @override
    def operation(self) -> str:
        return "admin_search_image_aliases"

    @override
    def describe(self, laid: ManyImagesAndACaller) -> str:
        return f"{laid.caller.username}이 별칭을 검색함"

    @override
    async def call(
        self, adapter: ImageAdapter, laid: ManyImagesAndACaller
    ) -> AdminSearchImageAliasesPayload:
        with ActingAs(laid.caller):
            return await adapter.admin_search_image_aliases(
                AdminSearchImageAliasesInput(limit=DEFAULT_PAGE)
            )


@dataclass(frozen=True)
class EveryLaidImageIsCounted(Then[ManyImagesAndACaller, AdminSearchImagesPayload]):
    """심은 것이 모두 세어진다."""

    @override
    def says(self) -> str:
        return "심은 이미지가 모두 세어진다"

    @override
    def look(
        self, laid: ManyImagesAndACaller, answered: Answered[AdminSearchImagesPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [
                Refused(type(answered.raised) if answered.raised else Exception, answered.raised)
            ]
        return [
            Same(
                "items",
                sorted(one.name for one in payload.items),
                sorted(one.name for one in laid.laid),
            ),
            Same("total_count", payload.total_count, len(laid.laid)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class OnePageComesBack(Then[ManyImagesAndACaller, AdminSearchImagesPayload]):
    """정한 만큼만 오고, 다음 쪽이 있다고 답한다."""

    size: int

    @override
    def says(self) -> str:
        return "정한 만큼만 오고 다음 쪽이 있다고 답한다"

    @override
    def look(
        self, laid: ManyImagesAndACaller, answered: Answered[AdminSearchImagesPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [
                Refused(type(answered.raised) if answered.raised else Exception, answered.raised)
            ]
        return [
            Same("items", len(payload.items), self.size),
            Same("total_count", payload.total_count, len(laid.laid)),
            Same("has_next_page", payload.has_next_page, True),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class NoAliasIsFound(Then[ManyImagesAndACaller, AdminSearchImageAliasesPayload]):
    """별칭을 하나도 붙이지 않았으므로 비어 있다."""

    @override
    def says(self) -> str:
        return "별칭이 하나도 없다"

    @override
    def look(
        self, laid: ManyImagesAndACaller, answered: Answered[AdminSearchImageAliasesPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [
                Refused(type(answered.raised) if answered.raised else Exception, answered.raised)
            ]
        return [
            Same("items", list(payload.items), []),
            Same("total_count", payload.total_count, 0),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class SearchingWithoutAFilterCountsEvery(
    Scenario[SeedingSession, ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]
):
    @override
    def summary(self) -> str:
        return "searching-without-a-filter-counts-every-image"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 조건 없이 검색하면 심어둔 이미지가 모두 답으로 온다"

    @override
    def given(self) -> Given[SeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone()

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]:
        return Searching(paging=ByOffset(limit=DEFAULT_PAGE))

    @override
    def then(self) -> Then[ManyImagesAndACaller, AdminSearchImagesPayload]:
        return EveryLaidImageIsCounted()


@dataclass(frozen=True)
class ThePageSizeDefaultsToFifty(
    Scenario[SeedingSession, ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]
):
    @override
    def summary(self) -> str:
        return "omitting-the-page-size-answers-with-fifty-and-says-there-is-more"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 페이지 크기를 생략하고 검색하면, 쉰 건까지만 오고 다음 쪽이 있다고 답한다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone(count=DEFAULT_PAGE + 1)

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]:
        return Searching()

    @override
    def then(self) -> Then[ManyImagesAndACaller, AdminSearchImagesPayload]:
        return OnePageComesBack(size=DEFAULT_PAGE)


@dataclass(frozen=True)
class APlainUserMayNotSearch(
    Scenario[SeedingSession, ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-images"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 이미지를 검색하려 하면 역할로 막힌다"

    @override
    def given(self) -> Given[SeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]:
        return Searching(paging=ByOffset(limit=DEFAULT_PAGE))

    @override
    def then(self) -> Then[ManyImagesAndACaller, AdminSearchImagesPayload]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class ACursorReadsFromTheFront(
    Scenario[SeedingSession, ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]
):
    @override
    def summary(self) -> str:
        return "a-cursor-search-answers-the-first-page-and-says-there-is-more"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 커서로 앞에서부터 읽으면 정한 만큼 오고 다음 쪽이 있다고 답한다"

    @override
    def given(self) -> Given[SeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone(count=3)

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]:
        return SearchingWithACursor(paging=ByCursor(first=2))

    @override
    def then(self) -> Then[ManyImagesAndACaller, AdminSearchImagesPayload]:
        return OnePageComesBack(size=2)


@dataclass(frozen=True)
class TheBaseConditionNarrowsFirst(
    Scenario[SeedingSession, ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]
):
    @override
    def summary(self) -> str:
        return "a-condition-given-from-outside-narrows-before-the-callers-filter"

    @override
    def describe(self) -> str:
        return (
            "바깥에서 한 레지스트리로 좁혀 준 조건이 먼저 걸리므로, "
            "그 레지스트리의 이미지만 답으로 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone()

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]:
        return SearchingWithACursor(paging=ByOffset(limit=DEFAULT_PAGE), narrowed=True)

    @override
    def then(self) -> Then[ManyImagesAndACaller, AdminSearchImagesPayload]:
        return EveryLaidImageIsCounted()


@dataclass(frozen=True)
class TwoPaginationModesAreRefused(
    Scenario[SeedingSession, ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]
):
    @override
    def summary(self) -> str:
        return "naming-two-pagination-modes-at-once-is-refused"

    @override
    def describe(self) -> str:
        return (
            "크기와 커서를 함께 주면 입력이 틀렸다는 이유로 거부된다. "
            "요청 타입이 아니라 어댑터가 페이지 방식을 고르면서 낸다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone()

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]:
        return SearchingWithACursor(paging=ByTwoModesAtOnce())

    @override
    def then(self) -> Then[ManyImagesAndACaller, AdminSearchImagesPayload]:
        return TheCallIsRefused(InvalidGraphQLParameters)


@dataclass(frozen=True)
class ABrokenCursorIsRefused(
    Scenario[SeedingSession, ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]
):
    @override
    def summary(self) -> str:
        return "a-cursor-that-cannot-be-read-is-refused"

    @override
    def describe(self) -> str:
        return "읽을 수 없는 커서 값을 주면 커서가 틀렸다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone()

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]:
        return SearchingWithACursor(paging=ByABrokenCursor())

    @override
    def then(self) -> Then[ManyImagesAndACaller, AdminSearchImagesPayload]:
        return TheCallIsRefused(InvalidCursor)


@dataclass(frozen=True)
class SearchingAliasesWithNoneAttached(
    Scenario[SeedingSession, ManyImagesAndACaller, ImageAdapter, AdminSearchImageAliasesPayload]
):
    @override
    def summary(self) -> str:
        return "searching-aliases-when-none-were-attached-answers-empty"

    @override
    def describe(self) -> str:
        return "별칭을 하나도 붙이지 않은 상태에서 슈퍼관리자가 별칭을 검색하면 답이 비어 있다"

    @override
    def given(self) -> Given[SeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone()

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, AdminSearchImageAliasesPayload]:
        return SearchingAliases()

    @override
    def then(self) -> Then[ManyImagesAndACaller, AdminSearchImageAliasesPayload]:
        return NoAliasIsFound()


@dataclass(frozen=True)
class APlainUserMayNotSearchAliases(
    Scenario[SeedingSession, ManyImagesAndACaller, ImageAdapter, AdminSearchImageAliasesPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-aliases"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 별칭을 검색하려 하면 역할로 막힌다"

    @override
    def given(self) -> Given[SeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, AdminSearchImageAliasesPayload]:
        return SearchingAliases()

    @override
    def then(self) -> Then[ManyImagesAndACaller, AdminSearchImageAliasesPayload]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[Any] = [
    SearchingWithoutAFilterCountsEvery(),
    ThePageSizeDefaultsToFifty(),
    APlainUserMayNotSearch(),
    ACursorReadsFromTheFront(),
    TheBaseConditionNarrowsFirst(),
    TwoPaginationModesAreRefused(),
    ABrokenCursorIsRefused(),
    SearchingAliasesWithNoneAttached(),
    APlainUserMayNotSearchAliases(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: Any, adapter: ImageAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
