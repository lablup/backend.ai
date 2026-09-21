"""What a vfolder scenario table says besides the call."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.vfolder.response import VFolderNode
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.testutils.scenario_steps import Given, Held, Same, SameAs, Skipped, Verdict
from bai_scenario.components.domain import WAS_HERE, GrantedUser, SomeoneOf, WrittenByThisRun
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
class VFolderNodeLook:
    """폴더 노드 하나를 통째로 본다. 기대는 심은 폴더에서 온다."""

    started: datetime

    def verdicts(self, node: VFolderNode, folder: VFolderData, at: str = "") -> list[Verdict]:
        """``at``은 답이 목록일 때 원소 자리를 앞에 붙인다."""
        return [
            Held(f"{at}id", node.id, SameAs[UUID](folder.id, "심은 폴더")),
            Same(f"{at}host", node.host, STORAGE_HOST),
            Same(f"{at}status", node.status, "ready"),
            Same(f"{at}metadata.name", node.metadata.name, folder.name),
            Same(f"{at}metadata.cloneable", node.metadata.cloneable, False),
            Same(f"{at}metadata.last_used", node.metadata.last_used, None),
            Same(
                f"{at}access_control.ownership_type",
                node.access_control.ownership_type,
                folder.ownership_type.value,
            ),
            Held(
                f"{at}ownership.user_id",
                node.ownership.user_id,
                SameAs[UUID | None](folder.user, "폴더 주인"),
            ),
            Held(
                f"{at}ownership.project_id",
                node.ownership.project_id,
                SameAs[UUID | None](folder.group, "폴더가 놓인 프로젝트"),
            ),
            Held(
                f"{at}ownership.creator_id",
                node.ownership.creator_id,
                SameAs[UUID | None](folder.creator_id, "만든 사람"),
            ),
            Same(f"{at}ownership.creator_email", node.ownership.creator_email, folder.creator),
            Same(f"{at}unmanaged_path", node.unmanaged_path, None),
            Skipped(f"{at}metadata.usage_mode", "타입이 이미 값을 못박는다"),
            Skipped(f"{at}metadata.quota_scope_id", "주인의 id로 만들어져 실행마다 다르다"),
            Skipped(f"{at}access_control.permission", "마운트 권한이라 이 표가 묻는 것이 아니다"),
            Skipped(f"{at}quota", "저장소가 답하는 값이라 여기서 말할 수 없다"),
            Held(
                f"{at}metadata.created_at", node.metadata.created_at, WrittenByThisRun(self.started)
            ),
        ]


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
class AReaderAndTwoFolders:
    """읽으려는 사람과, 그 사람이 닿을 수 있는 폴더, 닿을 수 없는 폴더."""

    readable: VFolderData
    unreadable: VFolderData
    caller: UserData


@dataclass(frozen=True)
class SomeoneWithTheirFolderAndAnothers(Given[Any, AReaderAndTwoFolders]):
    """자기 개인 폴더를 읽을 수 있는 사용자와, 공유받지 않은 남의 개인 폴더 하나."""

    @override
    def describe(self) -> str:
        return (
            "자기 개인 폴더 하나를 가진, 자기 개인 프로젝트에서 폴더를 읽을 수 있는 사용자 한 명과, "
            "그 사람에게 공유되지 않은 남의 개인 폴더 하나"
        )

    @override
    async def lay(self, seeding: Any) -> AReaderAndTwoFolders:
        domain = await seeding.creating(
            SeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        reader = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        other = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        readable = await seeding.creating_from(SeedPersonalVFolder(host=STORAGE_HOST), reader)
        unreadable = await seeding.creating_from(SeedPersonalVFolder(host=STORAGE_HOST), other)
        own = await seeding.personal_project_of(reader)
        await seeding.within(SomeoneReadingFoldersIn(own, lambda p: ProjectID(p.id), reader))
        return AReaderAndTwoFolders(
            seeding.made(readable), seeding.made(unreadable), seeding.made(reader)
        )


@dataclass(frozen=True)
class SomeonesFolderAndTheSuperadmin(Given[Any, AFolderAndItsReader]):
    """남의 개인 폴더 하나와, 아무 역할도 받지 않은 슈퍼관리자."""

    @override
    def describe(self) -> str:
        return "남의 개인 폴더 하나와, 아무 역할도 받지 않은 슈퍼관리자 한 명"

    @override
    async def lay(self, seeding: Any) -> AFolderAndItsReader:
        domain = await seeding.creating(
            SeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        owner = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        superadmin = await seeding.within(SomeoneOf(domain, role=UserRole.SUPERADMIN))
        folder = await seeding.creating_from(SeedPersonalVFolder(host=STORAGE_HOST), owner)
        return AFolderAndItsReader(seeding.made(folder), seeding.made(superadmin))


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
