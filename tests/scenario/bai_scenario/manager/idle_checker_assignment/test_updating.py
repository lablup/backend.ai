"""유휴 검사기 할당 수정 — 켜기와 끄기를 전환한다."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.idle_checker_assignment.request import (
    UpdateIdleCheckerAssignmentInput,
)
from ai.backend.common.dto.manager.v2.idle_checker_assignment.response import (
    IdleCheckerAssignmentNode,
)
from ai.backend.common.dto.manager.v2.idle_checker_assignment.types import IdleCheckerScopeTypeDTO
from ai.backend.common.exception import UnreachableError
from ai.backend.manager.api.adapters.idle_checker_assignment.adapter import (
    IdleCheckerAssignmentAdapter,
)
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
from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.components.idle_checker import (
    AssignmentsAndACaller,
    OneCheckerOnSomeDomains,
    assignment_ids,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type UpdatingStep = Scenario[
    TestSeedingSession,
    AssignmentsAndACaller,
    IdleCheckerAssignmentAdapter,
    IdleCheckerAssignmentNode,
]


@dataclass(frozen=True)
class DisablingTheLaidAssignment(
    When[AssignmentsAndACaller, IdleCheckerAssignmentAdapter, IdleCheckerAssignmentNode]
):
    """미리 저장한 할당 하나를 끈다."""

    @override
    def operation(self) -> str:
        return "update"

    @override
    def describe(self, laid: AssignmentsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 도메인 {laid.domains[0].name}의 할당을 끕니다",
            english=(
                f"{laid.caller.username} disables the assignment of the domain "
                f"{laid.domains[0].name}"
            ),
        )

    @override
    async def call(
        self, adapter: IdleCheckerAssignmentAdapter, laid: AssignmentsAndACaller
    ) -> IdleCheckerAssignmentNode:
        ids = await assignment_ids(adapter, laid)
        with ActingAs(laid.caller):
            payload = await adapter.update(
                UpdateIdleCheckerAssignmentInput(id=ids[0], enabled=False)
            )
        return payload.idle_checker_assignment


@dataclass(frozen=True)
class TheDisabledAssignmentNode(Then[AssignmentsAndACaller, IdleCheckerAssignmentNode]):
    """요청한 할당이 꺼진 상태로 반환된다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "요청한 할당 전체가 꺼진 상태로 반환됩니다",
            english="the whole assignment updated comes back disabled",
        )

    @override
    def look(
        self, laid: AssignmentsAndACaller, answered: Answered[IdleCheckerAssignmentNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(UnreachableError, answered.raised)]
        written = WrittenByThisRun(self.started)
        return [
            Same("scope_type", node.scope_type, IdleCheckerScopeTypeDTO.DOMAIN),
            Held(
                "scope_id",
                node.scope_id,
                SameAs(
                    laid.domains[0].id,
                    Says("미리 저장한 도메인", english="the domain seeded in advance"),
                ),
            ),
            Held(
                "idle_checker_id",
                node.idle_checker_id,
                SameAs(
                    laid.checker.id,
                    Says("미리 저장한 검사기", english="the checker seeded in advance"),
                ),
            ),
            Same("enabled", node.enabled, False),
            Held("created_at", node.created_at, written),
            Held("updated_at", node.updated_at, written),
        ]


@dataclass(frozen=True)
class TheSuperadminDisablesAnAssignment(
    Scenario[
        TestSeedingSession,
        AssignmentsAndACaller,
        IdleCheckerAssignmentAdapter,
        IdleCheckerAssignmentNode,
    ]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-disables-an-idle-checker-assignment"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 할당을 끄면, 요청한 할당이 꺼진 상태로 반환됩니다",
            english=("when the superadmin disables an assignment, it comes back disabled"),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AssignmentsAndACaller]:
        return OneCheckerOnSomeDomains(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[AssignmentsAndACaller, IdleCheckerAssignmentAdapter, IdleCheckerAssignmentNode]:
        return DisablingTheLaidAssignment()

    @override
    def then(self) -> Then[AssignmentsAndACaller, IdleCheckerAssignmentNode]:
        return TheDisabledAssignmentNode(started=self.started)


@dataclass(frozen=True)
class AnUpdateCarryingNoUserIsRefused(
    Scenario[
        TestSeedingSession,
        AssignmentsAndACaller,
        IdleCheckerAssignmentAdapter,
        IdleCheckerAssignmentNode,
    ]
):
    @override
    def summary(self) -> str:
        return "an-assignment-update-carrying-no-user-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "할당 둘이 있고 사용자 컨텍스트 없이 하나를 끄려 하면, 호출자를 알 수 없어 거부됩니다",
            english=(
                "when two assignments exist and one is disabled without a user context, "
                "it is rejected because the caller cannot be known"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AssignmentsAndACaller]:
        return OneCheckerOnSomeDomains()

    @override
    def when(
        self,
    ) -> When[AssignmentsAndACaller, IdleCheckerAssignmentAdapter, IdleCheckerAssignmentNode]:
        return DisablingTheLaidAssignment()

    @override
    def then(self) -> Then[AssignmentsAndACaller, IdleCheckerAssignmentNode]:
        return TheCallIsRefused(UnreachableError)


SCENARIOS: list[UpdatingStep] = [
    TheSuperadminDisablesAnAssignment(started=datetime.now(UTC)),
    AnUpdateCarryingNoUserIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_updating(
    scenario: UpdatingStep, adapter: IdleCheckerAssignmentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
