"""로그인 클라이언트 종류 검색 — 인증만 확인하고 누구에게나 전체를 답한다.

필터와 페이지 방식은 시나리오로 두지 않는다.
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
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.api.adapters.login_client_type.adapter import LoginClientTypeAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.login_client_type import (
    EveryLaidTypeIsCounted,
    ManyTypesAndACaller,
    ManyTypesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Searched = SearchLoginClientTypesPayload
type SearchingStep = Scenario[
    TestSeedingSession, ManyTypesAndACaller, LoginClientTypeAdapter, Searched
]


@dataclass(frozen=True)
class SearchingEveryType(When[ManyTypesAndACaller, LoginClientTypeAdapter, Searched]):
    """필터도 크기도 없이 전체를 검색한다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyTypesAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 필터 없이 전체를 조회합니다",
            english=f"{laid.caller.username} reads every login client type without a filter",
        )

    @override
    async def call(self, adapter: LoginClientTypeAdapter, laid: ManyTypesAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.search(SearchLoginClientTypesInput())


@dataclass(frozen=True)
class AUserGrantedNothingCountsEveryType(
    Scenario[TestSeedingSession, ManyTypesAndACaller, LoginClientTypeAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-counts-every-login-client-type-laid"

    @override
    def describe(self) -> str:
        return Says(
            (
                "로그인 클라이언트 유형 둘이 있을 때 아무 권한도 없는 사용자가 필터 없이 조회하면 둘 "
                "다 집계됩니다"
            ),
            english=(
                "when two login client types exist and a user granted nothing reads without a "
                "filter, both are counted"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyTypesAndACaller]:
        return ManyTypesAndSomeone(besides=1)

    @override
    def when(self) -> When[ManyTypesAndACaller, LoginClientTypeAdapter, Searched]:
        return SearchingEveryType()

    @override
    def then(self) -> Then[ManyTypesAndACaller, Searched]:
        return EveryLaidTypeIsCounted()


@dataclass(frozen=True)
class SearchingAsNobody(When[ManyTypesAndACaller, LoginClientTypeAdapter, Searched]):
    """사용자 컨텍스트 없이 전체를 검색한다."""

    @override
    def operation(self) -> str:
        return "search"

    @override
    def describe(self, laid: ManyTypesAndACaller) -> str:
        return Says(
            "사용자 컨텍스트 없이 전체를 조회합니다",
            english="reads every login client type without a user context",
        )

    @override
    async def call(self, adapter: LoginClientTypeAdapter, laid: ManyTypesAndACaller) -> Searched:
        return await adapter.search(SearchLoginClientTypesInput())


@dataclass(frozen=True)
class ASearchCarryingNoUserIsRefused(
    Scenario[TestSeedingSession, ManyTypesAndACaller, LoginClientTypeAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-search-carrying-no-user-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "종류 둘이 있고 사용자 컨텍스트 없이 검색하면, 호출자를 알 수 없어 거부됩니다",
            english=(
                "when two login client types exist and they are searched without a user context, "
                "it is rejected because the caller cannot be known"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyTypesAndACaller]:
        return ManyTypesAndSomeone()

    @override
    def when(self) -> When[ManyTypesAndACaller, LoginClientTypeAdapter, Searched]:
        return SearchingAsNobody()

    @override
    def then(self) -> Then[ManyTypesAndACaller, Searched]:
        return TheCallIsRefused(UnreachableError)


SCENARIOS: list[SearchingStep] = [
    AUserGrantedNothingCountsEveryType(),
    ASearchCarryingNoUserIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: LoginClientTypeAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
