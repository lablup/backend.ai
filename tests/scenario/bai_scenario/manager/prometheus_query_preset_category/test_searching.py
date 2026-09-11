"""분류 훑기 — 인증된 사용자 누구나, 이름으로 걸러서."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.prometheus_query_preset_category import (
    ACategoryAlone,
    ACategoryAndNobody,
    EveryLaidCategoryIsFound,
    ManyCategoriesAndACaller,
    ManyCategoriesAndSomeone,
    OnePageOfThemComesBack,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.request import (
    CategoryFilter,
    SearchCategoriesInput,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset_category.response import (
    SearchCategoriesPayload,
)
from ai.backend.manager.api.adapters.prometheus_query_preset_category.adapter import (
    PrometheusQueryPresetCategoryAdapter,
)
from ai.backend.manager.errors.user import UserNotFound
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

type Adapter = PrometheusQueryPresetCategoryAdapter
type Searched = SearchCategoriesPayload
type SearchingStep = Scenario[SeedingSession, ManyCategoriesAndACaller, Adapter, Searched]
type NobodyStep = Scenario[SeedingSession, ACategoryAlone, Adapter, Searched]


@dataclass(frozen=True)
class SearchingEverything(When[ManyCategoriesAndACaller, Adapter, Searched]):
    """필터도 크기도 없이 전체를 훑는다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyCategoriesAndACaller) -> str:
        return f"{laid.caller.username}이 필터 없이 전체 조회"

    @override
    async def call(self, adapter: Adapter, laid: ManyCategoriesAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search(SearchCategoriesInput())


@dataclass(frozen=True)
class SearchingByName(When[ManyCategoriesAndACaller, Adapter, Searched]):
    """심은 것 중 골라낸 하나의 이름으로 걸러 훑는다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyCategoriesAndACaller) -> str:
        return f"{laid.caller.username}이 이름 {laid.named.name}으로 걸러 조회"

    @override
    async def call(self, adapter: Adapter, laid: ManyCategoriesAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search(
                SearchCategoriesInput(
                    filter=CategoryFilter(name=StringFilter(equals=laid.named.name))
                )
            )


@dataclass(frozen=True)
class SearchingAsNobody(When[ACategoryAlone, Adapter, Searched]):
    """아무도 아닌 채로 훑는다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ACategoryAlone) -> str:
        return "아무도 아닌 채로 전체 조회"

    @override
    async def call(self, adapter: Adapter, laid: ACategoryAlone) -> Searched:
        return await adapter.search(SearchCategoriesInput())


@dataclass(frozen=True)
class OnlyTheNamedOneIsFound(Then[ManyCategoriesAndACaller, Searched]):
    """골라낸 하나만 세어진다."""

    @override
    def says(self) -> str:
        return "이름으로 고른 하나만 세어진다"

    @override
    def look(self, laid: ManyCategoriesAndACaller, answered: Answered[Searched]) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(UserNotFound, answered.raised)]
        return [
            Same("items", [one.name for one in page.items], [laid.named.name]),
            Same("total_count", page.total_count, 1),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class AnyoneCountsEveryOne(Scenario[SeedingSession, ManyCategoriesAndACaller, Adapter, Searched]):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-counts-every-category"

    @override
    def describe(self) -> str:
        return "분류 둘이 있고 아무 권한도 받지 않은 사용자가 필터 없이 훑으면, 둘을 모두 센다"

    @override
    def given(self) -> Given[SeedingSession, ManyCategoriesAndACaller]:
        return ManyCategoriesAndSomeone(besides=1)

    @override
    def when(self) -> When[ManyCategoriesAndACaller, Adapter, Searched]:
        return SearchingEverything()

    @override
    def then(self) -> Then[ManyCategoriesAndACaller, Searched]:
        return EveryLaidCategoryIsFound()


@dataclass(frozen=True)
class FilteringByNameKeepsThatOne(
    Scenario[SeedingSession, ManyCategoriesAndACaller, Adapter, Searched]
):
    @override
    def summary(self) -> str:
        return "filtering-by-name-keeps-only-the-category-of-that-name"

    @override
    def describe(self) -> str:
        return "이름이 다른 분류 셋이 있을 때 이름으로 걸러 훑으면, 그 이름의 것만 남는다"

    @override
    def given(self) -> Given[SeedingSession, ManyCategoriesAndACaller]:
        return ManyCategoriesAndSomeone(besides=2)

    @override
    def when(self) -> When[ManyCategoriesAndACaller, Adapter, Searched]:
        return SearchingByName()

    @override
    def then(self) -> Then[ManyCategoriesAndACaller, Searched]:
        return OnlyTheNamedOneIsFound()


@dataclass(frozen=True)
class OmittingThePageSizeAnswersTen(
    Scenario[SeedingSession, ManyCategoriesAndACaller, Adapter, Searched]
):
    @override
    def summary(self) -> str:
        return "omitting-the-page-size-answers-ten-and-says-there-is-a-next-page"

    @override
    def describe(self) -> str:
        return "분류 열하나가 있을 때 크기 없이 훑으면, 열 건까지 오고 다음 쪽이 있다고 답한다"

    @override
    def given(self) -> Given[SeedingSession, ManyCategoriesAndACaller]:
        return ManyCategoriesAndSomeone(besides=10)

    @override
    def when(self) -> When[ManyCategoriesAndACaller, Adapter, Searched]:
        return SearchingEverything()

    @override
    def then(self) -> Then[ManyCategoriesAndACaller, Searched]:
        return OnePageOfThemComesBack()


@dataclass(frozen=True)
class NobodyMayNotSearch(Scenario[SeedingSession, ACategoryAlone, Adapter, Searched]):
    @override
    def summary(self) -> str:
        return "a-call-carrying-no-user-may-not-search-categories"

    @override
    def describe(self) -> str:
        return "분류 하나가 있고 사용자 컨텍스트 없이 훑으면, 인증으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ACategoryAlone]:
        return ACategoryAndNobody()

    @override
    def when(self) -> When[ACategoryAlone, Adapter, Searched]:
        return SearchingAsNobody()

    @override
    def then(self) -> Then[ACategoryAlone, Searched]:
        return TheCallIsRefused(UserNotFound)


@pytest.mark.parametrize(
    "scenario",
    [AnyoneCountsEveryOne(), FilteringByNameKeepsThatOne(), OmittingThePageSizeAnswersTen()],
    ids=lambda s: s.summary(),
)
async def test_searching(
    scenario: SearchingStep, adapter: Adapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)


@pytest.mark.parametrize("scenario", [NobodyMayNotSearch()], ids=lambda s: s.summary())
async def test_searching_as_nobody(
    scenario: NobodyStep, adapter: Adapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
