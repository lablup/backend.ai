"""슬롯 이름으로 슬롯 종류의 id 찾기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.resource_slot import ResourceSlotTypeUUID
from ai.backend.manager.api.adapters.resource_slot.adapter import ResourceSlotAdapter
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    SameAs,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.resource_slot import ASlotTypeAndACaller, ASlotTypeAndSomeone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

UNKNOWN = "no-such-slot"

type LookingUpStep = Scenario[
    TestSeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeUUID
]


@dataclass(frozen=True)
class LookingUpByName(When[ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeUUID]):
    """이름으로 id를 찾는다. 이름을 지정하지 않으면 미리 만들어 둔 슬롯 종류의 이름을 쓴다."""

    named: str | None = None

    @override
    def operation(self) -> str:
        return "lookup_slot_type"

    @override
    def describe(self, laid: ASlotTypeAndACaller) -> str:
        return f"{laid.caller.username}이 {self.named or laid.slot_type.slot_name} 이름으로 id 찾기"

    @override
    async def call(
        self, adapter: ResourceSlotAdapter, laid: ASlotTypeAndACaller
    ) -> ResourceSlotTypeUUID:
        with ActingAs(laid.caller):
            return await adapter.lookup_slot_type(self.named or laid.slot_type.slot_name)


@dataclass(frozen=True)
class TheSlotTypeId(Then[ASlotTypeAndACaller, ResourceSlotTypeUUID]):
    """미리 만들어 둔 슬롯 종류의 id."""

    @override
    def says(self) -> str:
        return "미리 만들어 둔 슬롯 종류의 id가 반환된다"

    @override
    def look(
        self, laid: ASlotTypeAndACaller, answered: Answered[ResourceSlotTypeUUID]
    ) -> list[Verdict]:
        found = answered.response
        if found is None:
            return [MissingResponse(answered.raised)]
        return [
            Held[UUID](
                "id", found, SameAs(laid.slot_type.entity_id(), "미리 만들어 둔 슬롯 종류의 id")
            )
        ]


@dataclass(frozen=True)
class AUserGrantedNothingLooksUpByName(
    Scenario[TestSeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeUUID]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-looks-up-a-slot-type-by-name"

    @override
    def describe(self) -> str:
        return "아무 권한도 없는 사용자가 이름으로 id를 찾으면 그 슬롯 종류의 id가 반환된다"

    @override
    def given(self) -> Given[TestSeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAndSomeone()

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeUUID]:
        return LookingUpByName()

    @override
    def then(self) -> Then[ASlotTypeAndACaller, ResourceSlotTypeUUID]:
        return TheSlotTypeId()


@dataclass(frozen=True)
class ANameNothingAnswersToIsRefused(
    Scenario[TestSeedingSession, ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeUUID]
):
    @override
    def summary(self) -> str:
        return "looking-up-a-slot-name-nothing-answers-to-is-refused"

    @override
    def describe(self) -> str:
        return "존재하지 않는 이름으로 id를 찾으면 잘못된 요청으로 거부된다"

    @override
    def given(self) -> Given[TestSeedingSession, ASlotTypeAndACaller]:
        return ASlotTypeAndSomeone()

    @override
    def when(self) -> When[ASlotTypeAndACaller, ResourceSlotAdapter, ResourceSlotTypeUUID]:
        return LookingUpByName(named=UNKNOWN)

    @override
    def then(self) -> Then[ASlotTypeAndACaller, ResourceSlotTypeUUID]:
        return TheCallIsRefused(GenericBadRequest)


SCENARIOS: list[LookingUpStep] = [
    AUserGrantedNothingLooksUpByName(),
    ANameNothingAnswersToIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_looking_up(
    scenario: LookingUpStep, adapter: ResourceSlotAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
