"""배포 리비전 프리셋 검색하기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    SearchDeploymentRevisionPresetsInput,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    SearchDeploymentRevisionPresetsPayload,
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
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.deployment_revision_preset import (
    PresetsAndACaller,
    PresetsAndAnOutsider,
    PresetsAndSomeone,
    ThePresetNode,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = SearchDeploymentRevisionPresetsPayload
type SearchStep = Scenario[
    TestSeedingSession, PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer
]


@dataclass(frozen=True)
class SearchingPresets(When[PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]):
    """필터 없이 프리셋을 훑는다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: PresetsAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 프리셋을 훕습니다",
            english=f"{laid.caller.username} searches the presets",
        )

    @override
    async def call(
        self, adapter: DeploymentRevisionPresetAdapter, laid: PresetsAndACaller
    ) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.search(SearchDeploymentRevisionPresetsInput())


@dataclass(frozen=True)
class TheSeededPresetsComeBack(Then[PresetsAndACaller, Answer]):
    """심은 프리셋이 통째로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "심은 프리셋이 전체가 응답으로 옵니다",
            english="the presets seeded in advance come back",
        )

    @override
    def look(self, laid: PresetsAndACaller, answered: Answered[Answer]) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("total_count", page.total_count, len(laid.presets)),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]
        for i, (node, preset) in enumerate(zip(page.items, laid.presets, strict=False)):
            verdicts.extend(ThePresetNode(self.started).verdicts(node, preset, at=f"items[{i}]."))
        return verdicts


@dataclass(frozen=True)
class AReaderSearchesEveryPreset(
    Scenario[TestSeedingSession, PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-preset-reader-searches-every-preset"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋 조회 권한을 받은 사용자가 프리셋을 훑으면, 심은 프리셋이 모두 옵니다",
            english=(
                "when a user granted preset read searches the presets, every preset seeded "
                "in advance comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, PresetsAndACaller]:
        return PresetsAndSomeone(role=UserRole.USER)

    @override
    def when(self) -> When[PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]:
        return SearchingPresets()

    @override
    def then(self) -> Then[PresetsAndACaller, Answer]:
        return TheSeededPresetsComeBack(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingSearchesNoPreset(
    Scenario[TestSeedingSession, PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-searches-no-preset"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 프리셋을 훑으려 하면, 권한이 없다는 이유로 거부됩니다",
            english=(
                "when a user granted nothing tries to search the presets, the search is "
                "rejected because the user lacks permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, PresetsAndACaller]:
        return PresetsAndAnOutsider(role=UserRole.USER)

    @override
    def when(self) -> When[PresetsAndACaller, DeploymentRevisionPresetAdapter, Answer]:
        return SearchingPresets()

    @override
    def then(self) -> Then[PresetsAndACaller, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


STARTED = datetime.now(UTC)

SCENARIOS: list[SearchStep] = [
    AReaderSearchesEveryPreset(started=STARTED),
    AUserGrantedNothingSearchesNoPreset(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchStep,
    adapter: DeploymentRevisionPresetAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
