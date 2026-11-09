"""Loading login sessions by id for a DataLoader, checked per owning user."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.entity.login_session import LoginSessionID
from ai.backend.common.dto.manager.v2.login_session.response import LoginSessionNode
from ai.backend.manager.api.adapters.login_session.adapter import LoginSessionAdapter
from ai.backend.manager.data.auth.login_session_types import LoginSessionData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.login_session import SessionNodeLook, SessionsAndACaller, SessionsOfTwo
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Answer = list[LoginSessionNode | Exception | None]


@dataclass(frozen=True)
class LoadingMine(When[SessionsOfTwo, LoginSessionAdapter, Answer]):
    """The caller loads their active and revoked sessions."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: SessionsOfTwo) -> str:
        return Says(
            f"{laid.caller.username}이 자기 active 세션과 revoked 세션을 id 로 함께 읽습니다",
            english=(
                f"{laid.caller.username} loads their own active and revoked sessions by id together"
            ),
        )

    @override
    async def call(self, adapter: LoginSessionAdapter, laid: SessionsOfTwo) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([
                LoginSessionID(laid.active.id),
                LoginSessionID(laid.revoked.id),
            ])


@dataclass(frozen=True)
class LoadingMineAndAnothers(When[SessionsOfTwo, LoginSessionAdapter, Answer]):
    """The caller loads their active session and the session of another user."""

    @override
    def operation(self) -> str:
        return "batch_load_by_ids"

    @override
    def describe(self, laid: SessionsOfTwo) -> str:
        return Says(
            f"{laid.caller.username}이 자기 active 세션과 {laid.other.username}의 세션을 id 로 "
            "함께 읽습니다",
            english=(
                f"{laid.caller.username} loads their own active session and the session of "
                f"{laid.other.username} by id together"
            ),
        )

    @override
    async def call(self, adapter: LoginSessionAdapter, laid: SessionsOfTwo) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.batch_load_by_ids([
                LoginSessionID(laid.active.id),
                LoginSessionID(laid.others_session.id),
            ])


@dataclass(frozen=True)
class BothNodes(Then[SessionsOfTwo, Answer]):
    """Both sessions come back as nodes, in the order asked."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "두 세션이 요청한 순서대로 옵니다",
            english="both sessions come back in the order asked",
        )

    @override
    def look(self, laid: SessionsOfTwo, answered: Answered[Answer]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        seen: list[Verdict] = [Same("length", len(loaded), 2)]
        look = SessionNodeLook(self.started)
        expected: list[LoginSessionData] = [laid.active, laid.revoked]
        for index, (node, session) in enumerate(zip(loaded, expected, strict=False)):
            if isinstance(node, LoginSessionNode):
                seen.extend(look.verdicts(node, session, f"[{index}]."))
            else:
                seen.append(Same(f"[{index}]", type(node).__name__, "LoginSessionNode"))
        return seen


@dataclass(frozen=True)
class MineAndADenial(Then[SessionsOfTwo, Answer]):
    """The caller's own session comes back; the other user's is denied."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "자기 세션은 오고, 다른 사용자의 세션 자리에는 거부가 옵니다",
            english=(
                "their own session comes back, and a rejection stands in the place of the other "
                "user's session"
            ),
        )

    @override
    def look(self, laid: SessionsOfTwo, answered: Answered[Answer]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        seen: list[Verdict] = [Same("length", len(loaded), 2)]
        first = loaded[0] if loaded else None
        second = loaded[1] if len(loaded) > 1 else None
        if isinstance(first, LoginSessionNode):
            seen.extend(SessionNodeLook(self.started).verdicts(first, laid.active, "[0]."))
        else:
            seen.append(Same("[0]", type(first).__name__, "LoginSessionNode"))
        seen.append(Refused(NotEnoughPermission, second if isinstance(second, Exception) else None))
        return seen


type LoadingStep = Scenario[TestSeedingSession, SessionsOfTwo, LoginSessionAdapter, Answer]


@dataclass(frozen=True)
class AReaderLoadsTheirOwnSessions(
    Scenario[TestSeedingSession, SessionsOfTwo, LoginSessionAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-read-on-themselves-loads-their-own-login-sessions"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ 를 받은 사용자가 자기 세션 둘을 id 로 읽으면 둘 다 옵니다",
            english=(
                "when a user granted READ on their own user loads two of their own sessions by "
                "id, both come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SessionsOfTwo]:
        return SessionsAndACaller(permissions=(Permission.READ,))

    @override
    def when(self) -> When[SessionsOfTwo, LoginSessionAdapter, Answer]:
        return LoadingMine()

    @override
    def then(self) -> Then[SessionsOfTwo, Answer]:
        return BothNodes(started=self.started)


@dataclass(frozen=True)
class AReaderIsDeniedAnotherUsersSession(
    Scenario[TestSeedingSession, SessionsOfTwo, LoginSessionAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-read-on-themselves-is-denied-another-users-login-session"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ 를 받은 사용자가 자기 세션과 다른 사용자의 세션을 함께 읽으면, "
            "다른 사용자의 세션만 거부됩니다",
            english=(
                "when a user granted READ on their own user loads their own session together "
                "with another user's, only the other user's session is rejected"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SessionsOfTwo]:
        return SessionsAndACaller(permissions=(Permission.READ,))

    @override
    def when(self) -> When[SessionsOfTwo, LoginSessionAdapter, Answer]:
        return LoadingMineAndAnothers()

    @override
    def then(self) -> Then[SessionsOfTwo, Answer]:
        return MineAndADenial(started=self.started)


SCENARIOS: list[LoadingStep] = [
    AReaderLoadsTheirOwnSessions(started=datetime.now(UTC)),
    AReaderIsDeniedAnotherUsersSession(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_batch_loading(
    scenario: LoadingStep, adapter: LoginSessionAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
