"""Searching login sessions: every user's through the global role, the caller's own through their grant."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.login_session.request import (
    AdminSearchLoginSessionsInput,
    LoginSessionFilter,
    LoginSessionOrder,
    LoginSessionStatusFilter,
    MySearchLoginSessionsInput,
)
from ai.backend.common.dto.manager.v2.login_session.response import (
    AdminSearchLoginSessionsPayload,
    MySearchLoginSessionsPayload,
)
from ai.backend.common.dto.manager.v2.login_session.types import (
    LoginSessionOrderField,
    LoginSessionStatus,
    OrderDirection,
)
from ai.backend.manager.api.adapters.login_session.adapter import LoginSessionAdapter
from ai.backend.manager.data.auth.login_session_types import LoginSessionData
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
from bai_scenario.components.login_session import SessionNodeLook, SessionsAndACaller, SessionsOfTwo
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Searched = AdminSearchLoginSessionsPayload | MySearchLoginSessionsPayload


class ActiveOrRevoked:
    """The filter both searches send: active or revoked, which leaves the invalidated one out."""

    def build(self) -> LoginSessionFilter:
        return LoginSessionFilter(
            status=LoginSessionStatusFilter(
                in_=[LoginSessionStatus.ACTIVE, LoginSessionStatus.REVOKED]
            )
        )


@dataclass(frozen=True)
class SearchingEverySession(When[SessionsOfTwo, LoginSessionAdapter, Searched]):
    """Every user's sessions, active or revoked, by status descending, the first one."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: SessionsOfTwo) -> str:
        return Says(
            f"{laid.caller.username}이 세션 전체에서 상태가 active 나 revoked 인 것을 상태 "
            "내림차순으로 첫 하나만 조회합니다",
            english=(
                f"{laid.caller.username} searches every login session for active or revoked "
                "ones, by status descending, the first one only"
            ),
        )

    @override
    async def call(self, adapter: LoginSessionAdapter, laid: SessionsOfTwo) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                AdminSearchLoginSessionsInput(
                    filter=ActiveOrRevoked().build(),
                    order=[
                        LoginSessionOrder(
                            field=LoginSessionOrderField.STATUS, direction=OrderDirection.DESC
                        )
                    ],
                    limit=1,
                    offset=0,
                )
            )


@dataclass(frozen=True)
class SearchingMySessions(When[SessionsOfTwo, LoginSessionAdapter, Searched]):
    """The caller's own sessions, active or revoked, by status ascending, the first one."""

    @override
    def operation(self) -> str:
        return "my_search"

    @override
    def describe(self, laid: SessionsOfTwo) -> str:
        return Says(
            f"{laid.caller.username}이 자기 세션에서 상태가 active 나 revoked 인 것을 상태 "
            "오름차순으로 첫 하나만 조회합니다",
            english=(
                f"{laid.caller.username} searches their own login sessions for active or revoked "
                "ones, by status ascending, the first one only"
            ),
        )

    @override
    async def call(self, adapter: LoginSessionAdapter, laid: SessionsOfTwo) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.my_search(
                MySearchLoginSessionsInput(
                    filter=ActiveOrRevoked().build(),
                    order=[
                        LoginSessionOrder(
                            field=LoginSessionOrderField.STATUS, direction=OrderDirection.ASC
                        )
                    ],
                    limit=1,
                    offset=0,
                )
            )


@dataclass(frozen=True)
class TheFirstOfSome(Then[SessionsOfTwo, Searched]):
    """A page of one session out of ``total`` matching ones: the revoked or the active one."""

    started: datetime
    total: int
    revoked_first: bool

    @override
    def says(self) -> str:
        if self.revoked_first:
            return Says(
                f"걸린 {self.total}개 중 revoked 세션이 첫 페이지에 오고 다음 페이지가 있습니다",
                english=(
                    f"of the {self.total} matching sessions the revoked one comes on the first "
                    "page, and a next page follows"
                ),
            )
        return Says(
            f"걸린 {self.total}개 중 active 세션이 첫 페이지에 오고 다음 페이지가 있습니다",
            english=(
                f"of the {self.total} matching sessions the active one comes on the first page, "
                "and a next page follows"
            ),
        )

    @override
    def look(self, laid: SessionsOfTwo, answered: Answered[Searched]) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        expected: LoginSessionData = laid.revoked if self.revoked_first else laid.active
        seen: list[Verdict] = [
            Same("total_count", page.total_count, self.total),
            Same("has_next_page", page.has_next_page, True),
            Same("has_previous_page", page.has_previous_page, False),
            Same("items.length", len(page.items), 1),
        ]
        if len(page.items) == 1:
            seen.extend(
                SessionNodeLook(self.started).verdicts(page.items[0], expected, "items[0].")
            )
        return seen


