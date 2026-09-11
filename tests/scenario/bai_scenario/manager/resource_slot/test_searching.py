"""슬롯 종류 훑기 — 이름 필터가 무엇을 좁히고, 크기를 대지 않으면 몇 건이 오는가."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest
from bai_scenario.components.resource_slot import (
    EveryLaidSlotTypeIsCounted,
    ManySlotTypesAndACaller,
    ManySlotTypesAndSomeone,
    OnlyTheNamedSlotTypeIsLeft,
    TheFirstPageOfSlotTypes,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    AdminSearchResourceSlotTypesInput,
    ResourceSlotTypeFilter,
)
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    AdminSearchResourceSlotTypesPayload,
)
from ai.backend.manager.api.adapters.resource_slot.adapter import ResourceSlotAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

DEFAULT_PAGE = 10

type Searched = AdminSearchResourceSlotTypesPayload
type SearchingStep = Scenario[
    SeedingSession, ManySlotTypesAndACaller, ResourceSlotAdapter, Searched
]


@dataclass(frozen=True)
class SearchingEverySlotType(When[ManySlotTypesAndACaller, ResourceSlotAdapter, Searched]):
    """필터도 크기도 없이 전체를 훑는다."""

    @override
    def operation(self) -> str:
        return "search_slot_types"

    @override
    def describe(self, laid: ManySlotTypesAndACaller) -> str:
        return f"{laid.caller.username}이 필터 없이 전체 조회"

    @override
    async def call(self, adapter: ResourceSlotAdapter, laid: ManySlotTypesAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search_slot_types(AdminSearchResourceSlotTypesInput())


@dataclass(frozen=True)
class SearchingByName(When[ManySlotTypesAndACaller, ResourceSlotAdapter, Searched]):
    """심은 것 중 하나의 이름으로 걸러 훑는다."""

    @override
    def operation(self) -> str:
        return "search_slot_types"

    @override
    def describe(self, laid: ManySlotTypesAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.named.slot_name}으로 걸러 조회"

    @override
    async def call(self, adapter: ResourceSlotAdapter, laid: ManySlotTypesAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search_slot_types(
                AdminSearchResourceSlotTypesInput(
                    filter=ResourceSlotTypeFilter(
                        slot_name=StringFilter(equals=laid.named.slot_name)
                    )
                )
            )


@dataclass(frozen=True)
class AUserGrantedNothingCountsEverySlotType(
    Scenario[SeedingSession, ManySlotTypesAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-counts-every-slot-type-laid"

    @override
    def describe(self) -> str:
        return "슬롯 종류 둘이 있을 때 아무 권한도 받지 않은 사용자가 필터 없이 조회하면 둘을 모두 센다"

    @override
    def given(self) -> Given[SeedingSession, ManySlotTypesAndACaller]:
        return ManySlotTypesAndSomeone(besides=1)

    @override
    def when(self) -> When[ManySlotTypesAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingEverySlotType()

    @override
    def then(self) -> Then[ManySlotTypesAndACaller, Searched]:
        return EveryLaidSlotTypeIsCounted()


@dataclass(frozen=True)
class ANameFilterNarrows(
    Scenario[SeedingSession, ManySlotTypesAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-name-filter-narrows-the-answer-to-the-slot-type-it-names"

    @override
    def describe(self) -> str:
        return "슬롯 종류 여럿 중 하나의 이름으로 걸러 조회하면, 답에는 그 이름의 것만 남는다"

    @override
    def given(self) -> Given[SeedingSession, ManySlotTypesAndACaller]:
        return ManySlotTypesAndSomeone(besides=2)

    @override
    def when(self) -> When[ManySlotTypesAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingByName()

    @override
    def then(self) -> Then[ManySlotTypesAndACaller, Searched]:
        return OnlyTheNamedSlotTypeIsLeft()


@dataclass(frozen=True)
class OmittingThePageSizeGivesTen(
    Scenario[SeedingSession, ManySlotTypesAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "omitting-the-page-size-answers-ten-slot-types-and-a-next-page"

    @override
    def describe(self) -> str:
        return (
            "슬롯 종류 열하나가 있을 때 크기 없이 조회하면 열 건까지 오고 다음 쪽이 있다고 답한다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManySlotTypesAndACaller]:
        return ManySlotTypesAndSomeone(besides=DEFAULT_PAGE)

    @override
    def when(self) -> When[ManySlotTypesAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingEverySlotType()

    @override
    def then(self) -> Then[ManySlotTypesAndACaller, Searched]:
        return TheFirstPageOfSlotTypes(size=DEFAULT_PAGE)


SCENARIOS: list[SearchingStep] = [
    AUserGrantedNothingCountsEverySlotType(),
    ANameFilterNarrows(),
    OmittingThePageSizeGivesTen(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: ResourceSlotAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
