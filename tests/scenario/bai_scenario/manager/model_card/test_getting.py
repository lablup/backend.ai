"""모델 카드 하나를 id 로 읽기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.model_card.response import ModelCardNode
from ai.backend.manager.api.adapters.model_card.adapter import ModelCardAdapter
from ai.backend.manager.data.permission.types import Permission
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
from bai_scenario.components.model_card import ProjectCards, TwoProjectsOfCardsAndSomeone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type CardStep = Scenario[TestSeedingSession, ProjectCards, ModelCardAdapter, ModelCardNode]


@dataclass(frozen=True)
class GettingTheFirstCard(When[ProjectCards, ModelCardAdapter, ModelCardNode]):
    """첫 프로젝트의 카드 하나를 id 로 읽는다."""

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: ProjectCards) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.found[0].name} 카드를 id 로 조회합니다",
            english=f"{laid.caller.username} reads the card {laid.found[0].name} by id",
        )

    @override
    async def call(self, adapter: ModelCardAdapter, laid: ProjectCards) -> ModelCardNode:
        with ActingAs(laid.caller):
            return await adapter.get(laid.found[0].id)


@dataclass(frozen=True)
class TheWholeCard(Then[ProjectCards, ModelCardNode]):
    """선택 항목과 최소 요구까지 채워진 카드 전체가 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "선택 항목과 최소 자원 요구까지 채워진 카드 전체가 응답으로 옵니다",
            english=(
                "the whole card comes back with its optional fields and minimum resource "
                "requirement filled"
            ),
        )

    @override
    def look(self, laid: ProjectCards, answered: Answered[ModelCardNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [MissingResponse(answered.raised)]
        card = laid.found[0]
        return laid.look(self.started, card).verdicts("", node, card)


@dataclass(frozen=True)
class AReaderGetsTheCard(
    Scenario[TestSeedingSession, ProjectCards, ModelCardAdapter, ModelCardNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-model-card-read-gets-a-card-by-id"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트에서 모델 카드 읽기 권한을 받은 사용자가 카드를 id 로 조회하면 그 카드 "
            "전체가 응답으로 옵니다",
            english=(
                "when a user granted model card read in the project reads a card by id, the "
                "whole card comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ProjectCards]:
        return TwoProjectsOfCardsAndSomeone(granted=(Permission.READ,))

    @override
    def when(self) -> When[ProjectCards, ModelCardAdapter, ModelCardNode]:
        return GettingTheFirstCard()

    @override
    def then(self) -> Then[ProjectCards, ModelCardNode]:
        return TheWholeCard(started=self.started)


@dataclass(frozen=True)
class AUserWithoutReadIsRefused(
    Scenario[TestSeedingSession, ProjectCards, ModelCardAdapter, ModelCardNode]
):
    @override
    def summary(self) -> str:
        return "a-user-without-model-card-read-may-not-get-a-card"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트에서 모델 카드 수정 권한만 받고 읽기 권한은 없는 사용자가 카드를 id 로 "
            "조회하면 권한 부족으로 거부됩니다",
            english=(
                "when a user granted only model card update and not read in the project reads "
                "a card by id, the call is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ProjectCards]:
        return TwoProjectsOfCardsAndSomeone(granted=(Permission.UPDATE,))

    @override
    def when(self) -> When[ProjectCards, ModelCardAdapter, ModelCardNode]:
        return GettingTheFirstCard()

    @override
    def then(self) -> Then[ProjectCards, ModelCardNode]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[CardStep] = [
    AReaderGetsTheCard(started=datetime.now(UTC)),
    AUserWithoutReadIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_getting(
    scenario: CardStep, adapter: ModelCardAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
