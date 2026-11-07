"""유휴 검사기 검색 — global 역할 게이트를 거친다.

AND, OR, NOT 필터 조합과 페이지 방식은 시나리오로 두지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter, UUIDFilter
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
from ai.backend.common.dto.manager.v2.idle_checker.types import (
    CheckerTypeFilter,
    IdleCheckerOrderField,
    IdleCheckerTypeDTO,
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
            Same("items count", len(payload.items), len(laid.laid)),
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


@dataclass(frozen=True)
class SearchingCheckersNamedLike(When[CheckersAndACaller, IdleCheckerAdapter, Searched]):
    """이름이 지정한 값과 같은 검사기만 찾는다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: CheckersAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 이름이 {laid.laid[0].name}인 검사기만 조회합니다",
            english=(
                f"{laid.caller.username} reads with the name {laid.laid[0].name} as the filter"
            ),
        )

    @override
    async def call(self, adapter: IdleCheckerAdapter, laid: CheckersAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                SearchIdleCheckersInput(
                    filter=IdleCheckerFilter(name=StringFilter(equals=laid.laid[0].name))
                )
            )


@dataclass(frozen=True)
class SearchingCheckersOfATypeNoCheckerUses(When[CheckersAndACaller, IdleCheckerAdapter, Searched]):
    """심은 검사기가 쓰지 않는 종류를 필터로 찾는다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: CheckersAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 심은 검사기가 쓰지 않는 종류로 조회합니다",
            english=(
                f"{laid.caller.username} reads with a checker type none of the checkers "
                "seeded in advance uses"
            ),
        )

    @override
    async def call(self, adapter: IdleCheckerAdapter, laid: CheckersAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                SearchIdleCheckersInput(
                    filter=IdleCheckerFilter(
                        checker_type=CheckerTypeFilter(equals=IdleCheckerTypeDTO.UTILIZATION)
                    )
                )
            )


@dataclass(frozen=True)
class SearchingCheckersWrittenAfterTheNamedTime(
    When[CheckersAndACaller, IdleCheckerAdapter, Searched]
):
    """심은 검사기가 지어진 시각보다 1초 뒤에 지어진 검사기를 찾는다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: CheckersAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 검사기가 지어진 시각보다 1초 뒤를 조회합니다",
            english=(
                f"{laid.caller.username} reads with a time a second after the checkers were written"
            ),
        )

    @override
    async def call(self, adapter: IdleCheckerAdapter, laid: CheckersAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                SearchIdleCheckersInput(
                    filter=IdleCheckerFilter(
                        created_at=DateTimeFilter(
                            after=laid.laid[0].created_at + timedelta(seconds=1)
                        )
                    )
                )
            )


@dataclass(frozen=True)
class SearchingCheckersUpdatedAfterTheNamedTime(
    When[CheckersAndACaller, IdleCheckerAdapter, Searched]
):
    """심은 검사기가 고쳐진 시각보다 1초 뒤에 고쳐진 검사기를 찾는다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: CheckersAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 검사기가 고쳐진 시각보다 1초 뒤를 조회합니다",
            english=(
                f"{laid.caller.username} reads with a time a second after the checkers were updated"
            ),
        )

    @override
    async def call(self, adapter: IdleCheckerAdapter, laid: CheckersAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                SearchIdleCheckersInput(
                    filter=IdleCheckerFilter(
                        updated_at=DateTimeFilter(
                            after=laid.laid[0].updated_at + timedelta(seconds=1)
                        )
                    )
                )
            )


@dataclass(frozen=True)
class SearchingByTheCheckerId(When[CheckersAndACaller, IdleCheckerAdapter, Searched]):
    """심은 검사기 하나의 id 를 필터로 찾는다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: CheckersAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 미리 저장한 검사기 하나의 id 로 조회합니다",
            english=(
                f"{laid.caller.username} reads with the id of one checker seeded in advance "
                "as the filter"
            ),
        )

    @override
    async def call(self, adapter: IdleCheckerAdapter, laid: CheckersAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                SearchIdleCheckersInput(
                    filter=IdleCheckerFilter(entity_id=UUIDFilter(equals=laid.laid[0].id))
                )
            )


