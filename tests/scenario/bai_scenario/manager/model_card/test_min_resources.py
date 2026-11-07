"""모델 카드들의 최소 자원 요구 읽기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.dto.manager.v2.model_card.response import ResourceSlotEntryInfo
from ai.backend.manager.api.adapters.model_card.adapter import ModelCardAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Same,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.model_card import ProjectCards, TwoProjectsOfCardsAndSomeone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = dict[UUID, list[ResourceSlotEntryInfo]]
type RequirementStep = Scenario[TestSeedingSession, ProjectCards, ModelCardAdapter, Answer]


@dataclass(frozen=True)
class ReadingTwoOfTheProject(When[ProjectCards, ModelCardAdapter, Answer]):
    """첫 프로젝트의 카드 둘의 최소 요구를 읽는다."""

    @override
    def operation(self) -> str:
        return "min_resources"

    @override
    def describe(self, laid: ProjectCards) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.found[0].name}, {laid.found[1].name} 카드의 최소 "
            "자원 요구를 조회합니다",
            english=(
                f"{laid.caller.username} reads the minimum resource requirements of the cards "
                f"{laid.found[0].name} and {laid.found[1].name}"
            ),
        )

    @override
    async def call(self, adapter: ModelCardAdapter, laid: ProjectCards) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.min_resources([laid.found[0].id, laid.found[1].id])


@dataclass(frozen=True)
class ReadingOneOfEachProject(When[ProjectCards, ModelCardAdapter, Answer]):
    """첫 프로젝트의 카드와 다른 프로젝트의 카드의 최소 요구를 함께 읽는다."""

    @override
    def operation(self) -> str:
        return "min_resources"

    @override
    def describe(self, laid: ProjectCards) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.found[0].name}, 다른 프로젝트의 "
            f"{laid.elsewhere.name} 카드의 최소 자원 요구를 함께 조회합니다",
            english=(
                f"{laid.caller.username} reads the minimum resource requirements of the card "
                f"{laid.found[0].name} and the card {laid.elsewhere.name} of the other "
                "project together"
            ),
        )

    @override
    async def call(self, adapter: ModelCardAdapter, laid: ProjectCards) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.min_resources([laid.found[0].id, laid.elsewhere.id])


@dataclass(frozen=True)
class EachCardsRequirement(Then[ProjectCards, Answer]):
    """카드마다 심은 최소 요구가 온다."""

    @override
    def says(self) -> str:
        return Says(
            "요청한 카드마다 심은 최소 자원 요구가 옵니다",
            english="each requested card comes with the minimum resource requirement seeded",
        )

    @override
    def look(self, laid: ProjectCards, answered: Answered[Answer]) -> list[Verdict]:
        by_card = answered.response
        if by_card is None:
            return [MissingResponse(answered.raised)]
        verdicts: list[Verdict] = [Same("length", len(by_card), 2)]
        for card in laid.found[:2]:
            verdicts.append(Same(card.name, by_card.get(card.id), laid.entries(card)))
        return verdicts


@dataclass(frozen=True)
class AReaderReadsRequirements(
    Scenario[TestSeedingSession, ProjectCards, ModelCardAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-model-card-read-reads-the-minimum-resources"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트에서 모델 카드 읽기 권한을 받은 사용자가 그 프로젝트의 카드 둘의 최소 자원 "
            "요구를 조회하면 카드마다 심은 요구가 응답으로 옵니다",
            english=(
                "when a user granted model card read in the project reads the minimum resource "
                "requirements of two cards of that project, the requirement seeded for each "
                "card comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ProjectCards]:
        return TwoProjectsOfCardsAndSomeone(granted=(Permission.READ,))

    @override
    def when(self) -> When[ProjectCards, ModelCardAdapter, Answer]:
        return ReadingTwoOfTheProject()

    @override
    def then(self) -> Then[ProjectCards, Answer]:
        return EachCardsRequirement()


@dataclass(frozen=True)
class ACardOfAnotherProjectRefusesTheWholeCall(
    Scenario[TestSeedingSession, ProjectCards, ModelCardAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-card-of-a-project-without-read-refuses-the-whole-call"

    @override
    def describe(self) -> str:
        return Says(
            "한 프로젝트에서만 모델 카드 읽기 권한을 받은 사용자가 그 프로젝트의 카드와 다른 "
            "프로젝트의 카드의 최소 자원 요구를 함께 조회하면 호출 전체가 권한 부족으로 "
            "거부됩니다",
            english=(
                "when a user granted model card read in only one project reads the minimum "
                "resource requirements of a card of that project and a card of another project "
                "together, the whole call is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ProjectCards]:
        return TwoProjectsOfCardsAndSomeone(granted=(Permission.READ,))

    @override
    def when(self) -> When[ProjectCards, ModelCardAdapter, Answer]:
        return ReadingOneOfEachProject()

    @override
    def then(self) -> Then[ProjectCards, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[RequirementStep] = [
    AReaderReadsRequirements(),
    ACardOfAnotherProjectRefusesTheWholeCall(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_min_resources(
    scenario: RequirementStep, adapter: ModelCardAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
