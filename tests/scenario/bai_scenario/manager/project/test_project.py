"""프로젝트 만들기와 명부에 올리기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.domain import (
    WAS_HERE,
    SomeoneOf,
    WrittenByThisRun,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.project.project import SeedProject
from bai_scenario.seeds.rbac.role import SeedRole
from bai_scenario.seeds.resource_policy.project import SeedProjectPolicy

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.group.request import (
    AssignUsersToProjectInput,
    CreateProjectInput,
)
from ai.backend.common.dto.manager.v2.group.response import (
    AssignUsersToProjectPayload,
    ProjectNode,
)
from ai.backend.manager.api.adapters.project.adapter import ProjectAdapter
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.resource.types import ProjectResourcePolicyData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    Scenario,
    Skipped,
    Then,
    Verdict,
    When,
)

MADE = "research"

type Answer = ProjectNode | AssignUsersToProjectPayload


@dataclass(frozen=True)
class ADomainAPolicyAndACaller:
    """프로젝트를 만들 자리와, 만들 사람."""

    domain: DomainData
    policy: ProjectResourcePolicyData
    caller: UserData


@dataclass(frozen=True)
class AProjectAMemberAndACaller:
    """이미 있는 프로젝트, 거기 올릴 사람, 그리고 올리는 사람."""

    project: ProjectData
    role: RoleData
    member: UserData
    caller: UserData


@dataclass(frozen=True)
class ADomainAndAPolicy(Given[Any, ADomainAPolicyAndACaller]):
    """도메인 하나와, 프로젝트가 딛는 정책, 그리고 부를 사람 한 명."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"도메인 하나와 프로젝트 정책, 그리고 {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> ADomainAPolicyAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        policy = await seeding.once(SeedProjectPolicy())
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        return ADomainAPolicyAndACaller(
            seeding.made(domain), seeding.made(policy), seeding.made(caller)
        )


@dataclass(frozen=True)
class AProjectAndAMember(Given[Any, AProjectAMemberAndACaller]):
    """프로젝트 하나와 그 스코프의 역할, 올릴 사람, 그리고 슈퍼관리자."""

    @override
    def describe(self) -> str:
        return "프로젝트 하나와 그 프로젝트 스코프의 역할, 올릴 사용자, 그리고 슈퍼관리자"

    @override
    async def lay(self, seeding: Any) -> AProjectAMemberAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        policy = await seeding.once(SeedProjectPolicy())
        project = await seeding.creating_from_two(SeedProject(name_hint=MADE), domain, policy)
        member = await seeding.within(SomeoneOf(domain))
        role = await seeding.creating_from(
            SeedRole(lambda one: ProjectID(one.id), name_hint="project-member"), project
        )
        caller = await seeding.within(SomeoneOf(domain, role=UserRole.SUPERADMIN))
        return AProjectAMemberAndACaller(
            seeding.made(project),
            seeding.made(role),
            seeding.made(member),
            seeding.made(caller),
        )


@dataclass(frozen=True)
class MakingAProject(When[ADomainAPolicyAndACaller, ProjectAdapter, Answer]):
    """그 도메인 아래에 프로젝트를 만든다."""

    named: str = MADE

    @override
    def operation(self) -> str:
        return "admin_create"

    @override
    def describe(self, laid: ADomainAPolicyAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.domain.name} 아래에 {self.named}을 만듦"

    @override
    async def call(self, adapter: ProjectAdapter, laid: ADomainAPolicyAndACaller) -> Answer:
        with ActingAs(laid.caller):
            payload = await adapter.admin_create(
                CreateProjectInput(
                    name=self.named,
                    domain_name=laid.domain.name,
                    resource_policy=laid.policy.name,
                )
            )
        return payload.project


@dataclass(frozen=True)
class AssigningTheMember(When[AProjectAMemberAndACaller, ProjectAdapter, Answer]):
    """그 사용자를 프로젝트 명부에 올린다."""

    @override
    def operation(self) -> str:
        return "assign_users"

    @override
    def describe(self, laid: AProjectAMemberAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.member.username}을 {laid.project.name}에 배정"

    @override
    async def call(self, adapter: ProjectAdapter, laid: AProjectAMemberAndACaller) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.assign_users(
                laid.project.id,
                AssignUsersToProjectInput(user_ids=[laid.member.id], role_id=laid.role.id),
            )


@dataclass(frozen=True)
class TheProjectSitsUnderTheDomain(Then[ADomainAPolicyAndACaller, Answer]):
    """만든 프로젝트가 통째로 오고, 그 도메인과 정책 아래에 있다."""

    started: datetime
    named: str = MADE

    @override
    def says(self) -> str:
        return "만든 프로젝트 전체가 온다"

    @override
    def look(self, laid: ADomainAPolicyAndACaller, answered: Answered[Answer]) -> list[Verdict]:
        node = answered.response
        if not isinstance(node, ProjectNode):
            return [Refused(NotEnoughPermission, answered.raised)]
        written = WrittenByThisRun(self.started)
        return [
            Same("basic_info.name", node.basic_info.name, self.named),
            Same("basic_info.description", node.basic_info.description, None),
            Same("basic_info.integration_name", node.basic_info.integration_name, None),
            Same("organization.domain_name", node.organization.domain_name, laid.domain.name),
            Same(
                "organization.resource_policy", node.organization.resource_policy, laid.policy.name
            ),
            Same("storage.allowed_vfolder_hosts", node.storage.allowed_vfolder_hosts, []),
            Same("lifecycle.is_active", node.lifecycle.is_active, True),
            Skipped("id", "데이터베이스가 만든다"),
            Skipped("basic_info.type", "타입이 이미 값을 못박는다"),
            Held("lifecycle.created_at", node.lifecycle.created_at, written),
            Held("lifecycle.modified_at", node.lifecycle.modified_at, written),
        ]


@dataclass(frozen=True)
class TheRosterHoldsTheMember(Then[AProjectAMemberAndACaller, Answer]):
    """명부에 그 사람 하나가 올라 있다."""

    @override
    def says(self) -> str:
        return "명부에 배정한 사람만 올라 있다"

    @override
    def look(self, laid: AProjectAMemberAndACaller, answered: Answered[Answer]) -> list[Verdict]:
        payload = answered.response
        if not isinstance(payload, AssignUsersToProjectPayload):
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Same("items", [one.id for one in payload.items], [laid.member.id]),
        ]


