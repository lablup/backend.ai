"""What a vfolder scenario table says besides the call."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.config import (
    PresetModelConfig,
    PresetModelDefinition,
    PresetModelServiceConfig,
)
from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.vfolder.response import VFolderNode
from ai.backend.common.types import (
    VFolderHostPermission,
    VFolderHostPermissionMap,
    VFolderUsageMode,
)
from ai.backend.manager.data.deployment_revision_preset.types import DeploymentRevisionPresetData
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.data.vfolder.types import VFolderData, VFolderOperationStatus
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Says,
    Skipped,
    Then,
    Verdict,
)
from bai_scenario.components.domain import WAS_HERE, GrantedUser, SomeoneOf, WrittenByThisRun
from bai_scenario.seeds.deployment.revision_preset import TestSeedDeploymentRevisionPreset
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.entity_share.share import TestSeedShareTaken, TestSeedVFolderShare
from bai_scenario.seeds.project.project import TestSeedProject
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.resource_group.resource_group import TestSeedResourceGroup
from bai_scenario.seeds.resource_policy.project import TestSeedProjectPolicy
from bai_scenario.seeds.runtime_variant.runtime_variant import TestSeedRuntimeVariant
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
class SomeoneHoldingFolderPermissions(TestSeedNest[Laid[None]]):
    """그 사용자 자신의 스코프에서 vfolder 권한을 받은 사용자."""

    someone: Laid[UserData]
    permissions: tuple[Permission, ...]
    name_hint: str = "folder-holder"

    @override
    def kind(self) -> str:
        names = ", ".join(permission.name or "" for permission in self.permissions)
        return Says(
            f"자기 스코프에서 vfolder {names} 권한을 받은 사용자 준비",
            english=f"Prepare a user granted the {names} permission on vfolders in their own scope",
        )

    @override
    def lay(self, seed: TestSeeder) -> Laid[None]:
        role = seed.creating_from(
            TestSeedRole(lambda u: UserID(u.id), name_hint=self.name_hint), self.someone
        )
        for permission in self.permissions:
            seed.adding(
                TestSeedPermission(entity_type=VFolderEntityType(), permission=permission), role
            )
        return seed.granting(
            role, self.someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id)
        )


@dataclass(frozen=True)
class AFolderAndPeople:
    """폴더 하나와, 그것을 부를 사람, 그리고 필요하면 또 한 사람."""

    folder: VFolderData
    caller: UserData
    other: UserData | None


@dataclass(frozen=True)
class SomeoneWithAFolder(Given[Any, AFolderAndPeople]):
    """자기 개인 폴더 하나를 가진 사용자. 그 폴더에 받은 권한은 행이 정한다.

    ``in_own_scope``이면 역할을 그 사용자의 스코프에, 아니면 개인 프로젝트에 앉힌다.
    ``with_other``이면 그 폴더와 상관없는 사용자 한 명을 함께 둔다.
    """

    permissions: tuple[Permission, ...] = ()
    status: VFolderOperationStatus = VFolderOperationStatus.READY
    usage_mode: VFolderUsageMode = VFolderUsageMode.GENERAL
    cloneable: bool = False
    in_own_scope: bool = False
    with_other: bool = False

    @override
    def describe(self) -> str:
        if self.permissions:
            names = ", ".join(permission.name or "" for permission in self.permissions)
            grant_ko = f"자기 개인 폴더에 {names} 권한을 받은"
            grant_en = f"granted the {names} permission on their personal folder"
        else:
            grant_ko = "아무 권한도 받지 않은"
            grant_en = "holding no permission"
        state_ko = (
            "사용할 수 있는 상태의"
            if self.status is VFolderOperationStatus.READY
            else f"{self.status.value} 상태의"
        )
        state_en = "ready" if self.status is VFolderOperationStatus.READY else self.status.value
        parts_ko = [f"{state_ko} 개인 vfolder 하나를 가진, {grant_ko} 사용자 한 명"]
        parts_en = [f"one user with one {state_en} personal vfolder, {grant_en}"]
        if self.with_other:
            parts_ko.append("그 폴더를 쓰지 않는 다른 사용자 한 명")
            parts_en.append("one other user who does not use that folder")
        return Says(", 그리고 ".join(parts_ko), english=", and ".join(parts_en))

    @override
    async def lay(self, seeding: Any) -> AFolderAndPeople:
        domain = await seeding.creating(
            TestSeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        caller = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        other = (
            await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
            if self.with_other
            else None
        )
        folder = await seeding.creating_from(
            TestSeedPersonalVFolder(
                host=STORAGE_HOST,
                status=self.status,
                usage_mode=self.usage_mode,
                cloneable=self.cloneable,
            ),
            caller,
        )
        if self.permissions:
            if self.in_own_scope:
                await seeding.within(SomeoneHoldingFolderPermissions(caller, self.permissions))
            else:
                own = await seeding.personal_project_of(caller)
                await seeding.within(
                    SomeoneGrantedOnFoldersIn(
                        own, lambda p: ProjectID(p.id), caller, self.permissions
                    )
                )
        return AFolderAndPeople(
            seeding.made(folder),
            seeding.made(caller),
            seeding.made(other) if other is not None else None,
        )


@dataclass(frozen=True)
class ATwoFoldersAndPeople:
    """자기 폴더 둘과, 그것을 부를 사람, 그리고 또 한 사람."""

    first: VFolderData
    second: VFolderData
    caller: UserData
    other: UserData


@dataclass(frozen=True)
class SomeoneWithTwoOwnFolders(Given[Any, ATwoFoldersAndPeople]):
    """자기 개인 폴더 둘을 가진 사용자와, 그 사람과 상관없는 다른 사용자 한 명."""

    permissions: tuple[Permission, ...] = ()
    first_status: VFolderOperationStatus = VFolderOperationStatus.READY
    second_status: VFolderOperationStatus = VFolderOperationStatus.READY
    first_cloneable: bool = False
    in_own_scope: bool = True

    @override
    def describe(self) -> str:
        if self.permissions:
            names = ", ".join(permission.name or "" for permission in self.permissions)
            grant_ko = f"자기 스코프에서 vfolder {names} 권한을 받은"
            grant_en = f"granted the {names} permission on vfolders in their own scope"
        else:
            grant_ko = "아무 권한도 받지 않은"
            grant_en = "holding no permission"
        return Says(
            f"자기 개인 vfolder 둘을 가진, {grant_ko} 사용자 한 명과, "
            "그 사람과 상관없는 다른 사용자 한 명",
            english=(
                f"one user with two personal vfolders of their own, {grant_en}, and "
                "one other user unrelated to them"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> ATwoFoldersAndPeople:
        domain = await seeding.creating(
            TestSeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        caller = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        other = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        first = await seeding.creating_from(
            TestSeedPersonalVFolder(
                host=STORAGE_HOST,
                name_hint="first",
                status=self.first_status,
                cloneable=self.first_cloneable,
            ),
            caller,
        )
        second = await seeding.creating_from(
            TestSeedPersonalVFolder(
                host=STORAGE_HOST, name_hint="second", status=self.second_status
            ),
            caller,
        )
        if self.permissions:
            if self.in_own_scope:
                await seeding.within(SomeoneHoldingFolderPermissions(caller, self.permissions))
            else:
                own = await seeding.personal_project_of(caller)
                await seeding.within(
                    SomeoneGrantedOnFoldersIn(
                        own, lambda p: ProjectID(p.id), caller, self.permissions
                    )
                )
        return ATwoFoldersAndPeople(
            seeding.made(first),
            seeding.made(second),
            seeding.made(caller),
            seeding.made(other),
        )


@dataclass(frozen=True)
class AProjectAndMaker:
    """폴더를 받아줄 프로젝트와, 거기서 폴더를 만들 사람."""

    project: ProjectData
    caller: UserData


@dataclass(frozen=True)
class AProjectWhereSomeoneMayMakeFolders(Given[Any, AProjectAndMaker]):
    """프로젝트 하나와, 그 프로젝트에서 폴더를 만들 수 있는지가 행으로 정해진 사용자."""

    granted: bool

    @override
    def describe(self) -> str:
        grant_ko = (
            "그 프로젝트에서 vfolder 생성 권한을 받은" if self.granted else "아무 권한도 받지 않은"
        )
        grant_en = (
            "granted vfolder create in that project" if self.granted else "holding no permission"
        )
        return Says(
            f"vfolder 를 받아줄 프로젝트와, {grant_ko} 사용자 한 명",
            english=f"a project that can hold vfolders and one user {grant_en}",
        )

    @override
    async def lay(self, seeding: Any) -> AProjectAndMaker:
        domain = await seeding.creating(
            TestSeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        caller = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        policy = await seeding.once(TestSeedProjectPolicy())
        project = await seeding.creating_from_two(
            TestSeedProject(
                allowed_vfolder_hosts=VFolderHostPermissionMap({
                    STORAGE_HOST: set(VFolderHostPermission),
                })
            ),
            domain,
            policy,
        )
        if self.granted:
            role = await seeding.creating_from(
                TestSeedRole(lambda p: ProjectID(p.id), name_hint="folder-maker"), project
            )
            await seeding.adding(
                TestSeedPermission(entity_type=VFolderEntityType(), permission=Permission.CREATE),
                role,
            )
            await seeding.granting(
                role, caller, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id)
            )
        return AProjectAndMaker(seeding.made(project), seeding.made(caller))


@dataclass(frozen=True)
class AModelFolderPlace:
    """배포가 놓일 프로젝트·자원 그룹과, 모델 폴더, 런타임 종류, 리비전 프리셋, 부를 사람."""

    domain: DomainData
    project: ProjectData
    resource_group: ResourceGroupData
    caller: UserData
    variant: RuntimeVariantData
    preset: DeploymentRevisionPresetData
    folder: VFolderData


@dataclass(frozen=True)
class AModelFolderForDeployment(Given[Any, AModelFolderPlace]):
    """모델 폴더 하나를 배포할 수 있는 자리와 사람. 폴더의 용도는 행이 정한다."""

    usage_mode: VFolderUsageMode = VFolderUsageMode.MODEL
    granted: bool = True

    @override
    def describe(self) -> str:
        mode = self.usage_mode.value
        grant_ko = "배포를 만들 수 있는" if self.granted else "아무 권한도 받지 않은"
        grant_en = (
            "granted deployment create in that project" if self.granted else "holding no permission"
        )
        return Says(
            f"배포를 놓을 프로젝트와 자원 그룹, {mode} 용도 vfolder 하나, 런타임 종류와 "
            f"리비전 프리셋, 그리고 {grant_ko} 사용자 한 명",
            english=(
                f"a project and a resource group to hold deployments, one {mode} vfolder, "
                f"a runtime variant and a revision preset, and one user {grant_en}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> AModelFolderPlace:
        domain = await seeding.creating(
            TestSeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        caller = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        policy = await seeding.once(TestSeedProjectPolicy())
        project = await seeding.creating_from_two(TestSeedProject(), domain, policy)
        group = await seeding.creating(TestSeedResourceGroup())
        folder = await seeding.creating_from_two(
            TestSeedProjectVFolder(host=STORAGE_HOST, usage_mode=self.usage_mode),
            project,
            caller,
        )
        if self.granted:
            await seeding.within(
                SomeoneGrantedOnFoldersIn(
                    project, lambda p: ProjectID(p.id), caller, (Permission.READ,)
                )
            )
            role = await seeding.creating_from(
                TestSeedRole(lambda p: ProjectID(p.id), name_hint="deployer"), project
            )
            await seeding.adding(
                TestSeedPermission(
                    entity_type=DeploymentEntityType(), permission=Permission.CREATE
                ),
                role,
            )
            await seeding.granting(
                role, caller, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id)
            )
        variant = await seeding.creating(TestSeedRuntimeVariant())
        preset = await seeding.creating_from(
            TestSeedDeploymentRevisionPreset(
                model_definition=PresetModelDefinition(
                    models=[
                        PresetModelConfig(name="model", service=PresetModelServiceConfig(port=8000))
                    ]
                )
            ),
            variant,
        )
        return AModelFolderPlace(
            domain=seeding.made(domain),
            project=seeding.made(project),
            resource_group=seeding.made(group),
            caller=seeding.made(caller),
            variant=seeding.made(variant),
            preset=seeding.made(preset),
            folder=seeding.made(folder),
        )


@dataclass(frozen=True)
class TheNewFolderNode(Then[AProjectAndMaker, VFolderNode]):
    """방금 만든 폴더가 통째로 온다. 이름과 소유는 시나리오가 정한 값이다."""

    started: datetime
    named: str
    ownership_type: str

    @override
    def says(self) -> str:
        return Says(
            "방금 만든 vfolder 전체가 응답으로 옵니다",
            english="the whole vfolder just created comes back",
        )

    @override
    def look(self, laid: AProjectAndMaker, answered: Answered[VFolderNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        owner_id = laid.caller.id if self.ownership_type == "user" else None
        return [
            Held(
                "id",
                node.id,
                SameAs[UUID](node.entity_id, Says("응답의 entity_id", english="the entity_id")),
            ),
            Same("host", node.host, STORAGE_HOST),
            Same("status", node.status, "ready"),
            Same("metadata.name", node.metadata.name, self.named),
            Same("metadata.cloneable", node.metadata.cloneable, False),
            Same("metadata.last_used", node.metadata.last_used, None),
            Same(
                "access_control.ownership_type",
                node.access_control.ownership_type,
                self.ownership_type,
            ),
            Held(
                "ownership.user_id",
                node.ownership.user_id,
                SameAs[UUID | None](owner_id, Says("폴더 소유자", english="the folder owner")),
            ),
            Held(
                "ownership.project_id",
                node.ownership.project_id,
                SameAs[UUID | None](
                    laid.project.id,
                    Says("폴더가 놓인 프로젝트", english="the project the folder landed in"),
                ),
            ),
            Held(
                "ownership.creator_id",
                node.ownership.creator_id,
                SameAs[UUID | None](laid.caller.id, Says("만든 사람", english="the creator")),
            ),
            Same("ownership.creator_email", node.ownership.creator_email, laid.caller.email),
            Same("unmanaged_path", node.unmanaged_path, None),
            Skipped(
                "metadata.usage_mode",
                Says("타입이 이미 값을 고정합니다", english="the type already fixes the value"),
            ),
            Skipped(
                "metadata.quota_scope_id",
                Says(
                    "소유자의 id 로 만들어져 실행마다 다릅니다",
                    english="it is made from the owner's id, so it differs per run",
                ),
            ),
            Skipped(
                "access_control.permission",
                Says(
                    "마운트 권한이라 이 표가 확인하는 값이 아닙니다",
                    english="it is a mount permission, which this table does not check",
                ),
            ),
            Skipped(
                "quota",
                Says(
                    "저장소가 응답하는 값이라 여기서 말할 수 없습니다",
                    english="the storage answers it, so it cannot be stated here",
                ),
            ),
            Held("metadata.created_at", node.metadata.created_at, WrittenByThisRun(self.started)),
        ]


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
    first_status: VFolderOperationStatus = VFolderOperationStatus.READY
    second_status: VFolderOperationStatus = VFolderOperationStatus.READY

    @override
    def describe(self) -> str:
        if self.permissions:
            names = ", ".join(p.name for p in self.permissions if p.name is not None)
            grant_ko = f"자기 개인 프로젝트에서 폴더에 {names} 권한을 받은"
            grant_en = f"granted the {names} permission on vfolders in their personal project"
        else:
            grant_ko = "아무 권한도 받지 않은"
            grant_en = "holding no permission"
        states = (self.first_status, self.second_status)
        if all(state is VFolderOperationStatus.READY for state in states):
            folders_ko = "자기 개인 vfolder 둘을 가진"
            folders_en = "with two personal vfolders of their own"
        else:
            one_ko = (
                "사용할 수 있는 상태"
                if states[0] is VFolderOperationStatus.READY
                else states[0].value
            )
            two_ko = (
                "사용할 수 있는 상태"
                if states[1] is VFolderOperationStatus.READY
                else states[1].value
            )
            one_en = "ready" if states[0] is VFolderOperationStatus.READY else states[0].value
            two_en = "ready" if states[1] is VFolderOperationStatus.READY else states[1].value
            folders_ko = (
                f"{one_ko}의 자기 개인 vfolder 하나와 {two_ko}의 자기 개인 vfolder 하나를 가진"
            )
            folders_en = (
                f"with one {one_en} personal vfolder of their own and one {two_en} personal "
                "vfolder of their own"
            )
        return Says(
            f"{folders_ko}, {grant_ko} 사용자 한 명과, "
            "그 사람에게 공유되지 않은 남의 개인 vfolder 하나",
            english=(
                f"one user {folders_en}, {grant_en}, and one other user's personal vfolder not "
                "shared with them"
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
            TestSeedPersonalVFolder(host=STORAGE_HOST, name_hint="first", status=self.first_status),
            caller,
        )
        second = await seeding.creating_from(
            TestSeedPersonalVFolder(
                host=STORAGE_HOST, name_hint="second", status=self.second_status
            ),
            caller,
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
