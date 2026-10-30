"""What a session scenario table says besides the call."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.session.types import SessionEntityData
from ai.backend.manager.data.user.types import UserData
from ai.backend.testutils.scenario_steps import Given
from bai_scenario.components.domain import GrantedUser, SomeoneOf
from bai_scenario.components.resource_allocation import SomeoneReadingSessionsIn, lay_a_place
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest
from bai_scenario.seeds.session.session import TestSeedSession


@dataclass(frozen=True)
class SomeoneMakingSessions(TestSeedNest[GrantedUser]):
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
    def lay(self, seed: TestSeeder) -> GrantedUser:
        someone = seed.within(SomeoneOf(self.domain))
        role = seed.creating_from(
            TestSeedRole(lambda p: ProjectID(p.id), name_hint="session-owner"), self.project
        )
        seed.adding(
            TestSeedPermission(entity_type=SessionEntityType(), permission=Permission.CREATE), role
        )
        seed.adding(
            TestSeedPermission(entity_type=SessionEntityType(), permission=Permission.READ), role
        )
        grant = seed.granting(role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return GrantedUser(someone, grant)


@dataclass(frozen=True)
class SomeoneTerminatingSessionsIn(TestSeedNest[Laid[UserData]]):
    """그 프로젝트에서 세션을 종료할 수 있는 사용자."""

    domain: Laid[DomainData]
    project: Laid[ProjectData]

    @override
    def kind(self) -> str:
        return "프로젝트 범위의 세션 soft delete 권한을 받은 사용자 준비"

    @override
    def lay(self, seed: TestSeeder) -> Laid[UserData]:
        someone = seed.within(SomeoneOf(self.domain))
        role = seed.creating_from(
            TestSeedRole(lambda p: ProjectID(p.id), name_hint="session-terminator"), self.project
        )
        seed.adding(
            TestSeedPermission(entity_type=SessionEntityType(), permission=Permission.SOFT_DELETE),
            role,
        )
        seed.granting(role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return someone


class Terminator(enum.Enum):
    """세션을 종료하려는 사람."""

    SUPERADMIN = "superadmin"
    PROJECT_GRANTEE = "project-grantee"
    NOBODY_GRANTED = "nobody-granted"


@dataclass(frozen=True)
class APendingSessionAndACaller:
    """대기 중인 세션 하나와, 그것을 종료하려는 사용자."""

    session: SessionEntityData
    caller: UserData


@dataclass(frozen=True)
class APendingSessionAndSomeone(Given[Any, APendingSessionAndACaller]):
    """대기 세션 하나와 그 세션을 종료하려는 사용자를 둔다."""

    who: Terminator

    @override
    def describe(self) -> str:
        match self.who:
            case Terminator.SUPERADMIN:
                return "대기 세션 하나와 슈퍼관리자 한 명"
            case Terminator.PROJECT_GRANTEE:
                return (
                    "대기 세션 하나와 그 프로젝트 범위에서 세션 soft delete 권한을 받은 "
                    "일반 사용자 한 명"
                )
            case Terminator.NOBODY_GRANTED:
                return "대기 세션 하나와 아무 권한도 받지 않은 일반 사용자 한 명"

    @override
    async def lay(self, seeding: Any) -> APendingSessionAndACaller:
        place = await lay_a_place(seeding, slots=0)
        session = await seeding.creating_from_three(
            TestSeedSession(access_key=place.access_key), place.project, place.owner, place.group
        )
        caller: Laid[UserData]
        match self.who:
            case Terminator.SUPERADMIN:
                caller = await seeding.within(SomeoneOf(place.domain, role=UserRole.SUPERADMIN))
            case Terminator.PROJECT_GRANTEE:
                caller = await seeding.within(
                    SomeoneTerminatingSessionsIn(place.domain, place.project)
                )
            case Terminator.NOBODY_GRANTED:
                caller = await seeding.within(SomeoneOf(place.domain))
        return APendingSessionAndACaller(session=seeding.made(session), caller=seeding.made(caller))


class SessionReader(enum.Enum):
    """세션의 할당을 읽으려는 사람."""

    PROJECT_GRANTEE = "project-grantee"
    NOBODY_GRANTED = "nobody-granted"


@dataclass(frozen=True)
class APendingSessionAndSomeoneReadingIt(Given[Any, APendingSessionAndACaller]):
    """대기 세션 하나와 그 세션의 할당을 읽으려는 사용자를 둔다."""

    who: SessionReader

    @override
    def describe(self) -> str:
        match self.who:
            case SessionReader.PROJECT_GRANTEE:
                return (
                    "대기 세션 하나와 그 프로젝트 범위에서 세션 조회 권한을 받은 일반 사용자 한 명"
                )
            case SessionReader.NOBODY_GRANTED:
                return "대기 세션 하나와 아무 권한도 받지 않은 일반 사용자 한 명"

    @override
    async def lay(self, seeding: Any) -> APendingSessionAndACaller:
        place = await lay_a_place(seeding, slots=0)
        session = await seeding.creating_from_three(
            TestSeedSession(access_key=place.access_key), place.project, place.owner, place.group
        )
        caller: Laid[UserData]
        match self.who:
            case SessionReader.PROJECT_GRANTEE:
                caller = await seeding.within(
                    SomeoneReadingSessionsIn(
                        place.domain, place.project, lambda p: ProjectID(p.id), "프로젝트"
                    )
                )
            case SessionReader.NOBODY_GRANTED:
                caller = await seeding.within(SomeoneOf(place.domain))
        return APendingSessionAndACaller(session=seeding.made(session), caller=seeding.made(caller))
