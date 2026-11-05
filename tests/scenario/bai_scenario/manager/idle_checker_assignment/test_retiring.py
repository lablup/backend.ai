"""유휴 검사기 할당 purge — 하나를 지운다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.idle_checker import IdleCheckerAssignmentID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.idle_checker_assignment.request import (
    PurgeIdleCheckerAssignmentInput,
)
from ai.backend.common.dto.manager.v2.idle_checker_assignment.response import (
    PurgeIdleCheckerAssignmentPayload,
)
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
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.idle_checker import (
    AssignmentsAndACaller,
    OneCheckerOnSomeDomains,
    assignment_ids,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type RetiringStep = Scenario[
    TestSeedingSession, AssignmentsAndACaller, IdleCheckerAssignmentAdapter, PurgedOne
]


@dataclass(frozen=True)
class PurgedOne:
    """요청에 넣은 할당 id 와, 그 요청의 답."""

    id: IdleCheckerAssignmentID
    payload: PurgeIdleCheckerAssignmentPayload


@dataclass(frozen=True)
class PurgingTheLaidAssignment(
    When[AssignmentsAndACaller, IdleCheckerAssignmentAdapter, PurgedOne]
):
    """미리 저장한 할당 하나를 purge 한다."""

    @override
    def operation(self) -> str:
        return "purge"

    @override
    def describe(self, laid: AssignmentsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 도메인 {laid.domains[0].name}의 할당을 purge 합니다",
            english=(
                f"{laid.caller.username} purges the assignment of the domain {laid.domains[0].name}"
            ),
        )

    @override
    async def call(
        self, adapter: IdleCheckerAssignmentAdapter, laid: AssignmentsAndACaller
    ) -> PurgedOne:
        ids = await assignment_ids(adapter, laid)
        with ActingAs(laid.caller):
            payload = await adapter.purge(PurgeIdleCheckerAssignmentInput(id=ids[0]))
        return PurgedOne(id=ids[0], payload=payload)


@dataclass(frozen=True)
class ThePurgedAssignmentAnswers(Then[AssignmentsAndACaller, PurgedOne]):
    """요청에 넣은 할당의 id 그대로 반환된다."""

    @override
    def says(self) -> str:
        return Says(
            "요청에 넣은 할당의 id 로 반환됩니다",
            english="the purge is answered with the id of the assignment put in the request",
        )

    @override
    def look(self, laid: AssignmentsAndACaller, answered: Answered[PurgedOne]) -> list[Verdict]:
        answer = answered.response
        if answer is None:
            return [Refused(UnreachableError, answered.raised)]
        return [
            Held[UUID](
                "id",
                answer.payload.id,
                SameAs(
                    answer.id,
                    Says("요청에 넣은 할당", english="the assignment put in the request"),
                ),
            )
        ]


@dataclass(frozen=True)
class TheSuperadminPurgesAnAssignment(
    Scenario[TestSeedingSession, AssignmentsAndACaller, IdleCheckerAssignmentAdapter, PurgedOne]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-purges-an-idle-checker-assignment"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 할당 하나를 purge 하면, 요청에 넣은 할당의 id 로 반환됩니다",
            english=(
                "when the superadmin purges one assignment, the purge is answered with the id "
                "of the assignment put in the request"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AssignmentsAndACaller]:
        return OneCheckerOnSomeDomains(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AssignmentsAndACaller, IdleCheckerAssignmentAdapter, PurgedOne]:
        return PurgingTheLaidAssignment()

    @override
    def then(self) -> Then[AssignmentsAndACaller, PurgedOne]:
        return ThePurgedAssignmentAnswers()


@dataclass(frozen=True)
class APurgeCarryingNoUserIsRefused(
    Scenario[TestSeedingSession, AssignmentsAndACaller, IdleCheckerAssignmentAdapter, PurgedOne]
):
    @override
    def summary(self) -> str:
        return "an-assignment-purge-carrying-no-user-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "할당 둘이 있고 사용자 컨텍스트 없이 하나를 purge 하려 하면, 호출자를 알 수 없어 "
            "거부됩니다",
            english=(
                "when two assignments exist and one is purged without a user context, "
                "it is rejected because the caller cannot be known"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AssignmentsAndACaller]:
        return OneCheckerOnSomeDomains()

    @override
    def when(self) -> When[AssignmentsAndACaller, IdleCheckerAssignmentAdapter, PurgedOne]:
        return PurgingTheLaidAssignment()

    @override
    def then(self) -> Then[AssignmentsAndACaller, PurgedOne]:
        return TheCallIsRefused(UnreachableError)


SCENARIOS: list[RetiringStep] = [
    TheSuperadminPurgesAnAssignment(),
    APurgeCarryingNoUserIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_retiring(
    scenario: RetiringStep, adapter: IdleCheckerAssignmentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
