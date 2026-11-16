"""배포 리비전 프리셋 여럿을 id 로 한 번에 읽기."""

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
    Refused,
    Same,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.deployment_revision_preset import (
    PresetsAndACaller,
    PresetsAndAnOutsider,
    PresetsAndSomeone,
    ThePresetNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = list[DeploymentRevisionPresetNode | Exception | None]
type LoadStep = Scenario[
    TestSeedingSession, PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer
]


@dataclass(frozen=True)
class LoadingTheSeededPresets(When[PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]):
    """심은 프리셋들의 id 만 준다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: PresetsAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 심은 프리셋 {len(laid.presets)}개를 id 로 일괄 조회합니다",
            english=(
                f"{laid.caller.username} loads {len(laid.presets)} of the presets seeded "
                "in advance by id in one call"
            ),
        )

    @override
    async def call(
        self, adapter: DeploymentRevisionPresetAdapter, laid: PresetsAndACaller
    ) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([preset.id for preset in laid.presets])


@dataclass(frozen=True)
class ThePresetsComeBackInOrder(Then[PresetsAndACaller, Answer]):
    """심은 프리셋이 입력 순서대로 통째로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "심은 프리셋이 입력 순서대로 전체가 옵니다",
            english="the presets seeded in advance come back whole in input order",
        )

    @override
    def look(self, laid: PresetsAndACaller, answered: Answered[Answer]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        verdicts: list[Verdict] = [Same("length", len(loaded), len(laid.presets))]
        for i, (item, preset) in enumerate(zip(loaded, laid.presets, strict=False)):
            if isinstance(item, DeploymentRevisionPresetNode):
                verdicts.extend(ThePresetNode(self.started).verdicts(item, preset, at=f"[{i}]."))
            else:
                verdicts.append(Same(f"[{i}]", type(item).__name__, "DeploymentRevisionPresetNode"))
        return verdicts


@dataclass(frozen=True)
class EveryEntryIsRefused(Then[PresetsAndACaller, Answer]):
    """호출은 성공하고, 항목마다 권한 부족으로 거부가 온다."""

    @override
    def says(self) -> str:
        return Says(
            "항목마다 권한 부족으로 거부가 옵니다",
            english="a rejection for lack of permission comes back for each entry",
        )

    @override
    def look(self, laid: PresetsAndACaller, answered: Answered[Answer]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        return [
            Same("length", len(loaded), len(laid.presets)),
            *[
                Refused(NotEnoughPermission, item if isinstance(item, Exception) else None)
                for item in loaded
            ],
        ]


@dataclass(frozen=True)
class AReaderLoadsThePresetsById(
    Scenario[TestSeedingSession, PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-preset-reader-loads-the-presets-by-id"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋 조회 권한을 받은 사용자가 심은 프리셋 여럿을 id 로 일괄 조회하면, "
            "입력 순서대로 그 프리셋들이 옵니다",
            english=(
                "when a user granted preset read loads the presets seeded in advance by id "
                "in one call, they come back in input order"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, PresetsAndACaller]:
        return PresetsAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]:
        return LoadingTheSeededPresets()

    @override
    def then(self) -> Then[PresetsAndACaller, Answer]:
        return ThePresetsComeBackInOrder(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingGetsARefusalForEachPreset(
    Scenario[TestSeedingSession, PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-gets-a-rejection-for-each-preset"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 심은 프리셋 여럿을 id 로 일괄 조회하면, 호출은 "
            "성공하되 항목마다 권한 부족으로 거부가 옵니다",
            english=(
                "when a user granted nothing loads the presets seeded in advance by id in "
                "one call, the call succeeds but a rejection for lack of permission comes "
                "back for each entry"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, PresetsAndACaller]:
        return PresetsAndAnOutsider(role=UserRole.USER)

    @override
    def when(self) -> When[PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]:
        return LoadingTheSeededPresets()

    @override
    def then(self) -> Then[PresetsAndACaller, Answer]:
        return EveryEntryIsRefused()


STARTED = datetime.now(UTC)

SCENARIOS: list[LoadStep] = [
    AReaderLoadsThePresetsById(started=STARTED),
    AUserGrantedNothingGetsARefusalForEachPreset(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_batch_loading(
    scenario: LoadStep,
    adapter: DeploymentRevisionPresetAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
