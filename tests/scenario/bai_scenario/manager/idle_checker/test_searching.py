"""유휴 검사기 검색 — global 역할 게이트를 거친다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.idle_checker.request import SearchIdleCheckersInput
from ai.backend.common.dto.manager.v2.idle_checker.response import (
    IdleCheckerNode,
    SearchIdleCheckerPayload,
)
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
class EveryLaidCheckerComesWhole(Then[CheckersAndACaller, Searched]):
    """심은 검사기가 모두 한 번씩 집계되고, 각각이 통째로 온다. id 순으로 본다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 검사기가 모두 한 번씩 집계되어 전체가 반환됩니다",
            english=(
                "every checker seeded in advance is counted once, and each whole checker comes back"
            ),
        )

    @override
    def look(self, laid: CheckersAndACaller, answered: Answered[Searched]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(InsufficientPrivilege, answered.raised)]
        got = sorted(payload.items, key=lambda one: one.id)
        expected = sorted(laid.laid, key=lambda one: one.id)
        seen: list[Verdict] = [
            Same("total_count", payload.total_count, len(laid.laid)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]
        for i, (node, checker) in enumerate(zip(got, expected, strict=False)):
            seen.append(
                Held[IdleCheckerNode](
                    f"items[{i}]",
                    node,
                    SameAs(
                        checker_node_of(checker),
                        Says(
                            f"{i + 1}번째로 미리 저장한 검사기 전체",
                            english=f"the whole checker seeded in advance number {i + 1}",
                        ),
                    ),
                )
            )
        return seen


@dataclass(frozen=True)
class TheSuperadminSearchesCheckers(
    Scenario[TestSeedingSession, CheckersAndACaller, IdleCheckerAdapter, Searched]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-searches-idle-checkers-without-a-filter"

    @override
    def describe(self) -> str:
        return Says(
            "global 역할로 검사하는 연산이므로 superadmin 이 필터 없이 검색하면, "
            "심은 검사기가 모두 한 번씩 집계되어 반환됩니다",
            english=(
                "the operation is gated by the global role, so when the superadmin searches "
                "without a filter, every checker seeded in advance is counted once and comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, CheckersAndACaller]:
        return SomeCheckersAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[CheckersAndACaller, IdleCheckerAdapter, Searched]:
        return SearchingEveryChecker()

    @override
    def then(self) -> Then[CheckersAndACaller, Searched]:
        return EveryLaidCheckerComesWhole(started=self.started)


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
    TheSuperadminSearchesCheckers(started=datetime.now(UTC)),
    AUserWhoIsNotTheSuperadminMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: IdleCheckerAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
