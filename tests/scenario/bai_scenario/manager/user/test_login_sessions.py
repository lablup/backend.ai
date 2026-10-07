"""로그인 세션 — 누가 훑고, 누가 회수하고, 누가 차단을 푸는가."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.login_session.request import (
    AdminRevokeLoginSessionInput,
    AdminSearchLoginSessionsInput,
    AdminUnblockUserInput,
    MyRevokeLoginSessionInput,
    MySearchLoginSessionsInput,
)
from ai.backend.common.dto.manager.v2.login_session.response import (
    AdminSearchLoginSessionsPayload,
    LoginSessionNode,
    MySearchLoginSessionsPayload,
    RevokeLoginSessionPayload,
    UnblockUserPayload,
)
from ai.backend.manager.api.adapters.login_session.adapter import LoginSessionAdapter
from ai.backend.manager.data.auth.login_session_types import LoginSessionData
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.auth import InsufficientPrivilege, LoginSessionNotFoundError
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.components.user import AGrant
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.resource_policy.keypair import SeedKeypairPolicy
from bai_scenario.seeds.seeder import Laid
from bai_scenario.seeds.user.fields import SeedKeypairOf, SeedLoginSessionOf

type Searched = AdminSearchLoginSessionsPayload | MySearchLoginSessionsPayload


@dataclass(frozen=True)
class RevokedThenSearched:
    """회수한 답과, 그 뒤 같은 사람이 다시 훑은 답."""

    revoked: RevokeLoginSessionPayload
    after: Searched


type Answer = Searched | RevokedThenSearched | UnblockUserPayload


@dataclass(frozen=True)
class TwoPeopleAndTheirSessions:
    """부르는 사람과 다른 사람, 그리고 둘이 가진 세션."""

    caller: UserData
    other: UserData
    caller_session: LoginSessionData | None
    other_session: LoginSessionData | None


class SessionLayer:
    """사용자 한 명 아래에 키 하나와 그 키로 연 세션 하나를 심는다.

    세션이 담는 access key는 앞서 심은 키에서 읽는다.
    """

    _seeding: SeedingSession

    def __init__(self, seeding: SeedingSession) -> None:
        self._seeding = seeding

    async def session_of(self, user: Laid[UserData]) -> LoginSessionData:
        policy = await self._seeding.creating(SeedKeypairPolicy())
        key = await self._seeding.adding(
            SeedKeypairOf(resource_policy=self._seeding.made(policy).name), user
        )
        session = await self._seeding.adding(
            SeedLoginSessionOf(access_key=str(self._seeding.made(key).access_key)), user
        )
        return self._seeding.made(session)


@dataclass(frozen=True)
class SomeoneAndAnother(Given[Any, TwoPeopleAndTheirSessions]):
    """한 도메인의 사용자 둘.

    부르는 사람은 ``permissions``만큼 자기 사용자 권한을 받는다. 세션은 ``sessions``가
    말하는 쪽에 심는다.
    """

    permissions: tuple[Permission, ...] = ()
    caller_has_session: bool = True
    other_has_session: bool = True

    @override
    def describe(self) -> str:
        grant = (
            f"부르는 사람은 자기 사용자에 {', '.join(str(p.name) for p in self.permissions)} 권한을 받았다"
            if self.permissions
            else "부르는 사람은 아무 권한도 받지 않았다"
        )
        return f"도메인 하나와 사용자 둘, {grant}"

    @override
    async def lay(self, seeding: Any) -> TwoPeopleAndTheirSessions:
        layer = SessionLayer(seeding)
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(domain))
        other = await seeding.within(SomeoneOf(domain))
        caller_session = await layer.session_of(caller) if self.caller_has_session else None
        other_session = await layer.session_of(other) if self.other_has_session else None
        if self.permissions:
            await seeding.within(AGrant.on_user(caller, caller, *self.permissions))
        return TwoPeopleAndTheirSessions(
            seeding.made(caller), seeding.made(other), caller_session, other_session
        )


@dataclass(frozen=True)
class TheSuperadminAndOthers(Given[Any, TwoPeopleAndTheirSessions]):
    """슈퍼관리자 한 명과, 세션을 가진 사용자 한두 명."""

    both_have_sessions: bool = True

    @override
    def describe(self) -> str:
        if self.both_have_sessions:
            return "도메인 하나와 슈퍼관리자, 세션을 하나씩 가진 사용자 둘"
        return "도메인 하나와 슈퍼관리자, 세션 하나를 가진 사용자 하나"

    @override
    async def lay(self, seeding: Any) -> TwoPeopleAndTheirSessions:
        layer = SessionLayer(seeding)
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        first = await seeding.within(SomeoneOf(domain))
        first_session = await layer.session_of(first)
        second_session: LoginSessionData | None = None
        if self.both_have_sessions:
            second = await seeding.within(SomeoneOf(domain))
            second_session = await layer.session_of(second)
        caller = await seeding.within(SomeoneOf(domain, role=UserRole.SUPERADMIN))
        return TwoPeopleAndTheirSessions(
            seeding.made(caller),
            seeding.made(first),
            second_session,
            first_session,
        )


@dataclass(frozen=True)
class SomeoneGrantedOnDomain(Given[Any, TwoPeopleAndTheirSessions]):
    """도메인 스코프에서 사용자 권한을 받은 사람과, 세션을 가진 다른 사용자."""

    permission: Permission

    @override
    def describe(self) -> str:
        return (
            f"도메인 하나와 세션을 가진 사용자 하나, 부르는 사람은 도메인 스코프에서 "
            f"사용자 {self.permission.name} 권한을 받았다"
        )

    @override
    async def lay(self, seeding: Any) -> TwoPeopleAndTheirSessions:
        layer = SessionLayer(seeding)
        domain: Laid[DomainData] = await seeding.creating(
            SeedDomain(name_hint="home", description=WAS_HERE)
        )
        other = await seeding.within(SomeoneOf(domain))
        other_session = await layer.session_of(other)
        caller = await seeding.within(SomeoneOf(domain))
        await seeding.within(AGrant.on_domain(domain, caller, self.permission))
        return TwoPeopleAndTheirSessions(
            seeding.made(caller), seeding.made(other), None, other_session
        )


@dataclass(frozen=True)
class SearchingEverySession(When[TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]):
    """페이지 인자 없이 세션 전체를 훑는다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: TwoPeopleAndTheirSessions) -> str:
        return f"{laid.caller.username}이 세션 전체를 훑음"

    @override
    async def call(self, adapter: LoginSessionAdapter, laid: TwoPeopleAndTheirSessions) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.admin_search(AdminSearchLoginSessionsInput())


