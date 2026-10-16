"""런타임 변형 여럿 수정하기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.runtime_variant.request import (
    PartialBulkUpdateRuntimeVariantsInput,
    UpdateRuntimeVariantInput,
)
from ai.backend.common.dto.manager.v2.runtime_variant.response import RuntimeVariantNode
from ai.backend.manager.api.adapters.runtime_variant.adapter import RuntimeVariantAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.runtime_variant import (
    EveryLaidVariantComesBack,
    ManyVariantsAndACaller,
    ManyVariantsAndSomeone,
    NoLaidVariantIsProcessed,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

EDITED = "한 번에 고친 설명"

type Edited = PartialBulkPayload[RuntimeVariantNode]
type EditingStep = Scenario[
    TestSeedingSession, ManyVariantsAndACaller, RuntimeVariantAdapter, Edited
]


@dataclass(frozen=True)
class EditingEveryLaid(When[ManyVariantsAndACaller, RuntimeVariantAdapter, Edited]):
    """미리 만들어 둔 변형들의 설명을 한 번에 고친다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: ManyVariantsAndACaller) -> str:
        return f"{laid.caller.username}이 변형 {len(laid.laid)}개의 설명을 한 번에 고침"

    @override
    async def call(self, adapter: RuntimeVariantAdapter, laid: ManyVariantsAndACaller) -> Edited:
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_update(
                PartialBulkUpdateRuntimeVariantsInput(
                    items=[
                        UpdateRuntimeVariantInput(id=one.id, description=EDITED)
                        for one in laid.laid
                    ]
                )
            )


@dataclass(frozen=True)
class TheSuperadminEditsSeveralVariants(
    Scenario[TestSeedingSession, ManyVariantsAndACaller, RuntimeVariantAdapter, Edited]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-edits-several-variants-at-once"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 변형 여럿의 설명을 한 번에 바꾸면, 모두 새 설명으로 오고 실패한 것은 없다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyVariantsAndACaller]:
        return ManyVariantsAndSomeone(role=UserRole.SUPERADMIN, besides=1)

    @override
    def when(self) -> When[ManyVariantsAndACaller, RuntimeVariantAdapter, Edited]:
        return EditingEveryLaid()

    @override
    def then(self) -> Then[ManyVariantsAndACaller, Edited]:
        return EveryLaidVariantComesBack(started=self.started, described=EDITED)


@dataclass(frozen=True)
class AUserGrantedNothingEditsNone(
    Scenario[TestSeedingSession, ManyVariantsAndACaller, RuntimeVariantAdapter, Edited]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-edits-none-of-several-variants"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 변형 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyVariantsAndACaller]:
        return ManyVariantsAndSomeone(besides=1)

    @override
    def when(self) -> When[ManyVariantsAndACaller, RuntimeVariantAdapter, Edited]:
        return EditingEveryLaid()

    @override
    def then(self) -> Then[ManyVariantsAndACaller, Edited]:
        return NoLaidVariantIsProcessed(reason="Insufficient permission")


SCENARIOS: list[EditingStep] = [
    TheSuperadminEditsSeveralVariants(started=datetime.now(UTC)),
    AUserGrantedNothingEditsNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_editing(
    scenario: EditingStep, adapter: RuntimeVariantAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
