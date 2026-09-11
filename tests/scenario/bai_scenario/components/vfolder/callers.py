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
    READING,
    RETIRING,
    STORAGE_HOST,
    AFolderAndACaller,
    AFolderMakerAndTheirDomain,
    APersonalProjectAndItsOwner,
    AProjectAndACaller,
    FoldersAndACaller,
)
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.project.project import SeedProject
from bai_scenario.seeds.rbac.role import SeedPermission, SeedRole
from bai_scenario.seeds.resource_policy.project import SeedProjectPolicy
from bai_scenario.seeds.vfolder.vfolder import SeedFolderOf, SeedProjectFolderOf

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.types import VFolderHostPermission
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.vfolder.types import VFolderOperationStatus
from ai.backend.manager.models.project.lookups import PersonalProjectOfUserLookup
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
class SomeoneGrantedOverTheDomainWithAFolder(Given[Any, AFolderAndACaller]):
    """도메인 스코프에 폴더 권한을 받고 폴더를 하나 가진 사용자.

    이미 존재하는 폴더에 닿으려면 권한이 도메인에 있어야 한다. 폴더가 사는 개인 프로젝트를
    앞 단계가 지목할 수 없기 때문이다.
    """

    permissions: Sequence[Permission] = READING
    host_permissions: Sequence[VFolderHostPermission] = tuple(VFolderHostPermission)
    status: VFolderOperationStatus = VFolderOperationStatus.READY

    @override
    def describe(self) -> str:
        if self.status is VFolderOperationStatus.DELETE_PENDING:
            return "도메인 스코프에 폴더 권한을 받은 사용자와, 그 사람이 지워 휴지통에 둔 폴더"
        return "도메인 스코프에 폴더 권한을 받은 사용자와, 그 사람이 가진 폴더 하나"

    @override
    async def lay(self, seeding: SeedingSession) -> AFolderAndACaller:
        domain = await seeding.creating(
            SeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        caller = await seeding.within(
            SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST], host_permissions=self.host_permissions)
        )
        role = await seeding.creating_from(
            SeedRole(lambda d: DomainID(d.id), name_hint="folder-role"), domain
        )
        for one in self.permissions:
            await seeding.adding(
                SeedPermission(entity_type=VFolderEntityType(), permission=one), role
            )
        await seeding.granting(role, caller, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        folder = await seeding.creating_from(
            SeedFolderOf(host=STORAGE_HOST, status=self.status), caller
        )
        made = seeding.made(caller)
        return AFolderAndACaller(seeding.made(folder), made, made)


@dataclass(frozen=True)
class SomeoneElsesFolder(Given[Any, AFolderAndACaller]):
    """남이 가진 폴더 하나와, 그 폴더에 아무 권한도 받지 않은 다른 사용자."""

    role: UserRole = UserRole.USER
    status: VFolderOperationStatus = VFolderOperationStatus.READY

    @override
    def describe(self) -> str:
        return f"남이 가진 폴더 하나와, 아무 권한도 받지 않은 {self.role.value} 한 명"

    @override
    async def lay(self, seeding: SeedingSession) -> AFolderAndACaller:
        domain = await seeding.creating(
            SeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        owner = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        owners_role = await seeding.creating_from(
            SeedRole(lambda d: DomainID(d.id), name_hint="owner-role"), domain
        )
        for one in MAKING:
            await seeding.adding(
                SeedPermission(entity_type=VFolderEntityType(), permission=one), owners_role
            )
        await seeding.granting(
            owners_role, owner, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id)
        )
        folder = await seeding.creating_from(
            SeedFolderOf(host=STORAGE_HOST, status=self.status), owner
        )
        caller = await seeding.within(
            SomeoneOf(domain, role=self.role, vfolder_hosts=[STORAGE_HOST])
        )
        return AFolderAndACaller(seeding.made(folder), seeding.made(caller), seeding.made(owner))


@dataclass(frozen=True)
class SomeoneElsesTrashedFolderAndABroadGrant(Given[Any, AFolderAndACaller]):
    """남이 휴지통에 보낸 폴더와, 도메인 전체의 폴더에 지우기 권한을 받은 다른 사용자.

    권한을 넓게 받아도 남이 지운 폴더에는 미치지 않는다는 것을 보는 자리다.
    """

    @override
    def describe(self) -> str:
        return "남이 휴지통에 보낸 폴더와, 도메인 스코프에 폴더 지우기 권한을 받은 다른 사용자"

    @override
    async def lay(self, seeding: SeedingSession) -> AFolderAndACaller:
        domain = await seeding.creating(
            SeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        owner = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        owners_role = await seeding.creating_from(
            SeedRole(lambda d: DomainID(d.id), name_hint="owner-role"), domain
        )
        for one in MAKING:
            await seeding.adding(
                SeedPermission(entity_type=VFolderEntityType(), permission=one), owners_role
            )
        await seeding.granting(
            owners_role, owner, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id)
        )
        folder = await seeding.creating_from(
            SeedFolderOf(host=STORAGE_HOST, status=VFolderOperationStatus.DELETE_PENDING), owner
        )
        caller = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        callers_role = await seeding.creating_from(
            SeedRole(lambda d: DomainID(d.id), name_hint="folder-role"), domain
        )
        for one in RETIRING:
            await seeding.adding(
                SeedPermission(entity_type=VFolderEntityType(), permission=one), callers_role
            )
        await seeding.granting(
            callers_role, caller, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id)
        )
        return AFolderAndACaller(seeding.made(folder), seeding.made(caller), seeding.made(owner))


