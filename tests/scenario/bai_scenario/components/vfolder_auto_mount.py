"""What a vfolder auto-mount scenario table says besides the call."""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder_auto_mount import VFolderAutoMountEntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.v2.vfolder_auto_mount.response import (
    SearchVFolderAutoMountsPayload,
    VFolderAutoMountNode,
)
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.data.vfolder.types import VFolderData
from ai.backend.manager.data.vfolder_auto_mount.types import VFolderAutoMountData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.scenario_steps import (
    Answered,
    Condition,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Says,
    Then,
    Verdict,
)
from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.components.vfolder import STORAGE_HOST
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.project.project import TestSeedProject
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.resource_policy.project import TestSeedProjectPolicy
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest
from bai_scenario.seeds.vfolder.vfolder import TestSeedPersonalVFolder, TestSeedProjectVFolder
from bai_scenario.seeds.vfolder_auto_mount.vfolder_auto_mount import TestSeedVFolderAutoMount

MOUNTED_AT = "/home/work/extra"
"""Where the scenarios mount the folder."""


@dataclass(frozen=True)
class AProjectFolderAndAutoMounts:
    """프로젝트, 그 프로젝트의 폴더, 그리고 부를 사람."""

    project: ProjectData
    folder: VFolderData
    caller: UserData
    mount: VFolderAutoMountData | None


@dataclass(frozen=True)
class SomeoneGrantedOnAutoMounts(TestSeedNest[Laid[None]]):
    """그 프로젝트 범위에서 자동 마운트에 주어진 권한을 받은 사용자."""

    project: Laid[ProjectData]
    someone: Laid[UserData]
    permissions: tuple[Permission, ...]

    @override
    def kind(self) -> str:
        names = ", ".join(permission.name or "" for permission in self.permissions)
        return Says(
            f"프로젝트 범위에서 vfolder 자동 마운트 {names} 권한을 받은 사용자 준비",
            english=(
                f"Prepare a user granted the {names} permission on vfolder auto-mounts "
                "in the project"
            ),
        )

    @override
    def lay(self, seed: TestSeeder) -> Laid[None]:
        role = seed.creating_from(
            TestSeedRole(lambda p: ProjectID(p.id), name_hint="auto-mount-user"), self.project
        )
        for permission in self.permissions:
            seed.adding(
                TestSeedPermission(entity_type=VFolderAutoMountEntityType(), permission=permission),
                role,
            )
        return seed.granting(
            role, self.someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id)
        )


