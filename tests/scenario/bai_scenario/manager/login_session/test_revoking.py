"""Revoking a login session: the caller's own through their grant, anyone's through the global role."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.login_session.request import (
    AdminRevokeLoginSessionInput,
    MyRevokeLoginSessionInput,
)
from ai.backend.common.dto.manager.v2.login_session.response import RevokeLoginSessionPayload
from ai.backend.manager.api.adapters.login_session.adapter import LoginSessionAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.auth import InsufficientPrivilege
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
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.login_session import SessionsAndACaller, SessionsOfTwo
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario


@dataclass(frozen=True)
class RevokingMine(When[SessionsOfTwo, LoginSessionAdapter, RevokeLoginSessionPayload]):
    """The caller revokes the active session of the user holding three."""

    @override
    def operation(self) -> str:
        return "my_revoke"

    @override
    def describe(self, laid: SessionsOfTwo) -> str:
        return Says(
            f"{laid.caller.username}이 자기 active 세션을 회수합니다",
            english=f"{laid.caller.username} revokes their own active login session",
        )

    @override
    async def call(
        self, adapter: LoginSessionAdapter, laid: SessionsOfTwo
    ) -> RevokeLoginSessionPayload:
        with ActingAs(laid.caller):
            return await adapter.my_revoke(MyRevokeLoginSessionInput(session_id=laid.active.id))


@dataclass(frozen=True)
class RevokingAsAdmin(When[SessionsOfTwo, LoginSessionAdapter, RevokeLoginSessionPayload]):
    """The caller revokes the active session of the user holding three, through the admin call."""

    @override
    def operation(self) -> str:
        return "admin_revoke"

    @override
    def describe(self, laid: SessionsOfTwo) -> str:
        return Says(
            f"{laid.caller.username}이 관리자 호출로 {laid.owner.username}의 active 세션을 "
            "회수합니다",
            english=(
                f"{laid.caller.username} revokes the active login session of "
                f"{laid.owner.username} through the admin call"
            ),
        )

    @override
    async def call(
        self, adapter: LoginSessionAdapter, laid: SessionsOfTwo
    ) -> RevokeLoginSessionPayload:
        with ActingAs(laid.caller):
            return await adapter.admin_revoke(
                AdminRevokeLoginSessionInput(session_id=laid.active.id)
            )


@dataclass(frozen=True)
class Revoked(Then[SessionsOfTwo, RevokeLoginSessionPayload]):
    """The revoke succeeds."""

    @override
    def says(self) -> str:
        return Says("회수가 성공합니다", english="the revoke succeeds")

    @override
    def look(
        self, laid: SessionsOfTwo, answered: Answered[RevokeLoginSessionPayload]
    ) -> list[Verdict]:
        answer = answered.response
        if answer is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [Same("success", answer.success, True)]


type RevokingStep = Scenario[
    TestSeedingSession, SessionsOfTwo, LoginSessionAdapter, RevokeLoginSessionPayload
]


@dataclass(frozen=True)
class AnUpdaterRevokesTheirOwnSession(
    Scenario[TestSeedingSession, SessionsOfTwo, LoginSessionAdapter, RevokeLoginSessionPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-update-on-themselves-revokes-their-own-login-session"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ 와 UPDATE 를 받은 사용자가 자기 세션을 회수하면 성공합니다",
            english=(
                "a user granted READ and UPDATE on their own user revokes their own login session"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SessionsOfTwo]:
        return SessionsAndACaller(permissions=(Permission.READ, Permission.UPDATE))

    @override
    def when(self) -> When[SessionsOfTwo, LoginSessionAdapter, RevokeLoginSessionPayload]:
        return RevokingMine()

    @override
    def then(self) -> Then[SessionsOfTwo, RevokeLoginSessionPayload]:
        return Revoked()


@dataclass(frozen=True)
class AReaderMayNotRevokeTheirOwnSession(
    Scenario[TestSeedingSession, SessionsOfTwo, LoginSessionAdapter, RevokeLoginSessionPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-only-read-may-not-revoke-their-own-login-session"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ 만 받은 사용자가 자기 세션을 회수하면, 권한 검사가 막습니다",
            english=(
                "a user granted only READ on their own user is rejected by the permission check "
                "when revoking their own login session"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SessionsOfTwo]:
        return SessionsAndACaller(permissions=(Permission.READ,))

    @override
    def when(self) -> When[SessionsOfTwo, LoginSessionAdapter, RevokeLoginSessionPayload]:
        return RevokingMine()

    @override
    def then(self) -> Then[SessionsOfTwo, RevokeLoginSessionPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminRevokesAnotherUsersSession(
    Scenario[TestSeedingSession, SessionsOfTwo, LoginSessionAdapter, RevokeLoginSessionPayload]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-revokes-another-users-login-session"

    @override
    def describe(self) -> str:
        return Says(
            "전역 역할이 문인 관리자 회수에서 superadmin 이 다른 사용자의 세션을 회수하면 성공합니다",
            english=(
                "in an admin revoke gated by the global role, the superadmin revokes the login "
                "session of another user"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SessionsOfTwo]:
        return SessionsAndACaller(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[SessionsOfTwo, LoginSessionAdapter, RevokeLoginSessionPayload]:
        return RevokingAsAdmin()

    @override
    def then(self) -> Then[SessionsOfTwo, RevokeLoginSessionPayload]:
        return Revoked()


@dataclass(frozen=True)
class ARegularUserMayNotRevokeAsAdmin(
    Scenario[TestSeedingSession, SessionsOfTwo, LoginSessionAdapter, RevokeLoginSessionPayload]
):
    @override
    def summary(self) -> str:
        return "a-regular-user-may-not-revoke-a-login-session-as-admin"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ 와 UPDATE 를 받은 일반 사용자가 관리자 호출로 자기 세션을 회수하면, "
            "전역 역할 문이 막습니다",
            english=(
                "a regular user granted READ and UPDATE on their own user is rejected by the "
                "global role gate when revoking their own login session through the admin call"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SessionsOfTwo]:
        return SessionsAndACaller(permissions=(Permission.READ, Permission.UPDATE))

    @override
    def when(self) -> When[SessionsOfTwo, LoginSessionAdapter, RevokeLoginSessionPayload]:
        return RevokingAsAdmin()

    @override
    def then(self) -> Then[SessionsOfTwo, RevokeLoginSessionPayload]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[RevokingStep] = [
    AnUpdaterRevokesTheirOwnSession(),
    AReaderMayNotRevokeTheirOwnSession(),
    TheSuperadminRevokesAnotherUsersSession(),
    ARegularUserMayNotRevokeAsAdmin(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_revoking(
    scenario: RevokingStep, adapter: LoginSessionAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