@dataclass(frozen=True)
class TheirFoldersAndANeighbours(Given[Any, FoldersAndACaller]):
    """자기 스코프에 읽기 권한을 받은 사용자의 폴더 몇 개와, 같은 도메인에 있는 남의 폴더."""

    own: int = 2
    others: int = 1

    @override
    def describe(self) -> str:
        return f"자기 폴더 {self.own}개와 남의 폴더 {self.others}개, 그리고 그 폴더들의 주인"

    @override
    async def lay(self, seeding: SeedingSession) -> FoldersAndACaller:
        domain = await seeding.creating(
            SeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        caller = await seeding.within(
            SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST], max_vfolder_count=max(self.own, 10))
        )
        role = await seeding.creating_from(
            SeedRole(lambda u: UserID(u.id), name_hint="folder-role"), caller
        )
        for one in READING:
            await seeding.adding(
                SeedPermission(entity_type=VFolderEntityType(), permission=one), role
            )
        await seeding.granting(role, caller, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        own = [
            await seeding.creating_from(SeedFolderOf(host=STORAGE_HOST), caller)
            for _ in range(self.own)
        ]
        others = []
        for _ in range(self.others):
            neighbour = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
            others.append(
                await seeding.creating_from(
                    SeedFolderOf(host=STORAGE_HOST, name_hint="theirs"), neighbour
                )
            )
        return FoldersAndACaller(
            tuple(seeding.made(one) for one in own),
            tuple(seeding.made(one) for one in others),
            seeding.made(caller),
        )


@dataclass(frozen=True)
class FoldersOfTwoOthers(Given[Any, FoldersAndACaller]):
    """주인이 서로 다른 폴더 둘과, 아무 권한도 받지 않았지만 전부 보는 역할의 사용자."""

    role: UserRole = UserRole.SUPERADMIN

    @override
    def describe(self) -> str:
        return f"주인이 서로 다른 폴더 둘과, 아무 권한도 받지 않은 {self.role.value} 한 명"

    @override
    async def lay(self, seeding: SeedingSession) -> FoldersAndACaller:
        domain = await seeding.creating(
            SeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        folders = []
        for _ in range(2):
            neighbour = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
            folders.append(
                await seeding.creating_from(
                    SeedFolderOf(host=STORAGE_HOST, name_hint="theirs"), neighbour
                )
            )
        caller = await seeding.within(
            SomeoneOf(domain, role=self.role, vfolder_hosts=[STORAGE_HOST])
        )
        return FoldersAndACaller(
            tuple(seeding.made(one) for one in folders), (), seeding.made(caller)
        )


@dataclass(frozen=True)
class TheirFoldersToDelete(Given[Any, FoldersAndACaller]):
    """도메인 스코프에 지우기 권한을 받은 사용자와, 그 사람이 가진 폴더 둘."""

    own: int = 2

    @override
    def describe(self) -> str:
        return f"도메인 스코프에 폴더 지우기 권한을 받은 사용자와, 그 사람이 가진 폴더 {self.own}개"

    @override
    async def lay(self, seeding: SeedingSession) -> FoldersAndACaller:
        domain = await seeding.creating(
            SeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        caller = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        role = await seeding.creating_from(
            SeedRole(lambda d: DomainID(d.id), name_hint="folder-role"), domain
        )
        for one in RETIRING:
            await seeding.adding(
                SeedPermission(entity_type=VFolderEntityType(), permission=one), role
            )
        await seeding.granting(role, caller, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        own = [
            await seeding.creating_from(SeedFolderOf(host=STORAGE_HOST), caller)
            for _ in range(self.own)
        ]
        return FoldersAndACaller(tuple(seeding.made(one) for one in own), (), seeding.made(caller))


@dataclass(frozen=True)
class FoldersTheCallerMayAndMayNotDelete(Given[Any, FoldersAndACaller]):
    """자기 도메인의 자기 폴더 하나와, 다른 도메인에 있는 남의 폴더 하나.

    권한은 그것이 걸린 도메인 안에서만 통하므로, 한 요청에 둘을 함께 주면 하나는 지워지고
    하나는 막힌다.
    """

    @override
    def describe(self) -> str:
        return "자기 도메인의 자기 폴더 하나와, 다른 도메인에 있는 남의 폴더 하나"

    @override
    async def lay(self, seeding: SeedingSession) -> FoldersAndACaller:
        home = await seeding.creating(
            SeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        caller = await seeding.within(SomeoneOf(home, vfolder_hosts=[STORAGE_HOST]))
        role = await seeding.creating_from(
            SeedRole(lambda d: DomainID(d.id), name_hint="folder-role"), home
        )
        for one in RETIRING:
            await seeding.adding(
                SeedPermission(entity_type=VFolderEntityType(), permission=one), role
            )
        await seeding.granting(role, caller, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        mine = await seeding.creating_from(SeedFolderOf(host=STORAGE_HOST), caller)
        elsewhere = await seeding.creating(
            SeedDomain(name_hint="elsewhere", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        neighbour = await seeding.within(SomeoneOf(elsewhere, vfolder_hosts=[STORAGE_HOST]))
        theirs = await seeding.creating_from(
            SeedFolderOf(host=STORAGE_HOST, name_hint="theirs"), neighbour
        )
        return FoldersAndACaller(
            (seeding.made(mine),), (seeding.made(theirs),), seeding.made(caller)
        )


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


@dataclass(frozen=True)
class SomeoneNamingTheirPersonalProject(Given[Any, APersonalProjectAndItsOwner]):
    """사용자를 만들 때 딸려 만들어진 개인 프로젝트와, 거기에 생성 권한을 받은 그 사용자.

    개인 프로젝트는 시나리오가 심는 것이 아니라 사용자 생성이 함께 쓰는 행이라, 그 id는
    매니저의 조회 spec으로 찾는다.
    """

    @override
    def describe(self) -> str:
        return "사용자를 만들 때 딸려 만들어진 개인 프로젝트와, 거기에 생성 권한을 받은 그 사용자"

    @override
    async def lay(self, seeding: SeedingSession) -> APersonalProjectAndItsOwner:
        domain = await seeding.creating(
            SeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        caller = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        personal = await seeding.looking_up(
            PersonalProjectOfUserLookup(user_id=UserID(seeding.made(caller).id))
        )
        role = await seeding.creating_from(
            SeedRole(lambda _: personal, name_hint="folder-role"), caller
        )
        for one in MAKING:
            await seeding.adding(
                SeedPermission(entity_type=VFolderEntityType(), permission=one), role
            )
        await seeding.granting(role, caller, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return APersonalProjectAndItsOwner(personal, seeding.made(caller))


@dataclass(frozen=True)
class AProjectFolderAndANeighboursOwn(Given[Any, AProjectAndACaller]):
    """프로젝트가 가진 폴더 하나와, 같은 도메인에 있는 남의 개인 폴더 하나.

    프로젝트를 검색하면 그 프로젝트 것만 나와야 한다는 것을 보는 자리다.
    """

    @override
    def describe(self) -> str:
        return (
            "프로젝트 폴더 하나와 남의 개인 폴더 하나, 그리고 그 프로젝트에 읽기 권한을 받은 사용자"
        )

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
        for one in READING:
            await seeding.adding(
                SeedPermission(entity_type=VFolderEntityType(), permission=one), role
            )
        await seeding.granting(role, caller, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        theirs = await seeding.creating_from_two(
            SeedProjectFolderOf(host=STORAGE_HOST), caller, project
        )
        neighbour = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        personal = await seeding.creating_from(
            SeedFolderOf(host=STORAGE_HOST, name_hint="theirs"), neighbour
        )
        return AProjectAndACaller(
            project=seeding.made(project),
            caller=seeding.made(caller),
            seen=(seeding.made(theirs),),
            unseen=(seeding.made(personal),),
        )