@dataclass(frozen=True)
class SearchingMySessions(When[TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]):
    """자기 세션을 훑는다."""

    @override
    def operation(self) -> str:
        return "my_search"

    @override
    def describe(self, laid: TwoPeopleAndTheirSessions) -> str:
        return f"{laid.caller.username}이 자기 세션을 훑음"

    @override
    async def call(self, adapter: LoginSessionAdapter, laid: TwoPeopleAndTheirSessions) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.my_search(MySearchLoginSessionsInput())


@dataclass(frozen=True)
class RevokingASession(When[TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]):
    """자기 경로로 세션을 회수하고, 자기 세션을 다시 훑는다. `others`면 남의 세션을 준다."""

    others: bool = False

    @override
    def operation(self) -> str:
        return "my_revoke"

    @override
    def describe(self, laid: TwoPeopleAndTheirSessions) -> str:
        whose = laid.other.username if self.others else "자기"
        return f"{laid.caller.username}이 {whose} 세션을 회수"

    @override
    async def call(self, adapter: LoginSessionAdapter, laid: TwoPeopleAndTheirSessions) -> Answer:
        session = laid.other_session if self.others else laid.caller_session
        assert session is not None
        with ActingAs(laid.caller):
            revoked = await adapter.my_revoke(MyRevokeLoginSessionInput(session_id=session.id))
            after = await adapter.my_search(MySearchLoginSessionsInput())
        return RevokedThenSearched(revoked, after)


