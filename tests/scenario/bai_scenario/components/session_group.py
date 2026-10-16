"""What a session group scenario table says besides the call.

Two projects with a user-made group each, a deployment's group in the first, and another
user's group in the second. The caller is the owner only when the grant sits in the owner's
own scope, so what the caller reaches comes from the grant.
"""

from __future__ import annotations

import enum
from collections.abc import Collection
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.session_group import SessionGroupEntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.session_group.response import SessionGroupNode
from ai.backend.common.dto.manager.v2.session_group.types import (
    SessionGroupPlacementDirectionEnum,
    SessionGroupPlacementEnforcementEnum,
)
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.session_group.types import SessionGroupData
from ai.backend.manager.data.user.types import UserData
from ai.backend.testutils.scenario_steps import (
    Condition,
    Given,
    Held,
    Same,
    SameAs,
    Skipped,
    Verdict,
)
from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.seeds.deployment.deployment import TestSeedDeployment
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.project.project import TestSeedProject
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.resource_group.resource_group import TestSeedResourceGroup
from bai_scenario.seeds.resource_policy.project import TestSeedProjectPolicy
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest
from bai_scenario.seeds.session_group.session_group import (
    TestSeedDeploymentSessionGroup,
    TestSeedPrimaryReplicaGroupOf,
    TestSeedSessionGroup,
)


class Granting(enum.Enum):
    """부르는 사람이 받은 세션 그룹 권한."""

    READ = "읽기"
    UPDATE = "수정"

    def permission(self) -> Permission:
        match self:
            case Granting.READ:
                return Permission.READ
            case Granting.UPDATE:
                return Permission.UPDATE

    def project_role_hint(self) -> str:
        """프로젝트에 앉는 역할의 이름 힌트."""
        match self:
            case Granting.READ:
                return "session-group-reader"
            case Granting.UPDATE:
                return "session-group-updater"


class GrantedIn(enum.Enum):
    """부르는 사람이 세션 그룹 권한을 받은 곳."""

    NOWHERE = "아무 데서도"
    THE_PROJECT = "그룹들이 있는 프로젝트에서"
    THE_OTHER_PROJECT = "다른 프로젝트에서만"
    THEIR_OWN = "자기 스코프에서"
    THEIR_OWN_AND_THE_OTHER_PROJECT = "자기 스코프와 다른 프로젝트에서"

    def is_the_owner(self) -> bool:
        """부르는 사람이 그룹들을 만든 사람인지."""
        match self:
            case GrantedIn.THEIR_OWN | GrantedIn.THEIR_OWN_AND_THE_OTHER_PROJECT:
                return True
            case GrantedIn.NOWHERE | GrantedIn.THE_PROJECT | GrantedIn.THE_OTHER_PROJECT:
                return False


@dataclass(frozen=True)
class SessionGroupsAndACaller:
    """두 프로젝트의 세션 그룹들과, 그것을 부를 사람."""

    domain: DomainData
    project: ProjectData
    other_project: ProjectData
    owner: UserData
    users_group: SessionGroupData
    """그룹들이 있는 프로젝트에 사용자가 만든 그룹."""
    deployment_group: SessionGroupData
    """같은 프로젝트의 배포가 가진 그룹."""
    elsewhere_group: SessionGroupData
    """다른 프로젝트에 사용자가 만든 그룹."""
    strangers_group: SessionGroupData
    """다른 프로젝트에 다른 사용자가 만든 그룹."""
    caller: UserData


