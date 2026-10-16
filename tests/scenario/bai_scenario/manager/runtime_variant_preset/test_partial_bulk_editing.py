"""프리셋 여럿 수정하기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.runtime_variant_preset.request import (
    PartialBulkUpdateRuntimeVariantPresetsInput,
    UpdateRuntimeVariantPresetInput,
)
from ai.backend.common.dto.manager.v2.runtime_variant_preset.response import (
    RuntimeVariantPresetNode,
)
from ai.backend.manager.api.adapters.runtime_variant_preset.adapter import (
    RuntimeVariantPresetAdapter,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.runtime_variant_preset import (
    EveryLaidPresetComesBack,
    ManyPresetsAndACaller,
    ManyPresetsAndSomeone,
    NoLaidPresetIsProcessed,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

EDITED = "한 번에 고친 설명"

type Edited = PartialBulkPayload[RuntimeVariantPresetNode]
type EditingStep = Scenario[
    TestSeedingSession, ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Edited
]


@dataclass(frozen=True)
class EditingEveryLaid(When[ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Edited]):
    """미리 만들어 둔 프리셋들의 설명을 한 번에 고친다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        return f"{laid.caller.username}이 프리셋 {len(laid.laid)}개의 설명을 한 번에 고침"

    @override
    async def call(
        self, adapter: RuntimeVariantPresetAdapter, laid: ManyPresetsAndACaller
    ) -> Edited:
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_update(
                PartialBulkUpdateRuntimeVariantPresetsInput(
                    items=[
                        UpdateRuntimeVariantPresetInput(id=one.id, description=EDITED)
                        for one in laid.laid
                    ]
                )
            )


@dataclass(frozen=True)
class TheSuperadminEditsSeveralPresets(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Edited]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-edits-several-presets-at-once"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 프리셋 여럿의 설명을 한 번에 바꾸면, 모두 새 설명으로 오고 실패한 것은 없다"

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(role=UserRole.SUPERADMIN, besides=1)

    @override
    def when(self) -> When[ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Edited]:
        return EditingEveryLaid()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Edited]:
        return EveryLaidPresetComesBack(started=self.started, described=EDITED)


@dataclass(frozen=True)
class AUserGrantedNothingEditsNone(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-edits-none-of-several-presets"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 프리셋 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(besides=1)

    @override
    def when(self) -> When[ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Edited]:
        return EditingEveryLaid()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Edited]:
        return NoLaidPresetIsProcessed(reason="Insufficient permission")


SCENARIOS: list[EditingStep] = [
    TheSuperadminEditsSeveralPresets(started=datetime.now(UTC)),
    AUserGrantedNothingEditsNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_editing(
    scenario: EditingStep, adapter: RuntimeVariantPresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