@dataclass(frozen=True)
class RevokingAsAdmin(When[TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]):
    """관리자 경로로 세션을 회수하고, 세션 전체를 다시 훑는다. `missing`이면 없는 id를 준다."""

    missing: bool = False

    @override
    def operation(self) -> str:
        return "admin_revoke"

    @override
    def describe(self, laid: TwoPeopleAndTheirSessions) -> str:
        what = "없는 세션" if self.missing else f"{laid.other.username}의 세션"
        return f"{laid.caller.username}이 관리자 경로로 {what}을 회수"

    @override
    async def call(self, adapter: LoginSessionAdapter, laid: TwoPeopleAndTheirSessions) -> Answer:
        if self.missing:
            session_id = uuid4()
        else:
            assert laid.other_session is not None
            session_id = laid.other_session.id
        with ActingAs(laid.caller):
            revoked = await adapter.admin_revoke(
                AdminRevokeLoginSessionInput(session_id=session_id)
            )
            after = await adapter.admin_search(AdminSearchLoginSessionsInput())
        return RevokedThenSearched(revoked, after)


@dataclass(frozen=True)
class Unblocking(When[TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]):
    """사용자 이름으로 차단을 푼다. `nobody`면 어떤 사용자도 아닌 이름을 준다."""

    nobody: bool = False

    @override
    def operation(self) -> str:
        return "admin_unblock_user"

    @override
    def describe(self, laid: TwoPeopleAndTheirSessions) -> str:
        named = "없는 이름" if self.nobody else laid.other.username
        return f"{laid.caller.username}이 {named}의 차단을 풂"

    @override
    async def call(self, adapter: LoginSessionAdapter, laid: TwoPeopleAndTheirSessions) -> Answer:
        named = "no-such-user" if self.nobody else laid.other.username
        with ActingAs(laid.caller):
            return await adapter.admin_unblock_user(AdminUnblockUserInput(username=named))


class SessionNodeLook:
    """세션 노드 하나를 통째로 본다. 기대는 심은 세션에서 온다."""

    _started: datetime

    def __init__(self, started: datetime) -> None:
        self._started = started

    def verdicts(
        self, node: LoginSessionNode, expected: LoginSessionData, at: str
    ) -> list[Verdict]:
        return [
            Held(f"{at}id", node.id, SameAs(expected.id, "심은 세션")),
            Held(f"{at}user_id", node.user_id, SameAs(expected.user_id, "세션의 주인")),
            Held(f"{at}access_key", node.access_key, SameAs(expected.access_key, "세션을 연 키")),
            Same(f"{at}status", node.status, "active"),
            Held(f"{at}created_at", node.created_at, WrittenByThisRun(self._started)),
            Same(f"{at}last_accessed_at", node.last_accessed_at, None),
            Same(f"{at}invalidated_at", node.invalidated_at, None),
        ]


@dataclass(frozen=True)
class EverySessionInOrder(Then[TwoPeopleAndTheirSessions, Answer]):
    """심은 세션 둘이 순서대로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "심은 세션이 모두 순서대로 온다"

    @override
    def look(self, laid: TwoPeopleAndTheirSessions, answered: Answered[Answer]) -> list[Verdict]:
        page = answered.response
        if not isinstance(page, AdminSearchLoginSessionsPayload):
            return [Refused(InsufficientPrivilege, answered.raised)]
        first, second = laid.other_session, laid.caller_session
        assert first is not None and second is not None
        seen: list[Verdict] = [
            Same("total_count", page.total_count, 2),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
            Same("items.length", len(page.items), 2),
        ]
        if len(page.items) == 2:
            look = SessionNodeLook(self.started)
            seen.extend(look.verdicts(page.items[0], first, "items[0]."))
            seen.extend(look.verdicts(page.items[1], second, "items[1]."))
        return seen


@dataclass(frozen=True)
class OnlyMySession(Then[TwoPeopleAndTheirSessions, Answer]):
    """부르는 사람의 세션 하나만 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "자기 세션 하나만 온다"

    @override
    def look(self, laid: TwoPeopleAndTheirSessions, answered: Answered[Answer]) -> list[Verdict]:
        page = answered.response
        if not isinstance(page, MySearchLoginSessionsPayload):
            return [Refused(NotEnoughPermission, answered.raised)]
        assert laid.caller_session is not None
        seen: list[Verdict] = [
            Same("total_count", page.total_count, 1),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
            Same("items.length", len(page.items), 1),
        ]
        if len(page.items) == 1:
            seen.extend(
                SessionNodeLook(self.started).verdicts(
                    page.items[0], laid.caller_session, "items[0]."
                )
            )
        return seen


