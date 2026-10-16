"""슬롯 종류 여럿 삭제."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    PartialBulkPurgeResourceSlotTypesInput,
)
from ai.backend.common.dto.manager.v2.resource_slot.response import ResourceSlotTypeNode
from ai.backend.common.dto.manager.v2.resource_slot.types import NumberFormatInfo
from ai.backend.common.types import SlotTypes
from ai.backend.manager.api.adapters.resource_slot.adapter import ResourceSlotAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    SameAs,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.domain import Mentions
from bai_scenario.components.resource_slot import (
    ManySlotTypesAndACaller,
    ManySlotTypesAndSomeone,
    slot_type_verdicts,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

MISSING = UUID("00000000-0000-0000-0000-0000000000ff")

type Purged = PartialBulkPayload[ResourceSlotTypeNode]
type PurgingStep = Scenario[
    TestSeedingSession, ManySlotTypesAndACaller, ResourceSlotAdapter, Purged
]


@dataclass(frozen=True)
class PurgingEverySlotType(When[ManySlotTypesAndACaller, ResourceSlotAdapter, Purged]):
    """미리 만들어 둔 슬롯 종류들을 한 번에 삭제한다. `missing`이 있으면 그 id 도 함께 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "partial_bulk_purge_slot_types"

    @override
    def describe(self, laid: ManySlotTypesAndACaller) -> str:
        besides = " 와 없는 id 하나" if self.missing is not None else ""
        return f"{laid.caller.username}이 슬롯 종류 {len(laid.laid)}개{besides}를 한 번에 삭제함"

    @override
    async def call(self, adapter: ResourceSlotAdapter, laid: ManySlotTypesAndACaller) -> Purged:
        ids: list[UUID] = [slot_type.entity_id() for slot_type in laid.laid]
        if self.missing is not None:
            ids.append(self.missing)
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_purge_slot_types(
                PartialBulkPurgeResourceSlotTypesInput(ids=ids)
            )


@dataclass(frozen=True)
class EverySlotTypeIsPurged(Then[ManySlotTypesAndACaller, Purged]):
    """슬롯 종류가 모두 지워지기 전 모습으로 처리된 목록에 오고, `missing`만 실패 목록에 온다."""

    missing: UUID

    @override
    def says(self) -> str:
        return (
            "미리 만들어 둔 슬롯 종류가 모두 지워지기 전 모습으로 오고, 없는 id 는 대상이 없다는 "
            "이유로 실패 목록에 온다"
        )

    @override
    def look(self, laid: ManySlotTypesAndACaller, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        verdicts: list[Verdict] = [Same("successes count", len(payload.successes), len(laid.laid))]
        for i, (node, seed) in enumerate(zip(payload.successes, laid.laid, strict=False)):
            verdicts += slot_type_verdicts(
                node,
                at=f"successes[{i}].",
                named=seed.slot_name,
                slot_type=SlotTypes(seed.slot_type),
                required=seed.required,
                enabled=seed.enabled,
                display_name=seed.display_name,
                description=seed.description,
                display_unit=seed.display_unit,
                display_icon=seed.display_icon,
                number_format=NumberFormatInfo(
                    binary=seed.number_format.binary,
                    round_length=seed.number_format.round_length,
                ),
                rank=seed.rank,
            )
        verdicts.append(Same("failed count", len(payload.failed), 1))
        for failure in payload.failed:
            verdicts += [
                Held[UUID]("failed[0].id", failure.id, SameAs(self.missing, "요청에 넣은 없는 id")),
                Held("failed[0].message", failure.message, Mentions("not found")),
            ]
        return verdicts


@dataclass(frozen=True)
class NoSlotTypeIsPurged(Then[ManySlotTypesAndACaller, Purged]):
    """처리된 슬롯 종류 없이, 대상이 모두 같은 이유로 실패 목록에 온다."""

    reason: str

    @override
    def says(self) -> str:
        return "처리된 슬롯 종류 없이 대상이 모두 실패 목록에 온다"

    @override
    def look(self, laid: ManySlotTypesAndACaller, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes", payload.successes, []),
            Same("failed count", len(payload.failed), len(laid.laid)),
        ]
        for i, (failure, seed) in enumerate(zip(payload.failed, laid.laid, strict=False)):
            verdicts += [
                Held[UUID](
                    f"failed[{i}].id",
                    failure.id,
                    SameAs(seed.entity_id(), "미리 만들어 둔 슬롯 종류의 id"),
                ),
                Held(f"failed[{i}].message", failure.message, Mentions(self.reason)),
            ]
        return verdicts


@dataclass(frozen=True)
class TheSuperadminPurgesSeveralAndHearsOfTheMissingOne(
    Scenario[TestSeedingSession, ManySlotTypesAndACaller, ResourceSlotAdapter, Purged]
):
    missing: UUID = MISSING

    @override
    def summary(self) -> str:
        return "purging-several-slot-types-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return (
            "아무것도 참조하지 않는 슬롯 종류 둘과 없는 id 하나를 슈퍼관리자가 한 번에 삭제하면, "
            "둘은 지워지기 전 모습으로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManySlotTypesAndACaller]:
        return ManySlotTypesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManySlotTypesAndACaller, ResourceSlotAdapter, Purged]:
        return PurgingEverySlotType(missing=self.missing)

    @override
    def then(self) -> Then[ManySlotTypesAndACaller, Purged]:
        return EverySlotTypeIsPurged(missing=self.missing)


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNone(
    Scenario[TestSeedingSession, ManySlotTypesAndACaller, ResourceSlotAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purges-none-of-several-slot-types"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 슬롯 종류 여럿을 한 번에 삭제하려 하면, 지워진 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManySlotTypesAndACaller]:
        return ManySlotTypesAndSomeone()

    @override
    def when(self) -> When[ManySlotTypesAndACaller, ResourceSlotAdapter, Purged]:
        return PurgingEverySlotType()

    @override
    def then(self) -> Then[ManySlotTypesAndACaller, Purged]:
        return NoSlotTypeIsPurged(reason="Insufficient permission")


SCENARIOS: list[PurgingStep] = [
    TheSuperadminPurgesSeveralAndHearsOfTheMissingOne(),
    AUserGrantedNothingPurgesNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_purging(
    scenario: PurgingStep, adapter: ResourceSlotAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
