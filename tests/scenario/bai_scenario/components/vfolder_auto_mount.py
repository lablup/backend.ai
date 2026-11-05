"""What a vfolder auto-mount scenario table says besides the call."""

from __future__ import annotations

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
from bai_scenario.seeds.vfolder.vfolder import TestSeedProjectVFolder
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
        return [
            Held(
                "id",
                node.id,
                SameAs(node.entity_id, Says("응답의 entity_id", english="the entity_id")),
            ),
            Same("scope_type", node.scope_type, "project"),
            Held(
                "scope_id",
                node.scope_id,
                SameAs(
                    laid.project.id,
                    Says("폴더가 놓인 프로젝트", english="the project the folder is in"),
                ),
            ),
            Held(
                "vfolder_id",
                node.vfolder_id,
                SameAs[UUID](
                    laid.folder.id,
                    Says("자동 마운트한 vfolder", english="the auto-mounted vfolder"),
                ),
            ),
            Same("mount_destination", node.mount_destination, self.destination),
            Same("subpath", node.subpath, "."),
            Same("mount_permission", node.mount_permission, self.permission),
            Held("created_at", node.created_at, WrittenByThisRun(self.started)),
            Held("updated_at", node.updated_at, WrittenByThisRun(self.started)),
            (
                Held("deleted_at", node.deleted_at, WrittenByThisRun(self.started))
                if self.deleted
                else Same("deleted_at", node.deleted_at, None)
            ),
        ]


@dataclass(frozen=True)
class OneAutoMountOnPage(Then[AProjectFolderAndAutoMounts, SearchVFolderAutoMountsPayload]):
    """자동 마운트 하나가 실린 한 페이지가 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "자동 마운트 하나가 실린 한 페이지가 응답으로 옵니다",
            english="one page holding the one auto-mount comes back",
        )

    @override
    def look(
        self, laid: AProjectFolderAndAutoMounts, answered: Answered[SearchVFolderAutoMountsPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("total_count", page.total_count, 1),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
            Same("items.length", len(page.items), 1),
        ]
        if page.items:
            verdicts.extend(
                TheAutoMountNode(started=self.started).look(laid, Answered(response=page.items[0]))
            )
        return verdicts
