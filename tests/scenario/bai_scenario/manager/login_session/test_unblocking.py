"""Clearing the failed-login block of a user, through the global role."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.login_session.request import AdminUnblockUserInput
from ai.backend.common.dto.manager.v2.login_session.response import UnblockUserPayload
from ai.backend.manager.api.adapters.login_session.adapter import LoginSessionAdapter
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.auth import InsufficientPrivilege
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
class Unblocking(When[SessionsOfTwo, LoginSessionAdapter, UnblockUserPayload]):
    """The caller clears the block of the user holding three sessions, by username."""

    @override
    def operation(self) -> str:
        return "admin_unblock_user"

    @override
    def describe(self, laid: SessionsOfTwo) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.owner.username}의 차단을 해제합니다",
            english=f"{laid.caller.username} unblocks {laid.owner.username}",
        )

    @override
    async def call(self, adapter: LoginSessionAdapter, laid: SessionsOfTwo) -> UnblockUserPayload:
        with ActingAs(laid.caller):
            return await adapter.admin_unblock_user(
                AdminUnblockUserInput(username=laid.owner.username)
            )


@dataclass(frozen=True)
class Unblocked(Then[SessionsOfTwo, UnblockUserPayload]):
    """The unblock succeeds."""

    @override
    def says(self) -> str:
        return Says("차단 해제가 성공합니다", english="the unblock succeeds")

    @override
    def look(self, laid: SessionsOfTwo, answered: Answered[UnblockUserPayload]) -> list[Verdict]:
        answer = answered.response
        if answer is None:
            return [Refused(InsufficientPrivilege, answered.raised)]
        return [Same("success", answer.success, True)]


type UnblockingStep = Scenario[
    TestSeedingSession, SessionsOfTwo, LoginSessionAdapter, UnblockUserPayload
]


@dataclass(frozen=True)
class TheSuperadminUnblocksAUser(
    Scenario[TestSeedingSession, SessionsOfTwo, LoginSessionAdapter, UnblockUserPayload]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-unblocks-a-user"

    @override
    def describe(self) -> str:
        return Says(
            "전역 역할이 문인 차단 해제에서 superadmin 이 사용자 이름으로 차단을 해제하면 성공합니다",
            english=(
                "in an unblock gated by the global role, the superadmin clears the block of a "
                "user by username"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SessionsOfTwo]:
        return SessionsAndACaller(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[SessionsOfTwo, LoginSessionAdapter, UnblockUserPayload]:
        return Unblocking()

    @override
    def then(self) -> Then[SessionsOfTwo, UnblockUserPayload]:
        return Unblocked()


@dataclass(frozen=True)
class ARegularUserMayNotUnblock(
    Scenario[TestSeedingSession, SessionsOfTwo, LoginSessionAdapter, UnblockUserPayload]
):
    @override
    def summary(self) -> str:
        return "a-regular-user-may-not-unblock-a-user"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ 와 UPDATE 를 받은 일반 사용자가 자기 차단을 해제하면, 전역 역할 문이 "
            "막습니다",
            english=(
                "a regular user granted READ and UPDATE on their own user is rejected by the "
                "global role gate when clearing their own block"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SessionsOfTwo]:
        return SessionsAndACaller(permissions=(Permission.READ, Permission.UPDATE))

    @override
    def when(self) -> When[SessionsOfTwo, LoginSessionAdapter, UnblockUserPayload]:
        return Unblocking()

    @override
    def then(self) -> Then[SessionsOfTwo, UnblockUserPayload]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[UnblockingStep] = [
    TheSuperadminUnblocksAUser(),
    ARegularUserMayNotUnblock(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_unblocking(
    scenario: UnblockingStep, adapter: LoginSessionAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
