"""유휴 검사기 할당 여럿 수정하기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.idle_checker_assignment.request import (
    PartialBulkUpdateIdleCheckerAssignmentsInput,
    UpdateIdleCheckerAssignmentInput,
)
from ai.backend.manager.api.adapters.idle_checker_assignment.adapter import (
    IdleCheckerAssignmentAdapter,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.idle_checker import (
    AssignmentsAndACaller,
    AssignmentsAnswered,
    EveryAssignmentComesBack,
    NoAssignmentIsProcessed,
    OneCheckerOnSomeDomains,
    assignment_ids,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Adapter = IdleCheckerAssignmentAdapter
type EditingStep = Scenario[TestSeedingSession, AssignmentsAndACaller, Adapter, AssignmentsAnswered]


@dataclass(frozen=True)
class DisablingEveryAssignment(When[AssignmentsAndACaller, Adapter, AssignmentsAnswered]):
    """심은 할당들을 한 번에 끈다."""

    @override
    def operation(self) -> str:
        return "partial_bulk_update"

    @override
    def describe(self, laid: AssignmentsAndACaller) -> str:
        return f"{laid.caller.username}이 할당 {len(laid.domains)}개를 한 번에 끔"

    @override
    async def call(self, adapter: Adapter, laid: AssignmentsAndACaller) -> AssignmentsAnswered:
        ids = await assignment_ids(adapter, laid)
        with ActingAs(laid.caller):
            payload = await adapter.partial_bulk_update(
                PartialBulkUpdateIdleCheckerAssignmentsInput(
                    items=[
                        UpdateIdleCheckerAssignmentInput(id=assignment_id, enabled=False)
                        for assignment_id in ids
                    ]
                )
            )
        return AssignmentsAnswered(ids=ids, payload=payload)


@dataclass(frozen=True)
class TheSuperadminDisablesSeveral(
    Scenario[TestSeedingSession, AssignmentsAndACaller, Adapter, AssignmentsAnswered]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-disables-several-assignments-at-once"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 할당 여럿을 한 번에 끄면, 모두 꺼진 할당으로 오고 실패한 것은 없다"

    @override
    def given(self) -> Given[TestSeedingSession, AssignmentsAndACaller]:
        return OneCheckerOnSomeDomains(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AssignmentsAndACaller, Adapter, AssignmentsAnswered]:
        return DisablingEveryAssignment()

    @override
    def then(self) -> Then[AssignmentsAndACaller, AssignmentsAnswered]:
        return EveryAssignmentComesBack(started=self.started, enabled=False)


@dataclass(frozen=True)
class AUserGrantedNothingDisablesNone(
    Scenario[TestSeedingSession, AssignmentsAndACaller, Adapter, AssignmentsAnswered]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-disables-none-of-several-assignments"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 할당 여럿을 한 번에 끄려 하면, 끈 것 없이 모두 "
            "찾을 수 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, AssignmentsAndACaller]:
        return OneCheckerOnSomeDomains()

    @override
    def when(self) -> When[AssignmentsAndACaller, Adapter, AssignmentsAnswered]:
        return DisablingEveryAssignment()

    @override
    def then(self) -> Then[AssignmentsAndACaller, AssignmentsAnswered]:
        return NoAssignmentIsProcessed(reason="Cannot resolve the given idle_checker key")


SCENARIOS: list[EditingStep] = [
    TheSuperadminDisablesSeveral(started=datetime.now(UTC)),
    AUserGrantedNothingDisablesNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_editing(
    scenario: EditingStep, adapter: Adapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
