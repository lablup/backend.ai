"""모델 카드 여럿 수정."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.model_card.request import (
    PartialBulkUpdateModelCardsInput,
    UpdateModelCardInput,
)
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

EDITED = Says("수정한 제목", english="the edited title")

type Edited = PartialBulkPayload[ModelCardNode]
type CardStep = Scenario[TestSeedingSession, ModelCardsAndACaller, ModelCardAdapter, Edited]


@dataclass(frozen=True)
class EditingEveryTitle(When[ModelCardsAndACaller, ModelCardAdapter, Edited]):
    """미리 만든 카드들의 제목을 한 번에 고친다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: ModelCardsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 카드 {len(laid.cards) + len(laid.outside)}개의 제목을 "
            "한 번에 수정합니다",
            english=(
                f"{laid.caller.username} edits the titles of {len(laid.cards) + len(laid.outside)} "
                "cards at once"
            ),
        )

    @override
    async def call(self, adapter: ModelCardAdapter, laid: ModelCardsAndACaller) -> Edited:
        with ActingAs(laid.caller):
            return await adapter.partial_bulk_update(
                PartialBulkUpdateModelCardsInput(
                    items=[
                        UpdateModelCardInput(id=card.id, title=EDITED)
                        for card in (*laid.cards, *laid.outside)
                    ]
                )
            )


@dataclass(frozen=True)
class EveryCardIsEdited(Then[ModelCardsAndACaller, Edited]):
    """대상이 모두 새 제목으로 처리된 목록에 오고, 실패한 것은 없다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "대상 카드가 모두 새 제목으로 오고 실패한 것은 없습니다",
            english="every target card comes back with the new title and nothing failed",
        )

    @override
    def look(self, laid: ModelCardsAndACaller, answered: Answered[Edited]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        look = ModelCardLook(self.started, title=EDITED)
        verdicts: list[Verdict] = [Same("successes count", len(payload.successes), len(laid.cards))]
        for i, (node, card) in enumerate(zip(payload.successes, laid.cards, strict=False)):
            verdicts += look.verdicts(f"successes[{i}].", node, card)
        return [*verdicts, Same("failed", payload.failed, [])]


@dataclass(frozen=True)
class AUserGrantedUpdateEditsSeveral(
    Scenario[TestSeedingSession, ModelCardsAndACaller, ModelCardAdapter, Edited]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-update-edits-several-model-cards"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트에서 모델 카드 읽기와 수정 권한을 받은 사용자가 카드 여럿의 제목을 한 "
            "번에 변경하면 모두 새 제목으로 오고 실패한 것은 없습니다",
            english=(
                "when a user granted read and update permission on model cards in the project "
                "changes the titles of several cards at once, they all come back with the new "
                "title and nothing failed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ModelCardsAndACaller]:
        return CardsInAProjectAndSomeone(count=2, granted=(Permission.READ, Permission.UPDATE))

    @override
    def when(self) -> When[ModelCardsAndACaller, ModelCardAdapter, Edited]:
        return EditingEveryTitle()

    @override
    def then(self) -> Then[ModelCardsAndACaller, Edited]:
        return EveryCardIsEdited(started=self.started)


@dataclass(frozen=True)
class AUserGrantedUpdateEditsNoneOutside(
    Scenario[TestSeedingSession, ModelCardsAndACaller, ModelCardAdapter, Edited]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-card-outside-the-granted-project-is-not-edited"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트에서 모델 카드 읽기와 수정 권한을 받은 사용자가 그 프로젝트의 카드와 권한을 "
            "받지 않은 다른 프로젝트의 카드를 한 번에 수정하면, 그 프로젝트의 카드만 새 제목으로 "
            "오고 다른 프로젝트의 카드는 권한이 없다는 이유로 실패 목록에 옵니다",
            english=(
                "when a user granted read and update permission on model cards in the project "
                "edits a card of that project and a card of another project at once, only the "
                "card of that project comes back with the new title and the other one comes "
                "back in the failed list for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ModelCardsAndACaller]:
        return CardsInAProjectAndSomeone(
            count=1, granted=(Permission.READ, Permission.UPDATE), outside=1
        )

    @override
    def when(self) -> When[ModelCardsAndACaller, ModelCardAdapter, Edited]:
        return EditingEveryTitle()

    @override
    def then(self) -> Then[ModelCardsAndACaller, Edited]:
        return TheOutsideCardIsRefused(started=self.started, title=EDITED)


SCENARIOS: list[CardStep] = [
    AUserGrantedUpdateEditsSeveral(started=datetime.now(UTC)),
    AUserGrantedUpdateEditsNoneOutside(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_editing(
    scenario: CardStep, adapter: ModelCardAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
