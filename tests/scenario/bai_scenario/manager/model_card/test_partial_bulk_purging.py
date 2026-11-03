"""모델 카드 여럿 purge."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.model_card.request import PartialBulkPurgeModelCardsInput
from ai.backend.common.dto.manager.v2.model_card.response import ModelCardNode
from ai.backend.manager.api.adapters.model_card.adapter import ModelCardAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.model_card import (
    CardsInAProjectAndSomeone,
    Mentions,
    ModelCardLook,
    ModelCardsAndACaller,
    NoCardIsProcessed,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Purged = PartialBulkPayload[ModelCardNode]
type CardStep = Scenario[TestSeedingSession, ModelCardsAndACaller, ModelCardAdapter, Purged]


@dataclass(frozen=True)
class PurgingEveryCard(When[ModelCardsAndACaller, ModelCardAdapter, Purged]):
    """미리 만든 카드들을 한 번에 purge 한다. `missing`이 있으면 그 id 도 함께 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "partial_bulk_purge"

    @override
    def describe(self, laid: ModelCardsAndACaller) -> str:
        if self.missing is not None:
            return Says(
                f"{laid.caller.username}이 카드 {len(laid.cards)}개와 없는 id 하나를 한 번에 "
                "purge 합니다",
                english=(
                    f"{laid.caller.username} purges {len(laid.cards)} cards "
                    "and one missing id at once"
                ),
            )
        return Says(
            f"{laid.caller.username}이 카드 {len(laid.cards)}개를 한 번에 purge 합니다",
            english=f"{laid.caller.username} purges {len(laid.cards)} cards at once",
        )

    @override
    async def call(self, adapter: ModelCardAdapter, laid: ModelCardsAndACaller) -> Purged:
        ids: list[UUID] = [card.id for card in laid.cards]
        if self.missing is not None:
            ids.append(self.missing)
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_purge(PartialBulkPurgeModelCardsInput(ids=ids))


@dataclass(frozen=True)
class EveryCardIsPurged(Then[ModelCardsAndACaller, Purged]):
    """대상이 모두 purge 전 모습으로 처리된 목록에 온다. `missing`이 있으면 그 id 만 실패 목록에 온다."""

    started: datetime
    missing: UUID | None = None

    @override
    def says(self) -> str:
        if self.missing is None:
            return Says(
                "대상 카드가 모두 처리된 목록에 오고 실패한 것은 없습니다",
                english="every target card comes back in the processed list and nothing failed",
            )
        return Says(
            "대상 카드가 모두 처리된 목록에 오고, 없는 id 는 대상이 없다는 이유로 실패 목록에 "
            "옵니다",
            english=(
                "every target card comes back in the processed list, and the unknown id comes "
                "back in the failed list as not found"
            ),
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
        if self.missing is None:
            return [*verdicts, Same("failed", payload.failed, [])]
        verdicts.append(Same("failed count", len(payload.failed), 1))
        for failure in payload.failed:
            verdicts += [
                Held[UUID](
                    "failed[0].id",
                    failure.id,
                    SameAs(
                        self.missing,
                        Says("요청에 넣은 없는 id", english="the unknown id put in the request"),
                    ),
                ),
                Held("failed[0].message", failure.message, Mentions("No such model card")),
            ]
        return verdicts


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
class PurgingAnswersForTheMissingOne(
    Scenario[TestSeedingSession, ModelCardsAndACaller, ModelCardAdapter, Purged]
):
    started: datetime
    missing: UUID = UUID(int=1)

    @override
    def summary(self) -> str:
        return "purging-several-answers-for-the-missing-one"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 카드 둘과 없는 id 하나를 한 번에 purge 하면 둘은 처리된 목록에 오고, "
            "없는 id 는 대상이 없다는 이유로 실패 목록에 옵니다. 권한 검사는 superadmin 을 먼저 "
            "통과시키므로 없는 id 가 purge 까지 갑니다",
            english=(
                "when the superadmin purges two cards and one unknown id at once, the two come "
                "back in the processed list and the unknown id comes back in the failed list "
                "as not found. The permission check passes the superadmin first, so the "
                "unknown id reaches the purge"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ModelCardsAndACaller]:
        return CardsInAProjectAndSomeone(count=2, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ModelCardsAndACaller, ModelCardAdapter, Purged]:
        return PurgingEveryCard(missing=self.missing)

    @override
    def then(self) -> Then[ModelCardsAndACaller, Purged]:
        return EveryCardIsPurged(started=self.started, missing=self.missing)


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNone(
    Scenario[TestSeedingSession, ModelCardsAndACaller, ModelCardAdapter, Purged]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purges-none-of-several-model-cards"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 카드 여럿을 한 번에 purge 하려 하면 purge 된 것 "
            "없이 모두 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted nothing tries to purge several cards at once, nothing "
                "is purged and all come back in the failed list for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ModelCardsAndACaller]:
        return CardsInAProjectAndSomeone(count=2)

    @override
    def when(self) -> When[ModelCardsAndACaller, ModelCardAdapter, Purged]:
        return PurgingEveryCard()

    @override
    def then(self) -> Then[ModelCardsAndACaller, Purged]:
        return NoCardIsProcessed(reason="Insufficient permission")


SCENARIOS: list[CardStep] = [
    AUserGrantedPurgePurgesSeveral(started=datetime.now(UTC)),
    PurgingAnswersForTheMissingOne(started=datetime.now(UTC)),
    AUserGrantedNothingPurgesNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_purging(
    scenario: CardStep, adapter: ModelCardAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
