"""슬롯 종류 검색 — 각 필터가 무엇을 좁히고, 크기를 어떻게 지정하면 몇 건이 반환되는가."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    AdminSearchResourceSlotTypesInput,
    ResourceSlotTypeFilter,
)
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    AdminSearchResourceSlotTypesPayload,
)
from ai.backend.common.types import SlotTypes
from ai.backend.manager.api.adapters.resource_slot.adapter import ResourceSlotAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
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

DEFAULT_PAGE = 10

DISTINCT_DISPLAY = "눈에 띄는 슬롯"
"""표시 이름 필터로 골라낼 슬롯 종류에만 붙이는 표시 이름."""

type Searched = AdminSearchResourceSlotTypesPayload
type SearchingStep = Scenario[
    SeedingSession, ManySlotTypesAndACaller, ResourceSlotAdapter, Searched
]


@dataclass(frozen=True)
class SearchingEverySlotType(When[ManySlotTypesAndACaller, ResourceSlotAdapter, Searched]):
    """필터도 크기도 없이 전체를 검색한다."""

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
    """미리 만들어 둔 슬롯 종류 중 하나의 이름을 필터로 검색한다."""

    @override
    def operation(self) -> str:
        return "search_slot_types"

    @override
    def describe(self, laid: ManySlotTypesAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.named.slot_name} 이름 필터로 조회"

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
class SearchingByKind(When[ManySlotTypesAndACaller, ResourceSlotAdapter, Searched]):
    """미리 만들어 둔 슬롯 종류 중 하나의 종류를 필터로 검색한다."""

    @override
    def operation(self) -> str:
        return "search_slot_types"

    @override
    def describe(self, laid: ManySlotTypesAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.named.slot_type} 종류 필터로 조회"

    @override
    async def call(self, adapter: ResourceSlotAdapter, laid: ManySlotTypesAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search_slot_types(
                AdminSearchResourceSlotTypesInput(
                    filter=ResourceSlotTypeFilter(
                        slot_type=StringFilter(equals=laid.named.slot_type)
                    )
                )
            )


@dataclass(frozen=True)
class SearchingByDisplayName(When[ManySlotTypesAndACaller, ResourceSlotAdapter, Searched]):
    """미리 만들어 둔 슬롯 종류 중 하나의 표시 이름을 필터로 검색한다."""

    @override
    def operation(self) -> str:
        return "search_slot_types"

    @override
    def describe(self, laid: ManySlotTypesAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.named.display_name} 표시 이름 필터로 조회"

    @override
    async def call(self, adapter: ResourceSlotAdapter, laid: ManySlotTypesAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search_slot_types(
                AdminSearchResourceSlotTypesInput(
                    filter=ResourceSlotTypeFilter(
                        display_name=StringFilter(equals=laid.named.display_name)
                    )
                )
            )


@dataclass(frozen=True)
class SearchingTheFirst(When[ManySlotTypesAndACaller, ResourceSlotAdapter, Searched]):
    """앞에서 몇 건만 청한다. 크기가 아니라 커서 쪽의 개수다."""

    first: int

    @override
    def operation(self) -> str:
        return "search_slot_types"

    @override
    def describe(self, laid: ManySlotTypesAndACaller) -> str:
        return f"{laid.caller.username}이 앞에서 {self.first}건만 청해 조회"

    @override
    async def call(self, adapter: ResourceSlotAdapter, laid: ManySlotTypesAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search_slot_types(
                AdminSearchResourceSlotTypesInput(first=self.first)
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
        return "슬롯 종류 둘이 있을 때 아무 권한도 없는 사용자가 필터 없이 조회하면 둘 다 집계된다"

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
        return (
            "슬롯 종류 여럿 중 하나의 이름을 필터로 조회하면, 응답에는 그 이름의 슬롯 종류만 남는다"
        )

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
        return "슬롯 종류 11개가 있을 때 크기 없이 조회하면 10건까지 반환되고 다음 페이지가 있다고 응답한다"

    @override
    def given(self) -> Given[SeedingSession, ManySlotTypesAndACaller]:
        return ManySlotTypesAndSomeone(besides=DEFAULT_PAGE)

    @override
    def when(self) -> When[ManySlotTypesAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingEverySlotType()

    @override
    def then(self) -> Then[ManySlotTypesAndACaller, Searched]:
        return TheFirstPageOfSlotTypes(size=DEFAULT_PAGE)


@dataclass(frozen=True)
class AKindFilterNarrows(
    Scenario[SeedingSession, ManySlotTypesAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-kind-filter-narrows-the-answer-to-the-slot-types-of-that-kind"

    @override
    def describe(self) -> str:
        return (
            "종류가 다른 슬롯 종류 하나와 같은 종류 여럿이 있을 때 그 종류를 필터로 조회하면, "
            "응답에는 그 종류의 슬롯 종류만 남는다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManySlotTypesAndACaller]:
        return ManySlotTypesAndSomeone(besides=2, named_kind=SlotTypes.BYTES)

    @override
    def when(self) -> When[ManySlotTypesAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingByKind()

    @override
    def then(self) -> Then[ManySlotTypesAndACaller, Searched]:
        return OnlyTheNamedSlotTypeIsLeft()


@dataclass(frozen=True)
class ADisplayNameFilterNarrows(
    Scenario[SeedingSession, ManySlotTypesAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-display-name-filter-narrows-the-answer-to-the-slot-types-so-displayed"

    @override
    def describe(self) -> str:
        return (
            "표시 이름이 다른 슬롯 종류 하나와 같은 표시 이름 여럿이 있을 때 그 표시 이름을 필터로 조회하면, "
            "응답에는 그 표시 이름의 슬롯 종류만 남는다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManySlotTypesAndACaller]:
        return ManySlotTypesAndSomeone(besides=2, named_display_name=DISTINCT_DISPLAY)

    @override
    def when(self) -> When[ManySlotTypesAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingByDisplayName()

    @override
    def then(self) -> Then[ManySlotTypesAndACaller, Searched]:
        return OnlyTheNamedSlotTypeIsLeft()


@dataclass(frozen=True)
class AskingForTheFirstOneGivesOne(
    Scenario[SeedingSession, ManySlotTypesAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "asking-for-the-first-slot-type-answers-one-and-a-next-page"

    @override
    def describe(self) -> str:
        return "슬롯 종류 셋이 있을 때 앞에서 한 건만 청해 조회하면 한 건이 반환되고 다음 페이지가 있다고 응답한다"

    @override
    def given(self) -> Given[SeedingSession, ManySlotTypesAndACaller]:
        return ManySlotTypesAndSomeone(besides=2)

    @override
    def when(self) -> When[ManySlotTypesAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingTheFirst(first=1)

    @override
    def then(self) -> Then[ManySlotTypesAndACaller, Searched]:
        return TheFirstPageOfSlotTypes(size=1)


SCENARIOS: list[SearchingStep] = [
    AUserGrantedNothingCountsEverySlotType(),
    ANameFilterNarrows(),
    OmittingThePageSizeGivesTen(),
    AKindFilterNarrows(),
    ADisplayNameFilterNarrows(),
    AskingForTheFirstOneGivesOne(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: ResourceSlotAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
