"""배포 리비전 프리셋 하나 수정하기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    UpdateDeploymentRevisionPresetInput,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    UpdateDeploymentRevisionPresetPayload,
)
from ai.backend.manager.api.adapters.deployment_revision_preset.adapter import (
    DeploymentRevisionPresetAdapter,
)
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.deployment_revision_preset import (
    PresetsAndACaller,
    PresetsAndSomeone,
    ThePresetNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

EDITED = Says("한 번에 수정한 설명", english="the description edited at once")

type Answer = UpdateDeploymentRevisionPresetPayload
type EditStep = Scenario[
    TestSeedingSession, PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer
]


@dataclass(frozen=True)
class EditingTheFirstPreset(When[PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]):
    """심은 프리셋 하나의 설명만 고친다."""

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: PresetsAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 심은 프리셋 하나의 설명을 고칩니다",
            english=f"{laid.caller.username} changes the description of one of the presets",
        )

    @override
    async def call(
        self, adapter: DeploymentRevisionPresetAdapter, laid: PresetsAndACaller
    ) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.update(
                UpdateDeploymentRevisionPresetInput(id=laid.presets[0].id, description=EDITED)
            )


@dataclass(frozen=True)
class TheEditedPresetComesBack(Then[PresetsAndACaller, Answer]):
    """고친 프리셋이 통째로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "고친 프리셋이 전체가 응답으로 옵니다", english="the whole preset edited comes back"
        )

    @override
    def look(self, laid: PresetsAndACaller, answered: Answered[Answer]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return ThePresetNode(self.started, described=EDITED).verdicts(payload.preset, laid.presets[0])


@dataclass(frozen=True)
class TheSuperadminEditsAPreset(
    Scenario[TestSeedingSession, PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-edits-a-preset"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 심은 프리셋 하나의 설명을 고치면, 새 설명이 들어간 프리셋이 옵니다",
            english=(
                "when the superadmin changes the description of one of the presets seeded in "
                "advance, the preset comes back with the new description"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, PresetsAndACaller]:
        return PresetsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]:
        return EditingTheFirstPreset()

    @override
    def then(self) -> Then[PresetsAndACaller, Answer]:
        return TheEditedPresetComesBack(started=self.started)


@dataclass(frozen=True)
class APresetReaderEditsNoPreset(
    Scenario[TestSeedingSession, PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-preset-reader-edits-no-preset"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋 조회 권한만 받은 사용자가 심은 프리셋 하나의 설명을 고치려 하면, 권한이 "
            "없다는 이유로 거부됩니다",
            english=(
                "when a user granted only preset read tries to change the description of one "
                "of the presets, the edit is rejected because the user lacks permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, PresetsAndACaller]:
        return PresetsAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]:
        return EditingTheFirstPreset()

    @override
    def then(self) -> Then[PresetsAndACaller, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


STARTED = datetime.now(UTC)

SCENARIOS: list[EditStep] = [
    TheSuperadminEditsAPreset(started=STARTED),
    APresetReaderEditsNoPreset(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_updating(
    scenario: EditStep,
    adapter: DeploymentRevisionPresetAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
