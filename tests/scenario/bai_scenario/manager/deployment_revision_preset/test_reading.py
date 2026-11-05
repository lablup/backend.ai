"""배포 리비전 프리셋 하나 읽기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    DeploymentRevisionPresetNode,
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
    PresetsAndAnOutsider,
    PresetsAndSomeone,
    ThePresetNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = DeploymentRevisionPresetNode
type ReadStep = Scenario[
    TestSeedingSession, PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer
]


@dataclass(frozen=True)
class ReadingTheFirstPreset(When[PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]):
    """심은 프리셋 하나의 id 만 준다."""

    index: int = 0

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: PresetsAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 심은 프리셋 하나를 id 로 읽습니다",
            english=f"{laid.caller.username} reads one of the presets seeded in advance by id",
        )

    @override
    async def call(
        self, adapter: DeploymentRevisionPresetAdapter, laid: PresetsAndACaller
    ) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.get(laid.presets[self.index].id)


@dataclass(frozen=True)
class ThePresetReadComesBack(Then[PresetsAndACaller, Answer]):
    """읽은 프리셋이 통째로 온다."""

    started: datetime
    index: int = 0

    @override
    def says(self) -> str:
        return Says(
            "읽은 프리셋이 전체가 응답으로 옵니다", english="the whole preset read comes back"
        )

    @override
    def look(self, laid: PresetsAndACaller, answered: Answered[Answer]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [MissingResponse(answered.raised)]
        return ThePresetNode(self.started).verdicts(node, laid.presets[self.index])


@dataclass(frozen=True)
class AReaderReadsAPreset(
    Scenario[TestSeedingSession, PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-preset-reader-reads-a-preset"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋 조회 권한을 받은 사용자가 심은 프리셋 하나를 id 로 읽으면, 그 프리셋이 옵니다",
            english=(
                "when a user granted preset read reads one of the presets seeded in advance "
                "by id, that preset comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, PresetsAndACaller]:
        return PresetsAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]:
        return ReadingTheFirstPreset()

    @override
    def then(self) -> Then[PresetsAndACaller, Answer]:
        return ThePresetReadComesBack(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingReadsNoPreset(
    Scenario[TestSeedingSession, PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-reads-no-preset"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 심은 프리셋 하나를 id 로 읽으려 하면, 권한이 없다는 "
            "이유로 거부됩니다",
            english=(
                "when a user granted nothing tries to read one of the presets seeded in "
                "advance by id, the read is rejected because the user lacks permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, PresetsAndACaller]:
        return PresetsAndAnOutsider(role=UserRole.USER)

    @override
    def when(self) -> When[PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]:
        return ReadingTheFirstPreset()

    @override
    def then(self) -> Then[PresetsAndACaller, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


STARTED = datetime.now(UTC)

SCENARIOS: list[ReadStep] = [
    AReaderReadsAPreset(started=STARTED),
    AUserGrantedNothingReadsNoPreset(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadStep,
    adapter: DeploymentRevisionPresetAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