@dataclass(frozen=True)
class AProjectFolderAndSomeone(Given[Any, AProjectFolderAndAutoMounts]):
    """프로젝트 하나와 그 프로젝트의 폴더 하나, 그리고 그 프로젝트에서 부를 사람.

    ``permissions``가 비어 있으면 아무 역할도 받지 않는다. ``mounted``이면 그 폴더가
    이미 자동 마운트되어 있다.
    """

    permissions: tuple[Permission, ...] = ()
    mounted: bool = False

    @override
    def describe(self) -> str:
        if self.permissions:
            names = ", ".join(permission.name or "" for permission in self.permissions)
            who_ko = f"자동 마운트에 {names} 권한을 받은"
            who_en = f"granted the {names} permission on auto-mounts"
        else:
            who_ko = "아무 권한도 받지 않은"
            who_en = "holding no permission"
        parts_ko = [f"프로젝트 하나와 그 프로젝트의 vfolder 하나, 그리고 {who_ko} 사용자 한 명"]
        parts_en = [f"a project with one vfolder and one user {who_en}"]
        if self.mounted:
            parts_ko.append("그 폴더가 자동 마운트된 상태")
            parts_en.append("the folder already auto-mounted")
        return Says(", 그리고 ".join(parts_ko), english=", and ".join(parts_en))

    @override
    async def lay(self, seeding: Any) -> AProjectFolderAndAutoMounts:
        domain = await seeding.creating(
            TestSeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        caller = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        policy = await seeding.once(TestSeedProjectPolicy())
        project = await seeding.creating_from_two(TestSeedProject(), domain, policy)
        folder = await seeding.creating_from_two(
            TestSeedProjectVFolder(host=STORAGE_HOST), project, caller
        )
        if self.permissions:
            await seeding.within(SomeoneGrantedOnAutoMounts(project, caller, self.permissions))
        mount = (
            await seeding.creating_from_two(
                TestSeedVFolderAutoMount(in_project=True), folder, caller
            )
            if self.mounted
            else None
        )
        return AProjectFolderAndAutoMounts(
            project=seeding.made(project),
            folder=seeding.made(folder),
            caller=seeding.made(caller),
            mount=seeding.made(mount) if mount is not None else None,
        )


@dataclass(frozen=True)
class AutoMountNodeLook:
    """자동 마운트 노드 하나를 통째로 본다. ``at`` 은 답이 목록일 때 원소 자리를 붙인다."""

    started: datetime
    destination: str = MOUNTED_AT
    permission: str = "ro"
    deleted: bool = False

    def verdicts(
        self, node: VFolderAutoMountNode, project_id: UUID, folder_id: UUID, at: str = ""
    ) -> list[Verdict]:
        return [
            Held(
                f"{at}id",
                node.id,
                SameAs(node.entity_id, Says("응답의 entity_id", english="the entity_id")),
            ),
            Same(f"{at}scope_type", node.scope_type, "project"),
            Held(
                f"{at}scope_id",
                node.scope_id,
                SameAs(
                    project_id,
                    Says("폴더가 놓인 프로젝트", english="the project the folder is in"),
                ),
            ),
            Held(
                f"{at}vfolder_id",
                node.vfolder_id,
                SameAs[UUID](
                    folder_id,
                    Says("자동 마운트한 vfolder", english="the auto-mounted vfolder"),
                ),
            ),
            Same(f"{at}mount_destination", node.mount_destination, self.destination),
            Same(f"{at}subpath", node.subpath, "."),
            Same(f"{at}mount_permission", node.mount_permission, self.permission),
            Held(f"{at}created_at", node.created_at, WrittenByThisRun(self.started)),
            Held(f"{at}updated_at", node.updated_at, WrittenByThisRun(self.started)),
            (
                Held(f"{at}deleted_at", node.deleted_at, WrittenByThisRun(self.started))
                if self.deleted
                else Same(f"{at}deleted_at", node.deleted_at, None)
            ),
        ]


@dataclass(frozen=True)
class TheAutoMountNode(Then[AProjectFolderAndAutoMounts, VFolderAutoMountNode]):
    """방금 다룬 자동 마운트가 통째로 온다. 값은 시나리오가 정한다."""

    started: datetime
    destination: str = MOUNTED_AT
    permission: str = "ro"
    deleted: bool = False

    @override
    def says(self) -> str:
        state_ko = "삭제된" if self.deleted else "살아 있는"
        state_en = "deleted" if self.deleted else "live"
        return Says(
            f"{state_ko} 자동 마운트 전체가 응답으로 옵니다",
            english=f"the whole {state_en} auto-mount comes back",
        )

    @override
    def look(
        self, laid: AProjectFolderAndAutoMounts, answered: Answered[VFolderAutoMountNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return AutoMountNodeLook(
            self.started, self.destination, self.permission, self.deleted
        ).verdicts(node, laid.project.id, laid.folder.id)


type MountedFolder = tuple[VFolderData, VFolderAutoMountData]


@dataclass(frozen=True)
class AProjectAndAutoMountsToSearch:
    """검색하는 사람과, 그 프로젝트 안팎에서 걸러질 자동 마운트들."""

    project: ProjectData
    first: MountedFolder
    second: MountedFolder
    excluded: MountedFolder
    outside: MountedFolder
    caller: UserData


@dataclass(frozen=True)
class AProjectWithAutoMountsToSearch(Given[Any, AProjectAndAutoMountsToSearch]):
    """프로젝트 안에서 걸러질 자동 마운트 둘과 걸러지지 않을 하나, 그리고 그 밖의 하나.

    ``permissions`` 는 그 프로젝트 범위에서 자동 마운트에 받는 권한이다. ``fragment`` 는
    걸러질 주소들에 공통으로 드는 조각이고, 나머지 하나에는 들지 않는다.
    """

    permissions: tuple[Permission, ...] = (Permission.READ,)
    fragment: str = "match"

    @override
    def describe(self) -> str:
        names = ", ".join(permission.name or "" for permission in self.permissions)
        return Says(
            f"주소에 {self.fragment}가 든 자동 마운트 둘과 들지 않는 자동 마운트 하나를 가진 "
            f"프로젝트 하나, 그 프로젝트 밖에서 주소에 {self.fragment}가 든 자동 마운트 하나, "
            f"그리고 그 프로젝트 범위에서 자동 마운트 {names} 권한을 받은 사용자 한 명",
            english=(
                f"a project with two auto-mounts whose destination holds {self.fragment} and one "
                f"whose does not, one auto-mount outside that project whose destination holds "
                f"{self.fragment}, and one user granted the {names} permission on auto-mounts in "
                "that project"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> AProjectAndAutoMountsToSearch:
        domain = await seeding.creating(
            TestSeedDomain(name_hint="home", description=WAS_HERE, vfolder_hosts=[STORAGE_HOST])
        )
        caller = await seeding.within(SomeoneOf(domain, vfolder_hosts=[STORAGE_HOST]))
        policy = await seeding.once(TestSeedProjectPolicy())
        project = await seeding.creating_from_two(TestSeedProject(), domain, policy)
        first_folder = await seeding.creating_from_two(
            TestSeedProjectVFolder(host=STORAGE_HOST), project, caller
        )
        first = await seeding.creating_from_two(
            TestSeedVFolderAutoMount(
                in_project=True, mount_destination=f"/home/work/{self.fragment}-one"
            ),
            first_folder,
            caller,
        )
        second_folder = await seeding.creating_from_two(
            TestSeedProjectVFolder(host=STORAGE_HOST), project, caller
        )
        second = await seeding.creating_from_two(
            TestSeedVFolderAutoMount(
                in_project=True, mount_destination=f"/home/work/{self.fragment}-two"
            ),
            second_folder,
            caller,
        )
        excluded_folder = await seeding.creating_from_two(
            TestSeedProjectVFolder(host=STORAGE_HOST), project, caller
        )
        excluded = await seeding.creating_from_two(
            TestSeedVFolderAutoMount(in_project=True, mount_destination="/home/work/other"),
            excluded_folder,
            caller,
        )
        personal_folder = await seeding.creating_from(
            TestSeedPersonalVFolder(host=STORAGE_HOST), caller
        )
        outside = await seeding.creating_from_two(
            TestSeedVFolderAutoMount(
                in_project=False, mount_destination=f"/home/work/{self.fragment}-three"
            ),
            personal_folder,
            caller,
        )
        if self.permissions:
            await seeding.within(SomeoneGrantedOnAutoMounts(project, caller, self.permissions))
        return AProjectAndAutoMountsToSearch(
            project=seeding.made(project),
            first=(seeding.made(first_folder), seeding.made(first)),
            second=(seeding.made(second_folder), seeding.made(second)),
            excluded=(seeding.made(excluded_folder), seeding.made(excluded)),
            outside=(seeding.made(personal_folder), seeding.made(outside)),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class TheseAutoMounts(Condition[Collection[UUID]]):
    """답에 든 자동 마운트가 정해진 것들과 같다. id 는 실행마다 달라 무엇인지로 말한다."""

    wanted: frozenset[UUID]
    named: Says

    @override
    def says(self) -> str:
        return self.named

    @override
    def holds(self, got: Collection[UUID]) -> bool:
        return len(got) == len(self.wanted) and frozenset(got) == self.wanted


@dataclass(frozen=True)
class TheMatchingAutoMountsInOrder(
    Then[AProjectAndAutoMountsToSearch, SearchVFolderAutoMountsPayload]
):
    """걸러진 자동 마운트 둘만 주소 순서로 실린 한 페이지가 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "걸러진 자동 마운트 둘만 주소 순서로 실린 한 페이지가 응답으로 옵니다",
            english=(
                "one page holding only the two matching auto-mounts in destination order comes back"
            ),
        )

    @override
    def look(
        self,
        laid: AProjectAndAutoMountsToSearch,
        answered: Answered[SearchVFolderAutoMountsPayload],
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("total_count", page.total_count, 2),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
            Same("items.length", len(page.items), 2),
        ]
        if len(page.items) != 2:
            return verdicts
        for at, (mounted, node) in enumerate(
            zip((laid.first, laid.second), page.items, strict=True)
        ):
            folder, mount = mounted
            verdicts.extend(
                AutoMountNodeLook(self.started, destination=mount.mount_destination).verdicts(
                    node, laid.project.id, folder.id, at=f"items[{at}]."
                )
            )
        verdicts.append(
            Held(
                "items ids",
                [node.id for node in page.items],
                TheseAutoMounts(
                    frozenset({laid.first[1].id, laid.second[1].id}),
                    Says("걸러진 자동 마운트 둘", english="the two matching auto-mounts"),
                ),
            )
        )
        return verdicts
