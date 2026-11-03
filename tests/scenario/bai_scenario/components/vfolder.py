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
from ai.backend.testutils.scenario_steps import (
    Given,
    Held,
    Same,
    SameAs,
    Says,
    Skipped,
    Verdict,
)
from bai_scenario.components.domain import WAS_HERE, GrantedUser, SomeoneOf, WrittenByThisRun
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.entity_share.share import TestSeedShareTaken, TestSeedVFolderShare
from bai_scenario.seeds.project.project import TestSeedProject
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.resource_policy.project import TestSeedProjectPolicy
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest, TestSeedRow
from bai_scenario.seeds.vfolder.vfolder import TestSeedPersonalVFolder, TestSeedProjectVFolder

STORAGE_HOST = "local:volume1"
"""The one host the faked storage manager answers for."""


def seed_domain_with_storage() -> TestSeedRow[DomainData]:
    """A domain whose folders may land on the host the fake answers for."""
    return TestSeedDomain(name_hint="home", vfolder_hosts=[STORAGE_HOST])


@dataclass(frozen=True)
class VFolderNodeLook:
    """폴더 노드 하나를 통째로 본다. 기대는 심은 폴더에서 온다.

    ``name``이 있으면 이름은 심은 이름 대신 그 값이어야 한다.
    """

    started: datetime
    status: str = "ready"
    name: str | None = None
    cloneable: bool = False

    def verdicts(self, node: VFolderNode, folder: VFolderData, at: str = "") -> list[Verdict]:
        """``at``은 답이 목록일 때 원소 자리를 앞에 붙인다."""
        return [
            Held(
                f"{at}id",
                node.id,
                SameAs[UUID](
                    folder.id, Says("미리 저장한 vfolder", english="the vfolder seeded in advance")
                ),
            ),
            Same(f"{at}host", node.host, STORAGE_HOST),
            Same(f"{at}status", node.status, self.status),
            Same(
                f"{at}metadata.name",
                node.metadata.name,
                folder.name if self.name is None else self.name,
            ),
            Same(f"{at}metadata.cloneable", node.metadata.cloneable, self.cloneable),
            Same(f"{at}metadata.last_used", node.metadata.last_used, None),
            Same(
                f"{at}access_control.ownership_type",
                node.access_control.ownership_type,
                folder.ownership_type.value,
            ),
            Held(
                f"{at}ownership.user_id",
                node.ownership.user_id,
                SameAs[UUID | None](
                    folder.user, Says("vfolder 소유자", english="the vfolder owner")
                ),
            ),
            Held(
                f"{at}ownership.project_id",
                node.ownership.project_id,
                SameAs[UUID | None](
                    folder.group,
                    Says(
                        "vfolder 가 놓인 프로젝트",
                        english="the project the vfolder is placed in",
                    ),
                ),
            ),
            Held(
                f"{at}ownership.creator_id",
                node.ownership.creator_id,
                SameAs[UUID | None](
                    folder.creator_id,
                    Says("생성한 사용자", english="the user who created the vfolder"),
                ),
            ),
            Same(f"{at}ownership.creator_email", node.ownership.creator_email, folder.creator),
            Same(f"{at}unmanaged_path", node.unmanaged_path, None),
            Skipped(
                f"{at}metadata.usage_mode",
                Says("타입이 이미 값을 고정합니다", english="the type already fixes the value"),
            ),
            Skipped(
                f"{at}metadata.quota_scope_id",
                Says(
                    "소유자의 id 로 생성되어 실행마다 다릅니다",
                    english="it is made from the owner's id, so it differs per run",
                ),
            ),
            Skipped(
                f"{at}access_control.permission",
                Says(
                    "마운트 권한이라 이 표가 확인하는 값이 아닙니다",
                    english="it is a mount permission, which this table does not check",
                ),
            ),
            Skipped(
                f"{at}quota",
                Says(
                    "저장소가 응답하는 값이라 여기서 말할 수 없습니다",
                    english="the storage answers it, so it cannot be stated here",
                ),
            ),
            Held(
                f"{at}metadata.created_at", node.metadata.created_at, WrittenByThisRun(self.started)
            ),
        ]


