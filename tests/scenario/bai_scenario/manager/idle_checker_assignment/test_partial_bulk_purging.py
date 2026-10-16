"""유휴 검사기 할당 여럿 purge."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.idle_checker import IdleCheckerAssignmentID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.idle_checker_assignment.request import (
    PartialBulkPurgeIdleCheckerAssignmentsInput,
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
type PurgingStep = Scenario[TestSeedingSession, AssignmentsAndACaller, Adapter, AssignmentsAnswered]


@dataclass(frozen=True)
class PurgingEveryAssignment(When[AssignmentsAndACaller, Adapter, AssignmentsAnswered]):
    """심은 할당들을 한 번에 purge 한다. `missing`이 있으면 그 id 도 함께 넣는다."""

    missing: UUID | None = None

    @override
    def operation(self) -> str:
        return "partial_bulk_purge"

    @override
    def describe(self, laid: AssignmentsAndACaller) -> str:
        besides = " 와 없는 id 하나" if self.missing is not None else ""
        return f"{laid.caller.username}이 할당 {len(laid.domains)}개{besides}를 한 번에 purge 함"

    @override
    async def call(self, adapter: Adapter, laid: AssignmentsAndACaller) -> AssignmentsAnswered:
        ids = await assignment_ids(adapter, laid)
        named = [*ids]
        if self.missing is not None:
            named.append(IdleCheckerAssignmentID(self.missing))
        with ActingAs(laid.caller):
            payload = await adapter.partial_bulk_purge(
                PartialBulkPurgeIdleCheckerAssignmentsInput(ids=named)
            )
        return AssignmentsAnswered(ids=ids, payload=payload)


@dataclass(frozen=True)
class TheSuperadminPurgesSeveral(
    Scenario[TestSeedingSession, AssignmentsAndACaller, Adapter, AssignmentsAnswered]
):
    started: datetime
    missing: UUID = UUID(int=1)

    @override
    def summary(self) -> str:
        return "the-superadmin-purges-several-assignments-and-is-answered-for-the-missing-one"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 할당 둘과 없는 id 하나를 한 번에 purge 하면, 둘은 지우기 전 할당으로 "
            "오고 없는 id 는 대상이 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, AssignmentsAndACaller]:
        return OneCheckerOnSomeDomains(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AssignmentsAndACaller, Adapter, AssignmentsAnswered]:
        return PurgingEveryAssignment(missing=self.missing)

    @override
    def then(self) -> Then[AssignmentsAndACaller, AssignmentsAnswered]:
        return EveryAssignmentComesBack(started=self.started, enabled=True, missing=self.missing)


@dataclass(frozen=True)
class AUserGrantedNothingPurgesNone(
    Scenario[TestSeedingSession, AssignmentsAndACaller, Adapter, AssignmentsAnswered]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-purges-none-of-several-assignments"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 할당 여럿을 한 번에 purge 하려 하면, 지운 것 없이 "
            "모두 찾을 수 없다는 이유로 실패 목록에 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, AssignmentsAndACaller]:
        return OneCheckerOnSomeDomains()

    @override
    def when(self) -> When[AssignmentsAndACaller, Adapter, AssignmentsAnswered]:
        return PurgingEveryAssignment()

    @override
    def then(self) -> Then[AssignmentsAndACaller, AssignmentsAnswered]:
        return NoAssignmentIsProcessed(reason="Cannot resolve the given idle_checker key")


SCENARIOS: list[PurgingStep] = [
    TheSuperadminPurgesSeveral(started=datetime.now(UTC)),
    AUserGrantedNothingPurgesNone(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_partial_bulk_purging(
    scenario: PurgingStep, adapter: Adapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
