"""preset 검색 — 변형과 버전 필터가 무엇을 좁히고, 크기를 지정하지 않으면 몇 건이 반환되는가."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest
from bai_scenario.components.runtime_variant_preset import (
    VALID_AT,
    ManyPresetsAndACaller,
    ManyPresetsAndSomeone,
    PresetsAcrossVersions,
    PresetsInTwoVariants,
    TheFirstPageOfPresets,
    TheLaidPresetsAreLeft,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.dto.manager.query import UUIDFilter
from ai.backend.common.dto.manager.v2.runtime_variant_preset.request import (
    RuntimeVariantPresetFilter,
    SearchRuntimeVariantPresetsInput,
)
from ai.backend.common.dto.manager.v2.runtime_variant_preset.response import (
    SearchRuntimeVariantPresetsPayload,
)
from ai.backend.manager.api.adapters.runtime_variant_preset.adapter import (
    RuntimeVariantPresetAdapter,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

DEFAULT_PAGE = 10

type Searched = SearchRuntimeVariantPresetsPayload
type SearchingStep = Scenario[
    SeedingSession, ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Searched
]


@dataclass(frozen=True)
class SearchingEveryPreset(When[ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Searched]):
    """필터도 크기도 없이 전체를 검색한다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return f"{laid.caller.username}이 필터 없이 전체 조회"

    @override
    async def call(
        self, adapter: RuntimeVariantPresetAdapter, laid: ManyPresetsAndACaller
    ) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search(SearchRuntimeVariantPresetsInput())


@dataclass(frozen=True)
class SearchingByVariant(When[ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Searched]):
    """미리 만들어 둔 변형을 필터로 검색한다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return f"{laid.caller.username}이 변형 {laid.variant.name} 필터로 조회"

    @override
    async def call(
        self, adapter: RuntimeVariantPresetAdapter, laid: ManyPresetsAndACaller
    ) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search(
                SearchRuntimeVariantPresetsInput(
                    filter=RuntimeVariantPresetFilter(
                        runtime_variant_id=UUIDFilter(equals=laid.variant.id)
                    )
                )
            )


@dataclass(frozen=True)
class SearchingValidAtAVersion(When[ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Searched]):
    """한 런타임 버전에 유효한 preset만 필터로 검색한다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return f"{laid.caller.username}이 버전 {VALID_AT}에 유효한 preset만 조회"

    @override
    async def call(
        self, adapter: RuntimeVariantPresetAdapter, laid: ManyPresetsAndACaller
    ) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search(
                SearchRuntimeVariantPresetsInput(
                    filter=RuntimeVariantPresetFilter(runtime_version=VALID_AT)
                )
            )


@dataclass(frozen=True)
class AUserGrantedNothingCountsEveryPreset(
    Scenario[SeedingSession, ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-counts-every-preset-laid"

    @override
    def describe(self) -> str:
        return "preset 둘이 있을 때 아무 권한도 없는 사용자가 필터 없이 조회하면 둘 다 집계된다"

    @override
    def given(self) -> Given[SeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(besides=1)

    @override
    def when(self) -> When[ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Searched]:
        return SearchingEveryPreset()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Searched]:
        return TheLaidPresetsAreLeft()


@dataclass(frozen=True)
class AVariantFilterNarrows(
    Scenario[SeedingSession, ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-variant-filter-narrows-the-answer-to-that-variants-presets"

    @override
    def describe(self) -> str:
        return "두 변형에 preset이 나뉘어 있을 때 한 변형을 필터로 조회하면, 그 변형의 preset만 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ManyPresetsAndACaller]:
        return PresetsInTwoVariants()

    @override
    def when(self) -> When[ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Searched]:
        return SearchingByVariant()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Searched]:
        return TheLaidPresetsAreLeft()


@dataclass(frozen=True)
class AVersionFilterKeepsWhatIsValidThen(
    Scenario[SeedingSession, ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-version-filter-keeps-only-the-presets-valid-at-that-version"

    @override
    def describe(self) -> str:
        return (
            "추가 버전과 폐기 버전이 다른 preset들을 한 버전 필터로 조회하면, 추가 버전 이상이고 "
            "폐기 버전 미만인 preset만 반환된다. 비어 있는 쪽은 제한이 없다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyPresetsAndACaller]:
        return PresetsAcrossVersions()

    @override
    def when(self) -> When[ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Searched]:
        return SearchingValidAtAVersion()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Searched]:
        return TheLaidPresetsAreLeft()


@dataclass(frozen=True)
class OmittingThePageSizeGivesTen(
    Scenario[SeedingSession, ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "omitting-the-page-size-answers-ten-presets-and-a-next-page"

    @override
    def describe(self) -> str:
        return "preset 11개가 있을 때 크기 없이 조회하면 10건까지 반환되고 다음 페이지가 있다고 응답한다"

    @override
    def given(self) -> Given[SeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(besides=DEFAULT_PAGE)

    @override
    def when(self) -> When[ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Searched]:
        return SearchingEveryPreset()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Searched]:
        return TheFirstPageOfPresets(size=DEFAULT_PAGE)


SCENARIOS: list[SearchingStep] = [
    AUserGrantedNothingCountsEveryPreset(),
    AVariantFilterNarrows(),
    AVersionFilterKeepsWhatIsValidThen(),
    OmittingThePageSizeGivesTen(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: RuntimeVariantPresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
