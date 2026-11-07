"""유휴 검사기 할당 검색 — global 역할 게이트를 거친다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import UUIDFilter
from ai.backend.common.dto.manager.v2.idle_checker_assignment.request import (
    IdleCheckerAssignmentFilter,
    IdleCheckerAssignmentOrder,
    IdleCheckerAssignmentOrderField,
    SearchIdleCheckerAssignmentsInput,
)
from ai.backend.manager.api.adapters.idle_checker_assignment.adapter import (
    IdleCheckerAssignmentAdapter,
)
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.idle_checker import (
    AssignmentsAndACaller,
    AssignmentsAnswered,
    EveryAssignmentIsListed,
    OneCheckerOnSomeDomains,
    assignment_ids,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Searched = AssignmentsAnswered
type SearchingStep = Scenario[
    TestSeedingSession, AssignmentsAndACaller, IdleCheckerAssignmentAdapter, Searched
]


@dataclass(frozen=True)
class SearchingByTheChecker(When[AssignmentsAndACaller, IdleCheckerAssignmentAdapter, Searched]):
    """미리 저장한 검사기의 할당을, 시간순과 페이지 크기로 검색한다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: AssignmentsAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 검사기를 필터로, 할당의 시간순 정렬과 페이지 크기를 "
            "한 번에 조회합니다",
            english=(
                f"{laid.caller.username} reads with the checker as the filter, the time "
                "order and a page size in one request"
            ),
        )

    @override
    async def call(
        self, adapter: IdleCheckerAssignmentAdapter, laid: AssignmentsAndACaller
    ) -> Searched:
        ids = await assignment_ids(adapter, laid)
        with ActingAs(laid.caller):
            payload = await adapter.admin_search(
                SearchIdleCheckerAssignmentsInput(
                    filter=IdleCheckerAssignmentFilter(
                        idle_checker_id=UUIDFilter(equals=laid.checker.id)
                    ),
                    order=[
                        IdleCheckerAssignmentOrder(
                            field=IdleCheckerAssignmentOrderField.CREATED_AT
                        )
                    ],
                    first=10,
                )
            )
        return AssignmentsAnswered(ids=ids, payload=payload)


@dataclass(frozen=True)
class TheSuperadminSearchesAssignments(
    Scenario[TestSeedingSession, AssignmentsAndACaller, IdleCheckerAssignmentAdapter, Searched]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-searches-idle-checker-assignments"

    @override
    def describe(self) -> str:
        return Says(
            "global 역할로 검사하는 연산이므로 superadmin 이 검사기를 필터로, 할당의 시간순 "
            "정렬과 페이지 크기를 한 번에 검색하면, 그 검사기의 할당이 모두 한 번씩 "
            "집계되어 반환됩니다",
            english=(
                "the operation is gated by the global role, so when the superadmin searches "
                "with the checker as the filter, the time order and a page size in one "
                "request, the assignments of that checker are all counted once and come "
                "back whole"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AssignmentsAndACaller]:
        return OneCheckerOnSomeDomains(role=UserRole.SUPERADMIN, another_checker=True)

    @override
    def when(self) -> When[AssignmentsAndACaller, IdleCheckerAssignmentAdapter, Searched]:
        return SearchingByTheChecker()

    @override
    def then(self) -> Then[AssignmentsAndACaller, Searched]:
        return EveryAssignmentIsListed(started=self.started)


@dataclass(frozen=True)
class ASearchCarryingNoUserIsRefused(
    Scenario[TestSeedingSession, AssignmentsAndACaller, IdleCheckerAssignmentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "an-assignment-search-by-a-user-granted-nothing-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "할당 둘이 있고 아무 권한도 받지 않은 사용자가 검색하면, 역할 부족으로 거부됩니다",
            english=(
                "when two assignments exist and a user granted nothing searches, it is rejected "
                "for lack of role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AssignmentsAndACaller]:
        return OneCheckerOnSomeDomains()

    @override
    def when(self) -> When[AssignmentsAndACaller, IdleCheckerAssignmentAdapter, Searched]:
        return SearchingByTheChecker()

    @override
    def then(self) -> Then[AssignmentsAndACaller, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchingStep] = [
    TheSuperadminSearchesAssignments(started=datetime.now(UTC)),
    ASearchCarryingNoUserIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: IdleCheckerAssignmentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
