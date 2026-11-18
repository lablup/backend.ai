"""유휴 검사기 검색 — global 역할 게이트를 거친다.

AND, OR, NOT 필터 조합과 페이지 방식은 시나리오로 두지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.idle_checker.request import (
    IdleCheckerFilter,
    IdleCheckerOrder,
    SearchIdleCheckersInput,
)
from ai.backend.common.dto.manager.v2.idle_checker.response import (
    IdleCheckerNode,
    SearchIdleCheckerPayload,
)
from ai.backend.common.dto.manager.v2.idle_checker.types import IdleCheckerOrderField
from ai.backend.manager.api.adapters.idle_checker.adapter import IdleCheckerAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
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
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.idle_checker import (
    CheckersAndACaller,
    SomeCheckersAndSomeone,
    checker_node_of,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Searched = SearchIdleCheckerPayload
type SearchingStep = Scenario[TestSeedingSession, CheckersAndACaller, IdleCheckerAdapter, Searched]


@dataclass(frozen=True)
class SearchingEveryChecker(When[CheckersAndACaller, IdleCheckerAdapter, Searched]):
    """필터 없이 전체를 검색한다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: CheckersAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 필터 없이 전체를 조회합니다",
            english=f"{laid.caller.username} reads everything without a filter",
        )

    @override
    async def call(self, adapter: IdleCheckerAdapter, laid: CheckersAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(SearchIdleCheckersInput())


@dataclass(frozen=True)
class SearchingTheNamedCheckerOrderedAndPaged(
    When[CheckersAndACaller, IdleCheckerAdapter, Searched]
):
    """이름이 지정한 값과 같은 검사기만, 이름의 역순과 페이지 크기로 찾는다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: CheckersAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 이름이 {laid.laid[0].name}인 검사기를 필터로, "
            "이름의 역순 정렬과 페이지 크기를 한 번에 조회합니다",
            english=(
                f"{laid.caller.username} reads with the name {laid.laid[0].name} as the "
                "filter, the name order and a page size in one request"
            ),
        )

    @override
    async def call(self, adapter: IdleCheckerAdapter, laid: CheckersAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                SearchIdleCheckersInput(
                    filter=IdleCheckerFilter(name=StringFilter(equals=laid.laid[0].name)),
                    order=[
                        IdleCheckerOrder(
                            field=IdleCheckerOrderField.NAME, direction=OrderDirection.DESC
                        )
                    ],
                    first=10,
                )
            )


@dataclass(frozen=True)
class TheNamedCheckerAloneComesWhole(Then[CheckersAndACaller, Searched]):
    """필터가 나머지 검사기를 제외해 그 이름의 검사기 하나만 통째로 온다."""

    @override
    def says(self) -> str:
        return Says(
            "필터가 나머지 검사기를 제외해, 그 이름의 검사기 하나만 한 번씩 집계되어 "
            "전체가 반환됩니다",
            english=(
                "the filter excludes the other checkers, so only the one checker of that "
                "name is counted once and comes back whole"
            ),
        )

    @override
    def look(self, laid: CheckersAndACaller, answered: Answered[Searched]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(InsufficientPrivilege, answered.raised)]
        wanted = checker_node_of(laid.laid[0])
        seen: list[Verdict] = [
            Same("total_count", payload.total_count, 1),
            Same("items count", len(payload.items), 1),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]
        for i, node in enumerate(payload.items):
            seen.append(
                Held[IdleCheckerNode](
                    f"items[{i}]",
                    node,
                    SameAs(
                        wanted,
                        Says(
                            "미리 저장한 검사기 전체",
                            english="the whole checker seeded in advance",
                        ),
                    ),
                )
            )
        return seen


@dataclass(frozen=True)
class TheSuperadminSearchesCheckers(
    Scenario[TestSeedingSession, CheckersAndACaller, IdleCheckerAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-searches-idle-checkers-with-a-name-filter-and-an-order"

    @override
    def describe(self) -> str:
        return Says(
            "global 역할로 검사하는 연산이므로 superadmin 이 검사기 하나의 이름을 필터로, "
            "이름의 역순 정렬과 페이지 크기를 한 번에 조회하면, 그 이름의 검사기 하나만 "
            "한 번씩 집계되어 반환됩니다",
            english=(
                "the operation is gated by the global role, so when the superadmin reads "
                "with the name of one checker as the filter, the name order and a page size "
                "in one request, only that checker is counted once and comes back whole"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, CheckersAndACaller]:
        return SomeCheckersAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[CheckersAndACaller, IdleCheckerAdapter, Searched]:
        return SearchingTheNamedCheckerOrderedAndPaged()

    @override
    def then(self) -> Then[CheckersAndACaller, Searched]:
        return TheNamedCheckerAloneComesWhole()


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotSearch(
    Scenario[TestSeedingSession, CheckersAndACaller, IdleCheckerAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-idle-checkers"

    @override
    def describe(self) -> str:
        return Says(
            "global 역할로 검사하는 연산이므로 superadmin 이 아닌 사용자가 검색하면 "
            "역할 부족으로 거부됩니다",
            english=(
                "the operation is gated by the global role, so when a user who is not the "
                "superadmin searches, it is rejected for lack of role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, CheckersAndACaller]:
        return SomeCheckersAndSomeone()

    @override
    def when(self) -> When[CheckersAndACaller, IdleCheckerAdapter, Searched]:
        return SearchingEveryChecker()

    @override
    def then(self) -> Then[CheckersAndACaller, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchingStep] = [
    TheSuperadminSearchesCheckers(),
    AUserWhoIsNotTheSuperadminMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: IdleCheckerAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