@dataclass(frozen=True)
class SomeoneGrantedOnSessionGroups(TestSeedNest[Laid[UserData]]):
    """그 프로젝트에서 세션 그룹 권한을 받은 사용자.

    그룹은 프로젝트 스코프에 생기므로 역할도 거기 앉는다.
    """

    domain: Laid[DomainData]
    project: Laid[ProjectData]
    granting: Granting = Granting.READ

    @override
    def kind(self) -> str:
        return f"프로젝트에서 세션 그룹 {self.granting.value} 권한을 받은 사용자 준비"

    @override
    def lay(self, seed: TestSeeder) -> Laid[UserData]:
        someone = seed.within(SomeoneOf(self.domain))
        role = seed.creating_from(
            TestSeedRole(lambda p: ProjectID(p.id), name_hint=self.granting.project_role_hint()),
            self.project,
        )
        seed.adding(
            TestSeedPermission(
                entity_type=SessionGroupEntityType(), permission=self.granting.permission()
            ),
            role,
        )
        seed.granting(role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return someone


@dataclass(frozen=True)
class SomeoneGrantedOnTheirOwnSessionGroups(TestSeedNest[Laid[UserData]]):
    """자기 스코프에서 세션 그룹 권한을 받은 사용자.

    그룹은 만든 사람의 스코프에도 생기므로 역할이 거기 앉는다. ``also_in``이 있으면 그
    프로젝트에서도 같은 권한을 받는다.
    """

    domain: Laid[DomainData]
    also_in: Laid[ProjectData] | None = None
    granting: Granting = Granting.READ

    @override
    def kind(self) -> str:
        if self.also_in is None:
            return f"자기 스코프에서 세션 그룹 {self.granting.value} 권한을 받은 사용자 준비"
        return (
            f"자기 스코프와 한 프로젝트에서 세션 그룹 {self.granting.value} 권한을 받은 사용자 준비"
        )

    @override
    def lay(self, seed: TestSeeder) -> Laid[UserData]:
        someone = seed.within(SomeoneOf(self.domain))
        own = seed.creating_from(
            TestSeedRole(lambda u: UserID(u.id), name_hint="session-group-owner"), someone
        )
        seed.adding(
            TestSeedPermission(
                entity_type=SessionGroupEntityType(), permission=self.granting.permission()
            ),
            own,
        )
        seed.granting(own, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        if self.also_in is not None:
            in_project = seed.creating_from(
                TestSeedRole(
                    lambda p: ProjectID(p.id), name_hint=self.granting.project_role_hint()
                ),
                self.also_in,
            )
            seed.adding(
                TestSeedPermission(
                    entity_type=SessionGroupEntityType(), permission=self.granting.permission()
                ),
                in_project,
            )
            seed.granting(
                in_project, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id)
            )
        return someone


@dataclass(frozen=True)
class SessionGroupsInTwoProjects(Given[Any, SessionGroupsAndACaller]):
    """두 프로젝트의 사용자 그룹과 배포의 그룹, 그리고 정해진 곳에서 권한을 받은 사용자.

    권한이 자기 스코프에 있으면 부르는 사람이 그룹들을 만든 사람이다.
    """

    granted_in: GrantedIn = GrantedIn.NOWHERE
    granting: Granting = Granting.READ
    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        laid = (
            "한 프로젝트에 사용자가 만든 그룹과 배포의 그룹, 다른 프로젝트에 같은 사용자가 만든 "
            "그룹과 다른 사용자가 만든 그룹"
        )
        if self.granted_in.is_the_owner():
            return (
                f"{laid}, 그리고 {self.granted_in.value} 세션 그룹 {self.granting.value} "
                "권한을 받은 그룹들을 만든 사용자"
            )
        who = "슈퍼관리자" if self.role is UserRole.SUPERADMIN else "사용자"
        if self.granted_in is GrantedIn.NOWHERE:
            reach = "아무 권한도 받지 않은"
        else:
            reach = f"{self.granted_in.value} 세션 그룹 {self.granting.value} 권한을 받은"
        return f"{laid}, 그리고 {reach} {who} 한 명"

    @override
    async def lay(self, seeding: Any) -> SessionGroupsAndACaller:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        policy = await seeding.once(TestSeedProjectPolicy())
        project = await seeding.creating_from_two(TestSeedProject(name_hint="team"), domain, policy)
        other = await seeding.creating_from_two(TestSeedProject(name_hint="other"), domain, policy)
        resource_group = await seeding.creating(TestSeedResourceGroup())
        owner: Laid[UserData]
        match self.granted_in:
            case GrantedIn.THEIR_OWN:
                owner = await seeding.within(
                    SomeoneGrantedOnTheirOwnSessionGroups(domain, granting=self.granting)
                )
            case GrantedIn.THEIR_OWN_AND_THE_OTHER_PROJECT:
                owner = await seeding.within(
                    SomeoneGrantedOnTheirOwnSessionGroups(
                        domain, also_in=other, granting=self.granting
                    )
                )
            case GrantedIn.NOWHERE | GrantedIn.THE_PROJECT | GrantedIn.THE_OTHER_PROJECT:
                owner = await seeding.within(SomeoneOf(domain))
        stranger = await seeding.within(SomeoneOf(domain))

        users_group = await seeding.creating_from_two(TestSeedSessionGroup(), project, owner)
        elsewhere_group = await seeding.creating_from_two(TestSeedSessionGroup(), other, owner)
        strangers_group = await seeding.creating_from_two(TestSeedSessionGroup(), other, stranger)
        deployment = await seeding.creating_from_three(
            TestSeedDeployment(), project, resource_group, owner
        )
        deployment_group = await seeding.creating_from(TestSeedDeploymentSessionGroup(), deployment)
        await seeding.adding(
            TestSeedPrimaryReplicaGroupOf(session_group_id=seeding.made(deployment_group).id),
            deployment,
        )

        caller: Laid[UserData]
        match self.granted_in:
            case GrantedIn.NOWHERE:
                caller = await seeding.within(SomeoneOf(domain, role=self.role))
            case GrantedIn.THE_PROJECT:
                caller = await seeding.within(
                    SomeoneGrantedOnSessionGroups(domain, project, self.granting)
                )
            case GrantedIn.THE_OTHER_PROJECT:
                caller = await seeding.within(
                    SomeoneGrantedOnSessionGroups(domain, other, self.granting)
                )
            case GrantedIn.THEIR_OWN | GrantedIn.THEIR_OWN_AND_THE_OTHER_PROJECT:
                caller = owner
        return SessionGroupsAndACaller(
            domain=seeding.made(domain),
            project=seeding.made(project),
            other_project=seeding.made(other),
            owner=seeding.made(owner),
            users_group=seeding.made(users_group),
            deployment_group=seeding.made(deployment_group),
            elsewhere_group=seeding.made(elsewhere_group),
            strangers_group=seeding.made(strangers_group),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class TheseGroups(Condition[Collection[UUID]]):
    """답에 든 그룹이 정해진 그룹들과 같다. id는 실행마다 달라 레포트에는 무엇인지로 말한다."""

    wanted: frozenset[UUID]
    named: str

    @override
    def says(self) -> str:
        return self.named

    @override
    def holds(self, got: Collection[UUID]) -> bool:
        return len(got) == len(self.wanted) and frozenset(got) == self.wanted


@dataclass(frozen=True)
class UsersGroupLook:
    """사용자가 만든 그룹의 노드가 어떤 값으로 와야 하는지.

    배치 정책은 심은 값이 기본이고, 정책을 바꾼 행은 바뀐 값을 넘긴다.
    """

    started: datetime
    direction: SessionGroupPlacementDirectionEnum = SessionGroupPlacementDirectionEnum.PACK
    enforcement: SessionGroupPlacementEnforcementEnum = SessionGroupPlacementEnforcementEnum.STRICT

    def verdicts(
        self, prefix: str, node: SessionGroupNode, laid: SessionGroupsAndACaller
    ) -> list[Verdict]:
        return [
            Skipped(f"{prefix}id", "데이터베이스가 만든다"),
            Held[UUID](
                f"{prefix}entity_id",
                node.entity_id,
                SameAs(laid.users_group.id, "사용자가 만든 그룹의 id"),
            ),
            Held[UUID](
                f"{prefix}domain_id", node.domain_id, SameAs(laid.domain.id, "그 도메인의 id")
            ),
            Held[UUID](
                f"{prefix}project_id", node.project_id, SameAs(laid.project.id, "그 프로젝트의 id")
            ),
            Held[UUID](
                f"{prefix}owner_user_id",
                node.owner_user_id,
                SameAs(laid.owner.id, "만든 사람의 id"),
            ),
            Same(
                f"{prefix}placement_direction",
                node.placement_direction,
                self.direction,
            ),
            Same(
                f"{prefix}placement_enforcement",
                node.placement_enforcement,
                self.enforcement,
            ),
            Held(f"{prefix}created_at", node.created_at, WrittenByThisRun(self.started)),
            Same(f"{prefix}deleted_at", node.deleted_at, None),
        ]
