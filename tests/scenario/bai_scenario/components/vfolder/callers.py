"""폴더 시나리오의 전제 — 요청이 오기 전에 무엇이 서 있는가.

전제마다 자기가 심는 행을 직접 적는다. 권한을 어느 스코프에 주는지가 시나리오의 핵심이라
그 자리를 감추면 표를 읽어도 무엇을 확인하는지 알 수 없기 때문이다. 그래서 같은 모양이
여러 번 나오더라도 묶지 않는다.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from bai_scenario.components.domain import WAS_HERE, SomeoneOf
from bai_scenario.components.vfolder.stage import (
    MAKING,
    STORAGE_HOST,
    AFolderAndACaller,
    AFolderMakerAndTheirDomain,
    AProjectAndACaller,
)
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.project.project import SeedProject
from bai_scenario.seeds.rbac.role import SeedPermission, SeedRole
from bai_scenario.seeds.resource_policy.project import SeedProjectPolicy
from bai_scenario.seeds.vfolder.vfolder import SeedFolderOf

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.vfolder.types import VFolderOperationStatus
from ai.backend.testutils.scenario_steps import Given


@dataclass(frozen=True)
class SomeoneGrantedOverThemselves(Given[Any, AFolderMakerAndTheirDomain]):
    """자기 스코프에 폴더 권한을 받은 사용자 한 명. 아직 폴더는 없다.

    이 자리의 권한으로는 폴더를 만들고 내 폴더를 검색할 수 있다. 이미 만들어진 폴더에는
    미치지 않는다.
    """

    permissions: Sequence[Permission] = MAKING

    @override
    def describe(self) -> str:
        return "폴더를 받아줄 도메인과, 자기 스코프에 폴더 권한을 받은 사용자 한 명"

    @override
    async def lay(self, seeding: SeedingSession) -> AFolderMakerAndTheirDomain:
        domain = await seeding.creating(
            SeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        caller = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        role = await seeding.creating_from(
            SeedRole(lambda u: UserID(u.id), name_hint="folder-role"), caller
        )
        for one in self.permissions:
            await seeding.adding(
                SeedPermission(entity_type=VFolderEntityType(), permission=one), role
            )
        await seeding.granting(role, caller, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return AFolderMakerAndTheirDomain(seeding.made(domain), seeding.made(caller))


@dataclass(frozen=True)
class SomeoneGrantedNothing(Given[Any, AFolderMakerAndTheirDomain]):
    """아무 권한도 받지 않은 사용자 한 명. 역할만 시나리오가 고른다."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"폴더를 받아줄 도메인과, 아무 권한도 받지 않은 {self.role.value} 한 명"

    @override
    async def lay(self, seeding: SeedingSession) -> AFolderMakerAndTheirDomain:
        domain = await seeding.creating(
            SeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        caller = await seeding.within(
            SomeoneOf(domain, role=self.role, vfolder_hosts=[STORAGE_HOST])
        )
        return AFolderMakerAndTheirDomain(seeding.made(domain), seeding.made(caller))


@dataclass(frozen=True)
class SomeoneWhoMadeAFolderThemselves(Given[Any, AFolderAndACaller]):
    """자기 스코프에 생성 권한을 받고 폴더를 하나 만들어 둔 사용자.

    또 만들려는 요청이 무엇에 막히는지 보는 자리라, 권한은 만들기를 막는 쪽인 자기 스코프에
    준다.
    """

    max_vfolder_count: int = 10

    @override
    def describe(self) -> str:
        return "자기 스코프에 생성 권한을 받고 폴더를 하나 만들어 둔 사용자와 그 폴더"

    @override
    async def lay(self, seeding: SeedingSession) -> AFolderAndACaller:
        domain = await seeding.creating(
            SeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        caller = await seeding.within(
            SomeoneOf(
                domain, vfolder_hosts=[STORAGE_HOST], max_vfolder_count=self.max_vfolder_count
            )
        )
        role = await seeding.creating_from(
            SeedRole(lambda u: UserID(u.id), name_hint="folder-role"), caller
        )
        for one in MAKING:
            await seeding.adding(
                SeedPermission(entity_type=VFolderEntityType(), permission=one), role
            )
        await seeding.granting(role, caller, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        folder = await seeding.creating_from(SeedFolderOf(host=STORAGE_HOST), caller)
        made = seeding.made(caller)
        return AFolderAndACaller(seeding.made(folder), made, made)


@dataclass(frozen=True)
class SomeoneWhoseFolderIsInTheTrash(Given[Any, AFolderAndACaller]):
    """자기 스코프에 생성 권한을 받은 사용자와, 그 사람이 휴지통에 보낸 폴더 하나.

    휴지통에 있는 동안에는 이름이 아직 잡혀 있다. 되살리면 그 이름으로 돌아와야 하기
    때문이다.
    """

    @override
    def describe(self) -> str:
        return "자기 스코프에 생성 권한을 받은 사용자와, 그 사람이 휴지통에 보낸 폴더 하나"

    @override
    async def lay(self, seeding: SeedingSession) -> AFolderAndACaller:
        domain = await seeding.creating(
            SeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        caller = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        role = await seeding.creating_from(
            SeedRole(lambda u: UserID(u.id), name_hint="folder-role"), caller
        )
        for one in MAKING:
            await seeding.adding(
                SeedPermission(entity_type=VFolderEntityType(), permission=one), role
            )
        await seeding.granting(role, caller, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        folder = await seeding.creating_from(
            SeedFolderOf(host=STORAGE_HOST, status=VFolderOperationStatus.DELETE_PENDING), caller
        )
        made = seeding.made(caller)
        return AFolderAndACaller(seeding.made(folder), made, made)


@dataclass(frozen=True)
class SomeoneWhoseFolderIsGone(Given[Any, AFolderAndACaller]):
    """자기 스코프에 생성 권한을 받은 사용자와, 저장소에서 완전히 사라진 폴더 하나.

    행은 남아 있지만 이름 유일성 인덱스가 이 상태를 빼고 보므로, 그 이름은 다시 쓸 수 있다.
    """

    @override
    def describe(self) -> str:
        return "자기 스코프에 생성 권한을 받은 사용자와, 저장소에서 완전히 사라진 폴더 하나"

    @override
    async def lay(self, seeding: SeedingSession) -> AFolderAndACaller:
        domain = await seeding.creating(
            SeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        caller = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        role = await seeding.creating_from(
            SeedRole(lambda u: UserID(u.id), name_hint="folder-role"), caller
        )
        for one in MAKING:
            await seeding.adding(
                SeedPermission(entity_type=VFolderEntityType(), permission=one), role
            )
        await seeding.granting(role, caller, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        folder = await seeding.creating_from(
            SeedFolderOf(host=STORAGE_HOST, status=VFolderOperationStatus.DELETE_COMPLETE), caller
        )
        made = seeding.made(caller)
        return AFolderAndACaller(seeding.made(folder), made, made)


@dataclass(frozen=True)
class SomeoneGrantedOnAProject(Given[Any, AProjectAndACaller]):
    """프로젝트 하나와, 그 프로젝트에 폴더 권한을 받은 사용자."""

    permissions: Sequence[Permission] = MAKING

    @override
    def describe(self) -> str:
        return "프로젝트 하나와, 그 프로젝트에 폴더 권한을 받은 사용자 한 명"

    @override
    async def lay(self, seeding: SeedingSession) -> AProjectAndACaller:
        domain = await seeding.creating(
            SeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        policy = await seeding.once(SeedProjectPolicy())
        project = await seeding.creating_from_two(
            SeedProject(name_hint="team", vfolder_hosts=[STORAGE_HOST]), domain, policy
        )
        caller = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        role = await seeding.creating_from(
            SeedRole(lambda p: ProjectID(p.id), name_hint="folder-role"), project
        )
        for one in self.permissions:
            await seeding.adding(
                SeedPermission(entity_type=VFolderEntityType(), permission=one), role
            )
        await seeding.granting(role, caller, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return AProjectAndACaller(seeding.made(project), seeding.made(caller))


@dataclass(frozen=True)
class SomeoneGrantedNothingOnAProject(Given[Any, AProjectAndACaller]):
    """프로젝트 하나와, 그 프로젝트에 아무 권한도 받지 않은 사용자."""

    @override
    def describe(self) -> str:
        return "프로젝트 하나와, 그 프로젝트에 아무 권한도 받지 않은 사용자 한 명"

    @override
    async def lay(self, seeding: SeedingSession) -> AProjectAndACaller:
        domain = await seeding.creating(
            SeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        policy = await seeding.once(SeedProjectPolicy())
        project = await seeding.creating_from_two(
            SeedProject(name_hint="team", vfolder_hosts=[STORAGE_HOST]), domain, policy
        )
        caller = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        return AProjectAndACaller(seeding.made(project), seeding.made(caller))
