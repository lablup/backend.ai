"""유휴 검사기 할당 스코프 검색 — 도메인 둘 안에서 검색한다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.idle_checker_assignment.request import (
    IdleCheckerAssignmentScopeDTO,
    IdleCheckerScopeRefDTO,
    ScopedSearchIdleCheckerAssignmentsInput,
)
from ai.backend.common.dto.manager.v2.idle_checker_assignment.types import IdleCheckerScopeTypeDTO
from ai.backend.manager.api.adapters.idle_checker_assignment.adapter import (
    IdleCheckerAssignmentAdapter,
)
from ai.backend.manager.errors.permission import NotEnoughPermission
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
class SearchingInTwoDomains(When[AssignmentsAndACaller, IdleCheckerAssignmentAdapter, Searched]):
    """미리 저장한 도메인 둘을 스코프로 검색한다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: AssignmentsAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 도메인 {laid.domains[0].name}과 {laid.domains[1].name}을 "
            "스코프로 조회합니다",
            english=(
                f"{laid.caller.username} reads scoped to the domains {laid.domains[0].name} "
                f"and {laid.domains[1].name}"
            ),
        )

    @override
    async def call(
        self, adapter: IdleCheckerAssignmentAdapter, laid: AssignmentsAndACaller
    ) -> Searched:
        ids = await assignment_ids(adapter, laid)
        with ActingAs(laid.caller):
            payload = await adapter.scoped_search(
                ScopedSearchIdleCheckerAssignmentsInput(
                    scope=IdleCheckerAssignmentScopeDTO(
                        items=[
                            IdleCheckerScopeRefDTO(
                                scope_type=IdleCheckerScopeTypeDTO.DOMAIN, scope_id=domain.id
                            )
                            for domain in laid.domains
                        ]
                    )
                )
            )
        return AssignmentsAnswered(ids=ids, payload=payload)


@dataclass(frozen=True)
class TheSuperadminScopedSearchesAssignments(
    Scenario[TestSeedingSession, AssignmentsAndACaller, IdleCheckerAssignmentAdapter, Searched]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-scoped-searches-idle-checker-assignments"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 도메인 둘을 스코프로 검색하면, 그 도메인들의 할당이 모두 "
            "한 번씩 집계되어 반환됩니다",
            english=(
                "when the superadmin searches scoped to two domains, the assignments of those "
                "domains are all counted once and come back whole"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AssignmentsAndACaller]:
        return OneCheckerOnSomeDomains(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AssignmentsAndACaller, IdleCheckerAssignmentAdapter, Searched]:
        return SearchingInTwoDomains()

    @override
    def then(self) -> Then[AssignmentsAndACaller, Searched]:
        return EveryAssignmentIsListed(started=self.started)


@dataclass(frozen=True)
class AScopedSearchCarryingNoUserIsRefused(
    Scenario[TestSeedingSession, AssignmentsAndACaller, IdleCheckerAssignmentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-scoped-assignment-search-by-a-user-granted-nothing-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "할당 둘이 있고 아무 권한도 받지 않은 사용자가 스코프 검색하면, 권한 부족으로 "
            "거부됩니다",
            english=(
                "when two assignments exist and a user granted nothing searches with a scope, it "
                "is rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AssignmentsAndACaller]:
        return OneCheckerOnSomeDomains()

    @override
    def when(self) -> When[AssignmentsAndACaller, IdleCheckerAssignmentAdapter, Searched]:
        return SearchingInTwoDomains()

    @override
    def then(self) -> Then[AssignmentsAndACaller, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[SearchingStep] = [
    TheSuperadminScopedSearchesAssignments(started=datetime.now(UTC)),
    AScopedSearchCarryingNoUserIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_scoped_searching(
    scenario: SearchingStep,
    adapter: IdleCheckerAssignmentAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
