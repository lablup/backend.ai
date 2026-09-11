"""런타임 변형 검색 — 필터가 무엇을 좁히고, 크기를 지정하지 않으면 몇 건이 반환되는가."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest
from bai_scenario.components.runtime_variant import (
    EveryLaidVariantIsCounted,
    ManyVariantsAndACaller,
    ManyVariantsAndSomeone,
    OnlyTheNamedVariantIsLeft,
    TheFirstPageOfVariants,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.runtime_variant.request import (
    RuntimeVariantFilter,
    SearchRuntimeVariantsInput,
)
from ai.backend.common.dto.manager.v2.runtime_variant.response import SearchRuntimeVariantsPayload
from ai.backend.manager.api.adapters.runtime_variant.adapter import RuntimeVariantAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

DEFAULT_PAGE = 10

type Searched = SearchRuntimeVariantsPayload
type SearchingStep = Scenario[
    SeedingSession, ManyVariantsAndACaller, RuntimeVariantAdapter, Searched
]


@dataclass(frozen=True)
class SearchingEveryVariant(When[ManyVariantsAndACaller, RuntimeVariantAdapter, Searched]):
    """필터도 크기도 없이 전체를 검색한다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyVariantsAndACaller) -> str:
        return f"{laid.caller.username}이 필터 없이 전체 조회"

    @override
    async def call(self, adapter: RuntimeVariantAdapter, laid: ManyVariantsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search(SearchRuntimeVariantsInput())


@dataclass(frozen=True)
class SearchingByName(When[ManyVariantsAndACaller, RuntimeVariantAdapter, Searched]):
    """미리 만들어 둔 변형 중 하나의 이름을 필터로 검색한다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyVariantsAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.named.name} 이름 필터로 조회"

    @override
    async def call(self, adapter: RuntimeVariantAdapter, laid: ManyVariantsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search(
                SearchRuntimeVariantsInput(
                    filter=RuntimeVariantFilter(name=StringFilter(equals=laid.named.name))
                )
            )


@dataclass(frozen=True)
class AUserGrantedNothingCountsEveryVariant(
    Scenario[SeedingSession, ManyVariantsAndACaller, RuntimeVariantAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-counts-every-variant-laid"

    @override
    def describe(self) -> str:
        return "변형 둘이 있을 때 아무 권한도 없는 사용자가 필터 없이 조회하면 둘 다 집계된다"

    @override
    def given(self) -> Given[SeedingSession, ManyVariantsAndACaller]:
        return ManyVariantsAndSomeone(besides=1)

    @override
    def when(self) -> When[ManyVariantsAndACaller, RuntimeVariantAdapter, Searched]:
        return SearchingEveryVariant()

    @override
    def then(self) -> Then[ManyVariantsAndACaller, Searched]:
        return EveryLaidVariantIsCounted()


@dataclass(frozen=True)
class ANameFilterNarrows(
    Scenario[SeedingSession, ManyVariantsAndACaller, RuntimeVariantAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-name-filter-narrows-the-answer-to-the-variant-it-names"

    @override
    def describe(self) -> str:
        return "변형 여럿 중 하나의 이름을 필터로 조회하면, 응답에는 그 이름의 변형만 남는다"

    @override
    def given(self) -> Given[SeedingSession, ManyVariantsAndACaller]:
        return ManyVariantsAndSomeone(besides=2)

    @override
    def when(self) -> When[ManyVariantsAndACaller, RuntimeVariantAdapter, Searched]:
        return SearchingByName()

    @override
    def then(self) -> Then[ManyVariantsAndACaller, Searched]:
        return OnlyTheNamedVariantIsLeft()


@dataclass(frozen=True)
class OmittingThePageSizeGivesTen(
    Scenario[SeedingSession, ManyVariantsAndACaller, RuntimeVariantAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "omitting-the-page-size-answers-ten-variants-and-a-next-page"

    @override
    def describe(self) -> str:
        return (
            "변형 11개가 있을 때 크기 없이 조회하면 10건까지 반환되고 다음 페이지가 있다고 응답한다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyVariantsAndACaller]:
        return ManyVariantsAndSomeone(besides=DEFAULT_PAGE)

    @override
    def when(self) -> When[ManyVariantsAndACaller, RuntimeVariantAdapter, Searched]:
        return SearchingEveryVariant()

    @override
    def then(self) -> Then[ManyVariantsAndACaller, Searched]:
        return TheFirstPageOfVariants(size=DEFAULT_PAGE)


SCENARIOS: list[SearchingStep] = [
    AUserGrantedNothingCountsEveryVariant(),
    ANameFilterNarrows(),
    OmittingThePageSizeGivesTen(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: RuntimeVariantAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
