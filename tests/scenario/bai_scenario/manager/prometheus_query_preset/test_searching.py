"""프리셋 검색 — 인증된 사용자 누구나, 이름과 카테고리 필터로."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.prometheus_query_preset import (
    APresetAlone,
    APresetAndNobody,
    EveryLaidPresetIsFound,
    ManyPresetsAndACaller,
    ManyPresetsAndSomeone,
    OnePageOfThemComesBack,
    PresetsInTwoCategories,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.prometheus_query_preset.request import (
    QueryDefinitionFilter,
    SearchQueryDefinitionsInput,
)
from ai.backend.common.dto.manager.v2.prometheus_query_preset.response import (
    SearchQueryDefinitionsPayload,
)
from ai.backend.manager.api.adapters.prometheus_query_preset.adapter import (
    PrometheusQueryPresetAdapter,
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

type Searched = SearchQueryDefinitionsPayload
type SearchingStep = Scenario[
    SeedingSession, ManyPresetsAndACaller, PrometheusQueryPresetAdapter, Searched
]
type NobodyStep = Scenario[SeedingSession, APresetAlone, PrometheusQueryPresetAdapter, Searched]


@dataclass(frozen=True)
class SearchingEverything(When[ManyPresetsAndACaller, PrometheusQueryPresetAdapter, Searched]):
    """필터도 크기도 없이 전체를 검색한다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return f"{laid.caller.username}이 필터 없이 전체 조회"

    @override
    async def call(
        self, adapter: PrometheusQueryPresetAdapter, laid: ManyPresetsAndACaller
    ) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search(SearchQueryDefinitionsInput())


@dataclass(frozen=True)
class SearchingByName(When[ManyPresetsAndACaller, PrometheusQueryPresetAdapter, Searched]):
    """미리 만들어 둔 프리셋 중 골라낸 하나의 이름을 필터로 검색한다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.named.name} 이름 필터로 조회"

    @override
    async def call(
        self, adapter: PrometheusQueryPresetAdapter, laid: ManyPresetsAndACaller
    ) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search(
                SearchQueryDefinitionsInput(
                    filter=QueryDefinitionFilter(name=StringFilter(equals=laid.named.name))
                )
            )


@dataclass(frozen=True)
class SearchingByCategory(When[ManyPresetsAndACaller, PrometheusQueryPresetAdapter, Searched]):
    """미리 만들어 둔 카테고리를 필터로 검색한다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return f"{laid.caller.username}이 카테고리 필터로 조회"

    @override
    async def call(
        self, adapter: PrometheusQueryPresetAdapter, laid: ManyPresetsAndACaller
    ) -> Searched:
        if laid.category is None:
            raise AssertionError("this row lays no category to filter by")
        with ActingAs(laid.caller):
            return await adapter.search(
                SearchQueryDefinitionsInput(
                    filter=QueryDefinitionFilter(
                        category_id=UUIDFilter(equals=laid.category.id),
                    )
                )
            )


