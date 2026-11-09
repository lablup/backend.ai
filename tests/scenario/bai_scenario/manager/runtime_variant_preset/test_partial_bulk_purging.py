"""프리셋 여럿 purge."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.runtime_variant_preset.request import (
    PartialBulkPurgeRuntimeVariantPresetsInput,
)
from ai.backend.common.dto.manager.v2.runtime_variant_preset.response import (
    RuntimeVariantPresetNode,
)
from ai.backend.manager.api.adapters.runtime_variant_preset.adapter import (
    RuntimeVariantPresetAdapter,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.runtime_variant_preset import (
    EveryLaidPresetComesBack,
    ManyPresetsAndACaller,
    ManyPresetsAndSomeone,
    NoLaidPresetIsProcessed,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Purged = PartialBulkPayload[RuntimeVariantPresetNode]
type PurgingStep = Scenario[
    TestSeedingSession, ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Purged
]


@dataclass(frozen=True)
class PurgingEveryLaid(When[ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Purged]):
    """미리 만들어 둔 프리셋들을 한 번에 purge 한다. `missing`이 있으면 그 id 도 함께 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "partial_bulk_purge"

    @override
    def describe(self, laid: ManyPresetsAndACaller) -> str:
        besides = " 와 없는 id 하나" if self.missing is not None else ""
        besides_en = " and one unknown id" if self.missing is not None else ""
        return Says(
            f"{laid.caller.username}이 런타임 파라미터 {len(laid.laid)}개{besides}를 한 번에 "
            "purge 합니다",
            english=(
                f"{laid.caller.username} purges {len(laid.laid)} presets{besides_en} in one call"
            ),
        )

    @override
    async def call(
        self, adapter: RuntimeVariantPresetAdapter, laid: ManyPresetsAndACaller
    ) -> Purged:
        ids: list[UUID] = [one.id for one in laid.laid]
        if self.missing is not None:
            ids.append(self.missing)
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_purge(
                PartialBulkPurgeRuntimeVariantPresetsInput(ids=ids)
            )


@dataclass(frozen=True)
class PurgingAnswersForTheMissingOne(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Purged]
):
    started: datetime
    missing: UUID = UUID(int=1)

    @override
    def summary(self) -> str:
        return "purging-several-presets-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 런타임 파라미터 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 purge 되기 "
            "전 모습으로 처리된 목록에 오고 없는 id 는 실패 목록에 옵니다",
            english=(
                "when the superadmin purges two presets and one unknown id in one call, the two "
                "come back in the processed list as they were before the purge, and the unknown "
                "id comes back in the failed list"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(role=UserRole.SUPERADMIN, besides=1)

    @override
    def when(self) -> When[ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Purged]:
        return PurgingEveryLaid(missing=self.missing)

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Purged]:
        return EveryLaidPresetComesBack(started=self.started, missing=self.missing)


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNone(
    Scenario[TestSeedingSession, ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purges-none-of-several-presets"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 런타임 파라미터 여럿을 한 번에 purge 하려 하면, purge 된 "
            "것 없이 모두 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted nothing tries to purge several presets in one call, "
                "nothing is purged and every one comes back in the failed list for lack of "
                "permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyPresetsAndACaller]:
        return ManyPresetsAndSomeone(besides=1)

    @override
    def when(self) -> When[ManyPresetsAndACaller, RuntimeVariantPresetAdapter, Purged]:
        return PurgingEveryLaid()

    @override
    def then(self) -> Then[ManyPresetsAndACaller, Purged]:
        return NoLaidPresetIsProcessed(reason="Insufficient permission")


SCENARIOS: list[PurgingStep] = [
    PurgingAnswersForTheMissingOne(started=datetime.now(UTC)),
    AUserGrantedNothingPurgesNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_purging(
    scenario: PurgingStep, adapter: RuntimeVariantPresetAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
