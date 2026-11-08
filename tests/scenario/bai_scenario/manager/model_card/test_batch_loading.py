"""모델 카드 여러 개를 id 로 한 번에 읽기: 자리마다 무엇이 오는가."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.entity.model_card import ModelCardID
from ai.backend.common.dto.manager.v2.model_card.response import ModelCardNode
from ai.backend.manager.api.adapters.model_card.adapter import ModelCardAdapter
from ai.backend.manager.data.permission.types import Permission
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
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.model_card import ProjectCards, TwoProjectsOfCardsAndSomeone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = list[ModelCardNode | Exception | None]
type LoadStep = Scenario[TestSeedingSession, ProjectCards, ModelCardAdapter, Answer]


@dataclass(frozen=True)
class LoadingTwoOfTheProject(When[ProjectCards, ModelCardAdapter, Answer]):
    """첫 프로젝트의 카드 둘을 한 번에 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ProjectCards) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.found[0].name}, {laid.found[1].name} 카드를 id 로 "
            "일괄 조회합니다",
            english=(
                f"{laid.caller.username} loads the cards {laid.found[0].name} and "
                f"{laid.found[1].name} by id in one call"
            ),
        )

    @override
    async def call(self, adapter: ModelCardAdapter, laid: ProjectCards) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([
                ModelCardID(laid.found[0].id),
                ModelCardID(laid.found[1].id),
            ])


@dataclass(frozen=True)
class LoadingOneOfEachProject(When[ProjectCards, ModelCardAdapter, Answer]):
    """첫 프로젝트의 카드와 다른 프로젝트의 카드를 한 번에 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: ProjectCards) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.found[0].name}, 다른 프로젝트의 "
            f"{laid.elsewhere.name} 카드를 id 로 일괄 조회합니다",
            english=(
                f"{laid.caller.username} loads the card {laid.found[0].name} and the card "
                f"{laid.elsewhere.name} of the other project by id in one call"
            ),
        )

    @override
    async def call(self, adapter: ModelCardAdapter, laid: ProjectCards) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([
                ModelCardID(laid.found[0].id),
                ModelCardID(laid.elsewhere.id),
            ])


@dataclass(frozen=True)
class BothCardsInOrder(Then[ProjectCards, Answer]):
    """카드 둘이 입력 순서대로 전체가 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "카드 둘이 입력 순서대로 선택 항목과 최소 자원 요구까지 채워져 옵니다",
            english=(
                "both cards come back in input order with their optional fields and minimum "
                "resource requirement filled"
            ),
        )

    @override
    def look(self, laid: ProjectCards, answered: Answered[Answer]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        verdicts: list[Verdict] = [Same("length", len(loaded), 2)]
        for i, card in enumerate(laid.found[:2]):
            node = loaded[i] if i < len(loaded) else None
            if isinstance(node, ModelCardNode):
                verdicts += laid.look(self.started, card).verdicts(f"[{i}].", node, card)
            else:
                verdicts.append(Same(f"[{i}]", type(node).__name__, "ModelCardNode"))
        return verdicts


@dataclass(frozen=True)
class TheCardThenARefusal(Then[ProjectCards, Answer]):
    """읽을 수 있는 카드는 노드로, 다른 프로젝트의 카드 자리는 거부로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "읽을 수 있는 카드는 노드로, 권한이 없는 카드 항목은 권한 부족 거부로 옵니다",
            english=(
                "the readable card comes back as a node and the entry of the card without "
                "permission as a rejection for lack of permission"
            ),
        )

    @override
    def look(self, laid: ProjectCards, answered: Answered[Answer]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [MissingResponse(answered.raised)]
        verdicts: list[Verdict] = [Same("length", len(loaded), 2)]
        if len(loaded) != 2:
            return verdicts
        first, second = loaded
        card = laid.found[0]
        if isinstance(first, ModelCardNode):
            verdicts += laid.look(self.started, card).verdicts("[0].", first, card)
        else:
            verdicts.append(Same("[0]", type(first).__name__, "ModelCardNode"))
        verdicts.append(
            Refused(NotEnoughPermission, second if isinstance(second, Exception) else None)
        )
        return verdicts


@dataclass(frozen=True)
class AReaderLoadsTwoCards(Scenario[TestSeedingSession, ProjectCards, ModelCardAdapter, Answer]):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-model-card-read-loads-cards-by-id-in-order"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트에서 모델 카드 읽기 권한을 받은 사용자가 그 프로젝트의 카드 둘을 id 로 "
            "일괄 조회하면 입력 순서대로 두 카드가 응답으로 옵니다",
            english=(
                "when a user granted model card read in the project loads two cards of that "
                "project by id, both cards come back in input order"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ProjectCards]:
        return TwoProjectsOfCardsAndSomeone(granted=(Permission.READ,))

    @override
    def when(self) -> When[ProjectCards, ModelCardAdapter, Answer]:
        return LoadingTwoOfTheProject()

    @override
    def then(self) -> Then[ProjectCards, Answer]:
        return BothCardsInOrder(started=self.started)


@dataclass(frozen=True)
class ACardOfAnotherProjectGetsARefusal(
    Scenario[TestSeedingSession, ProjectCards, ModelCardAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-card-of-a-project-without-read-gets-a-rejection-in-the-batch"

    @override
    def describe(self) -> str:
        return Says(
            "한 프로젝트에서만 모델 카드 읽기 권한을 받은 사용자가 그 프로젝트의 카드와 다른 "
            "프로젝트의 카드를 함께 일괄 조회하면, 호출은 성공하되 다른 프로젝트의 카드 항목은 "
            "권한 부족으로 거부됩니다",
            english=(
                "when a user granted model card read in only one project loads a card of that "
                "project and a card of another project together, the call succeeds but the "
                "entry of the other project's card is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ProjectCards]:
        return TwoProjectsOfCardsAndSomeone(granted=(Permission.READ,))

    @override
    def when(self) -> When[ProjectCards, ModelCardAdapter, Answer]:
        return LoadingOneOfEachProject()

    @override
    def then(self) -> Then[ProjectCards, Answer]:
        return TheCardThenARefusal(started=self.started)


STARTED = datetime.now(UTC)

SCENARIOS: list[LoadStep] = [
    AReaderLoadsTwoCards(started=STARTED),
    ACardOfAnotherProjectGetsARefusal(started=STARTED),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_batch_loading(
    scenario: LoadStep, adapter: ModelCardAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
