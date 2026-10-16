"""배포 리비전 프리셋 여럿 수정하기, purge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    PartialBulkPurgeDeploymentRevisionPresetsInput,
    PartialBulkUpdateDeploymentRevisionPresetsInput,
    UpdateDeploymentRevisionPresetInput,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    DeploymentRevisionPresetNode,
)
from ai.backend.manager.api.adapters.deployment_revision_preset.adapter import (
    DeploymentRevisionPresetAdapter,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.deployment_revision_preset import (
    LAID_DESCRIPTION,
    EveryPresetComesBack,
    NoPresetIsProcessed,
    PresetsAndACaller,
    PresetsAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

EDITED = "한 번에 고친 설명"

type Answer = PartialBulkPayload[DeploymentRevisionPresetNode]
type PresetStep = Scenario[
    TestSeedingSession, PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer
]


@dataclass(frozen=True)
class EditingEveryPreset(When[PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]):
    """프리셋들의 설명을 한 번에 고친다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: PresetsAndACaller) -> str:
        return f"{laid.caller.username}이 프리셋 {len(laid.presets)}개의 설명을 한 번에 고침"

    @override
    async def call(
        self, adapter: DeploymentRevisionPresetAdapter, laid: PresetsAndACaller
    ) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_update(
                PartialBulkUpdateDeploymentRevisionPresetsInput(
                    items=[
                        UpdateDeploymentRevisionPresetInput(id=preset.id, description=EDITED)
                        for preset in laid.presets
                    ]
                )
            )


@dataclass(frozen=True)
class PurgingEveryPreset(When[PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]):
    """프리셋들을 한 번에 purge 한다. ``missing``이 있으면 그 id 도 함께 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "partial_bulk_purge"

    @override
    def describe(self, laid: PresetsAndACaller) -> str:
        besides = " 와 없는 id 하나" if self.missing is not None else ""
        return f"{laid.caller.username}이 프리셋 {len(laid.presets)}개{besides}를 한 번에 purge 함"

    @override
    async def call(
        self, adapter: DeploymentRevisionPresetAdapter, laid: PresetsAndACaller
    ) -> Answer:
        ids: list[UUID] = [preset.id for preset in laid.presets]
        if self.missing is not None:
            ids.append(self.missing)
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_purge(
                PartialBulkPurgeDeploymentRevisionPresetsInput(ids=ids)
            )


@dataclass(frozen=True)
class TheSuperadminEditsSeveralPresets(
    Scenario[TestSeedingSession, PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-edits-several-presets-at-once"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 프리셋 여럿의 설명을 한 번에 바꾸면, 모두 새 설명으로 오고 실패한 것은 없다"

    @override
    def given(self) -> Given[TestSeedingSession, PresetsAndACaller]:
        return PresetsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]:
        return EditingEveryPreset()

    @override
    def then(self) -> Then[PresetsAndACaller, Answer]:
        return EveryPresetComesBack(description=EDITED)


@dataclass(frozen=True)
class AReaderEditsNoPreset(
    Scenario[TestSeedingSession, PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-preset-reader-edits-none-of-several-presets"

    @override
    def describe(self) -> str:
        return (
            "프리셋을 읽을 수만 있는 사용자가 프리셋 여럿을 한 번에 고치려 하면, 고쳐진 것 없이 "
            "모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, PresetsAndACaller]:
        return PresetsAndSomeone()

    @override
    def when(self) -> When[PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]:
        return EditingEveryPreset()

    @override
    def then(self) -> Then[PresetsAndACaller, Answer]:
        return NoPresetIsProcessed(reason="Insufficient permission")


@dataclass(frozen=True)
class PurgingAnswersForTheMissingPreset(
    Scenario[TestSeedingSession, PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]
):
    missing: UUID = UUID(int=1)

    @override
    def summary(self) -> str:
        return "purging-several-presets-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 프리셋 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 purge 되기 전 "
            "모습으로 오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, PresetsAndACaller]:
        return PresetsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]:
        return PurgingEveryPreset(missing=self.missing)

    @override
    def then(self) -> Then[PresetsAndACaller, Answer]:
        return EveryPresetComesBack(description=LAID_DESCRIPTION, missing=self.missing)


@dataclass(frozen=True)
class AReaderPurgesNoPreset(
    Scenario[TestSeedingSession, PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-preset-reader-purges-none-of-several-presets"

    @override
    def describe(self) -> str:
        return (
            "프리셋을 읽을 수만 있는 사용자가 프리셋 여럿을 한 번에 purge 하려 하면, purge 된 "
            "것 없이 모두 권한이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, PresetsAndACaller]:
        return PresetsAndSomeone()

    @override
    def when(self) -> When[PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]:
        return PurgingEveryPreset()

    @override
    def then(self) -> Then[PresetsAndACaller, Answer]:
        return NoPresetIsProcessed(reason="Insufficient permission")


SCENARIOS: list[PresetStep] = [
    TheSuperadminEditsSeveralPresets(),
    AReaderEditsNoPreset(),
    PurgingAnswersForTheMissingPreset(),
    AReaderPurgesNoPreset(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk(
    scenario: PresetStep,
    adapter: DeploymentRevisionPresetAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
