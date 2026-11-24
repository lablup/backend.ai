"""What a project scenario table says besides the call.

How the adapter is built lives in the tables' own conftest, and the rows a scenario
lays come from ``seeds``. This holds the situations worth naming more than once.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.group.response import ProjectNode
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.data.user.types import UserData
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
from bai_scenario.components.domain import WAS_HERE, Mentions, SomeoneOf, WrittenByThisRun
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.project.project import TestSeedProject
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.resource_group.resource_group import LinkToProject, TestSeedResourceGroup
from bai_scenario.seeds.resource_policy.project import TestSeedProjectPolicy
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest


@dataclass(frozen=True)
class ManyProjectsAndACaller:
    """건드릴 프로젝트 여럿과, 호출자."""

    targets: tuple[ProjectData, ...]
    caller: UserData


@dataclass(frozen=True)
class ManyProjectsAndSomeone(Given[Any, ManyProjectsAndACaller]):
    """한 도메인 아래의 프로젝트 여럿과, 다른 도메인에 사는 사용자 한 명."""

    role: UserRole = UserRole.USER
    count: int = 2

    @override
    def describe(self) -> str:
        return Says(
            f"한 도메인 아래의 프로젝트 {self.count}개와, 다른 도메인에 사는 {self.role.value} 한 명",
            english=(
                f"{self.count} projects under one domain and one {self.role.value} "
                "in another domain"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> ManyProjectsAndACaller:
        home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        target = await seeding.creating(TestSeedDomain(name_hint="target", description=WAS_HERE))
        policy = await seeding.once(TestSeedProjectPolicy())
        projects = [
            await seeding.creating_from_two(TestSeedProject(name_hint="team"), target, policy)
            for _ in range(self.count)
        ]
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        return ManyProjectsAndACaller(
            targets=tuple(seeding.made(one) for one in projects),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class ProjectLook:
    """미리 만든 프로젝트의 노드가 어떤 값으로 와야 하는지. 나머지 값은 미리 만든 것에서 읽는다."""

    started: datetime
    described: str | None = None
    active: bool = True

    def verdicts(self, prefix: str, node: ProjectNode, laid: ProjectData) -> list[Verdict]:
        written = WrittenByThisRun(self.started)
        described = self.described if self.described is not None else laid.description
        return [
            Same(f"{prefix}name", node.basic_info.name, laid.name),
            Same(f"{prefix}description", node.basic_info.description, described),
            Same(f"{prefix}integration_name", node.basic_info.integration_name, None),
            Same(f"{prefix}domain_name", node.organization.domain_name, laid.domain_name),
            Same(
                f"{prefix}resource_policy", node.organization.resource_policy, laid.resource_policy
            ),
            Same(f"{prefix}allowed_vfolder_hosts", node.storage.allowed_vfolder_hosts, []),
            Same(f"{prefix}is_active", node.lifecycle.is_active, self.active),
            Skipped(
                f"{prefix}id",
                Says("데이터베이스가 생성합니다", english="the database generates it"),
            ),
            Skipped(
                f"{prefix}type",
                Says("타입이 이미 값을 고정합니다", english="the type already fixes the value"),
            ),
            Held[UUID](
                f"{prefix}entity_id",
                node.entity_id,
                SameAs(
                    laid.id,
                    Says(
                        "미리 저장한 프로젝트의 id",
                        english="the id of the project seeded in advance",
                    ),
                ),
            ),
            Held(f"{prefix}created_at", node.lifecycle.created_at, written),
            Held(f"{prefix}modified_at", node.lifecycle.modified_at, written),
        ]


@dataclass(frozen=True)
class NoProjectIsProcessed(Then[ManyProjectsAndACaller, PartialBulkPayload[ProjectNode]]):
    """처리된 프로젝트 없이, 대상이 모두 같은 이유로 실패 목록에 온다."""

    reason: str

    @override
    def says(self) -> str:
        return Says(
            "처리된 프로젝트 없이 대상이 모두 실패 목록에 옵니다",
            english="no project is processed and every target comes back in the failed list",
        )

    @override
    def look(
        self,
        laid: ManyProjectsAndACaller,
        answered: Answered[PartialBulkPayload[ProjectNode]],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes", payload.successes, []),
            Same("failed count", len(payload.failed), len(laid.targets)),
        ]
        for i, (failure, project) in enumerate(zip(payload.failed, laid.targets, strict=False)):
            verdicts += [
                Held[UUID](
                    f"failed[{i}].id",
                    failure.id,
                    SameAs(
                        project.id,
                        Says("대상 프로젝트의 id", english="the id of the target project"),
                    ),
                ),
                Held(f"failed[{i}].message", failure.message, Mentions(self.reason)),
            ]
        return verdicts


@dataclass(frozen=True)
class SomeoneReadingProjectsOfTheGroup(TestSeedNest[Laid[None]]):
    """그 리소스 그룹 범위에서 프로젝트를 읽을 수 있는 사용자."""

    group: Laid[ResourceGroupData]
    user: Laid[UserData]

    @override
    def kind(self) -> str:
        return Says(
            "리소스 그룹 범위의 프로젝트 읽기 역할을 받은 사용자 준비",
            english="Prepare a user granted the project read role in the resource group scope",
        )

    @override
    def lay(self, seed: TestSeeder) -> Laid[None]:
        role = seed.creating_from(
            TestSeedRole(lambda g: ResourceGroupID(g.id), name_hint="project-reader"), self.group
        )
        seed.adding(
            TestSeedPermission(entity_type=ProjectEntityType(), permission=Permission.READ), role
        )
        return seed.granting(
            role, self.user, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id)
        )


@dataclass(frozen=True)
class ProjectsOfAGroupAndACaller:
    """리소스 그룹 하나, 그 그룹을 쓸 수 있는 프로젝트들, 그리고 부를 사람."""

    group: ResourceGroupData
    linked: tuple[ProjectData, ...]
    caller: UserData


@dataclass(frozen=True)
class ProjectsOfAGroupAndSomeone(Given[Any, ProjectsOfAGroupAndACaller]):
    """리소스 그룹 하나와 프로젝트 셋. 그중 둘만 그 그룹을 쓸 수 있다.

    ``reading``이면 호출자가 그 그룹 범위에서 프로젝트 읽기 역할을 받는다.
    """

    role: UserRole = UserRole.USER
    reading: bool = False

    @override
    def describe(self) -> str:
        role = self.role.value
        if self.reading:
            who_ko = f"그 그룹 범위의 프로젝트 읽기 역할을 받은 {role}"
            who_en = f"the {role} granted the project read role in the resource group scope"
        else:
            who_ko = role
            who_en = f"one {role}"
        return Says(
            f"리소스 그룹 하나, 그 그룹을 쓸 수 있는 프로젝트 둘과 쓸 수 없는 하나, 그리고 {who_ko} 한 명",
            english=(
                f"one resource group, two projects that can use it and one that cannot, and {who_en}"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> ProjectsOfAGroupAndACaller:
        home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        policy = await seeding.once(TestSeedProjectPolicy())
        group = await seeding.creating(TestSeedResourceGroup())
        linked = [
            await seeding.creating_from_two(TestSeedProject(name_hint="linked"), home, policy)
            for _ in range(2)
        ]
        await seeding.creating_from_two(TestSeedProject(name_hint="unlinked"), home, policy)
        for one in linked:
            await seeding.linking(LinkToProject(), one, group)
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        if self.reading:
            await seeding.within(SomeoneReadingProjectsOfTheGroup(group, caller))
        return ProjectsOfAGroupAndACaller(
            group=seeding.made(group),
            linked=tuple(seeding.made(one) for one in linked),
            caller=seeding.made(caller),
        )
