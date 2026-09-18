"""세션 종료 — 여럿을 한 번에, 세션마다 따로 답한다.

권한 검사는 세션마다이고, 거부된 세션은 실패 목록에 들어가며 호출 자체는 거부되지 않는다.
기다리던 세션은 취소된 목록에, 없는 id는 건너뛴 목록에 들어간다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.session.request import TerminateSessionsInput
from ai.backend.common.dto.manager.v2.session.response import TerminateSessionsPayload
from ai.backend.manager.api.adapters.session.adapter import SessionAdapter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.session import (
    APendingSessionAndSomeone,
    ASessionAndACaller,
    MineIsCancelledTheirsIsRefused,
    SessionsInTwoProjectsAndSomeone,
    TheLaidOneIsCancelledTheUnknownIsSkipped,
    TheSessionIsCancelled,
    TheSessionIsRefused,
    TwoSessionsAndACaller,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type Terminated = TerminateSessionsPayload
type TerminatingStep = Scenario[SeedingSession, Any, SessionAdapter, Terminated]


@dataclass(frozen=True)
class Terminating(When[ASessionAndACaller, SessionAdapter, Terminated]):
    """미리 만들어 둔 세션을 종료한다. ``with_unknown``이면 없는 id를 뒤에 붙인다."""

    with_unknown: bool = False

    @override
    def operation(self) -> str:
        return "terminate"

    @override
    def describe(self, laid: ASessionAndACaller) -> str:
        target = f"{laid.session.name}(와)과 없는 id를" if self.with_unknown else laid.session.name
        return f"{laid.caller.username}이 {target} 종료"

    @override
    async def call(self, adapter: SessionAdapter, laid: ASessionAndACaller) -> Terminated:
        asked = [laid.session.id, uuid4()] if self.with_unknown else [laid.session.id]
        with ActingAs(laid.caller):
            return await adapter.terminate(TerminateSessionsInput(session_ids=asked))


@dataclass(frozen=True)
class TerminatingBoth(When[TwoSessionsAndACaller, SessionAdapter, Terminated]):
    """자기 프로젝트의 세션과 다른 프로젝트의 세션을 한 번에 종료한다."""

    @override
    def operation(self) -> str:
        return "terminate"

    @override
    def describe(self, laid: TwoSessionsAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.mine.name}(와)과 {laid.theirs.name}을 한 번에 종료"

    @override
    async def call(self, adapter: SessionAdapter, laid: TwoSessionsAndACaller) -> Terminated:
        with ActingAs(laid.caller):
            return await adapter.terminate(
                TerminateSessionsInput(session_ids=[laid.mine.id, laid.theirs.id])
            )


@dataclass(frozen=True)
class AUserGrantedTerminationCancelsTheirPendingSession(
    Scenario[SeedingSession, ASessionAndACaller, SessionAdapter, Terminated]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-termination-cancels-their-pending-session"

    @override
    def describe(self) -> str:
        return "그 프로젝트에서 세션을 종료할 수 있는 사용자가 기다리던 세션을 종료하면, 취소된 목록에 담겨 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ASessionAndACaller]:
        return APendingSessionAndSomeone(granted=True)

    @override
    def when(self) -> When[ASessionAndACaller, SessionAdapter, Terminated]:
        return Terminating()

    @override
    def then(self) -> Then[ASessionAndACaller, Terminated]:
        return TheSessionIsCancelled()


@dataclass(frozen=True)
class AUserGrantedNothingHasTheSessionRefused(
    Scenario[SeedingSession, ASessionAndACaller, SessionAdapter, Terminated]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-has-the-session-refused-in-a-terminate"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 세션을 종료하면, 그 세션이 실패 목록에 담겨 반환되고 "
            "아무것도 종료되지 않는다"
        )

    @override
    def given(self) -> Given[SeedingSession, ASessionAndACaller]:
        return APendingSessionAndSomeone()

    @override
    def when(self) -> When[ASessionAndACaller, SessionAdapter, Terminated]:
        return Terminating()

    @override
    def then(self) -> Then[ASessionAndACaller, Terminated]:
        return TheSessionIsRefused()


@dataclass(frozen=True)
class TheOtherProjectsSessionIsRefusedAlone(
    Scenario[SeedingSession, TwoSessionsAndACaller, SessionAdapter, Terminated]
):
    @override
    def summary(self) -> str:
        return "the-other-projects-session-is-refused-alone-while-the-own-one-is-cancelled"

    @override
    def describe(self) -> str:
        return (
            "첫 프로젝트에서만 세션을 종료할 수 있는 사용자가 두 프로젝트의 세션을 한 번에 종료하면, "
            "자기 프로젝트의 세션은 취소된 목록에, 다른 프로젝트의 세션은 실패 목록에 담겨 반환된다"
        )

    @override
    def given(self) -> Given[SeedingSession, TwoSessionsAndACaller]:
        return SessionsInTwoProjectsAndSomeone()

    @override
    def when(self) -> When[TwoSessionsAndACaller, SessionAdapter, Terminated]:
        return TerminatingBoth()

    @override
    def then(self) -> Then[TwoSessionsAndACaller, Terminated]:
        return MineIsCancelledTheirsIsRefused()


@dataclass(frozen=True)
class AnUnknownIdIsSkippedBesideACancelledOne(
    Scenario[SeedingSession, ASessionAndACaller, SessionAdapter, Terminated]
):
    @override
    def summary(self) -> str:
        return "an-unknown-id-in-a-terminate-is-skipped-beside-a-cancelled-one"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 기다리던 세션과 없는 id를 한 번에 종료하면, 세션은 취소된 목록에, "
            "없는 id는 건너뛴 목록에 담겨 반환된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ASessionAndACaller]:
        return APendingSessionAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ASessionAndACaller, SessionAdapter, Terminated]:
        return Terminating(with_unknown=True)

    @override
    def then(self) -> Then[ASessionAndACaller, Terminated]:
        return TheLaidOneIsCancelledTheUnknownIsSkipped()


SCENARIOS: list[TerminatingStep] = [
    AUserGrantedTerminationCancelsTheirPendingSession(),
    AUserGrantedNothingHasTheSessionRefused(),
    TheOtherProjectsSessionIsRefusedAlone(),
    AnUnknownIdIsSkippedBesideACancelledOne(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_terminating(
    scenario: TerminatingStep, adapter: SessionAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