@dataclass(frozen=True)
class SearchingAsNobody(When[APresetAlone, PrometheusQueryPresetAdapter, Searched]):
    """사용자 컨텍스트 없이 검색한다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: APresetAlone) -> str:
        return "사용자 컨텍스트 없이 전체 조회"

    @override
    async def call(self, adapter: PrometheusQueryPresetAdapter, laid: APresetAlone) -> Searched:
        return await adapter.search(SearchQueryDefinitionsInput())


@dataclass(frozen=True)
class OnlyTheNamedOneIsFound(Then[ManyPresetsAndACaller, Searched]):
    """골라낸 하나만 집계된다."""

    @override
    def says(self) -> str:
        return "이름 필터에 맞는 하나만 집계된다"

    @override
    def look(self, laid: ManyPresetsAndACaller, answered: Answered[Searched]) -> list[Verdict]:
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
class AnyoneCountsEveryOne(
    Scenario[SeedingSession, ManyPresetsAndACaller, PrometheusQueryPresetAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-counts-every-preset"

    @override
    def describe(self) -> str:
        return "프리셋 둘이 있고 아무 권한도 없는 사용자가 필터 없이 검색하면, 둘 다 집계된다"

    @override
    def given(self) -> Given[SeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(besides=1)

    @override
    def when(self) -> When[ManyPresetsAndACaller, PrometheusQueryPresetAdapter, Searched]:
        return SearchingEverything()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Searched]:
        return EveryLaidPresetIsFound()


@dataclass(frozen=True)
class FilteringByNameKeepsThatOne(
    Scenario[SeedingSession, ManyPresetsAndACaller, PrometheusQueryPresetAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "filtering-by-name-keeps-only-the-preset-of-that-name"

    @override
    def describe(self) -> str:
        return "이름이 다른 프리셋 셋이 있을 때 이름 필터로 검색하면, 그 이름의 프리셋만 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(besides=2)

    @override
    def when(self) -> When[ManyPresetsAndACaller, PrometheusQueryPresetAdapter, Searched]:
        return SearchingByName()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Searched]:
        return OnlyTheNamedOneIsFound()


@dataclass(frozen=True)
class FilteringByCategoryKeepsItsOwn(
    Scenario[SeedingSession, ManyPresetsAndACaller, PrometheusQueryPresetAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "filtering-by-category-keeps-only-the-presets-filed-under-it"

    @override
    def describe(self) -> str:
        return "두 카테고리에 프리셋이 나뉘어 있을 때 한 카테고리 필터로 검색하면, 그 카테고리의 프리셋만 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyPresetsAndACaller]:
        return PresetsInTwoCategories()

    @override
    def when(self) -> When[ManyPresetsAndACaller, PrometheusQueryPresetAdapter, Searched]:
        return SearchingByCategory()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Searched]:
        return EveryLaidPresetIsFound()


@dataclass(frozen=True)
class OmittingThePageSizeAnswersTen(
    Scenario[SeedingSession, ManyPresetsAndACaller, PrometheusQueryPresetAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "omitting-the-page-size-answers-ten-and-says-there-is-a-next-page"

    @override
    def describe(self) -> str:
        return "프리셋 11개가 있을 때 크기 없이 검색하면, 10건까지 반환되고 다음 페이지가 있다고 응답한다"

    @override
    def given(self) -> Given[SeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(besides=10)

    @override
    def when(self) -> When[ManyPresetsAndACaller, PrometheusQueryPresetAdapter, Searched]:
        return SearchingEverything()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Searched]:
        return OnePageOfThemComesBack()


@dataclass(frozen=True)
class NobodyMayNotSearch(
    Scenario[SeedingSession, APresetAlone, PrometheusQueryPresetAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-call-carrying-no-user-may-not-search-presets"

    @override
    def describe(self) -> str:
        return "프리셋 하나가 있고 사용자 컨텍스트 없이 검색하면, 인증 실패로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, APresetAlone]:
        return APresetAndNobody()

    @override
    def when(self) -> When[APresetAlone, PrometheusQueryPresetAdapter, Searched]:
        return SearchingAsNobody()

    @override
    def then(self) -> Then[APresetAlone, Searched]:
        return TheCallIsRefused(UserNotFound)


SCENARIOS: list[SearchingStep] = [
    AnyoneCountsEveryOne(),
    FilteringByNameKeepsThatOne(),
    FilteringByCategoryKeepsItsOwn(),
    OmittingThePageSizeAnswersTen(),
]

NOBODY_SCENARIOS: list[NobodyStep] = [NobodyMayNotSearch()]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: PrometheusQueryPresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)


@pytest.mark.parametrize("scenario", NOBODY_SCENARIOS, ids=lambda s: s.summary())
async def test_searching_as_nobody(
    scenario: NobodyStep, adapter: PrometheusQueryPresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
