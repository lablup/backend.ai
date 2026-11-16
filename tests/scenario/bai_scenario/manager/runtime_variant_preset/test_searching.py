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
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
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
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

DEFAULT_PAGE = 10

type Searched = SearchRuntimeVariantPresetsPayload
type SearchingStep = Scenario[
    TestSeedingSession, ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Searched
]


@dataclass(frozen=True)
class SearchingEveryPreset(When[ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Searched]):
    """필터와 페이지 크기를 지정하지 않고 전체를 검색한다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 필터 없이 전체를 조회합니다",
            english=f"{laid.caller.username} reads everything with no filter",
        )

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
        return Says(
            f"{laid.caller.username}이 인퍼런스 런타임 종류 필터로 조회: 대상: {laid.variant.name}",
            english=(
                f"{laid.caller.username} reads with the runtime variant filter: target: "
                f"{laid.variant.name}"
            ),
        )

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
        return Says(
            f"{laid.caller.username}이 버전 {VALID_AT}에 유효한 런타임 파라미터만 조회합니다",
            english=(f"{laid.caller.username} reads only the presets valid at version {VALID_AT}"),
        )

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
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-counts-every-preset-laid"

    @override
    def describe(self) -> str:
        return Says(
            "런타임 파라미터가 둘 있을 때 아무 권한도 없는 사용자가 필터 없이 조회하면 두 런타임 "
            "파라미터가 모두 반환됩니다",
            english=(
                "when two presets exist and a user granted nothing reads with no filter, both "
                "presets come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(besides=1)

    @override
    def when(self) -> When[ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Searched]:
        return SearchingEveryPreset()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Searched]:
        return TheLaidPresetsAreLeft()


@dataclass(frozen=True)
class AVariantFilterNarrows(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-variant-filter-narrows-the-answer-to-that-variants-presets"

    @override
    def describe(self) -> str:
        return Says(
            "런타임 파라미터가 두 인퍼런스 런타임 종류에 나뉘어 있을 때 한 인퍼런스 런타임 종류를 "
            "필터로 조회하면 해당 인퍼런스 런타임 종류의 런타임 파라미터만 반환됩니다",
            english=(
                "when presets are split across two runtime variants and one runtime variant is "
                "named in the filter, only the presets of that runtime variant come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return PresetsInTwoVariants()

    @override
    def when(self) -> When[ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Searched]:
        return SearchingByVariant()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Searched]:
        return TheLaidPresetsAreLeft()


@dataclass(frozen=True)
class AVersionFilterKeepsWhatIsValidThen(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-version-filter-keeps-only-the-presets-valid-at-that-version"

    @override
    def describe(self) -> str:
        return Says(
            "추가 버전과 폐기 버전이 서로 다른 런타임 파라미터를 버전 필터로 조회하면 추가 버전 "
            "이상이고 폐기 버전 미만인 런타임 파라미터만 반환됩니다. 값이 비어 있는 쪽에는 제한이 "
            "없습니다",
            english=(
                "when presets with different added and deprecated versions are read with a "
                "version filter, only the presets at or above the added version and below the "
                "deprecated version come back. An empty side places no limit"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return PresetsAcrossVersions()

    @override
    def when(self) -> When[ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Searched]:
        return SearchingValidAtAVersion()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Searched]:
        return TheLaidPresetsAreLeft()


@dataclass(frozen=True)
class OmittingThePageSizeGivesTen(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "omitting-the-page-size-answers-ten-presets-and-a-next-page"

    @override
    def describe(self) -> str:
        return Says(
            "런타임 파라미터가 11개 있을 때 페이지 크기를 생략하면 10건을 반환하고 다음 페이지가 "
            "있음을 표시합니다",
            english=(
                "when eleven presets exist and the page size is omitted, ten come back and the "
                "response marks that there is a next page"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(besides=DEFAULT_PAGE)

    @override
    def when(self) -> When[ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Searched]:
        return SearchingEveryPreset()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Searched]:
        return TheFirstPageOfPresets(size=DEFAULT_PAGE)


@dataclass(frozen=True)
class AUserWithoutReadPermissionIsRefused(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-without-read-permission-is-refused-on-search"

    @override
    def describe(self) -> str:
        return Says(
            "public 에서 런타임 파라미터 조회 권한이 없는 사용자가 검색하면 검색 전체가 거부됩니다",
            english=(
                "when a user without read permission on presets in public searches, the whole "
                "search is refused"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(reading_in_public=False)

    @override
    def when(self) -> When[ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Searched]:
        return SearchingEveryPreset()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[SearchingStep] = [
    AUserGrantedNothingCountsEveryPreset(),
    AVariantFilterNarrows(),
    AVersionFilterKeepsWhatIsValidThen(),
    OmittingThePageSizeGivesTen(),
    AUserWithoutReadPermissionIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: RuntimeVariantPresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
