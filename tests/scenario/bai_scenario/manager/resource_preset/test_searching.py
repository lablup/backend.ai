"""리소스 프리셋 검색 — 전체 검색은 superadmin 검사를 받는다, 이름 필터가 무엇을 좁히는가."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.resource_preset.request import (
    AdminSearchResourcePresetsInput,
    ResourcePresetFilter,
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
class SearchingByName(When[ManyPresetsAndACaller, ResourcePresetAdapter, Searched]):
    """미리 만들어 둔 첫 프리셋의 이름으로 좁힌다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 이름 {laid.laid[0].name}으로 프리셋을 조회합니다",
            english=f"{laid.caller.username} searches presets with the name {laid.laid[0].name}",
        )

    @override
    async def call(self, adapter: ResourcePresetAdapter, laid: ManyPresetsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search(
                AdminSearchResourcePresetsInput(
                    filter=ResourcePresetFilter(name=StringFilter(equals=laid.laid[0].name))
                )
            )


@dataclass(frozen=True)
class EveryPresetIsCounted(Then[ManyPresetsAndACaller, Searched]):
    """미리 저장한 프리셋이 모두 오고, 그밖의 것은 오지 않는다."""

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 프리셋이 모두 응답으로 오고, 그밖의 것은 오지 않습니다",
            english="every preset seeded in advance comes back, and only those",
        )

    @override
    def look(self, laid: ManyPresetsAndACaller, answered: Answered[Searched]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        seen: list[Verdict] = [
            Same("total_count", payload.total_count, len(laid.laid)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
            Same("len(items)", len(payload.items), len(laid.laid)),
        ]
        by_name = {node.name: node for node in payload.items}
        for i, preset in enumerate(sorted(laid.laid, key=lambda one: one.name)):
            node = by_name.get(preset.name)
            if node is None:
                seen.append(Same(f"items[{i}].name", None, preset.name))
                continue
            seen += preset_verdicts(f"items[{i}].", node, preset)
        return seen


@dataclass(frozen=True)
class OnlyTheNamedPresetIsLeft(Then[ManyPresetsAndACaller, Searched]):
    """필터가 지목한 이름의 프리셋만 온다."""

    @override
    def says(self) -> str:
        return Says(
            "필터가 지목한 이름의 프리셋만 응답으로 옵니다",
            english="only the preset the filter names comes back",
        )

    @override
    def look(self, laid: ManyPresetsAndACaller, answered: Answered[Searched]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        seen: list[Verdict] = [
            Same("total_count", payload.total_count, 1),
            Same("len(items)", len(payload.items), 1),
        ]
        if payload.items:
            seen += preset_verdicts("items[0].", payload.items[0], laid.laid[0])
        return seen


@dataclass(frozen=True)
class TheSuperadminFindsEveryPreset(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, ResourcePresetAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-finds-every-preset"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋 여럿이 있고 superadmin 이 필터 없이 조회하면, 미리 저장한 프리셋이 모두 "
            "반환됩니다",
            english=(
                "when several presets exist and the superadmin searches without a filter, every "
                "preset seeded in advance comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyPresetsAndACaller, ResourcePresetAdapter, Searched]:
        return SearchingEveryPreset()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Searched]:
        return EveryPresetIsCounted()


@dataclass(frozen=True)
class ANameFilterNarrows(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, ResourcePresetAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "filtering-preset-search-by-name-leaves-that-one"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 프리셋 하나의 이름으로 조회하면, 그 이름의 프리셋만 반환됩니다",
            english=(
                "when the superadmin searches with the name of one preset, only that preset "
                "comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyPresetsAndACaller, ResourcePresetAdapter, Searched]:
        return SearchingByName()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Searched]:
        return OnlyTheNamedPresetIsLeft()


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
    TheSuperadminFindsEveryPreset(),
    ANameFilterNarrows(),
    AUserWhoIsNotTheSuperadminMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: ResourcePresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
