"""모델 카드 수정."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.model_card.request import UpdateModelCardInput
from ai.backend.common.dto.manager.v2.model_card.response import ModelCardNode
from ai.backend.manager.api.adapters.model_card.adapter import ModelCardAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.model_card import (
    CardsInAProjectAndSomeone,
    ModelCardLook,
    ModelCardsAndACaller,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

EDITED = "고쳐 쓴 제목"

type CardStep = Scenario[TestSeedingSession, ModelCardsAndACaller, ModelCardAdapter, ModelCardNode]


@dataclass(frozen=True)
class EditingTheTitle(When[ModelCardsAndACaller, ModelCardAdapter, ModelCardNode]):
    """미리 만든 카드의 제목을 고친다. 답이 실은 노드를 벗겨서 준다."""

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: ModelCardsAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.cards[0].name}의 제목을 고침"

    @override
    async def call(self, adapter: ModelCardAdapter, laid: ModelCardsAndACaller) -> ModelCardNode:
        with ActingAs(laid.caller):
            payload = await adapter.update(UpdateModelCardInput(id=laid.cards[0].id, title=EDITED))
        return payload.model_card


@dataclass(frozen=True)
class TheEditedCard(Then[ModelCardsAndACaller, ModelCardNode]):
    """제목만 새 값이 되고 나머지는 그대로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "제목은 새 값이 되고 나머지는 그대로인 카드 전체"

    @override
    def look(self, laid: ModelCardsAndACaller, answered: Answered[ModelCardNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [MissingResponse(answered.raised)]
        look = ModelCardLook(self.started, title=EDITED)
        return look.verdicts("", node, laid.cards[0])


@dataclass(frozen=True)
class AUserGrantedUpdateEditsTheTitle(
    Scenario[TestSeedingSession, ModelCardsAndACaller, ModelCardAdapter, ModelCardNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-update-in-the-project-edits-a-model-card"

    @override
    def describe(self) -> str:
        return (
            "프로젝트에서 모델 카드 읽기와 수정 권한을 받은 사용자가 카드의 제목을 바꾸면, "
            "제목은 새 값이 되고 나머지는 그대로 남는다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ModelCardsAndACaller]:
        return CardsInAProjectAndSomeone(granted=(Permission.READ, Permission.UPDATE))

    @override
    def when(self) -> When[ModelCardsAndACaller, ModelCardAdapter, ModelCardNode]:
        return EditingTheTitle()

    @override
    def then(self) -> Then[ModelCardsAndACaller, ModelCardNode]:
        return TheEditedCard(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotEdit(
    Scenario[TestSeedingSession, ModelCardsAndACaller, ModelCardAdapter, ModelCardNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-edit-a-model-card"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 모델 카드를 수정하려 하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[TestSeedingSession, ModelCardsAndACaller]:
        return CardsInAProjectAndSomeone()

    @override
    def when(self) -> When[ModelCardsAndACaller, ModelCardAdapter, ModelCardNode]:
        return EditingTheTitle()

    @override
    def then(self) -> Then[ModelCardsAndACaller, ModelCardNode]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[CardStep] = [
    AUserGrantedUpdateEditsTheTitle(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotEdit(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_editing(
    scenario: CardStep, adapter: ModelCardAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
