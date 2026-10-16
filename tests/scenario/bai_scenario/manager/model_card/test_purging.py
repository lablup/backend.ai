"""모델 카드 purge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.dto.manager.v2.model_card.request import DeleteModelCardOptions
from ai.backend.common.dto.manager.v2.model_card.response import DeleteModelCardPayload
from ai.backend.manager.api.adapters.model_card.adapter import ModelCardAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    SameAs,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.model_card import CardsInAProjectAndSomeone, ModelCardsAndACaller
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Purged = DeleteModelCardPayload
type CardStep = Scenario[TestSeedingSession, ModelCardsAndACaller, ModelCardAdapter, Purged]


@dataclass(frozen=True)
class PurgingTheCard(When[ModelCardsAndACaller, ModelCardAdapter, Purged]):
    """미리 만든 카드를 purge 한다. 폴더는 그대로 둔다."""

    @override
    def operation(self) -> str:
        return "purge"

    @override
    def describe(self, laid: ModelCardsAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.cards[0].name}을 purge 함, 폴더는 그대로 둠"

    @override
    async def call(self, adapter: ModelCardAdapter, laid: ModelCardsAndACaller) -> Purged:
        with ActingAs(laid.caller):
            return await adapter.purge(laid.cards[0].id, DeleteModelCardOptions())


@dataclass(frozen=True)
class ThePurgedCardsId(Then[ModelCardsAndACaller, Purged]):
    """purge 한 카드의 id 가 온다."""

    @override
    def says(self) -> str:
        return "purge 한 카드의 id"

    @override
    def look(self, laid: ModelCardsAndACaller, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [Held[UUID]("id", payload.id, SameAs(laid.cards[0].id, "미리 만든 카드"))]


@dataclass(frozen=True)
class AUserGrantedPurgePurgesTheCard(
    Scenario[TestSeedingSession, ModelCardsAndACaller, ModelCardAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-purge-in-the-project-purges-a-model-card"

    @override
    def describe(self) -> str:
        return (
            "프로젝트에서 모델 카드 purge 권한을 받은 사용자가 카드를 purge 하면, "
            "그 카드의 id 가 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, ModelCardsAndACaller]:
        return CardsInAProjectAndSomeone(granted=(Permission.HARD_DELETE,))

    @override
    def when(self) -> When[ModelCardsAndACaller, ModelCardAdapter, Purged]:
        return PurgingTheCard()

    @override
    def then(self) -> Then[ModelCardsAndACaller, Purged]:
        return ThePurgedCardsId()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotPurge(
    Scenario[TestSeedingSession, ModelCardsAndACaller, ModelCardAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-purge-a-model-card"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 모델 카드를 purge 하려 하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[TestSeedingSession, ModelCardsAndACaller]:
        return CardsInAProjectAndSomeone()

    @override
    def when(self) -> When[ModelCardsAndACaller, ModelCardAdapter, Purged]:
        return PurgingTheCard()

    @override
    def then(self) -> Then[ModelCardsAndACaller, Purged]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[CardStep] = [
    AUserGrantedPurgePurgesTheCard(),
    AUserGrantedNothingMayNotPurge(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_purging(
    scenario: CardStep, adapter: ModelCardAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
