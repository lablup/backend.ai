"""리소스 프리셋 검색 — 전체 검색은 superadmin 검사를 받는다, 이름 필터가 무엇을 좁히는가."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.resource_preset.request import (
    AdminSearchResourcePresetsInput,
    ResourcePresetFilter,
    ResourcePresetOrder,
)
from ai.backend.common.dto.manager.v2.resource_preset.types import (
    ResourcePresetOrderDirection,
    ResourcePresetOrderField,
)
from ai.backend.common.dto.manager.v2.resource_preset.response import (
    AdminSearchResourcePresetsPayload,
)
from ai.backend.manager.api.adapters.resource_preset.adapter import ResourcePresetAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Same,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.resource_preset import (
    ManyPresetsAndACaller,
    ManyPresetsAndAnUnrelatedOne,
    ManyPresetsAndSomeone,
    preset_verdicts,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Searched = AdminSearchResourcePresetsPayload

type SearchingStep = Scenario[
    TestSeedingSession, ManyPresetsAndACaller, ResourcePresetAdapter, Searched
]


def _shared_prefix(laid: ManyPresetsAndACaller) -> str:
    """The part of the seeded names every one of them starts with."""
    return laid.laid[0].name.rsplit("-", 1)[0]


@dataclass(frozen=True)
class SearchingEveryPreset(When[ManyPresetsAndACaller, ResourcePresetAdapter, Searched]):
    """필터도 크기도 없이 전체를 검색한다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 필터 없이 프리셋 전체를 조회합니다",
            english=f"{laid.caller.username} searches every preset without a filter",
        )

    @override
    async def call(self, adapter: ResourcePresetAdapter, laid: ManyPresetsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search(AdminSearchResourcePresetsInput())


@dataclass(frozen=True)
class SearchingByNameInOrderWithAPage(
    When[ManyPresetsAndACaller, ResourcePresetAdapter, Searched]
):
    """이름이 공유하는 접두사로 좁히고, 이름 내림차순으로 첫 페이지만 읽는다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        prefix = _shared_prefix(laid)
        return Says(
            f"{laid.caller.username}이 이름이 {prefix}로 시작하는 프리셋을 이름 내림차순으로 첫 "
            "페이지만 조회합니다",
            english=(
                f"{laid.caller.username} searches the first page of presets whose name starts with "
                f"{prefix}, in descending name order"
            ),
        )

    @override
    async def call(self, adapter: ResourcePresetAdapter, laid: ManyPresetsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search(
                AdminSearchResourcePresetsInput(
                    filter=ResourcePresetFilter(
                        name=StringFilter(starts_with=_shared_prefix(laid))
                    ),
                    order=[
                        ResourcePresetOrder(
                            field=ResourcePresetOrderField.NAME,
                            direction=ResourcePresetOrderDirection.DESC,
                        )
                    ],
                    limit=1,
                )
            )


@dataclass(frozen=True)
class TheFirstFilteredPageInOrder(Then[ManyPresetsAndACaller, Searched]):
    """필터를 통과한 프리셋이 이름 내림차순 첫 페이지로 온다. 나머지와 무관한 프리셋은 오지 않는다."""

    @override
    def says(self) -> str:
        return Says(
            "필터를 통과한 프리셋이 이름 내림차순 첫 페이지로 오고, 필터가 제외한 프리셋은 오지 "
            "않습니다",
            english=(
                "the presets that pass the filter come back as the first page in descending name "
                "order, and the preset the filter excludes does not"
            ),
        )

    @override
    def look(self, laid: ManyPresetsAndACaller, answered: Answered[Searched]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        highest = max(laid.laid, key=lambda one: one.name)
        seen: list[Verdict] = [
            Same("total_count", payload.total_count, len(laid.laid)),
            Same("len(items)", len(payload.items), 1),
            Same("has_next_page", payload.has_next_page, len(laid.laid) > 1),
            Same("has_previous_page", payload.has_previous_page, False),
        ]
        if payload.items:
            seen += preset_verdicts("items[0].", payload.items[0], highest)
        return seen


@dataclass(frozen=True)
class ANameFilterNarrows(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, ResourcePresetAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "filtering-and-ordering-preset-search-gives-its-first-page"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 이름이 공유하는 접두사로 프리셋을 좁혀 이름 내림차순 첫 페이지를 "
            "조회하면, 그 접두사를 가진 프리셋 중 첫 하나만 반환되고 접두사를 갖지 않는 프리셋은 "
            "반환되지 않습니다",
            english=(
                "when the superadmin narrows presets by their shared name prefix and asks for the "
                "first page in descending name order, only the first of the presets holding that "
                "prefix comes back, and the preset without it does not"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndAnUnrelatedOne()

    @override
    def when(self) -> When[ManyPresetsAndACaller, ResourcePresetAdapter, Searched]:
        return SearchingByNameInOrderWithAPage()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Searched]:
        return TheFirstFilteredPageInOrder()


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotSearch(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, ResourcePresetAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-presets"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 프리셋 전체를 조회하려 하면 역할이 없다는 것으로 "
            "거부됩니다",
            english=(
                "a user who is not the superadmin searching every preset is rejected for lacking "
                "the role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone()

    @override
    def when(self) -> When[ManyPresetsAndACaller, ResourcePresetAdapter, Searched]:
        return SearchingEveryPreset()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchingStep] = [
    ANameFilterNarrows(),
    AUserWhoIsNotTheSuperadminMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: ResourcePresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