@dataclass(frozen=True)
class RevokedAndGone(Then[TwoPeopleAndTheirSessions, Answer]):
    """회수가 성공하고, 뒤이어 훑으면 그 세션이 없다."""

    @override
    def says(self) -> str:
        return "회수가 성공하고 뒤이은 조회에 세션이 없다"

    @override
    def look(self, laid: TwoPeopleAndTheirSessions, answered: Answered[Answer]) -> list[Verdict]:
        answer = answered.response
        if not isinstance(answer, RevokedThenSearched):
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Same("revoked.success", answer.revoked.success, True),
            Same("after.items", list(answer.after.items), []),
            Same("after.total_count", answer.after.total_count, 0),
            Same("after.has_next_page", answer.after.has_next_page, False),
            Same("after.has_previous_page", answer.after.has_previous_page, False),
        ]


@dataclass(frozen=True)
class Unblocked(Then[TwoPeopleAndTheirSessions, Answer]):
    """차단 해제가 성공한다."""

    @override
    def says(self) -> str:
        return "차단 해제가 성공한다"

    @override
    def look(self, laid: TwoPeopleAndTheirSessions, answered: Answered[Answer]) -> list[Verdict]:
        answer = answered.response
        if not isinstance(answer, UnblockUserPayload):
            return [Refused(InsufficientPrivilege, answered.raised)]
        return [Same("success", answer.success, True)]


type SessionStep = Scenario[SeedingSession, TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]