type SearchingStep = Scenario[TestSeedingSession, SessionsOfTwo, LoginSessionAdapter, Searched]


@dataclass(frozen=True)
class TheSuperadminSearchesEverySession(
    Scenario[TestSeedingSession, SessionsOfTwo, LoginSessionAdapter, Searched]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-searches-every-users-login-sessions"

    @override
    def describe(self) -> str:
        return Says(
            "전역 역할이 문인 세션 전체 검색에서 superadmin 이 상태 필터, 상태 정렬, 페이지를 주면, "
            "사용자와 무관하게 필터에 맞는 세션이 세어지고 필터에 걸리는 세션은 빠집니다",
            english=(
                "when the superadmin searches every session, gated by the global role, with a "
                "status filter, a status order and a page, the matching sessions of every user "
                "are counted and the session the filter excludes is left out"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SessionsOfTwo]:
        return SessionsAndACaller(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[SessionsOfTwo, LoginSessionAdapter, Searched]:
        return SearchingEverySession()

    @override
    def then(self) -> Then[SessionsOfTwo, Searched]:
        return TheFirstOfSome(started=self.started, total=3, revoked_first=True)


@dataclass(frozen=True)
class ARegularUserMayNotSearchEverySession(
    Scenario[TestSeedingSession, SessionsOfTwo, LoginSessionAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-regular-user-may-not-search-every-login-session"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ 를 받은 일반 사용자가 세션 전체 검색을 하면, 전역 역할 문이 막습니다",
            english=(
                "a regular user granted READ on their own user is rejected by the global role "
                "gate when searching every login session"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SessionsOfTwo]:
        return SessionsAndACaller(permissions=(Permission.READ,))

    @override
    def when(self) -> When[SessionsOfTwo, LoginSessionAdapter, Searched]:
        return SearchingEverySession()

    @override
    def then(self) -> Then[SessionsOfTwo, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class AReaderSearchesTheirOwnSessions(
    Scenario[TestSeedingSession, SessionsOfTwo, LoginSessionAdapter, Searched]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-read-on-themselves-searches-their-own-login-sessions"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 READ 를 받은 사용자가 상태 필터, 상태 정렬, 페이지를 주고 자기 세션을 "
            "조회하면, 다른 사용자의 세션과 필터에 걸리는 세션은 빠집니다",
            english=(
                "when a user granted READ on their own user searches their own sessions with a "
                "status filter, a status order and a page, the session of another user and the "
                "session the filter excludes are left out"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SessionsOfTwo]:
        return SessionsAndACaller(permissions=(Permission.READ,))

    @override
    def when(self) -> When[SessionsOfTwo, LoginSessionAdapter, Searched]:
        return SearchingMySessions()

    @override
    def then(self) -> Then[SessionsOfTwo, Searched]:
        return TheFirstOfSome(started=self.started, total=2, revoked_first=False)


@dataclass(frozen=True)
class AUserWithoutReadMayNotSearchTheirSessions(
    Scenario[TestSeedingSession, SessionsOfTwo, LoginSessionAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-only-update-may-not-search-their-own-login-sessions"

    @override
    def describe(self) -> str:
        return Says(
            "자기 사용자에 UPDATE 만 받은 사용자가 자기 세션을 조회하면, 본인이어도 권한 검사가 막습니다",
            english=(
                "a user granted only UPDATE on their own user is rejected by the permission "
                "check when searching their own sessions"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, SessionsOfTwo]:
        return SessionsAndACaller(permissions=(Permission.UPDATE,))

    @override
    def when(self) -> When[SessionsOfTwo, LoginSessionAdapter, Searched]:
        return SearchingMySessions()

    @override
    def then(self) -> Then[SessionsOfTwo, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[SearchingStep] = [
    TheSuperadminSearchesEverySession(started=datetime.now(UTC)),
    ARegularUserMayNotSearchEverySession(),
    AReaderSearchesTheirOwnSessions(started=datetime.now(UTC)),
    AUserWithoutReadMayNotSearchTheirSessions(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: LoginSessionAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
