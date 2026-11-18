"""What a login session scenario table says besides the call.

A login session is a field row of the user who signed in. A table needs the caller, the
user whose sessions the call reads or revokes, and another user holding a session.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.login_session.response import LoginSessionNode
from ai.backend.manager.data.auth.login_session_types import LoginSessionData, LoginSessionStatus
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData
from ai.backend.testutils.scenario_steps import (
    Given,
    Held,
    Same,
    SameAs,
    Says,
    Verdict,
)
from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.components.user import AGrant
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.resource_policy.keypair import TestSeedKeypairPolicy
from bai_scenario.seeds.seeder import Laid
from bai_scenario.seeds.user.fields import TestSeedKeypairOf, TestSeedLoginSessionOf


@dataclass(frozen=True)
class SessionsOfTwo:
    """The caller, the user holding three sessions, and another user holding one.

    ``owner`` is the caller itself unless the caller is the superadmin.
    """

    caller: UserData
    owner: UserData
    other: UserData
    active: LoginSessionData
    revoked: LoginSessionData
    invalidated: LoginSessionData
    others_session: LoginSessionData


@dataclass(frozen=True)
class SessionsAndACaller(Given[Any, SessionsOfTwo]):
    """One domain and two users with sessions.

    A regular caller holds the three sessions itself and ``permissions`` on its own user.
    A superadmin caller holds none; another user holds the three.
    """

    role: UserRole = UserRole.USER
    permissions: tuple[Permission, ...] = ()

    @override
    def describe(self) -> str:
        if self.role is UserRole.SUPERADMIN:
            return Says(
                "도메인 하나와 superadmin 호출자, 세션 셋을 가진 사용자와 세션 하나를 가진 사용자",
                english=(
                    "one domain, a superadmin caller, a user holding three sessions and a user "
                    "holding one"
                ),
            )
        names = ", ".join(str(p.name) for p in self.permissions)
        return Says(
            f"도메인 하나와 세션 셋을 가진 호출자, 세션 하나를 가진 다른 사용자, 호출자는 자기 "
            f"사용자에 {names} 권한을 받았습니다",
            english=(
                "one domain, a caller holding three sessions and another user holding one, and "
                f"the caller holds the {names} permission on their own user"
            ),
        )

    @override
    async def lay(self, seeding: TestSeedingSession) -> SessionsOfTwo:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        owner = (
            await seeding.within(SomeoneOf(domain)) if self.role is UserRole.SUPERADMIN else caller
        )
        other = await seeding.within(SomeoneOf(domain))
        if self.permissions:
            await seeding.within(AGrant.on_user(caller, caller, *self.permissions))
        owner_key = await self._key_of(seeding, owner)
        active = await seeding.adding(TestSeedLoginSessionOf(access_key=owner_key), owner)
        revoked = await seeding.adding(
            TestSeedLoginSessionOf(access_key=owner_key, status=LoginSessionStatus.REVOKED),
            owner,
        )
        invalidated = await seeding.adding(
            TestSeedLoginSessionOf(access_key=owner_key, status=LoginSessionStatus.INVALIDATED),
            owner,
        )
        other_key = await self._key_of(seeding, other)
        others_session = await seeding.adding(TestSeedLoginSessionOf(access_key=other_key), other)
        return SessionsOfTwo(
            caller=seeding.made(caller),
            owner=seeding.made(owner),
            other=seeding.made(other),
            active=seeding.made(active),
            revoked=seeding.made(revoked),
            invalidated=seeding.made(invalidated),
            others_session=seeding.made(others_session),
        )

    async def _key_of(self, seeding: TestSeedingSession, user: Laid[UserData]) -> str:
        policy = await seeding.creating(TestSeedKeypairPolicy())
        key = await seeding.adding(
            TestSeedKeypairOf(resource_policy=seeding.made(policy).name), user
        )
        return str(seeding.made(key).access_key)


class SessionNodeLook:
    """Every field of one session node, expected from the session seeded in advance."""

    _started: datetime

    def __init__(self, started: datetime) -> None:
        self._started = started

    def verdicts(
        self, node: LoginSessionNode, expected: LoginSessionData, at: str
    ) -> list[Verdict]:
        seeded = Says("미리 저장한 세션", english="the session seeded in advance")
        return [
            Held(f"{at}id", node.id, SameAs(expected.id, seeded)),
            Held(f"{at}field_id", node.field_id, SameAs(expected.id, seeded)),
            Held(
                f"{at}user_id",
                node.user_id,
                SameAs(expected.user_id, Says("세션 소유자", english="the session owner")),
            ),
            Held(
                f"{at}access_key",
                node.access_key,
                SameAs(
                    expected.access_key,
                    Says("세션을 연 키", english="the key that opened the session"),
                ),
            ),
            Same(f"{at}status", node.status.value, expected.status.value),
            Held(f"{at}created_at", node.created_at, WrittenByThisRun(self._started)),
            Same(f"{at}last_accessed_at", node.last_accessed_at, None),
            Same(f"{at}invalidated_at", node.invalidated_at, None),
        ]