@dataclass(frozen=True)
class SomeoneMakingFolders(TestSeedNest[GrantedUser]):
    """자기 폴더를 만들고 조회할 수 있는 사용자.

    범위는 사용자 자신이다. 개인 폴더는 만든 사람의 스코프에 생기므로 역할도 거기 앉는다.
    """

    domain: Laid[DomainData]

    @override
    def kind(self) -> str:
        return Says(
            "vfolder 를 생성할 수 있는 사용자 준비",
            english="Prepare a user who can create vfolders",
        )

    @override
    def lay(self, seed: TestSeeder) -> GrantedUser:
        someone = seed.within(SomeoneOf(self.domain, vfolder_hosts=[STORAGE_HOST]))
        role = seed.creating_from(
            TestSeedRole(lambda u: UserID(u.id), name_hint="folder-owner"), someone
        )
        seed.adding(
            TestSeedPermission(entity_type=VFolderEntityType(), permission=Permission.CREATE), role
        )
        seed.adding(
            TestSeedPermission(entity_type=VFolderEntityType(), permission=Permission.READ), role
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
        return Says(
            "vfolder 를 놓을 수 있는 도메인과, 거기서 vfolder 를 생성할 수 있는 사용자 한 명",
            english=("a domain that can hold vfolders and one user who can create a vfolder there"),
        )

    @override
    async def lay(self, seeding: Any) -> AFolderMakerAndTheirDomain:
        domain = await seeding.creating(
            TestSeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        granted = await seeding.within(SomeoneMakingFolders(domain))
        return AFolderMakerAndTheirDomain(seeding.made(domain), seeding.made(granted.user))


@dataclass(frozen=True)
class SomeoneReadingFoldersIn[S](TestSeedNest[Laid[None]]):
    """그 스코프에서 폴더를 읽을 수 있게 된 사용자."""

    scope: Laid[S]
    scope_of: Callable[[S], EntityIdentifier]
    someone: Laid[UserData]

    @override
    def kind(self) -> str:
        return Says(
            "vfolder 읽기 권한 부여",
            english="Grant permission to read vfolders",
        )

    @override
    def lay(self, seed: TestSeeder) -> Laid[None]:
        role = seed.creating_from(
            TestSeedRole(self.scope_of, name_hint="folder-reader"), self.scope
        )
        seed.adding(
            TestSeedPermission(entity_type=VFolderEntityType(), permission=Permission.READ), role
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
        grant_ko = (
            "자기 개인 프로젝트에서 폴더를 읽을 수 있는"
            if self.granted
            else "아무 권한도 받지 않은"
        )
        grant_en = (
            "who can read vfolders in their personal project"
            if self.granted
            else "holding no permission"
        )
        return Says(
            f"자기 개인 vfolder 하나를 가진, {grant_ko} 사용자 한 명",
            english=f"one user with one personal vfolder of their own, {grant_en}",
        )

    @override
    async def lay(self, seeding: Any) -> AFolderAndItsReader:
        domain = await seeding.creating(
            TestSeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        someone = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        folder = await seeding.creating_from(TestSeedPersonalVFolder(host=STORAGE_HOST), someone)
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
        grant_ko = (
            "그 프로젝트에서 폴더를 읽을 수 있는" if self.granted else "아무 권한도 받지 않은"
        )
        grant_en = (
            "who can read vfolders in that project" if self.granted else "holding no permission"
        )
        return Says(
            f"vfolder 하나를 가진 프로젝트와, {grant_ko} 사용자 한 명",
            english=f"a project with one vfolder and one user {grant_en}",
        )

    @override
    async def lay(self, seeding: Any) -> AFolderAndItsReader:
        domain = await seeding.creating(
            TestSeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        someone = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        policy = await seeding.once(TestSeedProjectPolicy())
        project = await seeding.creating_from_two(TestSeedProject(), domain, policy)
        folder = await seeding.creating_from_two(
            TestSeedProjectVFolder(host=STORAGE_HOST), project, someone
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
        answer_ko = "받아들인" if self.accepted else "아직 응답하지 않은"
        answer_en = "accepted" if self.accepted else "not yet answered"
        return Says(
            f"남의 개인 vfolder 를 읽기로 공유 제안받아 {answer_ko}, "
            "자기 개인 프로젝트에서 vfolder 를 읽을 수 있는 사용자 한 명",
            english=(
                "one user offered another user's personal vfolder to read, "
                f"{answer_en}, and able to read vfolders in their personal project"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> AFolderAndItsReader:
        domain = await seeding.creating(
            TestSeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        owner = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        reader = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        folder = await seeding.creating_from(TestSeedPersonalVFolder(host=STORAGE_HOST), owner)
        offer = await seeding.creating_from_three(
            TestSeedVFolderShare(cap=Permission.READ), owner, folder, reader
        )
        if self.accepted:
            await seeding.accepting(TestSeedShareTaken(), offer)
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
        return Says(
            "자기 개인 vfolder 하나를 가진, 자기 개인 프로젝트에서 vfolder 를 읽을 수 있는 사용자 "
            "한 명과, 그 사람에게 공유되지 않은 남의 개인 vfolder 하나",
            english=(
                "one user with one personal vfolder of their own who can read vfolders in "
                "their personal project, and one other user's personal vfolder not shared "
                "with them"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> AReaderAndTwoFolders:
        domain = await seeding.creating(
            TestSeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        reader = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        other = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        readable = await seeding.creating_from(TestSeedPersonalVFolder(host=STORAGE_HOST), reader)
        unreadable = await seeding.creating_from(TestSeedPersonalVFolder(host=STORAGE_HOST), other)
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
        return Says(
            "남의 개인 vfolder 하나와, 아무 역할도 받지 않은 superadmin 한 명",
            english="one personal vfolder of another user and one superadmin holding no role",
        )

    @override
    async def lay(self, seeding: Any) -> AFolderAndItsReader:
        domain = await seeding.creating(
            TestSeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        owner = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        superadmin = await seeding.within(SomeoneOf(domain, role=UserRole.SUPERADMIN))
        folder = await seeding.creating_from(TestSeedPersonalVFolder(host=STORAGE_HOST), owner)
        return AFolderAndItsReader(seeding.made(folder), seeding.made(superadmin))


@dataclass(frozen=True)
class SomeoneWithNoGrant(Given[Any, AFolderMakerAndTheirDomain]):
    """폴더를 놓을 수 있는 도메인과, 아무 권한도 받지 않은 사용자 한 명."""

    @override
    def describe(self) -> str:
        return Says(
            "vfolder 를 놓을 수 있는 도메인과, 아무 권한도 받지 않은 사용자 한 명",
            english="a domain that can hold vfolders and one user holding no permission",
        )

    @override
    async def lay(self, seeding: Any) -> AFolderMakerAndTheirDomain:
        domain = await seeding.creating(
            TestSeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        caller = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        return AFolderMakerAndTheirDomain(seeding.made(domain), seeding.made(caller))


@dataclass(frozen=True)
class SomeoneGrantedOnFoldersIn[S](TestSeedNest[Laid[None]]):
    """그 스코프에서 폴더에 주어진 권한을 받은 사용자."""

    scope: Laid[S]
    scope_of: Callable[[S], EntityIdentifier]
    someone: Laid[UserData]
    permissions: tuple[Permission, ...]

    @override
    def kind(self) -> str:
        return Says("vfolder 권한 부여", english="Grant vfolder permissions")

    @override
    def lay(self, seed: TestSeeder) -> Laid[None]:
        role = seed.creating_from(
            TestSeedRole(self.scope_of, name_hint="folder-writer"), self.scope
        )
        for permission in self.permissions:
            seed.adding(
                TestSeedPermission(entity_type=VFolderEntityType(), permission=permission), role
            )
        return seed.granting(
            role, self.someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id)
        )


@dataclass(frozen=True)
class TwoOwnFoldersAndAnothers:
    """자기 개인 폴더 둘과 남의 개인 폴더 하나, 그리고 그것들에 손대려는 사람."""

    own: tuple[VFolderData, VFolderData]
    others: VFolderData
    caller: UserData


@dataclass(frozen=True)
class SomeoneWithTwoFoldersAndAnothers(Given[Any, TwoOwnFoldersAndAnothers]):
    """자기 개인 폴더 둘을 가진 사용자와, 공유받지 않은 남의 개인 폴더 하나.

    사용자가 자기 개인 프로젝트에서 폴더에 받은 권한은 행이 정한다.
    """

    permissions: tuple[Permission, ...] = ()

    @override
    def describe(self) -> str:
        if self.permissions:
            names = ", ".join(p.name for p in self.permissions if p.name is not None)
            grant_ko = f"자기 개인 프로젝트에서 폴더에 {names} 권한을 받은"
            grant_en = f"granted the {names} permission on vfolders in their personal project"
        else:
            grant_ko = "아무 권한도 받지 않은"
            grant_en = "holding no permission"
        return Says(
            f"자기 개인 vfolder 둘을 가진, {grant_ko} 사용자 한 명과, "
            "그 사람에게 공유되지 않은 남의 개인 vfolder 하나",
            english=(
                f"one user with two personal vfolders of their own, {grant_en}, and one "
                "other user's personal vfolder not shared with them"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> TwoOwnFoldersAndAnothers:
        domain = await seeding.creating(
            TestSeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        caller = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        other = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        first = await seeding.creating_from(
            TestSeedPersonalVFolder(host=STORAGE_HOST, name_hint="first"), caller
        )
        second = await seeding.creating_from(
            TestSeedPersonalVFolder(host=STORAGE_HOST, name_hint="second"), caller
        )
        others = await seeding.creating_from(TestSeedPersonalVFolder(host=STORAGE_HOST), other)
        if self.permissions:
            own = await seeding.personal_project_of(caller)
            await seeding.within(
                SomeoneGrantedOnFoldersIn(own, lambda p: ProjectID(p.id), caller, self.permissions)
            )
        return TwoOwnFoldersAndAnothers(
            (seeding.made(first), seeding.made(second)),
            seeding.made(others),
            seeding.made(caller),
        )
