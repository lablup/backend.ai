"""이미지 검색 — 오프셋만 사용하는 검색과, 커서를 사용하는 검색."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

import pytest

from ai.backend.common.data.entity.image import ImageID
from ai.backend.common.data.filter_specs import UUIDEqualMatchSpec
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.image.request import (
    AdminSearchImageAliasesInput,
    AdminSearchImagesInput,
    ImageAliasFilterInputDTO,
    ImageAliasOrderByInputDTO,
    ImageFilterInputDTO,
    ImageOrderByInputDTO,
    ImageStatusFilterInputDTO,
    SearchImageAliasesInput,
)
from ai.backend.common.dto.manager.v2.image.response import (
    AdminSearchImageAliasesPayload,
    AdminSearchImagesPayload,
    SearchImageAliasesPayload,
)
from ai.backend.common.dto.manager.v2.image.types import (
    ImageAliasOrderField,
    ImageOrderField,
    ImageStatusType,
    OrderDirection,
)
from ai.backend.manager.api.adapters.image.adapter import ImageAdapter
from ai.backend.manager.errors.api import InvalidCursor, InvalidGraphQLParameters
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.image.searchable_fields import ImageSearchableFields
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.image import (
    AliasesAndACaller,
    AliasesOnTwoImagesAndSomeone,
    AnAliasAndACaller,
    AnAliasAndAPlainUser,
    AnAliasAndSomeone,
    ByABrokenCursor,
    ByCursor,
    ByOffset,
    ByTwoModesAtOnce,
    Filled,
    ImagesInTwoRegistries,
    ImagesWithTwoStatuses,
    ManyImagesAndACaller,
    ManyImagesAndSomeone,
    Paging,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

DEFAULT_PAGE = 50
"""요청이 크기를 생략했을 때 어댑터가 채우는 한 페이지의 크기."""


@dataclass(frozen=True)
class Searching(When[ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]):
    """크기와 오프셋, 또는 커서로 페이지를 고르는 검색."""

    paging: Paging = field(default_factory=ByOffset)
    named_only: bool = False
    status: ImageStatusType | None = None
    descending: bool = False

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyImagesAndACaller) -> str:
        conditions: list[str] = []
        if self.named_only:
            conditions.append(f"{laid.named.name} 이름으로")
        if self.status is not None:
            conditions.append(f"{self.status.value} 상태로")
        if self.descending:
            conditions.append("이름 내림차순으로 정렬해")
        conditions.append(self.paging.says())
        return f"{laid.caller.username}이 {' '.join(conditions)} 검색함"

    @override
    async def call(
        self, adapter: ImageAdapter, laid: ManyImagesAndACaller
    ) -> AdminSearchImagesPayload:
        filter_input = None
        if self.named_only or self.status is not None:
            filter_input = ImageFilterInputDTO(
                name=StringFilter(equals=str(laid.named.name)) if self.named_only else None,
                status=(
                    ImageStatusFilterInputDTO(equals=self.status)
                    if self.status is not None
                    else None
                ),
            )
        order = (
            [
                ImageOrderByInputDTO(
                    field=ImageOrderField.NAME,
                    direction=OrderDirection.DESC,
                )
            ]
            if self.descending
            else None
        )
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                AdminSearchImagesInput(
                    filter=filter_input,
                    order=order,
                    **self.paging.asked(),
                )
            )


@dataclass(frozen=True)
class SearchingWithACursor(When[ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]):
    """커서를 사용하는 검색. 호출 측이 지정하는 기본 조건도 이 경로에만 있다."""

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
        narrowing = (
            [
                ImageSearchableFields.own.registry_id.filter.equals(
                    UUIDEqualMatchSpec(value=laid.registry.id, negated=False)
                )
            ]
            if self.narrowed
            else None
        )
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
class SearchingTheAliasesOf(When[AnAliasAndACaller, ImageAdapter, AdminSearchImageAliasesPayload]):
    """별칭이 등록된 전제에서 별칭을 검색한다."""

    @override
    def operation(self) -> str:
        return "admin_search_image_aliases"

    @override
    def describe(self, laid: AnAliasAndACaller) -> str:
        return f"{laid.caller.username}이 별칭을 검색함"

    @override
    async def call(
        self, adapter: ImageAdapter, laid: AnAliasAndACaller
    ) -> AdminSearchImageAliasesPayload:
        with ActingAs(laid.caller):
            return await adapter.admin_search_image_aliases(
                AdminSearchImageAliasesInput(limit=DEFAULT_PAGE)
            )


@dataclass(frozen=True)
class SearchingTheAliasesOfTheImage(
    When[AnAliasAndACaller, ImageAdapter, SearchImageAliasesPayload]
):
    """그 이미지를 스코프로 별칭을 검색한다."""

    @override
    def operation(self) -> str:
        return "image_search_aliases"

    @override
    def describe(self, laid: AnAliasAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.image.name}의 별칭을 검색함"

    @override
    async def call(
        self, adapter: ImageAdapter, laid: AnAliasAndACaller
    ) -> SearchImageAliasesPayload:
        with ActingAs(laid.caller):
            return await adapter.image_search_aliases(
                ImageID(laid.image.id), SearchImageAliasesInput(limit=DEFAULT_PAGE)
            )


@dataclass(frozen=True)
class SearchingAliasesForOneImage(
    When[AliasesAndACaller, ImageAdapter, AdminSearchImageAliasesPayload]
):
    """한 이미지에 등록된 별칭만 이름 내림차순으로 검색한다."""

    @override
    def operation(self) -> str:
        return "admin_search_image_aliases"

    @override
    def describe(self, laid: AliasesAndACaller) -> str:
        return f"{laid.caller.username}이 한 이미지의 별칭을 이름 내림차순으로 검색함"

    @override
    async def call(
        self, adapter: ImageAdapter, laid: AliasesAndACaller
    ) -> AdminSearchImageAliasesPayload:
        with ActingAs(laid.caller):
            return await adapter.admin_search_image_aliases(
                AdminSearchImageAliasesInput(
                    filter=ImageAliasFilterInputDTO(
                        image_id=UUIDFilter(equals=laid.image.id),
                    ),
                    order=[
                        ImageAliasOrderByInputDTO(
                            field=ImageAliasOrderField.ALIAS,
                            direction=OrderDirection.DESC,
                        )
                    ],
                    limit=DEFAULT_PAGE,
                )
            )


@dataclass(frozen=True)
class TheAttachedAliasIsFound[
    TPayload: (AdminSearchImageAliasesPayload, SearchImageAliasesPayload)
](Then[AnAliasAndACaller, TPayload]):
    """등록해 둔 별칭 1개가 반환된다. 전체 별칭 검색과 한 이미지의 별칭 검색이 같이 쓴다."""

    @override
    def says(self) -> str:
        return "등록해 둔 별칭이 반환된다"

    @override
    def look(self, laid: AnAliasAndACaller, answered: Answered[TPayload]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Held("응답", answered.response, Filled())]
        return [
            Same("items", [one.alias for one in payload.items], [laid.alias.alias]),
            Same("total_count", payload.total_count, 1),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class EveryLaidImageIsCounted(Then[ManyImagesAndACaller, AdminSearchImagesPayload]):
    """미리 만들어 둔 이미지가 모두 집계된다."""

    @override
    def says(self) -> str:
        return "미리 만들어 둔 이미지가 모두 집계된다"

    @override
    def look(
        self, laid: ManyImagesAndACaller, answered: Answered[AdminSearchImagesPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Held("응답", answered.response, Filled())]
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
class OnlyTheNamedImageIsReturned(Then[ManyImagesAndACaller, AdminSearchImagesPayload]):
    """이름이 일치하는 이미지만 반환된다."""

    @override
    def says(self) -> str:
        return "이름이 일치하는 이미지만 반환된다"

    @override
    def look(
        self, laid: ManyImagesAndACaller, answered: Answered[AdminSearchImagesPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Held("응답", answered.response, Filled())]
        return [
            Same("items", [one.name for one in payload.items], [str(laid.named.name)]),
            Same("total_count", payload.total_count, 1),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class OnlyTheAliveImageIsReturned(Then[ManyImagesAndACaller, AdminSearchImagesPayload]):
    """삭제된 이미지는 제외하고 살아 있는 이미지만 반환된다."""

    @override
    def says(self) -> str:
        return "살아 있는 이미지만 반환된다"

    @override
    def look(
        self, laid: ManyImagesAndACaller, answered: Answered[AdminSearchImagesPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Held("응답", answered.response, Filled())]
        return [
            Same("items", [one.name for one in payload.items], [str(laid.named.name)]),
            Same("total_count", payload.total_count, 1),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheMiddleOfTheDescendingOrderIsReturned(Then[ManyImagesAndACaller, AdminSearchImagesPayload]):
    """이름 내림차순으로 정렬한 뒤 첫 항목을 제외한 2개가 반환된다."""

    @override
    def says(self) -> str:
        return "정렬된 결과의 가운데 2개와 앞뒤 페이지 표시가 반환된다"

    @override
    def look(
        self, laid: ManyImagesAndACaller, answered: Answered[AdminSearchImagesPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Held("응답", answered.response, Filled())]
        ordered = sorted((str(one.name) for one in laid.laid), reverse=True)
        return [
            Same("items", [one.name for one in payload.items], ordered[1:3]),
            Same("total_count", payload.total_count, len(laid.laid)),
            Same("has_next_page", payload.has_next_page, True),
            Same("has_previous_page", payload.has_previous_page, True),
        ]


@dataclass(frozen=True)
class OnlyTheAliasesOfTheNamedImageAreReturned(
    Then[AliasesAndACaller, AdminSearchImageAliasesPayload]
):
    """선택한 이미지의 별칭만 이름 내림차순으로 반환된다."""

    @override
    def says(self) -> str:
        return "해당 이미지의 별칭만 이름 내림차순으로 반환된다"

    @override
    def look(
        self, laid: AliasesAndACaller, answered: Answered[AdminSearchImageAliasesPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Held("응답", answered.response, Filled())]
        expected = sorted((one.alias for one in laid.aliases), reverse=True)
        return [
            Same("items", [one.alias for one in payload.items], expected),
            Same("total_count", payload.total_count, len(expected)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class OnePageComesBack(Then[ManyImagesAndACaller, AdminSearchImagesPayload]):
    """지정한 개수만 반환되고, 다음 페이지가 있다고 알린다."""

    size: int

    @override
    def says(self) -> str:
        return "지정한 개수만 반환되고 다음 페이지가 있다고 알린다"

    @override
    def look(
        self, laid: ManyImagesAndACaller, answered: Answered[AdminSearchImagesPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Held("응답", answered.response, Filled())]
        return [
            Same("length", len(payload.items), self.size),
            Same("total_count", payload.total_count, len(laid.laid)),
            Same("has_next_page", payload.has_next_page, True),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class NoAliasIsFound(Then[ManyImagesAndACaller, AdminSearchImageAliasesPayload]):
    """별칭을 하나도 등록하지 않았으므로 비어 있다."""

    @override
    def says(self) -> str:
        return "별칭이 하나도 없다"

    @override
    def look(
        self, laid: ManyImagesAndACaller, answered: Answered[AdminSearchImageAliasesPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Held("응답", answered.response, Filled())]
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
        return "슈퍼관리자가 조건 없이 검색하면 미리 만들어 둔 이미지가 모두 반환된다"

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
class SearchingByNameReturnsOnlyTheMatch(
    Scenario[SeedingSession, ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]
):
    @override
    def summary(self) -> str:
        return "filtering-images-by-name-returns-only-the-match"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 한 이미지의 이름으로 검색하면 그 이미지만 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone(count=3)

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]:
        return Searching(paging=ByOffset(limit=DEFAULT_PAGE), named_only=True)

    @override
    def then(self) -> Then[ManyImagesAndACaller, AdminSearchImagesPayload]:
        return OnlyTheNamedImageIsReturned()


@dataclass(frozen=True)
class SearchingByStatusReturnsOnlyAliveImages(
    Scenario[SeedingSession, ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]
):
    @override
    def summary(self) -> str:
        return "filtering-images-by-status-returns-only-alive-images"

    @override
    def describe(self) -> str:
        return (
            "살아 있는 이미지와 삭제된 이미지 중 살아 있는 상태로 검색하면 해당 이미지만 반환된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyImagesAndACaller]:
        return ImagesWithTwoStatuses()

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]:
        return Searching(
            paging=ByOffset(limit=DEFAULT_PAGE),
            status=ImageStatusType.ALIVE,
        )

    @override
    def then(self) -> Then[ManyImagesAndACaller, AdminSearchImagesPayload]:
        return OnlyTheAliveImageIsReturned()


@dataclass(frozen=True)
class OrderingAndOffsetChooseTheMiddlePage(
    Scenario[SeedingSession, ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]
):
    @override
    def summary(self) -> str:
        return "ordering-by-name-and-offsetting-returns-the-middle-page"

    @override
    def describe(self) -> str:
        return "이름 내림차순으로 정렬하고 첫 항목을 제외하면 두 번째와 세 번째 이미지가 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone(count=4)

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]:
        return Searching(
            paging=ByOffset(limit=2, offset=1),
            descending=True,
        )

    @override
    def then(self) -> Then[ManyImagesAndACaller, AdminSearchImagesPayload]:
        return TheMiddleOfTheDescendingOrderIsReturned()


@dataclass(frozen=True)
class ThePageSizeDefaultsToFifty(
    Scenario[SeedingSession, ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]
):
    @override
    def summary(self) -> str:
        return "omitting-the-page-size-answers-with-fifty-and-says-there-is-more"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 페이지 크기를 생략하고 검색하면, 50개까지만 반환되고 다음 페이지가 있다고 알린다"

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
        return "슈퍼관리자가 아닌 사용자가 이미지를 검색하려 하면 슈퍼관리자 권한 부족으로 거부된다"

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
class ACursorAloneReadsFromTheFront(
    Scenario[SeedingSession, ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]
):
    @override
    def summary(self) -> str:
        return "a-cursor-alone-answers-the-first-page-and-says-there-is-more"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 크기와 오프셋 없이 커서만 지정해 검색하면 지정한 개수만 반환되고 다음 페이지가 있다고 알린다"

    @override
    def given(self) -> Given[SeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone(count=3)

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]:
        return Searching(paging=ByCursor(first=2))

    @override
    def then(self) -> Then[ManyImagesAndACaller, AdminSearchImagesPayload]:
        return OnePageComesBack(size=2)


@dataclass(frozen=True)
class ASizeBesideACursorIsRefused(
    Scenario[SeedingSession, ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]
):
    @override
    def summary(self) -> str:
        return "a-size-beside-a-cursor-is-refused"

    @override
    def describe(self) -> str:
        return "크기와 커서를 함께 지정하면 입력이 잘못되어 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone()

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]:
        return Searching(paging=ByTwoModesAtOnce())

    @override
    def then(self) -> Then[ManyImagesAndACaller, AdminSearchImagesPayload]:
        return TheCallIsRefused(InvalidGraphQLParameters)


@dataclass(frozen=True)
class ACursorReadsFromTheFront(
    Scenario[SeedingSession, ManyImagesAndACaller, ImageAdapter, AdminSearchImagesPayload]
):
    @override
    def summary(self) -> str:
        return "a-cursor-search-answers-the-first-page-and-says-there-is-more"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 커서로 앞에서부터 조회하면 지정한 개수만 반환되고 다음 페이지가 있다고 알린다"

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
            "이미지가 레지스트리 2개에 나뉘어 있을 때 호출 측이 한쪽으로 좁혀 주면, "
            "그 레지스트리의 이미지만 반환되고 다른 쪽은 집계되지 않는다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyImagesAndACaller]:
        return ImagesInTwoRegistries()

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
            "크기와 커서를 함께 지정하면 입력이 잘못되어 거부된다. "
            "요청 타입이 아니라 어댑터가 페이지 방식을 고르는 과정에서 발생한다"
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
        return "해석할 수 없는 커서 값을 지정하면 커서가 잘못되어 거부된다"

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
        return "별칭을 하나도 등록하지 않은 상태에서 슈퍼관리자가 별칭을 검색하면 응답이 비어 있다"

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
class SearchingAliasesFindsTheAttachedOne(
    Scenario[SeedingSession, AnAliasAndACaller, ImageAdapter, AdminSearchImageAliasesPayload]
):
    @override
    def summary(self) -> str:
        return "searching-aliases-answers-with-the-one-that-was-attached"

    @override
    def describe(self) -> str:
        return "별칭이 등록되어 있을 때 슈퍼관리자가 별칭을 검색하면 그 별칭이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AnAliasAndACaller]:
        return AnAliasAndSomeone()

    @override
    def when(self) -> When[AnAliasAndACaller, ImageAdapter, AdminSearchImageAliasesPayload]:
        return SearchingTheAliasesOf()

    @override
    def then(self) -> Then[AnAliasAndACaller, AdminSearchImageAliasesPayload]:
        return TheAttachedAliasIsFound()


@dataclass(frozen=True)
class FilteringAndOrderingAliases(
    Scenario[SeedingSession, AliasesAndACaller, ImageAdapter, AdminSearchImageAliasesPayload]
):
    @override
    def summary(self) -> str:
        return "filtering-aliases-by-image-and-ordering-by-name"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 한 이미지의 별칭만 이름 내림차순으로 검색하면 해당 별칭만 정렬되어 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AliasesAndACaller]:
        return AliasesOnTwoImagesAndSomeone()

    @override
    def when(self) -> When[AliasesAndACaller, ImageAdapter, AdminSearchImageAliasesPayload]:
        return SearchingAliasesForOneImage()

    @override
    def then(self) -> Then[AliasesAndACaller, AdminSearchImageAliasesPayload]:
        return OnlyTheAliasesOfTheNamedImageAreReturned()


@dataclass(frozen=True)
class APlainUserMayNotSearchAliases(
    Scenario[SeedingSession, ManyImagesAndACaller, ImageAdapter, AdminSearchImageAliasesPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-aliases"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 별칭을 검색하려 하면 슈퍼관리자 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ManyImagesAndACaller]:
        return ManyImagesAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[ManyImagesAndACaller, ImageAdapter, AdminSearchImageAliasesPayload]:
        return SearchingAliases()

    @override
    def then(self) -> Then[ManyImagesAndACaller, AdminSearchImageAliasesPayload]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class AReaderOfTheImageSearchesItsAliases(
    Scenario[SeedingSession, AnAliasAndACaller, ImageAdapter, SearchImageAliasesPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-who-can-read-the-image-gets-its-aliases"

    @override
    def describe(self) -> str:
        return (
            "그 이미지에 권한을 받은 사용자가 그 이미지의 별칭을 검색하면 등록해 둔 별칭이 반환된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnAliasAndACaller]:
        return AnAliasAndAPlainUser(granted=True)

    @override
    def when(self) -> When[AnAliasAndACaller, ImageAdapter, SearchImageAliasesPayload]:
        return SearchingTheAliasesOfTheImage()

    @override
    def then(self) -> Then[AnAliasAndACaller, SearchImageAliasesPayload]:
        return TheAttachedAliasIsFound()


@dataclass(frozen=True)
class AUserWithNoPermissionMayNotSearchTheImageAliases(
    Scenario[SeedingSession, AnAliasAndACaller, ImageAdapter, SearchImageAliasesPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-who-cannot-read-the-image-is-refused-its-aliases"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 그 이미지의 별칭을 검색하려 하면 권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnAliasAndACaller]:
        return AnAliasAndAPlainUser(granted=False)

    @override
    def when(self) -> When[AnAliasAndACaller, ImageAdapter, SearchImageAliasesPayload]:
        return SearchingTheAliasesOfTheImage()

    @override
    def then(self) -> Then[AnAliasAndACaller, SearchImageAliasesPayload]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[Any] = [
    SearchingWithoutAFilterCountsEvery(),
    SearchingByNameReturnsOnlyTheMatch(),
    SearchingByStatusReturnsOnlyAliveImages(),
    OrderingAndOffsetChooseTheMiddlePage(),
    ThePageSizeDefaultsToFifty(),
    ACursorAloneReadsFromTheFront(),
    ASizeBesideACursorIsRefused(),
    APlainUserMayNotSearch(),
    ACursorReadsFromTheFront(),
    TheBaseConditionNarrowsFirst(),
    TwoPaginationModesAreRefused(),
    ABrokenCursorIsRefused(),
    SearchingAliasesWithNoneAttached(),
    SearchingAliasesFindsTheAttachedOne(),
    FilteringAndOrderingAliases(),
    APlainUserMayNotSearchAliases(),
    AReaderOfTheImageSearchesItsAliases(),
    AUserWithNoPermissionMayNotSearchTheImageAliases(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: Any, adapter: ImageAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
