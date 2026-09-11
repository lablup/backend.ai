"""로그인 클라이언트 종류 훑기 — 이름 필터가 무엇을 좁히고, 기본 페이지 크기가 쉰이다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest
from bai_scenario.components.login_client_type import (
    EveryLaidTypeIsCounted,
    ManyTypesAndACaller,
    ManyTypesAndSomeone,
    OnlyTheNamedTypeIsLeft,
    TheFirstPageOfTypes,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.login_client_type.request import (
    LoginClientTypeFilter,
    SearchLoginClientTypesInput,
)
from ai.backend.common.dto.manager.v2.login_client_type.response import (
    SearchLoginClientTypesPayload,
)
from ai.backend.manager.api.adapters.login_client_type.adapter import LoginClientTypeAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When

DEFAULT_PAGE = 50

type Searched = SearchLoginClientTypesPayload
type SearchingStep = Scenario[SeedingSession, ManyTypesAndACaller, LoginClientTypeAdapter, Searched]


@dataclass(frozen=True)
class SearchingEveryType(When[ManyTypesAndACaller, LoginClientTypeAdapter, Searched]):
    """필터도 크기도 없이 전체를 훑는다."""

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
class SearchingByName(When[ManyTypesAndACaller, LoginClientTypeAdapter, Searched]):
    """심은 것 중 하나의 이름으로 걸러 훑는다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyTypesAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.named.name}으로 걸러 조회"

    @override
    async def call(self, adapter: LoginClientTypeAdapter, laid: ManyTypesAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search(
                SearchLoginClientTypesInput(
                    filter=LoginClientTypeFilter(name=StringFilter(equals=laid.named.name))
                )
            )


@dataclass(frozen=True)
class AUserGrantedNothingCountsEveryType(
    Scenario[SeedingSession, ManyTypesAndACaller, LoginClientTypeAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-counts-every-login-client-type-laid"

    @override
    def describe(self) -> str:
        return "종류 둘이 있을 때 아무 권한도 받지 않은 사용자가 필터 없이 조회하면 둘을 모두 센다"

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
class ANameFilterNarrows(
    Scenario[SeedingSession, ManyTypesAndACaller, LoginClientTypeAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-name-filter-narrows-the-answer-to-the-login-client-type-it-names"

    @override
    def describe(self) -> str:
        return "종류 여럿 중 하나의 이름으로 걸러 조회하면, 답에는 그 이름의 것만 남는다"

    @override
    def given(self) -> Given[SeedingSession, ManyTypesAndACaller]:
        return ManyTypesAndSomeone(besides=2)

    @override
    def when(self) -> When[ManyTypesAndACaller, LoginClientTypeAdapter, Searched]:
        return SearchingByName()

    @override
    def then(self) -> Then[ManyTypesAndACaller, Searched]:
        return OnlyTheNamedTypeIsLeft()


@dataclass(frozen=True)
class OmittingThePageSizeGivesFifty(
    Scenario[SeedingSession, ManyTypesAndACaller, LoginClientTypeAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "omitting-the-page-size-answers-fifty-login-client-types-and-a-next-page"

    @override
    def describe(self) -> str:
        return (
            "종류 쉰하나가 있을 때 크기 없이 조회하면 쉰 건까지 오고 다음 쪽이 있다고 답한다. "
            "기본 페이지 크기가 다른 카탈로그의 열이 아니라 쉰이다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyTypesAndACaller]:
        return ManyTypesAndSomeone(besides=DEFAULT_PAGE)

    @override
    def when(self) -> When[ManyTypesAndACaller, LoginClientTypeAdapter, Searched]:
        return SearchingEveryType()

    @override
    def then(self) -> Then[ManyTypesAndACaller, Searched]:
        return TheFirstPageOfTypes(size=DEFAULT_PAGE)


SCENARIOS: list[SearchingStep] = [
    AUserGrantedNothingCountsEveryType(),
    ANameFilterNarrows(),
    OmittingThePageSizeGivesFifty(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: LoginClientTypeAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