@dataclass(frozen=True)
class TheSuperadminSearchesEverySession(
    Scenario[SeedingSession, TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-searches-every-users-login-sessions"

    @override
    def describe(self) -> str:
        return (
            "전역 역할이 문인 세션 검색에서 슈퍼관리자가 페이지 인자 없이 훑으면, "
            "사용자와 무관하게 심은 세션이 생성 시각 내림차순으로 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, TwoPeopleAndTheirSessions]:
        return TheSuperadminAndOthers()

    @override
    def when(self) -> When[TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]:
        return SearchingEverySession()

    @override
    def then(self) -> Then[TwoPeopleAndTheirSessions, Answer]:
        return EverySessionInOrder(started=self.started)


@dataclass(frozen=True)
class OnlyTheSuperadminSearchesEverySession(
    Scenario[SeedingSession, TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-every-login-session"

    @override
    def describe(self) -> str:
        return "권한 받은 사용자가 세션 전체 검색을 하려 하면, 전역 역할 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, TwoPeopleAndTheirSessions]:
        return SomeoneGrantedOnDomain(Permission.READ)

    @override
    def when(self) -> When[TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]:
        return SearchingEverySession()

    @override
    def then(self) -> Then[TwoPeopleAndTheirSessions, Answer]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class AGrantedUserSearchesOnlyTheirOwnSessions(
    Scenario[SeedingSession, TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-read-on-themselves-searches-only-their-own-login-sessions"

    @override
    def describe(self) -> str:
        return "자기 스코프에서 READ를 받은 사용자가 훑으면, 다른 사용자의 세션은 빠진다"

    @override
    def given(self) -> Given[SeedingSession, TwoPeopleAndTheirSessions]:
        return SomeoneAndAnother(permissions=(Permission.READ,))

    @override
    def when(self) -> When[TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]:
        return SearchingMySessions()

    @override
    def then(self) -> Then[TwoPeopleAndTheirSessions, Answer]:
        return OnlyMySession(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearchTheirSessions(
    Scenario[SeedingSession, TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-their-own-login-sessions"

    @override
    def describe(self) -> str:
        return "역할 없이 자기 세션을 훑으려 하면, 본인이어도 스코프 권한 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, TwoPeopleAndTheirSessions]:
        return SomeoneAndAnother(other_has_session=False)

    @override
    def when(self) -> When[TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]:
        return SearchingMySessions()

    @override
    def then(self) -> Then[TwoPeopleAndTheirSessions, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AGrantedUserRevokesTheirOwnSession(
    Scenario[SeedingSession, TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-update-on-themselves-revokes-their-own-login-session"

    @override
    def describe(self) -> str:
        return (
            "자기 스코프에서 READ와 UPDATE를 받은 사용자가 자기 세션을 회수하면, "
            "성공이 오고 그 세션은 더 조회되지 않으며 사용자가 회수했다는 이력이 생긴다"
        )

    @override
    def given(self) -> Given[SeedingSession, TwoPeopleAndTheirSessions]:
        return SomeoneAndAnother(
            permissions=(Permission.READ, Permission.UPDATE), other_has_session=False
        )

    @override
    def when(self) -> When[TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]:
        return RevokingASession()

    @override
    def then(self) -> Then[TwoPeopleAndTheirSessions, Answer]:
        return RevokedAndGone()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRevokeTheirSession(
    Scenario[SeedingSession, TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-revoke-their-own-login-session"

    @override
    def describe(self) -> str:
        return "역할 없이 회수하려 하면, 소유자 조회 단계가 막는다"

    @override
    def given(self) -> Given[SeedingSession, TwoPeopleAndTheirSessions]:
        return SomeoneAndAnother(other_has_session=False)

    @override
    def when(self) -> When[TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]:
        return RevokingASession()

    @override
    def then(self) -> Then[TwoPeopleAndTheirSessions, Answer]:
        return TheCallIsRefused(GenericBadRequest)


@dataclass(frozen=True)
class AReaderMayNotRevokeTheirSession(
    Scenario[SeedingSession, TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-only-read-may-not-revoke-their-own-login-session"

    @override
    def describe(self) -> str:
        return "READ만 받고 회수하려 하면, 엔티티 권한 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, TwoPeopleAndTheirSessions]:
        return SomeoneAndAnother(permissions=(Permission.READ,), other_has_session=False)

    @override
    def when(self) -> When[TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]:
        return RevokingASession()

    @override
    def then(self) -> Then[TwoPeopleAndTheirSessions, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class OwnGrantsMayNotRevokeSomeoneElsesSession(
    Scenario[SeedingSession, TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-only-on-themselves-may-not-revoke-another-users-login-session"

    @override
    def describe(self) -> str:
        return (
            "자기 스코프에서만 READ와 UPDATE를 받은 사용자가 다른 사용자의 세션을 주면, "
            "그 소유자에 대한 조회 단계가 막는다"
        )

    @override
    def given(self) -> Given[SeedingSession, TwoPeopleAndTheirSessions]:
        return SomeoneAndAnother(
            permissions=(Permission.READ, Permission.UPDATE), caller_has_session=False
        )

    @override
    def when(self) -> When[TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]:
        return RevokingASession(others=True)

    @override
    def then(self) -> Then[TwoPeopleAndTheirSessions, Answer]:
        return TheCallIsRefused(GenericBadRequest)


@dataclass(frozen=True)
class TheSuperadminRevokesSomeoneElsesSession(
    Scenario[SeedingSession, TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-revokes-another-users-login-session"

    @override
    def describe(self) -> str:
        return (
            "전역 역할이 문인 관리자 회수에서 슈퍼관리자가 다른 사용자의 세션을 회수하면, "
            "성공이 오고 세션 전체 검색에서 빠지며 관리자가 회수했다는 이력이 생긴다"
        )

    @override
    def given(self) -> Given[SeedingSession, TwoPeopleAndTheirSessions]:
        return TheSuperadminAndOthers(both_have_sessions=False)

    @override
    def when(self) -> When[TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]:
        return RevokingAsAdmin()

    @override
    def then(self) -> Then[TwoPeopleAndTheirSessions, Answer]:
        return RevokedAndGone()


@dataclass(frozen=True)
class TheSuperadminMayNotRevokeAMissingSession(
    Scenario[SeedingSession, TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "even-the-superadmin-may-not-revoke-a-login-session-that-does-not-exist"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 없는 세션 id를 주면, 입력 검증이 막는다"

    @override
    def given(self) -> Given[SeedingSession, TwoPeopleAndTheirSessions]:
        return TheSuperadminAndOthers(both_have_sessions=False)

    @override
    def when(self) -> When[TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]:
        return RevokingAsAdmin(missing=True)

    @override
    def then(self) -> Then[TwoPeopleAndTheirSessions, Answer]:
        return TheCallIsRefused(LoginSessionNotFoundError)


@dataclass(frozen=True)
class OnlyTheSuperadminRevokesAsAdmin(
    Scenario[SeedingSession, TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-revoke-a-login-session-as-admin"

    @override
    def describe(self) -> str:
        return "권한 받은 사용자가 관리자 회수를 하려 하면, 전역 역할 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, TwoPeopleAndTheirSessions]:
        return SomeoneGrantedOnDomain(Permission.UPDATE)

    @override
    def when(self) -> When[TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]:
        return RevokingAsAdmin()

    @override
    def then(self) -> Then[TwoPeopleAndTheirSessions, Answer]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class TheSuperadminUnblocksAUser(
    Scenario[SeedingSession, TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-unblocks-a-user"

    @override
    def describe(self) -> str:
        return (
            "전역 역할이 문인 차단 해제에서 슈퍼관리자가 사용자 이름을 주면, "
            "성공이 오고 그 이름의 차단 기록이 사라진다"
        )

    @override
    def given(self) -> Given[SeedingSession, TwoPeopleAndTheirSessions]:
        return TheSuperadminAndOthers(both_have_sessions=False)

    @override
    def when(self) -> When[TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]:
        return Unblocking()

    @override
    def then(self) -> Then[TwoPeopleAndTheirSessions, Answer]:
        return Unblocked()


@dataclass(frozen=True)
class UnblockingANameNobodyHoldsSucceeds(
    Scenario[SeedingSession, TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "unblocking-a-username-nobody-holds-still-succeeds"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 어떤 사용자도 아닌 이름을 주면, 존재를 확인하지 않고 성공이 온다"

    @override
    def given(self) -> Given[SeedingSession, TwoPeopleAndTheirSessions]:
        return TheSuperadminAndOthers(both_have_sessions=False)

    @override
    def when(self) -> When[TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]:
        return Unblocking(nobody=True)

    @override
    def then(self) -> Then[TwoPeopleAndTheirSessions, Answer]:
        return Unblocked()


@dataclass(frozen=True)
class OnlyTheSuperadminUnblocks(
    Scenario[SeedingSession, TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-unblock-a-user"

    @override
    def describe(self) -> str:
        return "권한 받은 사용자가 차단을 풀려 하면, 전역 역할 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, TwoPeopleAndTheirSessions]:
        return SomeoneGrantedOnDomain(Permission.UPDATE)

    @override
    def when(self) -> When[TwoPeopleAndTheirSessions, LoginSessionAdapter, Answer]:
        return Unblocking()

    @override
    def then(self) -> Then[TwoPeopleAndTheirSessions, Answer]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SessionStep] = [
    TheSuperadminSearchesEverySession(started=datetime.now(UTC)),
    OnlyTheSuperadminSearchesEverySession(),
    AGrantedUserSearchesOnlyTheirOwnSessions(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotSearchTheirSessions(),
    AGrantedUserRevokesTheirOwnSession(),
    AUserGrantedNothingMayNotRevokeTheirSession(),
    AReaderMayNotRevokeTheirSession(),
    OwnGrantsMayNotRevokeSomeoneElsesSession(),
    TheSuperadminRevokesSomeoneElsesSession(),
    TheSuperadminMayNotRevokeAMissingSession(),
    OnlyTheSuperadminRevokesAsAdmin(),
    TheSuperadminUnblocksAUser(),
    UnblockingANameNobodyHoldsSucceeds(),
    OnlyTheSuperadminUnblocks(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_login_sessions(
    scenario: SessionStep,
    login_session_adapter: LoginSessionAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, login_session_adapter, engine)
