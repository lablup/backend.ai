"""프리셋 검색 — 변형·버전 필터와 기본 페이지 크기에 따른 결과를 검증한다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

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

DEFAULT_PAGE = 10

type Searched = SearchRuntimeVariantPresetsPayload
type SearchingStep = Scenario[
    SeedingSession, ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Searched
]


@dataclass(frozen=True)
class SearchingEveryPreset(When[ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Searched]):
    """필터와 페이지 크기를 지정하지 않고 전체를 검색한다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return f"{laid.caller.username}이 필터 없이 전체를 조회"

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
        return f"{laid.caller.username}이 변형 필터로 조회 — 대상: {laid.variant.name}"

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
    """한 런타임 버전에 유효한 프리셋만 필터로 검색한다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return f"{laid.caller.username}이 버전 {VALID_AT}에 유효한 프리셋만 조회"

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
        return "프리셋이 둘 있을 때 아무 권한도 없는 사용자가 필터 없이 조회하면 두 프리셋이 모두 반환된다"

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
        return "프리셋이 두 변형에 나뉘어 있을 때 한 변형을 필터로 조회하면 해당 변형의 프리셋만 반환된다"

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
            "추가 버전과 폐기 버전이 서로 다른 프리셋을 버전 필터로 조회하면 추가 버전 이상이고 "
            "폐기 버전 미만인 프리셋만 반환된다. 값이 비어 있는 쪽에는 제한이 없다"
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
        return "프리셋이 11개 있을 때 페이지 크기를 생략하면 10건을 반환하고 다음 페이지가 있음을 표시한다"

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
