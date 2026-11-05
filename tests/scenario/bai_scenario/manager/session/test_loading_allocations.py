"""세션과 커널의 자원 할당을 id 로 일괄 조회."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.entity.kernel import KernelID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.dto.manager.v2.kernel.response import ResourceAllocationGQLDTO
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.resource_allocation import Granted
from bai_scenario.components.session_reads import (
    ASessionWithAKernelAndSomeone,
    LaidSessionAndCaller,
    allocation_dump,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type BySession = list[ResourceAllocationGQLDTO | Exception]
type ByKernel = list[ResourceAllocationGQLDTO]


@dataclass(frozen=True)
class LoadingTheSessionAllocation(When[LaidSessionAndCaller, SessionAdapter, BySession]):
    @override
    def operation(self) -> str:
        return "batch_resource_allocation_by_session"

    @override
    def describe(self, laid: LaidSessionAndCaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.session.name} 세션의 자원 할당을 id 로 일괄 "
            "조회합니다",
            english=(
                f"{laid.caller.username} loads the resource allocation of the session "
                f"{laid.session.name} by id"
            ),
        )

    @override
    async def call(self, adapter: SessionAdapter, laid: LaidSessionAndCaller) -> BySession:
        with ActingAs(laid.caller):
            return await adapter.batch_resource_allocation_by_session([
                SessionID(laid.session.id)
            ])


@dataclass(frozen=True)
class LoadingTheKernelAllocation(When[LaidSessionAndCaller, SessionAdapter, ByKernel]):
    @override
    def operation(self) -> str:
        return "batch_resource_allocation_by_kernel"

    @override
    def describe(self, laid: LaidSessionAndCaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.session.name} 세션 커널의 자원 할당을 id 로 일괄 "
            "조회합니다",
            english=(
                f"{laid.caller.username} loads the resource allocation of the kernel of "
                f"{laid.session.name} by id"
            ),
        )

    @override
    async def call(self, adapter: SessionAdapter, laid: LaidSessionAndCaller) -> ByKernel:
        with ActingAs(laid.caller):
            return await adapter.batch_resource_allocation_by_kernel([
                KernelID(laid.kernel.id)
            ])


@dataclass(frozen=True)
class TheSessionAllocation(Then[LaidSessionAndCaller, BySession]):
    @override
    def says(self) -> str:
        return Says(
            "그 세션의 자원 할당이 요청한 양만큼 한 항목으로 반환됩니다",
            english=(
                "the resource allocation of the session comes back as one entry holding what "
                "it asked for"
            ),
        )

    @override
    def look(self, laid: LaidSessionAndCaller, answered: Answered[BySession]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        first = loaded[0] if loaded else None
        if not isinstance(first, ResourceAllocationGQLDTO):
            return [Same("length", len(loaded), 1), Same("[0]", type(first).__name__, "a node")]
        return [
            Same("length", len(loaded), 1),
            Held(
                "[0]",
                first.model_dump(),
                SameAs(
                    allocation_dump(laid.slot_name, laid.quantity),
                    Says("저장된 자원 할당", english="the stored resource allocation"),
                ),
            ),
        ]


@dataclass(frozen=True)
class TheKernelAllocation(Then[LaidSessionAndCaller, ByKernel]):
    @override
    def says(self) -> str:
        return Says(
            "그 커널의 자원 할당이 요청한 양만큼 한 항목으로 반환됩니다",
            english=(
                "the resource allocation of the kernel comes back as one entry holding what "
                "it asked for"
            ),
        )

    @override
    def look(self, laid: LaidSessionAndCaller, answered: Answered[ByKernel]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        return [
            Same("length", len(loaded), 1),
            Held(
                "[0]",
                loaded[0].model_dump(),
                SameAs(
                    allocation_dump(laid.slot_name, laid.quantity),
                    Says("저장된 자원 할당", english="the stored resource allocation"),
                ),
            ),
        ]


@dataclass(frozen=True)
class TheEntryIsRefused(Then[Any, list[Any]]):
    @override
    def says(self) -> str:
        return Says(
            "그 항목은 권한 부족으로 거부됩니다",
            english="that entry is rejected for lack of permission",
        )

    @override
    def look(self, laid: Any, answered: Answered[list[Any]]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        entry = loaded[0] if loaded else None
        return [
            Same("length", len(loaded), 1),
            Refused(NotEnoughPermission, entry if isinstance(entry, Exception) else None),
        ]


@dataclass(frozen=True)
class LoadingTheSessionAllocationRow(
    Scenario[TestSeedingSession, LaidSessionAndCaller, SessionAdapter, BySession]
):
    granted: Granted = Granted.THE_PROJECT

    @override
    def summary(self) -> str:
        return f"a-session-allocation-is-batch-loaded-{self.granted.value}"

    @override
    def describe(self) -> str:
        if self.granted is Granted.NOTHING:
            return Says(
                "아무 권한도 받지 않은 사용자가 세션의 자원 할당을 일괄 조회하면, 호출은 "
                "성공하되 그 항목은 권한 부족으로 거부됩니다",
                english=(
                    "when a user granted nothing loads the resource allocation of a session, "
                    "the call succeeds but that entry is rejected for lack of permission"
                ),
            )
        return Says(
            "그 프로젝트에서 세션 읽기 권한을 받은 사용자가 세션의 자원 할당을 일괄 조회하면, "
            "요청한 양만큼의 할당이 반환됩니다",
            english=(
                "when a user granted session read in the project loads the resource allocation "
                "of a session, the allocation it asked for comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, LaidSessionAndCaller]:
        return ASessionWithAKernelAndSomeone(granted=self.granted)

    @override
    def when(self) -> When[LaidSessionAndCaller, SessionAdapter, BySession]:
        return LoadingTheSessionAllocation()

    @override
    def then(self) -> Then[LaidSessionAndCaller, BySession]:
        if self.granted is Granted.NOTHING:
            return TheEntryIsRefused()
        return TheSessionAllocation()


@dataclass(frozen=True)
class LoadingTheKernelAllocationRow(
    Scenario[TestSeedingSession, LaidSessionAndCaller, SessionAdapter, ByKernel]
):
    granted: Granted = Granted.THE_PROJECT

    @override
    def summary(self) -> str:
        return f"a-kernel-allocation-is-batch-loaded-{self.granted.value}"

    @override
    def describe(self) -> str:
        if self.granted is Granted.NOTHING:
            return Says(
                "아무 권한도 받지 않은 사용자가 커널의 자원 할당을 일괄 조회하면, 권한 부족으로 "
                "거부됩니다",
                english=(
                    "when a user granted nothing loads the resource allocation of a kernel, the "
                    "call is rejected for lack of permission"
                ),
            )
        return Says(
            "그 프로젝트에서 세션 읽기 권한을 받은 사용자가 커널의 자원 할당을 일괄 조회하면, "
            "요청한 양만큼의 할당이 반환됩니다",
            english=(
                "when a user granted session read in the project loads the resource allocation "
                "of a kernel, the allocation it asked for comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, LaidSessionAndCaller]:
        return ASessionWithAKernelAndSomeone(granted=self.granted)

    @override
    def when(self) -> When[LaidSessionAndCaller, SessionAdapter, ByKernel]:
        return LoadingTheKernelAllocation()

    @override
    def then(self) -> Then[LaidSessionAndCaller, ByKernel]:
        if self.granted is Granted.NOTHING:
            return TheCallIsRefused(NotEnoughPermission)
        return TheKernelAllocation()


SCENARIOS: list[Scenario[Any, Any, Any, Any]] = [
    LoadingTheSessionAllocationRow(granted=Granted.THE_PROJECT),
    LoadingTheSessionAllocationRow(granted=Granted.NOTHING),
    LoadingTheKernelAllocationRow(granted=Granted.THE_PROJECT),
    LoadingTheKernelAllocationRow(granted=Granted.NOTHING),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_loading_allocations(
    scenario: Scenario[Any, Any, Any, Any],
    adapter: SessionAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)