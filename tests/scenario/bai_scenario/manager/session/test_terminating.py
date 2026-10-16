"""세션 종료 (옛 이름)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.dto.manager.v2.session.request import TerminateSessionsInput
from ai.backend.common.dto.manager.v2.session.response import TerminateSessionsPayload
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    SameAs,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.session import (
    APendingSessionAndACaller,
    APendingSessionAndSomeone,
    Terminator,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Terminated = TerminateSessionsPayload
type SessionStep = Scenario[
    TestSeedingSession, APendingSessionAndACaller, SessionAdapter, Terminated
]


@dataclass(frozen=True)
class TerminatingTheSession(When[APendingSessionAndACaller, SessionAdapter, Terminated]):
    """대기 세션을 옛 이름으로 종료한다."""

    @override
    def operation(self) -> str:
        return "terminate"

    @override
    def describe(self, laid: APendingSessionAndACaller) -> str:
        return f"{laid.caller.username}이 대기 세션을 종료함"

    @override
    async def call(self, adapter: SessionAdapter, laid: APendingSessionAndACaller) -> Terminated:
        with ActingAs(laid.caller):
            return await adapter.terminate(TerminateSessionsInput(session_ids=[laid.session.id]))


@dataclass(frozen=True)
class TheSessionIsCancelled(Then[APendingSessionAndACaller, Terminated]):
    @override
    def says(self) -> str:
        return "대기 세션이 취소된 목록에 오고, 나머지 목록은 비어 있다"

    @override
    def look(
        self, laid: APendingSessionAndACaller, answered: Answered[Terminated]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        verdicts: list[Verdict] = [
            Same("cancelled count", len(payload.cancelled), 1),
            Same("terminating", payload.terminating, []),
            Same("force_terminated", payload.force_terminated, []),
            Same("skipped", payload.skipped, []),
        ]
        for session_id in payload.cancelled:
            verdicts.append(
                Held[UUID]("cancelled[0]", session_id, SameAs(laid.session.id, "대기 세션의 id"))
            )
        return verdicts


@dataclass(frozen=True)
class ASuperadminTerminates(
    Scenario[TestSeedingSession, APendingSessionAndACaller, SessionAdapter, Terminated]
):
    @override
    def summary(self) -> str:
        return "a-superadmin-terminates-a-pending-session"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 대기 세션을 종료하면, 취소된 목록에 온다"

    @override
    def given(self) -> Given[TestSeedingSession, APendingSessionAndACaller]:
        return APendingSessionAndSomeone(who=Terminator.SUPERADMIN)

    @override
    def when(self) -> When[APendingSessionAndACaller, SessionAdapter, Terminated]:
        return TerminatingTheSession()

    @override
    def then(self) -> Then[APendingSessionAndACaller, Terminated]:
        return TheSessionIsCancelled()


@dataclass(frozen=True)
class AUserGrantedNothingIsRefused(
    Scenario[TestSeedingSession, APendingSessionAndACaller, SessionAdapter, Terminated]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-terminate"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 대기 세션을 종료하려 하면, 호출 전체가 거부된다"

    @override
    def given(self) -> Given[TestSeedingSession, APendingSessionAndACaller]:
        return APendingSessionAndSomeone(who=Terminator.NOBODY_GRANTED)

    @override
    def when(self) -> When[APendingSessionAndACaller, SessionAdapter, Terminated]:
        return TerminatingTheSession()

    @override
    def then(self) -> Then[APendingSessionAndACaller, Terminated]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[SessionStep] = [
    ASuperadminTerminates(),
    AUserGrantedNothingIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_terminating(
    scenario: SessionStep, adapter: SessionAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
