"""슬롯 종류 조회 — 이름을 풀어낸 뒤 조회한다. 어느 단계도 인증만 확인한다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_slot import (
    ASlotTypeAndACaller,
    ASlotTypeAndSomeone,
    TheSlotTypeNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.dto.manager.v2.resource_slot.response import ResourceSlotTypeNode
from ai.backend.manager.api.adapters.resource_slot.adapter import ResourceSlotAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

UNKNOWN = "no-such-slot"

type ReadingStep = Scenario[
    SeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode
]


@dataclass(frozen=True)
class ReadingByName(When[ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]):
    """이름으로 조회한다. 이름을 지정하지 않으면 미리 만들어 둔 슬롯 종류의 이름을 쓴다."""

    named: str | None = None

    @override
    def operation(self) -> str:
        return "get_slot_type"

    @override
    def describe(self, laid: ASlotTypeAndACaller) -> str:
        return f"{laid.caller.username}이 {self.named or laid.slot_type.slot_name} 이름으로 조회"

    @override
    async def call(
        self, adapter: ResourceSlotAdapter, laid: ASlotTypeAndACaller
    ) -> ResourceSlotTypeNode:
        with ActingAs(laid.caller):
            return await adapter.get_slot_type(self.named or laid.slot_type.slot_name)


@dataclass(frozen=True)
class AUserGrantedNothingReadsByName(
    Scenario[SeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-reads-a-slot-type-by-name"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 이름으로 조회하면 그 슬롯 종류 전체가 반환된다. "
            "이름을 풀어내는 단계도 그 뒤의 조회도 인증만 확인한다"
        )

    @override
    def given(self) -> Given[SeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAndSomeone()

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]:
        return ReadingByName()

    @override
    def then(self) -> Then[ASlotTypeAndACaller, ResourceSlotTypeNode]:
        return TheSlotTypeNode()


@dataclass(frozen=True)
class ANameNothingAnswersToIsNotFound(
    Scenario[SeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]
):
    @override
    def summary(self) -> str:
        return "reading-a-slot-name-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "존재하지 않는 이름으로 조회하면 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAndSomeone()

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeNode]:
        return ReadingByName(named=UNKNOWN)

    @override
    def then(self) -> Then[ASlotTypeAndACaller, ResourceSlotTypeNode]:
        return TheCallIsRefused(EntityNotFoundError)


SCENARIOS: list[ReadingStep] = [
    AUserGrantedNothingReadsByName(),
    ANameNothingAnswersToIsNotFound(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep, adapter: ResourceSlotAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
