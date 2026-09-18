"""로그인 클라이언트 종류 검색 — 인증만 확인하고 누구에게나 전체를 답하며, 앞에서 청한 만큼만 자른다.

필터는 시나리오로 두지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.login_client_type.request import (
    SearchLoginClientTypesInput,
)
from ai.backend.common.dto.manager.v2.login_client_type.response import (
    SearchLoginClientTypesPayload,
)
from ai.backend.manager.api.adapters.login_client_type.adapter import LoginClientTypeAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.login_client_type import (
    EveryLaidTypeIsCounted,
    ManyTypesAndACaller,
    ManyTypesAndSomeone,
    TheFirstPageOfTypes,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type Searched = SearchLoginClientTypesPayload
type SearchingStep = Scenario[SeedingSession, ManyTypesAndACaller, LoginClientTypeAdapter, Searched]


@dataclass(frozen=True)
class SearchingEveryType(When[ManyTypesAndACaller, LoginClientTypeAdapter, Searched]):
    """필터도 크기도 없이 전체를 검색한다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyTypesAndACaller) -> str:
        return f"{laid.caller.username}이 필터 없이 전체 조회"

    @override
    async def call(self, adapter: LoginClientTypeAdapter, laid: ManyTypesAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search(SearchLoginClientTypesInput())


@dataclass(frozen=True)
class SearchingTheFirst(When[ManyTypesAndACaller, LoginClientTypeAdapter, Searched]):
    """앞에서 몇 건만 청한다. 크기가 아니라 커서 쪽의 개수다."""

    first: int

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyTypesAndACaller) -> str:
        return f"{laid.caller.username}이 앞에서 {self.first}건만 청해 조회"

    @override
    async def call(self, adapter: LoginClientTypeAdapter, laid: ManyTypesAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search(SearchLoginClientTypesInput(first=self.first))


@dataclass(frozen=True)
class AUserGrantedNothingCountsEveryType(
    Scenario[SeedingSession, ManyTypesAndACaller, LoginClientTypeAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-counts-every-login-client-type-laid"

    @override
    def describe(self) -> str:
        return "종류 둘이 있을 때 아무 권한도 없는 사용자가 필터 없이 조회하면 둘 다 집계된다"

    @override
    def given(self) -> Given[SeedingSession, ManyTypesAndACaller]:
        return ManyTypesAndSomeone(besides=1)

    @override
    def when(self) -> When[ManyTypesAndACaller, LoginClientTypeAdapter, Searched]:
        return SearchingEveryType()

    @override
    def then(self) -> Then[ManyTypesAndACaller, Searched]:
        return EveryLaidTypeIsCounted()


@dataclass(frozen=True)
class AskingForTheFirstTwoGivesTwo(
    Scenario[SeedingSession, ManyTypesAndACaller, LoginClientTypeAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "asking-for-the-first-two-login-client-types-answers-two-and-a-next-page"

    @override
    def describe(self) -> str:
        return "종류 셋이 있을 때 앞에서 두 건만 청해 조회하면 두 건이 반환되고 다음 페이지가 있다고 응답한다"

    @override
    def given(self) -> Given[SeedingSession, ManyTypesAndACaller]:
        return ManyTypesAndSomeone(besides=2)

    @override
    def when(self) -> When[ManyTypesAndACaller, LoginClientTypeAdapter, Searched]:
        return SearchingTheFirst(first=2)

    @override
    def then(self) -> Then[ManyTypesAndACaller, Searched]:
        return TheFirstPageOfTypes(size=2)


SCENARIOS: list[SearchingStep] = [
    AUserGrantedNothingCountsEveryType(),
    AskingForTheFirstTwoGivesTwo(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: LoginClientTypeAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
