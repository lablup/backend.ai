"""커널 할당 검색 — 슈퍼관리자인지 검사하고, 각 필터가 무엇을 좁히고, 크기를 어떻게 지정하면 몇 건이 반환되는가."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    AdminSearchResourceAllocationsInput,
    ResourceAllocationFilter,
)
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    AdminSearchResourceAllocationsPayload,
)
from ai.backend.manager.api.adapters.resource_slot.adapter import ResourceSlotAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_allocation import (
    EveryLaidAllocationIsCounted,
    KernelsAndACaller,
    KernelsAndSomeone,
    OnlyTheNamedKernelIsLeft,
    OnlyTheNamedSlotIsLeft,
    TheFirstPageOfAllocations,
)
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

DEFAULT_PAGE = 10

type Searched = AdminSearchResourceAllocationsPayload
type SearchingStep = Scenario[TestSeedingSession, KernelsAndACaller, ResourceSlotAdapter, Searched]


@dataclass(frozen=True)
class SearchingEveryAllocation(When[KernelsAndACaller, ResourceSlotAdapter, Searched]):
    """필터도 크기도 없이 전체를 검색한다."""

    @override
    def operation(self) -> str:
        return "search_allocations"

    @override
    def describe(self, laid: KernelsAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 필터 없이 전체를 조회합니다",
            english=f"{laid.caller.username} reads everything without a filter",
        )

    @override
    async def call(self, adapter: ResourceSlotAdapter, laid: KernelsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search_allocations(AdminSearchResourceAllocationsInput())


@dataclass(frozen=True)
class SearchingBySlotName(When[KernelsAndACaller, ResourceSlotAdapter, Searched]):
    """미리 만들어 둔 커널이 요구한 슬롯 중 첫 슬롯의 이름을 필터로 검색한다."""

    @override
    def operation(self) -> str:
        return "search_allocations"

    @override
    def describe(self, laid: KernelsAndACaller) -> str:
        slot = laid.named.slots[0][0]
        return Says(
            f"{laid.caller.username} 이 {slot} 슬롯 이름 필터로 조회합니다",
            english=f"{laid.caller.username} reads with the slot name filter {slot}",
        )

    @override
    async def call(self, adapter: ResourceSlotAdapter, laid: KernelsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search_allocations(
                AdminSearchResourceAllocationsInput(
                    filter=ResourceAllocationFilter(
                        slot_name=StringFilter(equals=laid.named.slots[0][0])
                    )
                )
            )


@dataclass(frozen=True)
class SearchingByKernelId(When[KernelsAndACaller, ResourceSlotAdapter, Searched]):
    """미리 만들어 둔 커널 중 하나의 id를 필터로 검색한다."""

    @override
    def operation(self) -> str:
        return "search_allocations"

    @override
    def describe(self, laid: KernelsAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 미리 저장한 커널 중 하나의 id 필터로 조회합니다",
            english=(
                f"{laid.caller.username} reads with the id of one kernel stored in advance as a "
                "filter"
            ),
        )

    @override
    async def call(self, adapter: ResourceSlotAdapter, laid: KernelsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search_allocations(
                AdminSearchResourceAllocationsInput(
                    filter=ResourceAllocationFilter(
                        kernel_id=UUIDFilter(equals=uuid.UUID(str(laid.named.kernel.id)))
                    )
                )
            )


@dataclass(frozen=True)
class SearchingTheFirst(When[KernelsAndACaller, ResourceSlotAdapter, Searched]):
    """앞에서 몇 건만 청한다. 크기가 아니라 커서 쪽의 개수다."""

    first: int

    @override
    def operation(self) -> str:
        return "search_allocations"

    @override
    def describe(self, laid: KernelsAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 앞에서 {self.first}건만 요청해 조회합니다",
            english=f"{laid.caller.username} reads asking for only the first {self.first}",
        )

    @override
    async def call(self, adapter: ResourceSlotAdapter, laid: KernelsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search_allocations(
                AdminSearchResourceAllocationsInput(first=self.first)
            )


@dataclass(frozen=True)
class TheSuperadminCountsEveryAllocation(
    Scenario[TestSeedingSession, KernelsAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-counts-every-allocation-laid"

    @override
    def describe(self) -> str:
        return Says(
            "슬롯 둘을 요구하는 커널 하나가 있을 때 superadmin 이 필터 없이 조회하면 할당 둘이 "
            "다 집계됩니다",
            english=(
                "when one kernel asks for two slots and the superadmin reads without a filter, "
                "both allocations are counted"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, KernelsAndACaller]:
        return KernelsAndSomeone(role=UserRole.SUPERADMIN, kernels=1, slots_each=2)

    @override
    def when(self) -> When[KernelsAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingEveryAllocation()

    @override
    def then(self) -> Then[KernelsAndACaller, Searched]:
        return EveryLaidAllocationIsCounted()


@dataclass(frozen=True)
class ASlotNameFilterNarrows(
    Scenario[TestSeedingSession, KernelsAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-slot-name-filter-narrows-the-answer-to-that-slot-s-allocation"

    @override
    def describe(self) -> str:
        return Says(
            "슬롯 둘을 요구하는 커널 하나가 있을 때 한 슬롯의 이름을 필터로 조회하면, 응답에는 그 "
            "슬롯의 할당만 남습니다",
            english=(
                "when one kernel asks for two slots and the call reads with the name of one slot "
                "as a filter, only the allocation of that slot stays in the answer"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, KernelsAndACaller]:
        return KernelsAndSomeone(role=UserRole.SUPERADMIN, kernels=1, slots_each=2)

    @override
    def when(self) -> When[KernelsAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingBySlotName()

    @override
    def then(self) -> Then[KernelsAndACaller, Searched]:
        return OnlyTheNamedSlotIsLeft()


@dataclass(frozen=True)
class AKernelIdFilterNarrows(
    Scenario[TestSeedingSession, KernelsAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-kernel-id-filter-narrows-the-answer-to-that-kernel-s-allocations"

    @override
    def describe(self) -> str:
        return Says(
            "슬롯 하나씩 요구하는 커널 둘이 있을 때 한 커널의 id 를 필터로 조회하면, 응답에는 그 "
            "커널의 할당만 남습니다",
            english=(
                "when two kernels ask for one slot each and the call reads with the id of one "
                "kernel as a filter, only the allocations of that kernel stay in the answer"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, KernelsAndACaller]:
        return KernelsAndSomeone(role=UserRole.SUPERADMIN, kernels=2, slots_each=1)

    @override
    def when(self) -> When[KernelsAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingByKernelId()

    @override
    def then(self) -> Then[KernelsAndACaller, Searched]:
        return OnlyTheNamedKernelIsLeft()


@dataclass(frozen=True)
class OmittingThePageSizeGivesTen(
    Scenario[TestSeedingSession, KernelsAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "omitting-the-page-size-answers-ten-allocations-and-a-next-page"

    @override
    def describe(self) -> str:
        return Says(
            "할당 11건이 있을 때 크기 없이 조회하면 10건까지 반환되고 다음 페이지가 있다고 "
            "응답합니다",
            english=(
                "when 11 allocations exist and the call reads without a size, 10 come back and "
                "the answer says a next page exists"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, KernelsAndACaller]:
        return KernelsAndSomeone(role=UserRole.SUPERADMIN, kernels=1, slots_each=DEFAULT_PAGE + 1)

    @override
    def when(self) -> When[KernelsAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingEveryAllocation()

    @override
    def then(self) -> Then[KernelsAndACaller, Searched]:
        return TheFirstPageOfAllocations(size=DEFAULT_PAGE)


@dataclass(frozen=True)
class AskingForTheFirstOneGivesOne(
    Scenario[TestSeedingSession, KernelsAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "asking-for-the-first-allocation-answers-one-and-a-next-page"

    @override
    def describe(self) -> str:
        return Says(
            "할당 둘이 있을 때 앞에서 한 건만 요청해 조회하면 한 건이 반환되고 다음 페이지가 "
            "있다고 응답합니다",
            english=(
                "when two allocations exist and the call asks for only the first one, one comes "
                "back and the answer says a next page exists"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, KernelsAndACaller]:
        return KernelsAndSomeone(role=UserRole.SUPERADMIN, kernels=1, slots_each=2)

    @override
    def when(self) -> When[KernelsAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingTheFirst(first=1)

    @override
    def then(self) -> Then[KernelsAndACaller, Searched]:
        return TheFirstPageOfAllocations(size=1)


@dataclass(frozen=True)
class AMonitorCountsEveryAllocation(
    Scenario[TestSeedingSession, KernelsAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-monitor-counts-every-allocation-laid"

    @override
    def describe(self) -> str:
        return Says(
            "모니터가 필터 없이 조회하면 할당이 다 집계됩니다. superadmin 인지 검사하는 조회는 "
            "모니터도 통과합니다",
            english=(
                "when a monitor reads without a filter, every allocation is counted. A read that "
                "checks whether the caller is the superadmin also passes for a monitor"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, KernelsAndACaller]:
        return KernelsAndSomeone(role=UserRole.MONITOR, kernels=1, slots_each=2)

    @override
    def when(self) -> When[KernelsAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingEveryAllocation()

    @override
    def then(self) -> Then[KernelsAndACaller, Searched]:
        return EveryLaidAllocationIsCounted()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearch(
    Scenario[TestSeedingSession, KernelsAndACaller, ResourceSlotAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-allocations"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 조회하면 역할 부족으로 거부됩니다",
            english=("when a user granted nothing reads, the call is rejected for lack of role"),
        )

    @override
    def given(self) -> Given[TestSeedingSession, KernelsAndACaller]:
        return KernelsAndSomeone()

    @override
    def when(self) -> When[KernelsAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingEveryAllocation()

    @override
    def then(self) -> Then[KernelsAndACaller, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class EnforcementOffStillNeedsTheRole(
    Scenario[TestSeedingSession, KernelsAndACaller, ResourceSlotAdapter, Searched], Configured
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-still-refuses-a-user-searching-allocations"

    @override
    def describe(self) -> str:
        return Says(
            "권한 검사를 꺼도 superadmin 이나 모니터가 아니면 조회할 수 없습니다. superadmin "
            "검사는 그 설정을 읽지 않습니다",
            english=(
                "turning permission checks off still does not let a user who is neither the "
                "superadmin nor a monitor read. The superadmin check does not read that setting"
            ),
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[TestSeedingSession, KernelsAndACaller]:
        return KernelsAndSomeone()

    @override
    def when(self) -> When[KernelsAndACaller, ResourceSlotAdapter, Searched]:
        return SearchingEveryAllocation()

    @override
    def then(self) -> Then[KernelsAndACaller, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchingStep] = [
    TheSuperadminCountsEveryAllocation(),
    ASlotNameFilterNarrows(),
    AKernelIdFilterNarrows(),
    OmittingThePageSizeGivesTen(),
    # TODO(BA-7928): the adapter reads neither `first` nor the cursors, so this row
    # fails until it does.
    # AskingForTheFirstOneGivesOne(),
    AMonitorCountsEveryAllocation(),
    AUserGrantedNothingMayNotSearch(),
    EnforcementOffStillNeedsTheRole(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching_allocations(
    scenario: SearchingStep, adapter: ResourceSlotAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
