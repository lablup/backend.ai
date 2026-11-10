"""모델 카드 훑기, 그리고 누가 물을 수 있는가."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.model_card.request import SearchModelCardsInput
from ai.backend.common.dto.manager.v2.model_card.response import SearchModelCardsPayload
from ai.backend.manager.api.adapters.model_card.adapter import ModelCardAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import NothingIsFound, TheCallIsRefused
from bai_scenario.components.domain import ADomainAndACaller, ADomainAndSomeone
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Searched = SearchModelCardsPayload
type CardStep = Scenario[TestSeedingSession, ADomainAndACaller, ModelCardAdapter, Searched]


@dataclass(frozen=True)
class SearchingEveryCard(When[ADomainAndACaller, ModelCardAdapter, Searched]):
    """필터 없이 전체를 훑는다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ADomainAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 필터 없이 전체를 조회합니다",
            english=f"{laid.caller.username} reads every card without a filter",
        )

    @override
    async def call(self, adapter: ModelCardAdapter, laid: ADomainAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(SearchModelCardsInput())


@dataclass(frozen=True)
class NoCardLaidMeansNoneFound(
    Scenario[TestSeedingSession, ADomainAndACaller, ModelCardAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-scenario-that-laid-no-model-card-finds-none"

    @override
    def describe(self) -> str:
        return Says(
            "모델 카드를 하나도 미리 저장하지 않은 상태에서 superadmin 이 전체를 조회하면 응답이 "
            "비어 있습니다",
            english=(
                "with no model card seeded, a superadmin reading every card gets an empty answer"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainAndACaller]:
        return ADomainAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADomainAndACaller, ModelCardAdapter, Searched]:
        return SearchingEveryCard()

    @override
    def then(self) -> Then[ADomainAndACaller, Searched]:
        return NothingIsFound()


@dataclass(frozen=True)
class APlainUserMayNotSearchEveryCard(
    Scenario[TestSeedingSession, ADomainAndACaller, ModelCardAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-every-model-card"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 전체 모델 카드 조회를 요청하면 역할로 차단됩니다",
            english=(
                "when a user who is not the superadmin asks to read every model card, "
                "the role blocks it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainAndACaller]:
        return ADomainAndSomeone()

    @override
    def when(self) -> When[ADomainAndACaller, ModelCardAdapter, Searched]:
        return SearchingEveryCard()

    @override
    def then(self) -> Then[ADomainAndACaller, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[CardStep] = [
    NoCardLaidMeansNoneFound(),
    APlainUserMayNotSearchEveryCard(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_model_card(
    scenario: CardStep, adapter: ModelCardAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