@dataclass(frozen=True)
class OrderingCheckersByName(When[CheckersAndACaller, IdleCheckerAdapter, Searched]):
    """이름의 역순으로 정렬해 찾는다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: CheckersAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 이름의 역순으로 정렬해 조회합니다",
            english=f"{laid.caller.username} reads ordered by name, the reverse direction",
        )

    @override
    async def call(self, adapter: IdleCheckerAdapter, laid: CheckersAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                SearchIdleCheckersInput(
                    order=[
                        IdleCheckerOrder(
                            field=IdleCheckerOrderField.NAME, direction=OrderDirection.DESC
                        )
                    ]
                )
            )


@dataclass(frozen=True)
class TheNamedCheckerAloneComesWhole(Then[CheckersAndACaller, Searched]):
    """미리 저장한 검사기 하나만 한 번씩 집계되어 통째로 온다."""

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 검사기 하나만 한 번씩 집계되어 전체가 반환됩니다",
            english=("only the one checker seeded in advance is counted once and comes back whole"),
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
class NothingComesBack(Then[CheckersAndACaller, Searched]):
    """아무 검사기도 집계되지 않습니다."""

    @override
    def says(self) -> str:
        return Says(
            "아무 검사기도 집계되지 않습니다",
            english="no checker is counted",
        )

    @override
    def look(self, laid: CheckersAndACaller, answered: Answered[Searched]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(InsufficientPrivilege, answered.raised)]
        return [
            Same("total_count", payload.total_count, 0),
            Same("items count", len(payload.items), 0),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheyComeBackInNameOrder(Then[CheckersAndACaller, Searched]):
    """심은 검사기가 이름의 역순으로 모두 한 번씩 집계되어 온다."""

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 검사기가 이름의 역순으로 모두 한 번씩 집계되어 반환됩니다",
            english=(
                "every checker seeded in advance is counted once, in the reverse order "
                "of their names"
            ),
        )

    @override
    def look(self, laid: CheckersAndACaller, answered: Answered[Searched]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(InsufficientPrivilege, answered.raised)]
        expected = sorted(laid.laid, key=lambda one: one.name, reverse=True)
        seen: list[Verdict] = [
            Same("total_count", payload.total_count, len(laid.laid)),
            Same("items count", len(payload.items), len(laid.laid)),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]
        for i, (node, checker) in enumerate(zip(payload.items, expected, strict=False)):
            seen.append(
                Held[IdleCheckerNode](
                    f"items[{i}]",
                    node,
                    SameAs(
                        checker_node_of(checker),
                        Says(
                            f"이름이 {i + 1}번째로 느린 미리 저장한 검사기 전체",
                            english=(
                                f"the whole checker seeded in advance with the number "
                                f"{i + 1} name in the reverse order"
                            ),
                        ),
                    ),
                )
            )
        return seen


@dataclass(frozen=True)
class ANameFilterNarrows(
    Scenario[TestSeedingSession, CheckersAndACaller, IdleCheckerAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-name-filter-narrows-the-answer-to-that-checker"

    @override
    def describe(self) -> str:
        return Says(
            "검사기 여럿 중 하나의 이름을 필터로 조회하면 그 이름의 검사기 하나만 반환됩니다",
            english=(
                "when the call reads with the name of one of several checkers as a filter, "
                "only the one checker of that name comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, CheckersAndACaller]:
        return SomeCheckersAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[CheckersAndACaller, IdleCheckerAdapter, Searched]:
        return SearchingCheckersNamedLike()

    @override
    def then(self) -> Then[CheckersAndACaller, Searched]:
        return TheNamedCheckerAloneComesWhole()


@dataclass(frozen=True)
class ACheckerTypeNoCheckerUsesLeavesNothing(
    Scenario[TestSeedingSession, CheckersAndACaller, IdleCheckerAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-checker-type-no-checker-uses-leaves-nothing"

    @override
    def describe(self) -> str:
        return Says(
            "심은 검사기가 쓰지 않는 종류를 필터로 조회하면 아무 검사기도 반환되지 않습니다",
            english=(
                "when the call reads with a checker type none of the checkers uses as a "
                "filter, no checker comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, CheckersAndACaller]:
        return SomeCheckersAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[CheckersAndACaller, IdleCheckerAdapter, Searched]:
        return SearchingCheckersOfATypeNoCheckerUses()

    @override
    def then(self) -> Then[CheckersAndACaller, Searched]:
        return NothingComesBack()


@dataclass(frozen=True)
class ACreatedAtFilterAfterTheWrittenTimeLeavesNothing(
    Scenario[TestSeedingSession, CheckersAndACaller, IdleCheckerAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-created-at-filter-after-the-written-time-leaves-nothing"

    @override
    def describe(self) -> str:
        return Says(
            "검사기가 지어진 시각보다 뒤를 필터로 조회하면 아무 검사기도 반환되지 않습니다",
            english=(
                "when the call reads with a time after the checkers were written as a "
                "filter, no checker comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, CheckersAndACaller]:
        return SomeCheckersAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[CheckersAndACaller, IdleCheckerAdapter, Searched]:
        return SearchingCheckersWrittenAfterTheNamedTime()

    @override
    def then(self) -> Then[CheckersAndACaller, Searched]:
        return NothingComesBack()


@dataclass(frozen=True)
class AnUpdatedAtFilterAfterTheWrittenTimeLeavesNothing(
    Scenario[TestSeedingSession, CheckersAndACaller, IdleCheckerAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "an-updated-at-filter-after-the-written-time-leaves-nothing"

    @override
    def describe(self) -> str:
        return Says(
            "검사기가 고쳐진 시각보다 뒤를 필터로 조회하면 아무 검사기도 반환되지 않습니다",
            english=(
                "when the call reads with a time after the checkers were updated as a "
                "filter, no checker comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, CheckersAndACaller]:
        return SomeCheckersAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[CheckersAndACaller, IdleCheckerAdapter, Searched]:
        return SearchingCheckersUpdatedAfterTheNamedTime()

    @override
    def then(self) -> Then[CheckersAndACaller, Searched]:
        return NothingComesBack()


@dataclass(frozen=True)
class AnEntityIdFilterNarrows(
    Scenario[TestSeedingSession, CheckersAndACaller, IdleCheckerAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "an-entity-id-filter-narrows-the-answer-to-that-checker"

    @override
    def describe(self) -> str:
        return Says(
            "검사기 하나의 id 를 필터로 조회하면 그 검사기 하나만 반환됩니다",
            english=(
                "when the call reads with the id of one checker as a filter, only that "
                "one checker comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, CheckersAndACaller]:
        return SomeCheckersAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[CheckersAndACaller, IdleCheckerAdapter, Searched]:
        return SearchingByTheCheckerId()

    @override
    def then(self) -> Then[CheckersAndACaller, Searched]:
        return TheNamedCheckerAloneComesWhole()


@dataclass(frozen=True)
class AnOrderByNameBringsThemBackInNameOrder(
    Scenario[TestSeedingSession, CheckersAndACaller, IdleCheckerAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "an-order-by-name-brings-the-checkers-back-in-name-order"

    @override
    def describe(self) -> str:
        return Says(
            "이름의 역순으로 정렬해 조회하면 검사기가 이름의 역순으로 반환됩니다",
            english=(
                "when the call reads ordered by name in the reverse direction, the "
                "checkers come back in the reverse order of their names"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, CheckersAndACaller]:
        return SomeCheckersAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[CheckersAndACaller, IdleCheckerAdapter, Searched]:
        return OrderingCheckersByName()

    @override
    def then(self) -> Then[CheckersAndACaller, Searched]:
        return TheyComeBackInNameOrder()


SCENARIOS: list[SearchingStep] = [
    TheSuperadminSearchesCheckers(started=datetime.now(UTC)),
    AUserWhoIsNotTheSuperadminMayNotSearch(),
    ANameFilterNarrows(),
    ACheckerTypeNoCheckerUsesLeavesNothing(),
    ACreatedAtFilterAfterTheWrittenTimeLeavesNothing(),
    AnUpdatedAtFilterAfterTheWrittenTimeLeavesNothing(),
    AnEntityIdFilterNarrows(),
    AnOrderByNameBringsThemBackInNameOrder(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: IdleCheckerAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
