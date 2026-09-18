"""What a vfolder scenario table says besides the call."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.scenario_steps import Answered, Given, Refused, Same, Then, Verdict
from bai_scenario.components.domain import WAS_HERE, GrantedUser, SomeoneOf
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.entity_share.share import SeedShareTaken, SeedVFolderShare
from bai_scenario.seeds.project.project import SeedProject
from bai_scenario.seeds.rbac.role import SeedPermission, SeedRole
from bai_scenario.seeds.resource_policy.project import SeedProjectPolicy
from bai_scenario.seeds.seeder import Laid, Seeder, SeedNest, SeedRow
from bai_scenario.seeds.vfolder.vfolder import SeedPersonalVFolder, SeedProjectVFolder

STORAGE_HOST = "local:volume1"
"""The one host the faked storage manager answers for."""


def seed_domain_with_storage() -> SeedRow[DomainData]:
    """A domain whose folders may land on the host the fake answers for."""
    return SeedDomain(name_hint="home", vfolder_hosts=[STORAGE_HOST])


@dataclass(frozen=True)
class SomeoneMakingFolders(SeedNest[GrantedUser]):
    """자기 폴더를 만들고 조회할 수 있는 사용자.

    범위는 사용자 자신이다. 개인 폴더는 만든 사람의 스코프에 생기므로 역할도 거기 앉는다.
    """

    domain: Laid[DomainData]

    @override
    def kind(self) -> str:
        return "폴더를 만들 수 있는 사용자 준비"

    @override
    def lay(self, seed: Seeder) -> GrantedUser:
        someone = seed.within(SomeoneOf(self.domain, vfolder_hosts=[STORAGE_HOST]))
        role = seed.creating_from(
            SeedRole(lambda u: UserID(u.id), name_hint="folder-owner"), someone
        )
        seed.adding(
            SeedPermission(entity_type=VFolderEntityType(), permission=Permission.CREATE), role
        )
        seed.adding(
            SeedPermission(entity_type=VFolderEntityType(), permission=Permission.READ), role
        )
        grant = seed.granting(role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return GrantedUser(someone, grant)


@dataclass(frozen=True)
class AFolderMakerAndTheirDomain:
    """폴더를 만들 수 있는 사람과, 그 폴더가 놓일 도메인."""

    domain: DomainData
    caller: UserData


@dataclass(frozen=True)
class SomeoneWhoMayMakeFolders(Given[Any, AFolderMakerAndTheirDomain]):
    """폴더 생성·조회 권한을 받은 사용자와, 그 폴더를 받아줄 도메인."""

    @override
    def describe(self) -> str:
        return "폴더를 놓을 수 있는 도메인과, 거기서 폴더를 만들 수 있는 사용자 한 명"

    @override
    async def lay(self, seeding: Any) -> AFolderMakerAndTheirDomain:
        domain = await seeding.creating(
            SeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        granted = await seeding.within(SomeoneMakingFolders(domain))
        return AFolderMakerAndTheirDomain(seeding.made(domain), seeding.made(granted.user))


@dataclass(frozen=True)
class SomeoneReadingFoldersIn[S](SeedNest[Laid[None]]):
    """그 스코프에서 폴더를 읽을 수 있게 된 사용자."""

    scope: Laid[S]
    scope_of: Callable[[S], EntityIdentifier]
    someone: Laid[UserData]

    @override
    def kind(self) -> str:
        return "폴더 읽기 권한 부여"

    @override
    def lay(self, seed: Seeder) -> Laid[None]:
        role = seed.creating_from(SeedRole(self.scope_of, name_hint="folder-reader"), self.scope)
        seed.adding(
            SeedPermission(entity_type=VFolderEntityType(), permission=Permission.READ), role
        )
        return seed.granting(
            role, self.someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id)
        )


@dataclass(frozen=True)
class AFolderAndItsReader:
    """닿으려는 폴더 하나와, 닿으려는 사람."""

    folder: VFolderData
    caller: UserData


@dataclass(frozen=True)
class SomeoneWithAFolderOfTheirOwn(Given[Any, AFolderAndItsReader]):
    """자기 개인 폴더 하나를 가진 사용자. 개인 프로젝트에서 폴더를 읽을 수 있는지는 행이 정한다."""

    granted: bool

    @override
    def describe(self) -> str:
        grant = (
            "자기 개인 프로젝트에서 폴더를 읽을 수 있는"
            if self.granted
            else "아무 권한도 받지 않은"
        )
        return f"자기 개인 폴더 하나를 가진, {grant} 사용자 한 명"

    @override
    async def lay(self, seeding: Any) -> AFolderAndItsReader:
        domain = await seeding.creating(
            SeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        someone = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        folder = await seeding.creating_from(SeedPersonalVFolder(host=STORAGE_HOST), someone)
        if self.granted:
            own = await seeding.personal_project_of(someone)
            await seeding.within(SomeoneReadingFoldersIn(own, lambda p: ProjectID(p.id), someone))
        return AFolderAndItsReader(seeding.made(folder), seeding.made(someone))


@dataclass(frozen=True)
class AProjectFolderAndSomeone(Given[Any, AFolderAndItsReader]):
    """프로젝트 폴더 하나와 사용자 한 명. 그 프로젝트에서 폴더를 읽을 수 있는지는 행이 정한다."""

    granted: bool

    @override
    def describe(self) -> str:
        grant = "그 프로젝트에서 폴더를 읽을 수 있는" if self.granted else "아무 권한도 받지 않은"
        return f"폴더 하나를 가진 프로젝트와, {grant} 사용자 한 명"

    @override
    async def lay(self, seeding: Any) -> AFolderAndItsReader:
        domain = await seeding.creating(
            SeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        someone = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        policy = await seeding.once(SeedProjectPolicy())
        project = await seeding.creating_from_two(SeedProject(), domain, policy)
        folder = await seeding.creating_from_two(
            SeedProjectVFolder(host=STORAGE_HOST), project, someone
        )
        if self.granted:
            await seeding.within(
                SomeoneReadingFoldersIn(project, lambda p: ProjectID(p.id), someone)
            )
        return AFolderAndItsReader(seeding.made(folder), seeding.made(someone))


@dataclass(frozen=True)
class AFolderOfferedToSomeone(Given[Any, AFolderAndItsReader]):
    """남의 개인 폴더가 읽기로 공유 제안된 사용자. 받아들였는지는 행이 정한다."""

    accepted: bool

    @override
    def describe(self) -> str:
        answer = "받아들인" if self.accepted else "아직 답하지 않은"
        return (
            "남의 개인 폴더를 읽기로 공유 제안받아 "
            f"{answer}, 자기 개인 프로젝트에서 폴더를 읽을 수 있는 사용자 한 명"
        )

    @override
    async def lay(self, seeding: Any) -> AFolderAndItsReader:
        domain = await seeding.creating(
            SeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        owner = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        reader = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        folder = await seeding.creating_from(SeedPersonalVFolder(host=STORAGE_HOST), owner)
        offer = await seeding.creating_from_three(
            SeedVFolderShare(cap=Permission.READ), owner, folder, reader
        )
        if self.accepted:
            await seeding.accepting(SeedShareTaken(), offer)
        own = await seeding.personal_project_of(reader)
        await seeding.within(SomeoneReadingFoldersIn(own, lambda p: ProjectID(p.id), reader))
        return AFolderAndItsReader(seeding.made(folder), seeding.made(reader))


@dataclass(frozen=True)
class SomeoneWithNoGrant(Given[Any, AFolderMakerAndTheirDomain]):
    """폴더를 놓을 수 있는 도메인과, 아무 권한도 받지 않은 사용자 한 명."""

    @override
    def describe(self) -> str:
        return "폴더를 놓을 수 있는 도메인과, 아무 권한도 받지 않은 사용자 한 명"

    @override
    async def lay(self, seeding: Any) -> AFolderMakerAndTheirDomain:
        domain = await seeding.creating(
            SeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        caller = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        return AFolderMakerAndTheirDomain(seeding.made(domain), seeding.made(caller))


@dataclass(frozen=True)
class TwoFoldersAndAReaderOfOne:
    """자기 개인 폴더와 남의 개인 폴더, 그리고 자기 것만 읽을 수 있는 사람."""

    mine: VFolderData
    theirs: VFolderData
    caller: UserData


@dataclass(frozen=True)
class SomeoneWithTheirOwnFolderBesideAnothers(Given[Any, TwoFoldersAndAReaderOfOne]):
    """자기 개인 프로젝트에서 폴더를 읽을 수 있는 사용자와, 그 사람의 폴더, 그리고 남의 폴더."""

    @override
    def describe(self) -> str:
        return "자기 개인 폴더 하나를 가진, 자기 개인 프로젝트에서 폴더를 읽을 수 있는 사용자 한 명과, 남의 개인 폴더 하나"

    @override
    async def lay(self, seeding: Any) -> TwoFoldersAndAReaderOfOne:
        domain = await seeding.creating(
            SeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        reader = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        mine = await seeding.creating_from(SeedPersonalVFolder(host=STORAGE_HOST), reader)
        own = await seeding.personal_project_of(reader)
        await seeding.within(SomeoneReadingFoldersIn(own, lambda p: ProjectID(p.id), reader))
        other = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        theirs = await seeding.creating_from(SeedPersonalVFolder(host=STORAGE_HOST), other)
        return TwoFoldersAndAReaderOfOne(
            seeding.made(mine), seeding.made(theirs), seeding.made(reader)
        )


@dataclass(frozen=True)
class MineAnswersItsBitsTheirsIsRefused(
    Then[TwoFoldersAndAReaderOfOne, list[list[PermissionBitDTO] | Exception]]
):
    """자기 폴더는 받은 권한 비트로, 남의 폴더는 거부로 답한다."""

    @override
    def says(self) -> str:
        return "자기 폴더는 읽기 비트로, 남의 폴더는 권한 부족의 거부로, 요청한 순서대로 답한다"

    @override
    def look(
        self,
        laid: TwoFoldersAndAReaderOfOne,
        answered: Answered[list[list[PermissionBitDTO] | Exception]],
    ) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        mine = items[0] if len(items) > 0 else None
        theirs = items[1] if len(items) > 1 else None
        return [
            Same("len(items)", len(items), 2),
            Same("items[0]", mine, [PermissionBitDTO.READ]),
            Refused(NotEnoughPermission, theirs if isinstance(theirs, Exception) else None),
        ]
