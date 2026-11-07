"""모델 카드를 배포할 수 있는 프리셋 찾기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.deployment_revision_preset.request import (
    DeploymentRevisionPresetFilter,
    DeploymentRevisionPresetOrder,
    SearchDeploymentRevisionPresetsInput,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.response import (
    SearchDeploymentRevisionPresetsPayload,
)
from ai.backend.common.dto.manager.v2.deployment_revision_preset.types import (
    DeploymentRevisionPresetOrderField,
)
from ai.backend.manager.api.adapters.model_card.adapter import ModelCardAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.model_card_deploy import (
    FITTING,
    PresetsForACard,
    PresetsForACardAndAReader,
    TheLastFittingPresetComesFirst,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Page = SearchDeploymentRevisionPresetsPayload
type PresetStep = Scenario[TestSeedingSession, PresetsForACard, ModelCardAdapter, Page]


@dataclass(frozen=True)
class FindingPresetsForTheCard(When[PresetsForACard, ModelCardAdapter, Page]):
    """이름 접두사로 거르고 이름 역순으로 정렬해 첫 한 개를 묻는다."""

    @override
    def operation(self) -> str:
        return "available_presets"

    @override
    def describe(self, laid: PresetsForACard) -> str:
        return Says(
            f"{laid.caller.username}이 카드 {laid.card.name}을 배포할 수 있는 프리셋을 이름이 "
            f"'{FITTING}'로 시작하는 것만, 이름 역순으로 첫 한 개 찾습니다",
            english=(
                f"{laid.caller.username} looks for presets card {laid.card.name} can be deployed "
                f"on, named starting with '{FITTING}', in reverse name order, first one only"
            ),
        )

    @override
    async def call(self, adapter: ModelCardAdapter, laid: PresetsForACard) -> Page:
        with ActingAs(laid.caller):
            return await adapter.available_presets(
                laid.card.id,
                SearchDeploymentRevisionPresetsInput(
                    filter=DeploymentRevisionPresetFilter(name=StringFilter(starts_with=FITTING)),
                    order=[
                        DeploymentRevisionPresetOrder(
                            field=DeploymentRevisionPresetOrderField.NAME,
                            direction=OrderDirection.DESC,
                        )
                    ],
                    limit=1,
                    offset=0,
                ),
            )


@dataclass(frozen=True)
class AReaderFindsThePresetsMeetingTheCard(
    Scenario[TestSeedingSession, PresetsForACard, ModelCardAdapter, Page]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-reader-finds-the-presets-meeting-the-card"

    @override
    def describe(self) -> str:
        return Says(
            "프리셋과 카드를 읽을 수 있는 사용자가 카드를 배포할 수 있는 프리셋을 이름으로 거르고 "
            "정렬해 한 쪽만 찾으면, 카드가 요구하는 최소 자원을 채우는 프리셋만 세어지고 모자란 "
            "프리셋과 필터에 걸리지 않는 프리셋은 오지 않습니다",
            english=(
                "when a user who can read presets and the card looks for the presets the card "
                "can be deployed on, filtered and ordered by name, one page at a time, only the "
                "presets meeting the minimum resources the card requires are counted, and "
                "neither the preset falling short nor the one the filter excludes comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, PresetsForACard]:
        return PresetsForACardAndAReader()

    @override
    def when(self) -> When[PresetsForACard, ModelCardAdapter, Page]:
        return FindingPresetsForTheCard()

    @override
    def then(self) -> Then[PresetsForACard, Page]:
        return TheLastFittingPresetComesFirst(started=self.started)


SCENARIOS: list[PresetStep] = [
    AReaderFindsThePresetsMeetingTheCard(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_available_presets(
    scenario: PresetStep, adapter: ModelCardAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
