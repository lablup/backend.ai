"""배포 리비전 프리셋 purge 하기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    DeleteDeploymentRevisionPresetPayload,
)
from ai.backend.manager.api.adapters.deployment_revision_preset.adapter import (
    DeploymentRevisionPresetAdapter,
)
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.deployment_revision_preset import (
    PRESET_ID,
    PresetsAndACaller,
    PresetsAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = DeleteDeploymentRevisionPresetPayload
type RetireStep = Scenario[
    TestSeedingSession, PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer
]


@dataclass(frozen=True)
class PurgingTheFirstPreset(When[PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]):
    """심은 프리셋 하나의 id 만 준다."""

    @override
    def operation(self) -> str:
        return "purge"

    @override
    def describe(self, laid: PresetsAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 심은 프리셋 하나를 purge 합니다",
            english=f"{laid.caller.username} purges one of the presets seeded in advance",
        )

    @override
    async def call(
        self, adapter: DeploymentRevisionPresetAdapter, laid: PresetsAndACaller
    ) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.purge(laid.presets[0].id)


@dataclass(frozen=True)
class ThePresetIsGone(Then[PresetsAndACaller, Answer]):
    """purge 한 프리셋의 id 가 응답으로 온다."""

    @override
    def says(self) -> str:
        return Says(
            "purge 한 프리셋의 id 가 응답으로 옵니다",
            english="the id of the purged preset comes back",
        )

    @override
    def look(self, laid: PresetsAndACaller, answered: Answered[Answer]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            Held[UUID]("id", payload.id, SameAs(laid.presets[0].id, PRESET_ID)),
            Held[UUID]("entity_id", payload.entity_id, SameAs(laid.presets[0].id, PRESET_ID)),
        ]


@dataclass(frozen=True)
class AUserGrantedHardDeletePurgesAPreset(
    Scenario[TestSeedingSession, PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-hard-delete-purges-a-preset"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋 영구 삭제 권한을 받은 사용자가 심은 프리셋 하나를 purge 하면, 그 프리셋의 "
            "id 가 옵니다",
            english=(
                "when a user granted preset hard delete purges one of the presets seeded in "
                "advance, the id of that preset comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, PresetsAndACaller]:
        return PresetsAndSomeone(permission=Permission.HARD_DELETE)

    @override
    def when(self) -> When[PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]:
        return PurgingTheFirstPreset()

    @override
    def then(self) -> Then[PresetsAndACaller, Answer]:
        return ThePresetIsGone()


@dataclass(frozen=True)
class APresetReaderPurgesNoPreset(
    Scenario[TestSeedingSession, PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-preset-reader-purges-no-preset"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋 조회 권한만 받은 사용자가 심은 프리셋 하나를 purge 하려 하면, 권한이 없다는 "
            "이유로 거부됩니다",
            english=(
                "when a user granted only preset read tries to purge one of the presets seeded "
                "in advance, the purge is rejected because the user lacks permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, PresetsAndACaller]:
        return PresetsAndSomeone()

    @override
    def when(self) -> When[PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]:
        return PurgingTheFirstPreset()

    @override
    def then(self) -> Then[PresetsAndACaller, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[RetireStep] = [
    AUserGrantedHardDeletePurgesAPreset(),
    APresetReaderPurgesNoPreset(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_retiring(
    scenario: RetireStep,
    adapter: DeploymentRevisionPresetAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