@dataclass(frozen=True)
class TheSuperadminMakesAProject(
    Scenario[SeedingSession, ADomainAPolicyAndACaller, ProjectAdapter, Answer]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-makes-a-project-in-a-domain"

    @override
    def describe(self) -> str:
        return (
            "도메인과 프로젝트 정책이 있을 때 슈퍼관리자가 프로젝트를 만들면, "
            "그 이름의 프로젝트가 그 도메인 아래에 생긴다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADomainAPolicyAndACaller]:
        return ADomainAndAPolicy(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADomainAPolicyAndACaller, ProjectAdapter, Answer]:
        return MakingAProject()

    @override
    def then(self) -> Then[ADomainAPolicyAndACaller, Answer]:
        return TheProjectSitsUnderTheDomain(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotMakeAProject(
    Scenario[SeedingSession, ADomainAPolicyAndACaller, ProjectAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-make-a-project"

    @override
    def describe(self) -> str:
        return (
            "프로젝트 생성은 역할이 아니라 도메인 스코프의 권한이 지키므로, "
            "아무 권한도 받지 않은 사용자는 권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADomainAPolicyAndACaller]:
        return ADomainAndAPolicy()

    @override
    def when(self) -> When[ADomainAPolicyAndACaller, ProjectAdapter, Answer]:
        return MakingAProject(named="refused")

    @override
    def then(self) -> Then[ADomainAPolicyAndACaller, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AssigningAUserPutsThemOnTheRoster(
    Scenario[SeedingSession, AProjectAMemberAndACaller, ProjectAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "assigning-a-user-to-a-project-puts-them-on-its-roster"

    @override
    def describe(self) -> str:
        return (
            "프로젝트와 그 프로젝트 스코프의 역할이 있을 때 사용자를 배정하면, "
            "그 사용자가 명부에 오른다"
        )

    @override
    def given(self) -> Given[SeedingSession, AProjectAMemberAndACaller]:
        return AProjectAndAMember()

    @override
    def when(self) -> When[AProjectAMemberAndACaller, ProjectAdapter, Answer]:
        return AssigningTheMember()

    @override
    def then(self) -> Then[AProjectAMemberAndACaller, Answer]:
        return TheRosterHoldsTheMember()


SCENARIOS: list[Scenario[SeedingSession, Any, ProjectAdapter, Answer]] = [
    TheSuperadminMakesAProject(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotMakeAProject(),
    AssigningAUserPutsThemOnTheRoster(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_project(
    scenario: Scenario[SeedingSession, Any, ProjectAdapter, Answer],
    adapter: ProjectAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
