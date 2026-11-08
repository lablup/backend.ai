"""모델 카드 여럿 삭제 (이전 이름의 호출)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.dto.manager.v2.model_card.request import (
    BulkDeleteModelCardsInput,
    DeleteModelCardOptions,
)
from ai.backend.common.dto.manager.v2.model_card.response import BulkDeleteModelCardsPayload
from ai.backend.manager.api.adapters.model_card.adapter import ModelCardAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, RefusedItem
from bai_scenario.components.model_card import (
    PERMISSION_REASON,
    CardsInAProjectAndSomeone,
    ModelCardsAndACaller,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Deleted = BulkDeleteModelCardsPayload
type CardStep = Scenario[TestSeedingSession, ModelCardsAndACaller, ModelCardAdapter, Deleted]

TARGET = Says("대상 카드", english="the target card")


@dataclass(frozen=True)
class DeletingEveryCard(When[ModelCardsAndACaller, ModelCardAdapter, Deleted]):
    """미리 만든 카드들을 다른 프로젝트의 카드까지 함께 한 번에 삭제한다. vfolder 는 남긴다."""

    @override
    def operation(self) -> str:
        return "admin_bulk_delete"

    @override
    def describe(self, laid: ModelCardsAndACaller) -> str:
        count = len(laid.cards) + len(laid.outside)
        return Says(
            f"{laid.caller.username}이 카드 {count}개를 vfolder 는 남기고 한 번에 삭제합니다",
            english=(
                f"{laid.caller.username} deletes {count} cards at once, keeping their vfolders"
            ),
        )

    @override
    async def call(self, adapter: ModelCardAdapter, laid: ModelCardsAndACaller) -> Deleted:
        ids = [card.id for card in (*laid.cards, *laid.outside)]
        with ActingAs(laid.caller):
            return await adapter.admin_bulk_delete(
                BulkDeleteModelCardsInput(ids=ids),
                DeleteModelCardOptions(delete_associated_vfolder=False),
            )


@dataclass(frozen=True)
class EveryCardIsDeleted(Then[ModelCardsAndACaller, Deleted]):
    """대상 카드의 id 가 모두 처리된 목록에 오고, 실패한 것은 없다."""

    @override
    def says(self) -> str:
        return Says(
            "대상 카드의 id 가 모두 처리된 목록에 오고 실패한 것은 없습니다",
            english="the id of every target card comes back in the processed list and nothing failed",
        )

    @override
    def look(self, laid: ModelCardsAndACaller, answered: Answered[Deleted]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        verdicts: list[Verdict] = [Same("successes count", len(payload.successes), len(laid.cards))]
        for i, (got, card) in enumerate(zip(payload.successes, laid.cards, strict=False)):
            verdicts.append(Held[UUID](f"successes[{i}]", got, SameAs(card.id, TARGET)))
        return [*verdicts, Same("failed", payload.failed, [])]


@dataclass(frozen=True)
class OnlyTheOutsideCardIsKept(Then[ModelCardsAndACaller, Deleted]):
    """그 프로젝트의 카드 id 는 처리된 목록에, 다른 프로젝트의 카드는 실패 목록에 온다."""

    @override
    def says(self) -> str:
        return Says(
            "그 프로젝트의 카드 id 는 처리된 목록에 오고, 다른 프로젝트의 카드만 권한이 없다는 "
            "이유로 실패 목록에 옵니다",
            english=(
                "the id of the card of that project comes back in the processed list, and only "
                "the card in the other project comes back in the failed list for lack of "
                "permission"
            ),
        )

    @override
    def look(self, laid: ModelCardsAndACaller, answered: Answered[Deleted]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [Same("successes count", len(payload.successes), len(laid.cards))]
        for i, (got, card) in enumerate(zip(payload.successes, laid.cards, strict=False)):
            verdicts.append(Held[UUID](f"successes[{i}]", got, SameAs(card.id, TARGET)))
        verdicts.append(Same("failed count", len(payload.failed), len(laid.outside)))
        for i, (failure, card) in enumerate(zip(payload.failed, laid.outside, strict=False)):
            verdicts += [
                Held[UUID](
                    f"failed[{i}].card_id",
                    failure.card_id,
                    SameAs(
                        card.id,
                        Says("다른 프로젝트의 카드", english="the card in the other project"),
                    ),
                ),
                RefusedItem(
                    f"failed[{i}].message", NotEnoughPermission, PERMISSION_REASON, failure.message
                ),
            ]
        return verdicts


@dataclass(frozen=True)
class AUserGrantedPurgeDeletesSeveral(
    Scenario[TestSeedingSession, ModelCardsAndACaller, ModelCardAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-purge-deletes-several-model-cards"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트에서 모델 카드 purge 권한을 받은 사용자가 카드 둘을 한 번에 삭제하면 둘의 "
            "id 가 처리된 목록에 오고 실패한 것은 없습니다",
            english=(
                "when a user granted purge permission on model cards in the project deletes two "
                "cards at once, the ids of both come back in the processed list and nothing failed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ModelCardsAndACaller]:
        return CardsInAProjectAndSomeone(count=2, granted=(Permission.HARD_DELETE,))

    @override
    def when(self) -> When[ModelCardsAndACaller, ModelCardAdapter, Deleted]:
        return DeletingEveryCard()

    @override
    def then(self) -> Then[ModelCardsAndACaller, Deleted]:
        return EveryCardIsDeleted()


@dataclass(frozen=True)
class ACardOutsideTheGrantedProjectIsNotDeleted(
    Scenario[TestSeedingSession, ModelCardsAndACaller, ModelCardAdapter, Deleted]
):
    @override
    def summary(self) -> str:
        return "a-card-outside-the-granted-project-is-not-deleted"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트에서 모델 카드 purge 권한을 받은 사용자가 그 프로젝트의 카드와 권한을 받지 "
            "않은 다른 프로젝트의 카드를 한 번에 삭제하면, 그 프로젝트의 카드만 처리된 목록에 "
            "오고 다른 프로젝트의 카드는 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted purge permission on model cards in the project deletes a "
                "card of that project and a card of another project at once, only the card of "
                "that project comes back in the processed list and the other one comes back in "
                "the failed list for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ModelCardsAndACaller]:
        return CardsInAProjectAndSomeone(count=1, granted=(Permission.HARD_DELETE,), outside=1)

    @override
    def when(self) -> When[ModelCardsAndACaller, ModelCardAdapter, Deleted]:
        return DeletingEveryCard()

    @override
    def then(self) -> Then[ModelCardsAndACaller, Deleted]:
        return OnlyTheOutsideCardIsKept()


SCENARIOS: list[CardStep] = [
    AUserGrantedPurgeDeletesSeveral(),
    ACardOutsideTheGrantedProjectIsNotDeleted(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_bulk_deleting(
    scenario: CardStep, adapter: ModelCardAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
