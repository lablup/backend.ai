"""커널 할당 조회 — 커널 id를 세션으로 풀어내면서 그 세션에 대한 권한을 검사하고, 통과하면 조회한다.

풀어내는 단계는 권한이 없을 때와 커널이 없을 때 같은 답을 한다. 슈퍼관리자에게만 없다는 사실을
그대로 답한다.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_slot.response import ResourceAllocationNode
from ai.backend.manager.api.adapters.resource_slot.adapter import ResourceSlotAdapter
from ai.backend.manager.errors.base.field import FieldNotFoundError
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.errors.resource_slot import ResourceAllocationNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_allocation import (
    AKernelAndACaller,
    AKernelAndSomeone,
    Granted,
    TheAllocationNode,
)
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

UNKNOWN_KERNEL = uuid.UUID(int=0)
UNKNOWN_SLOT = "no-such-slot"

type ReadingStep = Scenario[
    SeedingSession, AKernelAndACaller, ResourceSlotAdapter, ResourceAllocationNode
]


@dataclass(frozen=True)
class ReadingAKernelSlot(When[AKernelAndACaller, ResourceSlotAdapter, ResourceAllocationNode]):
    """커널 id와 슬롯 이름으로 조회한다. 지정하지 않으면 미리 만들어 둔 커널과 그 첫 슬롯을 쓴다."""

    unknown_kernel: bool = False
    slot: str | None = None

    def _slot(self, laid: AKernelAndACaller) -> str:
        return self.slot or laid.kernel.slots[0][0]

    @override
    def operation(self) -> str:
        return "get_kernel_allocation"

    @override
    def describe(self, laid: AKernelAndACaller) -> str:
        kernel = "존재하지 않는 커널 id" if self.unknown_kernel else "미리 만들어 둔 커널의 id"
        return f"{laid.caller.username}이 {kernel}와 {self._slot(laid)} 슬롯 이름으로 조회"

    @override
    async def call(
        self, adapter: ResourceSlotAdapter, laid: AKernelAndACaller
    ) -> ResourceAllocationNode:
        kernel_id = UNKNOWN_KERNEL if self.unknown_kernel else uuid.UUID(str(laid.kernel.kernel.id))
        with ActingAs(laid.caller):
            return await adapter.get_kernel_allocation(kernel_id, self._slot(laid))


@dataclass(frozen=True)
class TheSuperadminReadsAKernelSlot(
    Scenario[SeedingSession, AKernelAndACaller, ResourceSlotAdapter, ResourceAllocationNode]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reads-a-kernel-slot-allocation"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 커널 id와 슬롯 이름으로 조회하면 그 할당 전체가 반환된다. "
            "커널은 아직 스케줄링되지 않았으므로 요구한 양만 있고 실제 사용량은 없다"
        )

    @override
    def given(self) -> Given[SeedingSession, AKernelAndACaller]:
        return AKernelAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AKernelAndACaller, ResourceSlotAdapter, ResourceAllocationNode]:
        return ReadingAKernelSlot()

    @override
    def then(self) -> Then[AKernelAndACaller, ResourceAllocationNode]:
        return TheAllocationNode()


@dataclass(frozen=True)
class AUserReadingSessionsInTheProjectReadsAKernelSlot(
    Scenario[SeedingSession, AKernelAndACaller, ResourceSlotAdapter, ResourceAllocationNode]
):
    @override
    def summary(self) -> str:
        return "a-user-reading-sessions-in-the-project-reads-a-kernel-slot-allocation"

    @override
    def describe(self) -> str:
        return (
            "프로젝트 범위에서 세션을 읽을 수 있는 사용자가 조회하면 그 할당 전체가 반환된다. "
            "할당은 커널이 속한 세션의 것이므로, 세션에 대한 권한이 할당을 읽게 한다"
        )

    @override
    def given(self) -> Given[SeedingSession, AKernelAndACaller]:
        return AKernelAndSomeone(granted=Granted.THE_PROJECT)

    @override
    def when(self) -> When[AKernelAndACaller, ResourceSlotAdapter, ResourceAllocationNode]:
        return ReadingAKernelSlot()

    @override
    def then(self) -> Then[AKernelAndACaller, ResourceAllocationNode]:
        return TheAllocationNode()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadAKernelSlot(
    Scenario[SeedingSession, AKernelAndACaller, ResourceSlotAdapter, ResourceAllocationNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-a-kernel-slot-allocation"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 조회하면 커널 id를 풀어낼 수 없다는 이유로 거부된다. "
            "커널 id를 세션으로 풀어내는 단계가 그 세션에 대한 권한을 검사하고, "
            "권한이 없을 때와 커널이 없을 때 같은 답을 한다"
        )

    @override
    def given(self) -> Given[SeedingSession, AKernelAndACaller]:
        return AKernelAndSomeone()

    @override
    def when(self) -> When[AKernelAndACaller, ResourceSlotAdapter, ResourceAllocationNode]:
        return ReadingAKernelSlot()

    @override
    def then(self) -> Then[AKernelAndACaller, ResourceAllocationNode]:
        return TheCallIsRefused(GenericBadRequest)


@dataclass(frozen=True)
class AKernelIdNothingAnswersToIsNotFound(
    Scenario[SeedingSession, AKernelAndACaller, ResourceSlotAdapter, ResourceAllocationNode]
):
    @override
    def summary(self) -> str:
        return "reading-a-kernel-id-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 존재하지 않는 커널 id로 조회하면 대상을 찾을 수 없다는 이유로 거부된다. "
            "모든 검사를 통과하는 슈퍼관리자에게는 없다는 사실을 그대로 답한다"
        )

    @override
    def given(self) -> Given[SeedingSession, AKernelAndACaller]:
        return AKernelAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AKernelAndACaller, ResourceSlotAdapter, ResourceAllocationNode]:
        return ReadingAKernelSlot(unknown_kernel=True)

    @override
    def then(self) -> Then[AKernelAndACaller, ResourceAllocationNode]:
        return TheCallIsRefused(FieldNotFoundError)


@dataclass(frozen=True)
class ASlotTheKernelDidNotAskForIsNotFound(
    Scenario[SeedingSession, AKernelAndACaller, ResourceSlotAdapter, ResourceAllocationNode]
):
    @override
    def summary(self) -> str:
        return "reading-a-slot-the-kernel-did-not-ask-for-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 그 커널이 요구하지 않은 슬롯 이름으로 조회하면 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AKernelAndACaller]:
        return AKernelAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AKernelAndACaller, ResourceSlotAdapter, ResourceAllocationNode]:
        return ReadingAKernelSlot(slot=UNKNOWN_SLOT)

    @override
    def then(self) -> Then[AKernelAndACaller, ResourceAllocationNode]:
        return TheCallIsRefused(ResourceAllocationNotFound)


@dataclass(frozen=True)
class AUserGrantedNothingReadingAnUnknownKernelIsRefusedTheSameWay(
    Scenario[SeedingSession, AKernelAndACaller, ResourceSlotAdapter, ResourceAllocationNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-reading-an-unknown-kernel-id-is-refused-the-same-way"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 존재하지 않는 커널 id로 조회해도 커널 id를 풀어낼 수 없다는 "
            "같은 이유로 거부된다. 답으로는 그 커널이 있는지 알 수 없다"
        )

    @override
    def given(self) -> Given[SeedingSession, AKernelAndACaller]:
        return AKernelAndSomeone()

    @override
    def when(self) -> When[AKernelAndACaller, ResourceSlotAdapter, ResourceAllocationNode]:
        return ReadingAKernelSlot(unknown_kernel=True)

    @override
    def then(self) -> Then[AKernelAndACaller, ResourceAllocationNode]:
        return TheCallIsRefused(GenericBadRequest)


@dataclass(frozen=True)
class EnforcementOffLetsAnyoneReadAKernelSlot(
    Scenario[SeedingSession, AKernelAndACaller, ResourceSlotAdapter, ResourceAllocationNode],
    Configured,
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-read-a-kernel-slot-allocation"

    @override
    def describe(self) -> str:
        return "권한 검사를 끄면 아무 권한도 없는 사용자도 할당을 조회할 수 있다"

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, AKernelAndACaller]:
        return AKernelAndSomeone()

    @override
    def when(self) -> When[AKernelAndACaller, ResourceSlotAdapter, ResourceAllocationNode]:
        return ReadingAKernelSlot()

    @override
    def then(self) -> Then[AKernelAndACaller, ResourceAllocationNode]:
        return TheAllocationNode()


SCENARIOS: list[ReadingStep] = [
    TheSuperadminReadsAKernelSlot(),
    AUserReadingSessionsInTheProjectReadsAKernelSlot(),
    AUserGrantedNothingMayNotReadAKernelSlot(),
    AKernelIdNothingAnswersToIsNotFound(),
    ASlotTheKernelDidNotAskForIsNotFound(),
    AUserGrantedNothingReadingAnUnknownKernelIsRefusedTheSameWay(),
    EnforcementOffLetsAnyoneReadAKernelSlot(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading_allocations(
    scenario: ReadingStep, adapter: ResourceSlotAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
