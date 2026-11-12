"""모델 카드 여럿 purge."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.model_card.request import PartialBulkPurgeModelCardsInput
from ai.backend.common.dto.manager.v2.model_card.response import ModelCardNode
from ai.backend.manager.api.adapters.model_card.adapter import ModelCardAdapter
from ai.backend.manager.data.permission.types import Permission
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
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.model_card import (
    CardsInAProjectAndSomeone,
    ModelCardLook,
    ModelCardsAndACaller,
    TheOutsideCardIsRefused,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Purged = PartialBulkPayload[ModelCardNode]
type CardStep = Scenario[TestSeedingSession, ModelCardsAndACaller, ModelCardAdapter, Purged]


@dataclass(frozen=True)
class PurgingEveryCard(When[ModelCardsAndACaller, ModelCardAdapter, Purged]):
    """미리 만든 카드들을 다른 프로젝트의 카드까지 함께 한 번에 purge 한다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_purge"

    @override
    def describe(self, laid: ModelCardsAndACaller) -> str:
        count = len(laid.cards) + len(laid.outside)
        return Says(
            f"{laid.caller.username}이 카드 {count}개를 한 번에 purge 합니다",
            english=f"{laid.caller.username} purges {count} cards at once",
        )

    @override
    async def call(self, adapter: ModelCardAdapter, laid: ModelCardsAndACaller) -> Purged:
        ids = [card.id for card in (*laid.cards, *laid.outside)]
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_purge(PartialBulkPurgeModelCardsInput(ids=ids))


@dataclass(frozen=True)
class EveryCardIsPurged(Then[ModelCardsAndACaller, Purged]):
    """대상이 모두 purge 전 모습으로 처리된 목록에 오고, 실패한 것은 없다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "대상 카드가 모두 처리된 목록에 오고 실패한 것은 없습니다",
            english="every target card comes back in the processed list and nothing failed",
        )

    @override
    def look(self, laid: ModelCardsAndACaller, answered: Answered[Purged]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        look = ModelCardLook(self.started)
        verdicts: list[Verdict] = [Same("successes count", len(payload.successes), len(laid.cards))]
        for i, (node, card) in enumerate(zip(payload.successes, laid.cards, strict=False)):
            verdicts += look.verdicts(f"successes[{i}].", node, card)
        return [*verdicts, Same("failed", payload.failed, [])]


@dataclass(frozen=True)
class AUserGrantedPurgePurgesSeveral(
    Scenario[TestSeedingSession, ModelCardsAndACaller, ModelCardAdapter, Purged]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-purge-purges-several-model-cards"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트에서 모델 카드 purge 권한을 받은 사용자가 카드 둘을 한 번에 purge 하면 "
            "둘 다 처리된 목록에 오고 실패한 것은 없습니다",
            english=(
                "when a user granted purge permission on model cards in the project purges "
                "two cards at once, both come back in the processed list and nothing failed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ModelCardsAndACaller]:
        return CardsInAProjectAndSomeone(count=2, granted=(Permission.HARD_DELETE,))

    @override
    def when(self) -> When[ModelCardsAndACaller, ModelCardAdapter, Purged]:
        return PurgingEveryCard()

    @override
    def then(self) -> Then[ModelCardsAndACaller, Purged]:
        return EveryCardIsPurged(started=self.started)


@dataclass(frozen=True)
class ACardOutsideTheGrantedProjectIsNotPurged(
    Scenario[TestSeedingSession, ModelCardsAndACaller, ModelCardAdapter, Purged]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-card-outside-the-granted-project-is-not-purged"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트에서 모델 카드 purge 권한을 받은 사용자가 그 프로젝트의 카드와 권한을 받지 "
            "않은 다른 프로젝트의 카드를 한 번에 purge 하면, 그 프로젝트의 카드만 처리된 목록에 "
            "오고 다른 프로젝트의 카드는 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted purge permission on model cards in the project purges a "
                "card of that project and a card of another project at once, only the card of "
                "that project comes back in the processed list and the other one comes back in "
                "the failed list for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ModelCardsAndACaller]:
        return CardsInAProjectAndSomeone(count=1, granted=(Permission.HARD_DELETE,), outside=1)

    @override
    def when(self) -> When[ModelCardsAndACaller, ModelCardAdapter, Purged]:
        return PurgingEveryCard()

    @override
    def then(self) -> Then[ModelCardsAndACaller, Purged]:
        return TheOutsideCardIsRefused(started=self.started)


SCENARIOS: list[CardStep] = [
    AUserGrantedPurgePurgesSeveral(started=datetime.now(UTC)),
    ACardOutsideTheGrantedProjectIsNotPurged(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_purging(
    scenario: CardStep, adapter: ModelCardAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
