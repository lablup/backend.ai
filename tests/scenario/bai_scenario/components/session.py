"""What a session scenario table says besides the call.

A session waits in the project it was requested in, so terminating it asks for the
permission a role in that project grants. A table lays the session, and the caller
with or without that role.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.kernel.response import ResourceAllocationGQLDTO
from ai.backend.common.dto.manager.v2.session.response import TerminateSessionsPayload
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.session.types import SessionEntityData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Skipped,
    Then,
    Verdict,
)
from bai_scenario.components.domain import GrantedUser, SomeoneOf
from bai_scenario.components.resource_allocation import (
    LaidPlace,
    SomeoneReadingSessionsIn,
    lay_a_place,
)
from bai_scenario.components.system import role_named
from bai_scenario.seeds.rbac.role import SeedPermission, SeedRole
from bai_scenario.seeds.seeder import Laid, Seeder, SeedNest
from bai_scenario.seeds.session.session import SeedSession

MESSAGE_IS_FREE_TEXT = "이유는 문자열로 오고, 문자열은 바뀌어도 되는 값이다"


@dataclass(frozen=True)
class SomeoneMakingSessions(SeedNest[GrantedUser]):
    """그 프로젝트에서 세션을 만들고 조회할 수 있는 사용자.

    세션은 자기가 속한 프로젝트를 이름으로 대므로 역할이 프로젝트 스코프에 앉고, 그 역할을
    주는 일이 곧 그 사람을 프로젝트 명부에 올리는 일이 된다.
    """

    domain: Laid[DomainData]
    project: Laid[ProjectData]

    @override
    def kind(self) -> str:
        return "그 프로젝트에서 세션을 만들 수 있는 사용자 준비"

    @override
    def lay(self, seed: Seeder) -> GrantedUser:
        someone = seed.within(SomeoneOf(self.domain))
        role = seed.creating_from(
            SeedRole(lambda p: ProjectID(p.id), name_hint="session-owner"), self.project
        )
        seed.adding(
            SeedPermission(entity_type=SessionEntityType(), permission=Permission.CREATE), role
        )
        seed.adding(
            SeedPermission(entity_type=SessionEntityType(), permission=Permission.READ), role
        )
        grant = seed.granting(role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return GrantedUser(someone, grant)


@dataclass(frozen=True)
class SomeoneTerminatingSessionsIn(SeedNest[Laid[UserData]]):
    """그 프로젝트의 세션을 종료할 수 있는 사용자."""

    domain: Laid[DomainData]
    project: Laid[ProjectData]

    @override
    def kind(self) -> str:
        return "그 프로젝트의 세션을 종료할 수 있는 사용자 준비"

    @override
    def lay(self, seed: Seeder) -> Laid[UserData]:
        someone = seed.within(SomeoneOf(self.domain))
        role = seed.creating_from(
            SeedRole(lambda p: ProjectID(p.id), name_hint="session-terminator"), self.project
        )
        seed.adding(
            SeedPermission(entity_type=SessionEntityType(), permission=Permission.SOFT_DELETE),
            role,
        )
        seed.granting(role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return someone


@dataclass(frozen=True)
class ASessionAndACaller:
    """종료할 세션 하나와, 종료를 호출할 사용자."""

    session: SessionEntityData
    caller: UserData


@dataclass(frozen=True)
class TwoSessionsAndACaller:
    """서로 다른 프로젝트에서 기다리는 세션 둘과, 첫 세션의 프로젝트에서만 종료할 수 있는 사용자."""

    mine: SessionEntityData
    theirs: SessionEntityData
    caller: UserData


async def lay_a_pending_session(seeding: Any, place: LaidPlace) -> Laid[SessionEntityData]:
    """그 자리에서 스케줄링을 기다리는 세션 하나를 만든다."""
    session: Laid[SessionEntityData] = await seeding.creating_from_three(
        SeedSession(access_key=place.access_key), place.project, place.owner, place.group
    )
    return session


@dataclass(frozen=True)
class APendingSessionAndSomeone(Given[Any, ASessionAndACaller]):
    """기다리는 세션 하나와 사용자 한 명. 그 프로젝트에서 세션을 종료할 수 있는지는 행이 정한다."""

    granted: bool = False
    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        who = (
            "그 프로젝트에서 세션을 종료할 수 있는 일반 사용자 한 명"
            if self.granted
            else f"{role_named(self.role)} 한 명"
        )
        return f"스케줄링을 기다리는 세션 하나와, {who}"

    @override
    async def lay(self, seeding: Any) -> ASessionAndACaller:
        place = await lay_a_place(seeding, slots=0)
        session = await lay_a_pending_session(seeding, place)
        caller: Laid[UserData]
        if self.granted:
            caller = await seeding.within(SomeoneTerminatingSessionsIn(place.domain, place.project))
        else:
            caller = await seeding.within(SomeoneOf(place.domain, role=self.role))
        return ASessionAndACaller(seeding.made(session), seeding.made(caller))


@dataclass(frozen=True)
class SessionsInTwoProjectsAndSomeone(Given[Any, TwoSessionsAndACaller]):
    """서로 다른 프로젝트의 세션 둘과, 첫 프로젝트에서만 세션을 종료할 수 있는 사용자."""

    @override
    def describe(self) -> str:
        return (
            "서로 다른 프로젝트에서 기다리는 세션 둘과, "
            "첫 프로젝트에서만 세션을 종료할 수 있는 일반 사용자 한 명"
        )

    @override
    async def lay(self, seeding: Any) -> TwoSessionsAndACaller:
        here = await lay_a_place(seeding, slots=0)
        there = await lay_a_place(seeding, slots=0)
        mine = await lay_a_pending_session(seeding, here)
        theirs = await lay_a_pending_session(seeding, there)
        caller = await seeding.within(SomeoneTerminatingSessionsIn(here.domain, here.project))
        return TwoSessionsAndACaller(seeding.made(mine), seeding.made(theirs), seeding.made(caller))


@dataclass(frozen=True)
class TheSessionIsCancelled(Then[ASessionAndACaller, TerminateSessionsPayload]):
    """기다리던 세션이 취소된 목록에 반환되고, 실패 목록은 비어 있다."""

    @override
    def says(self) -> str:
        return "미리 만들어 둔 세션이 취소된 목록에 반환되고, 실패 목록은 비어 있다"

    @override
    def look(
        self, laid: ASessionAndACaller, answered: Answered[TerminateSessionsPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Held[list[UUID]](
                "cancelled",
                list(payload.cancelled),
                SameAs[list[UUID]]([laid.session.id], "미리 만들어 둔 세션"),
            ),
            Same("terminating", list(payload.terminating), []),
            Same("force_terminated", list(payload.force_terminated), []),
            Same("skipped", list(payload.skipped), []),
            Same("failed", list(payload.failed), []),
        ]


@dataclass(frozen=True)
class TheSessionIsRefused(Then[ASessionAndACaller, TerminateSessionsPayload]):
    """세션이 실패 목록에 반환되고, 네 결과 목록은 비어 있다."""

    @override
    def says(self) -> str:
        return "미리 만들어 둔 세션이 실패 목록에 반환되고, 결과 목록은 전부 비어 있다"

    @override
    def look(
        self, laid: ASessionAndACaller, answered: Answered[TerminateSessionsPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Same("cancelled", list(payload.cancelled), []),
            Same("terminating", list(payload.terminating), []),
            Same("force_terminated", list(payload.force_terminated), []),
            Same("skipped", list(payload.skipped), []),
            Held[list[UUID]](
                "failed[*].session_id",
                [one.session_id for one in payload.failed],
                SameAs[list[UUID]]([laid.session.id], "미리 만들어 둔 세션"),
            ),
            Skipped("failed[*].message", MESSAGE_IS_FREE_TEXT),
        ]


@dataclass(frozen=True)
class TheLaidOneIsCancelledTheUnknownIsSkipped(Then[ASessionAndACaller, TerminateSessionsPayload]):
    """기다리던 세션은 취소된 목록에, 없는 id는 건너뛴 목록에 반환된다."""

    @override
    def says(self) -> str:
        return "미리 만들어 둔 세션은 취소된 목록에, 없는 id는 건너뛴 목록에 반환된다"

    @override
    def look(
        self, laid: ASessionAndACaller, answered: Answered[TerminateSessionsPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Held[list[UUID]](
                "cancelled",
                list(payload.cancelled),
                SameAs[list[UUID]]([laid.session.id], "미리 만들어 둔 세션"),
            ),
            Same("terminating", list(payload.terminating), []),
            Same("force_terminated", list(payload.force_terminated), []),
            Same("len(skipped)", len(payload.skipped), 1),
            Skipped("skipped[0]", "호출이 만든 없는 id라 미리 알 수 없다"),
            Same("failed", list(payload.failed), []),
        ]


@dataclass(frozen=True)
class MineIsCancelledTheirsIsRefused(Then[TwoSessionsAndACaller, TerminateSessionsPayload]):
    """자기 프로젝트의 세션은 취소된 목록에, 다른 프로젝트의 세션은 실패 목록에 반환된다."""

    @override
    def says(self) -> str:
        return "자기 프로젝트의 세션은 취소된 목록에, 다른 프로젝트의 세션은 실패 목록에 반환된다"

    @override
    def look(
        self, laid: TwoSessionsAndACaller, answered: Answered[TerminateSessionsPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Held[list[UUID]](
                "cancelled",
                list(payload.cancelled),
                SameAs[list[UUID]]([laid.mine.id], "자기 프로젝트의 세션"),
            ),
            Same("terminating", list(payload.terminating), []),
            Same("force_terminated", list(payload.force_terminated), []),
            Same("skipped", list(payload.skipped), []),
            Held[list[UUID]](
                "failed[*].session_id",
                [one.session_id for one in payload.failed],
                SameAs[list[UUID]]([laid.theirs.id], "다른 프로젝트의 세션"),
            ),
            Skipped("failed[*].message", MESSAGE_IS_FREE_TEXT),
        ]


@dataclass(frozen=True)
class SessionsInTwoProjectsAndAReaderOfOne(Given[Any, TwoSessionsAndACaller]):
    """서로 다른 프로젝트의 세션 둘과, 첫 프로젝트에서만 세션을 읽을 수 있는 사용자."""

    @override
    def describe(self) -> str:
        return (
            "서로 다른 프로젝트에서 기다리는 세션 둘과, "
            "첫 프로젝트 범위에서만 세션을 읽을 수 있는 일반 사용자 한 명"
        )

    @override
    async def lay(self, seeding: Any) -> TwoSessionsAndACaller:
        here = await lay_a_place(seeding, slots=0)
        there = await lay_a_place(seeding, slots=0)
        mine = await lay_a_pending_session(seeding, here)
        theirs = await lay_a_pending_session(seeding, there)
        caller = await seeding.within(
            SomeoneReadingSessionsIn(
                here.domain, here.project, lambda p: ProjectID(p.id), "프로젝트"
            )
        )
        return TwoSessionsAndACaller(seeding.made(mine), seeding.made(theirs), seeding.made(caller))


@dataclass(frozen=True)
class MineAnswersItsAllocationTheirsIsRefused(
    Then[TwoSessionsAndACaller, list[ResourceAllocationGQLDTO | Exception]]
):
    """자기 프로젝트의 세션은 할당으로, 다른 프로젝트의 세션은 거부로 답한다."""

    @override
    def says(self) -> str:
        return "자기 프로젝트의 세션은 빈 할당으로, 다른 프로젝트의 세션은 권한 부족의 거부로, 요청한 순서대로 답한다"

    @override
    def look(
        self,
        laid: TwoSessionsAndACaller,
        answered: Answered[list[ResourceAllocationGQLDTO | Exception]],
    ) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        mine = items[0] if len(items) > 0 else None
        theirs = items[1] if len(items) > 1 else None
        seen: list[Verdict] = [Same("len(items)", len(items), 2)]
        if isinstance(mine, ResourceAllocationGQLDTO):
            seen.extend([
                Same("items[0].requested.entries", mine.requested.entries, []),
                Same("items[0].used.entries", mine.used.entries, []),
                Same("items[0].allocated.entries", mine.allocated.entries, []),
            ])
        else:
            seen.append(Same("items[0]", mine, "할당"))
        seen.append(Refused(NotEnoughPermission, theirs if isinstance(theirs, Exception) else None))
        return seen
