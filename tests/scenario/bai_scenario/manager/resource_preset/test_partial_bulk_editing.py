"""리소스 프리셋 여럿 수정하기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import (
    BinarySizeInput,
    PartialBulkPayload,
    ResourceSlotEntryInput,
)
from ai.backend.common.dto.manager.v2.resource_preset.request import (
    PartialBulkUpdateResourcePresetItemInput,
    PartialBulkUpdateResourcePresetsInput,
)
from ai.backend.common.dto.manager.v2.resource_preset.response import ResourcePresetNode
from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.types import BinarySize
from ai.backend.manager.api.adapters.resource_preset.adapter import ResourcePresetAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_preset import (
    EveryPresetComesBack,
    ManyPresetsAndACaller,
    ManyPresetsAndSomeone,
    NoPresetIsProcessed,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

SHARED_MEMORY = 1073741824

type Edited = PartialBulkPayload[ResourcePresetNode]
type EditingStep = Scenario[
    TestSeedingSession, ManyPresetsAndACaller, ResourcePresetAdapter, Edited
]


@dataclass(frozen=True)
class EditingEveryTarget(When[ManyPresetsAndACaller, ResourcePresetAdapter, Edited]):
    """대상 프리셋들의 공유 메모리를 한 번에 바꾼다. `slotless`면 첫째의 자원을 필수 슬롯 없이 바꾼다."""

    slotless: bool = False

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        if self.slotless:
            return (
                f"{laid.caller.username}이 프리셋 {len(laid.laid)}개를 한 번에 고치며 "
                "첫째의 자원을 필수 슬롯 없이 바꿈"
            )
        return f"{laid.caller.username}이 프리셋 {len(laid.laid)}개의 공유 메모리를 한 번에 바꿈"

    @override
    async def call(self, adapter: ResourcePresetAdapter, laid: ManyPresetsAndACaller) -> Edited:
        items = [
            PartialBulkUpdateResourcePresetItemInput(
                id=preset.id, shared_memory=BinarySizeInput(expr=str(SHARED_MEMORY))
            )
            for preset in laid.laid
        ]
        if self.slotless:
            items[0] = PartialBulkUpdateResourcePresetItemInput(
                id=laid.laid[0].id,
                resource_slots=[ResourceSlotEntryInput(resource_type="cpu", quantity="1")],
            )
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_update(
                PartialBulkUpdateResourcePresetsInput(items=items)
            )


@dataclass(frozen=True)
class TheSuperadminEditsSeveralPresets(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, ResourcePresetAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-edits-several-presets-at-once"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 프리셋 여럿의 공유 메모리를 한 번에 바꾸면, 모두 새 공유 메모리로 "
            "오고 실패한 것은 없다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyPresetsAndACaller, ResourcePresetAdapter, Edited]:
        return EditingEveryTarget()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Edited]:
        return EveryPresetComesBack(shared_memory=BinarySize.to_size_info(SHARED_MEMORY))


@dataclass(frozen=True)
class AUserGrantedNothingEditsNone(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, ResourcePresetAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-edits-none-of-several-presets"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 프리셋 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone()

    @override
    def when(self) -> When[ManyPresetsAndACaller, ResourcePresetAdapter, Edited]:
        return EditingEveryTarget()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Edited]:
        return NoPresetIsProcessed(reason="Insufficient permission")


@dataclass(frozen=True)
class SlotsWithoutTheIntrinsicOnesAreRefused(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, ResourcePresetAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "editing-several-with-slots-missing-intrinsic-ones-is-refused"

    @override
    def describe(self) -> str:
        return (
            "프리셋 여럿을 고치며 하나의 자원을 필수 슬롯 없이 바꾸면, 요청 전체가 입력 "
            "오류로 거부된다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyPresetsAndACaller, ResourcePresetAdapter, Edited]:
        return EditingEveryTarget(slotless=True)

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Edited]:
        return TheCallIsRefused(InvalidAPIParameters)


SCENARIOS: list[EditingStep] = [
    TheSuperadminEditsSeveralPresets(),
    AUserGrantedNothingEditsNone(),
    SlotsWithoutTheIntrinsicOnesAreRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_editing(
    scenario: EditingStep, adapter: ResourcePresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
