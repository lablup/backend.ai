"""리소스 프리셋 여럿 purge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.resource_preset.request import (
    PartialBulkPurgeResourcePresetsInput,
)
from ai.backend.common.dto.manager.v2.resource_preset.response import ResourcePresetNode
from ai.backend.manager.api.adapters.resource_preset.adapter import ResourcePresetAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.resource_preset import (
    EveryPresetComesBack,
    ManyPresetsAndACaller,
    ManyPresetsAndSomeone,
    NoPresetIsProcessed,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Purged = PartialBulkPayload[ResourcePresetNode]
type PurgingStep = Scenario[
    TestSeedingSession, ManyPresetsAndACaller, ResourcePresetAdapter, Purged
]


@dataclass(frozen=True)
class PurgingEveryTarget(When[ManyPresetsAndACaller, ResourcePresetAdapter, Purged]):
    """대상 프리셋들을 한 번에 purge 한다. `missing`이 있으면 그 id 도 함께 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "partial_bulk_purge"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        if self.missing is not None:
            besides_ko = " 와 없는 id 하나"
            besides_en = " and one unknown id"
        else:
            besides_ko = ""
            besides_en = ""
        return Says(
            f"{laid.caller.username}이 프리셋 {len(laid.laid)}개{besides_ko}를 한 번에 purge 합니다",
            english=(f"{laid.caller.username} purges {len(laid.laid)} presets{besides_en} at once"),
        )

    @override
    async def call(self, adapter: ResourcePresetAdapter, laid: ManyPresetsAndACaller) -> Purged:
        ids: list[UUID] = [preset.id for preset in laid.laid]
        if self.missing is not None:
            ids.append(self.missing)
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_purge(PartialBulkPurgeResourcePresetsInput(ids=ids))


@dataclass(frozen=True)
class PurgingAnswersForTheMissingOne(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, ResourcePresetAdapter, Purged]
):
    missing: UUID = UUID(int=1)

    @override
    def summary(self) -> str:
        return "purging-several-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 삭제된 노드로 오고 없는 id 는 "
            "대상이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "purging two presets and one unknown id at once answers the two as deleted nodes "
                "and the unknown id in the failed list because no target answers to it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyPresetsAndACaller, ResourcePresetAdapter, Purged]:
        return PurgingEveryTarget(missing=self.missing)

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Purged]:
        return EveryPresetComesBack(missing=self.missing)


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNone(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, ResourcePresetAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purges-none-of-several-presets"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 프리셋 여럿을 한 번에 purge 하려 하면, 삭제된 것 "
            "없이 모두 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "a user granted nothing trying to purge several presets at once gets none "
                "purged and every one in the failed list for not enough permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone()

    @override
    def when(self) -> When[ManyPresetsAndACaller, ResourcePresetAdapter, Purged]:
        return PurgingEveryTarget()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Purged]:
        return NoPresetIsProcessed(reason="Insufficient permission")


SCENARIOS: list[PurgingStep] = [
    PurgingAnswersForTheMissingOne(),
    AUserGrantedNothingPurgesNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_purging(
    scenario: PurgingStep, adapter: ResourcePresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
