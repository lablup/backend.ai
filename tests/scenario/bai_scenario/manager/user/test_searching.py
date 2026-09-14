"""사용자 훑기 — 전역, 역할, 도메인, 프로젝트, 스코프 여럿으로."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from itertools import pairwise
from typing import Any, override

import pytest
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.domain import WAS_HERE, SomeoneOf
from bai_scenario.components.user import AGrant
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.project.project import SeedProject
from bai_scenario.seeds.rbac.role import SeedRole
from bai_scenario.seeds.resource_policy.keypair import SeedKeypairPolicy
from bai_scenario.seeds.resource_policy.project import SeedProjectPolicy
from bai_scenario.seeds.resource_policy.user import SeedUserPolicy
from bai_scenario.seeds.seeder import Laid, Seeder, SeedNest
from bai_scenario.seeds.user.user import SeedUserOf

from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.common.dto.manager.v2.user.request import (
    AdminSearchUsersInput,
    ScopedSearchUsersInput,
    SearchUsersRequest,
)
from ai.backend.common.dto.manager.v2.user.response import (
    AdminSearchUsersPayload,
    SearchUsersPayload,
)
from ai.backend.common.dto.manager.v2.user.types import UserScope
from ai.backend.manager.api.adapters.user.adapter import UserAdapter
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.user.types import UserData, UserStatus
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Condition,
    Given,
    Held,
    Refused,
    Same,
    Scenario,
    Then,
    Verdict,
    When,
)

type Answer = SearchUsersPayload | AdminSearchUsersPayload
type SearchStep = Scenario[SeedingSession, Any, UserAdapter, Answer]

NO_SUCH_DOMAIN = "no-such-domain"


def _names(users: Sequence[UserData]) -> list[str]:
    return sorted(one.username for one in users)


@dataclass(frozen=True)
class AnAskerAndWhomTheyReach:
    """훑는 사람과, 그 사람이 받아야 할 사용자들. 스코프로 쓸 행을 함께 든다."""

    caller: UserData
    reached: tuple[UserData, ...]
    domain: DomainData
    other_domain: DomainData | None = None
    project: ProjectData | None = None
    role: RoleData | None = None


@dataclass(frozen=True)
class SomeoneInADomain(Given[Any, AnAskerAndWhomTheyReach]):
    """도메인 하나와 부르는 사람. `granted`면 그 도메인 스코프의 사용자 READ를 받는다.

    `with_neighbours`면 같은 도메인에 사용자 하나, 다른 도메인에 사용자 하나를 더 둔다.
    """

    role: UserRole = UserRole.USER
    granted: bool = False
    with_neighbours: bool = False

    @override
    def describe(self) -> str:
        parts = ["도메인 하나와 부르는 사람"]
        if self.with_neighbours:
            parts.append("같은 도메인 사용자 하나와 다른 도메인 사용자 하나")
        if self.granted:
            parts.append("부르는 사람은 그 도메인 스코프의 사용자 READ를 받았다")
        return ", ".join(parts)

    @override
    async def lay(self, seeding: Any) -> AnAskerAndWhomTheyReach:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        reached = []
        other_domain = None
        if self.with_neighbours:
            reached.append(await seeding.within(SomeoneOf(home)))
            other_domain = await seeding.creating(
                SeedDomain(name_hint="other", description=WAS_HERE)
            )
            await seeding.within(SomeoneOf(other_domain))
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        reached.append(caller)
        if self.granted:
            await seeding.within(AGrant.on_domain(home, caller, Permission.READ))
        return AnAskerAndWhomTheyReach(
            caller=seeding.made(caller),
            reached=tuple(seeding.made(one) for one in reached),
            domain=seeding.made(home),
            other_domain=seeding.made(other_domain) if other_domain is not None else None,
        )


@dataclass(frozen=True)
class ManyUsersAndTheSuperadmin(Given[Any, AnAskerAndWhomTheyReach]):
    """도메인 하나에 사용자 여럿, 그리고 슈퍼관리자."""

    count: int

    @override
    def describe(self) -> str:
        return f"도메인 하나와 사용자 {self.count}명, 그리고 슈퍼관리자"

    @override
    async def lay(self, seeding: Any) -> AnAskerAndWhomTheyReach:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        users = [await seeding.within(SomeoneOf(home)) for _ in range(self.count)]
        caller = await seeding.within(SomeoneOf(home, role=UserRole.SUPERADMIN))
        return AnAskerAndWhomTheyReach(
            caller=seeding.made(caller),
            reached=tuple(seeding.made(one) for one in [*users, caller]),
            domain=seeding.made(home),
        )


@dataclass(frozen=True)
class SomeoneDeletedOf(SeedNest[Laid[UserData]]):
    """그 도메인에 속했다가 삭제 상태가 된 사용자 한 명."""

    domain: Laid[DomainData]

    @override
    def kind(self) -> str:
        return "도메인에 속한 삭제 상태 사용자 한 명 준비"

    @override
    def lay(self, seed: Seeder) -> Laid[UserData]:
        seed.once(SeedProjectPolicy())
        policy = seed.creating(SeedUserPolicy())
        key_policy = seed.creating(SeedKeypairPolicy())
        return seed.provisioning(
            SeedUserOf(is_active=False, status=UserStatus.DELETED), self.domain, policy, key_policy
        )


@dataclass(frozen=True)
class AnActiveAndADeletedUser(Given[Any, AnAskerAndWhomTheyReach]):
    """도메인 하나에 활성 사용자 하나, 삭제 상태 사용자 하나, 그리고 슈퍼관리자."""

    @override
    def describe(self) -> str:
        return "도메인 하나와 활성 사용자 하나, 삭제 상태 사용자 하나, 그리고 슈퍼관리자"

    @override
    async def lay(self, seeding: Any) -> AnAskerAndWhomTheyReach:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        active = await seeding.within(SomeoneOf(home))
        deleted = await seeding.within(SomeoneDeletedOf(home))
        caller = await seeding.within(SomeoneOf(home, role=UserRole.SUPERADMIN))
        return AnAskerAndWhomTheyReach(
            caller=seeding.made(caller),
            reached=tuple(seeding.made(one) for one in [active, deleted, caller]),
            domain=seeding.made(home),
        )


@dataclass(frozen=True)
class TwoUsersOneHoldingARole(Given[Any, AnAskerAndWhomTheyReach]):
    """도메인 하나와 사용자 둘, 그중 첫 사람만 역할 하나를 받았다.

    부르는 사람이 슈퍼관리자가 아니면 그 도메인 스코프의 사용자 READ를 받는다.
    """

    role: UserRole

    @override
    def describe(self) -> str:
        if self.role == UserRole.SUPERADMIN:
            return "도메인 하나와 사용자 둘, 첫 사람만 역할 하나를 받았고, 부르는 사람은 슈퍼관리자"
        return (
            "도메인 하나와 사용자 둘, 첫 사람만 역할 하나를 받았고, "
            "부르는 사람은 그 도메인 스코프의 사용자 READ를 받았다"
        )

    @override
    async def lay(self, seeding: Any) -> AnAskerAndWhomTheyReach:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        holder = await seeding.within(SomeoneOf(home))
        await seeding.within(SomeoneOf(home))
        role = await seeding.creating_from(
            SeedRole(lambda one: one.id, name_hint="holder-role"), home
        )
        await seeding.granting(
            role, holder, role_id=lambda one: one.id, user_id=lambda one: UserID(one.id)
        )
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        if self.role != UserRole.SUPERADMIN:
            await seeding.within(AGrant.on_domain(home, caller, Permission.READ))
        return AnAskerAndWhomTheyReach(
            caller=seeding.made(caller),
            reached=(seeding.made(holder),),
            domain=seeding.made(home),
            role=seeding.made(role),
        )


@dataclass(frozen=True)
class AProjectAndSomeone(Given[Any, AnAskerAndWhomTheyReach]):
    """도메인 하나와 그 프로젝트 하나, 아무 권한도 받지 않은 사람."""

    @override
    def describe(self) -> str:
        return "도메인 하나와 프로젝트 하나, 아무 권한도 받지 않은 사용자 한 명"

    @override
    async def lay(self, seeding: Any) -> AnAskerAndWhomTheyReach:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        policy = await seeding.once(SeedProjectPolicy())
        project = await seeding.creating_from_two(SeedProject(name_hint="research"), home, policy)
        caller = await seeding.within(SomeoneOf(home))
        return AnAskerAndWhomTheyReach(
            caller=seeding.made(caller),
            reached=(),
            domain=seeding.made(home),
            project=seeding.made(project),
        )


@dataclass(frozen=True)
class AProjectWithAMember(Given[Any, AnAskerAndWhomTheyReach]):
    """도메인 하나와 프로젝트 하나, 명부에 오른 사용자와 오르지 않은 사용자.

    부르는 사람은 그 프로젝트 스코프의 사용자 READ를 받았다.
    """

    @override
    def describe(self) -> str:
        return (
            "도메인 하나와 프로젝트 하나, 명부에 오른 사용자 하나와 오르지 않은 사용자 하나, "
            "부르는 사람은 그 프로젝트 스코프의 사용자 READ를 받았다"
        )

    @override
    async def lay(self, seeding: Any) -> AnAskerAndWhomTheyReach:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        policy = await seeding.once(SeedProjectPolicy())
        project = await seeding.creating_from_two(SeedProject(name_hint="research"), home, policy)
        member = await seeding.within(SomeoneOf(home))
        await seeding.joining(
            project, member, project_id=lambda one: ProjectID(one.id), user_id=_user_id
        )
        await seeding.within(SomeoneOf(home))
        caller = await seeding.within(SomeoneOf(home))
        await seeding.within(AGrant.on_project(project, caller, Permission.READ))
        return AnAskerAndWhomTheyReach(
            caller=seeding.made(caller),
            reached=(seeding.made(member),),
            domain=seeding.made(home),
            project=seeding.made(project),
        )


@dataclass(frozen=True)
class TwoScopes(Given[Any, AnAskerAndWhomTheyReach]):
    """도메인 둘, 둘째 도메인의 프로젝트 하나와 그 명부 사용자 하나.

    부르는 사람은 첫 도메인 스코프의 사용자 READ를 받고, `both`면 그 프로젝트 스코프에도 받는다.
    """

    both: bool

    @override
    def describe(self) -> str:
        granted = (
            "첫 도메인 스코프와 그 프로젝트 스코프의 사용자 READ를 받았다"
            if self.both
            else "첫 도메인 스코프의 사용자 READ만 받았다"
        )
        return f"도메인 둘과 둘째 도메인의 프로젝트 하나와 그 명부 사용자 하나, 부르는 사람은 {granted}"

    @override
    async def lay(self, seeding: Any) -> AnAskerAndWhomTheyReach:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        other = await seeding.creating(SeedDomain(name_hint="other", description=WAS_HERE))
        policy = await seeding.once(SeedProjectPolicy())
        project = await seeding.creating_from_two(SeedProject(name_hint="research"), other, policy)
        member = await seeding.within(SomeoneOf(other))
        await seeding.joining(
            project, member, project_id=lambda one: ProjectID(one.id), user_id=_user_id
        )
        caller = await seeding.within(SomeoneOf(home))
        await seeding.within(AGrant.on_domain(home, caller, Permission.READ))
        if self.both:
            await seeding.within(AGrant.on_project(project, caller, Permission.READ))
        return AnAskerAndWhomTheyReach(
            caller=seeding.made(caller),
            reached=(seeding.made(caller), seeding.made(member)),
            domain=seeding.made(home),
            other_domain=seeding.made(other),
            project=seeding.made(project),
        )


def _user_id(one: UserData) -> UserID:
    return UserID(one.id)


def _project(laid: AnAskerAndWhomTheyReach) -> ProjectData:
    if laid.project is None:
        raise ValueError("this row laid no project")
    return laid.project


@dataclass(frozen=True)
class SearchingEveryone(When[AnAskerAndWhomTheyReach, UserAdapter, Answer]):
    """필터 없이 전체를 훑는다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: AnAskerAndWhomTheyReach) -> str:
        return f"{laid.caller.username}이 필터 없이 전체 조회"

    @override
    async def call(self, adapter: UserAdapter, laid: AnAskerAndWhomTheyReach) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.admin_search(SearchUsersRequest())


@dataclass(frozen=True)
class GqlSearchingEveryone(When[AnAskerAndWhomTheyReach, UserAdapter, Answer]):
    """커서와 페이지 인자 없이 GQL로 전체를 훑는다."""

    @override
    def operation(self) -> str:
        return "gql_admin_search"

    @override
    def describe(self, laid: AnAskerAndWhomTheyReach) -> str:
        return f"{laid.caller.username}이 페이지 인자 없이 GQL 전체 조회"

    @override
    async def call(self, adapter: UserAdapter, laid: AnAskerAndWhomTheyReach) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.gql_admin_search(AdminSearchUsersInput())


@dataclass(frozen=True)
class SearchingByRole(When[AnAskerAndWhomTheyReach, UserAdapter, Answer]):
    """심은 역할로 걸러 훑는다."""

    @override
    def operation(self) -> str:
        return "role_search"

    @override
    def describe(self, laid: AnAskerAndWhomTheyReach) -> str:
        return f"{laid.caller.username}이 역할로 걸러 조회"

    @override
    async def call(self, adapter: UserAdapter, laid: AnAskerAndWhomTheyReach) -> Answer:
        if laid.role is None:
            raise ValueError("this row laid no role")
        with ActingAs(laid.caller):
            return await adapter.role_search(laid.role.id, SearchUsersRequest())


@dataclass(frozen=True)
class SearchingTheDomain(When[AnAskerAndWhomTheyReach, UserAdapter, Answer]):
    """도메인 이름으로 훑는다. `named`가 있으면 그 이름을 쓴다."""

    named: str | None = None

    @override
    def operation(self) -> str:
        return "domain_search"

    @override
    def describe(self, laid: AnAskerAndWhomTheyReach) -> str:
        return f"{laid.caller.username}이 {self.named or laid.domain.name}으로 조회"

    @override
    async def call(self, adapter: UserAdapter, laid: AnAskerAndWhomTheyReach) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.domain_search(self.named or laid.domain.name, SearchUsersRequest())


@dataclass(frozen=True)
class GqlSearchingTheDomain(When[AnAskerAndWhomTheyReach, UserAdapter, Answer]):
    """GQL로 도메인 이름을 주고 훑는다."""

    @override
    def operation(self) -> str:
        return "gql_search_by_domain"

    @override
    def describe(self, laid: AnAskerAndWhomTheyReach) -> str:
        return f"{laid.caller.username}이 {laid.domain.name}으로 GQL 조회"

    @override
    async def call(self, adapter: UserAdapter, laid: AnAskerAndWhomTheyReach) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.gql_search_by_domain(laid.domain.name, AdminSearchUsersInput())


@dataclass(frozen=True)
class SearchingTheProject(When[AnAskerAndWhomTheyReach, UserAdapter, Answer]):
    """프로젝트로 훑는다."""

    @override
    def operation(self) -> str:
        return "project_search"

    @override
    def describe(self, laid: AnAskerAndWhomTheyReach) -> str:
        return f"{laid.caller.username}이 {_project(laid).name}으로 조회"

    @override
    async def call(self, adapter: UserAdapter, laid: AnAskerAndWhomTheyReach) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.project_search(_project(laid).id, SearchUsersRequest())


@dataclass(frozen=True)
class GqlSearchingTheProject(When[AnAskerAndWhomTheyReach, UserAdapter, Answer]):
    """GQL로 프로젝트를 주고 훑는다."""

    @override
    def operation(self) -> str:
        return "gql_search_by_project"

    @override
    def describe(self, laid: AnAskerAndWhomTheyReach) -> str:
        return f"{laid.caller.username}이 {_project(laid).name}으로 GQL 조회"

    @override
    async def call(self, adapter: UserAdapter, laid: AnAskerAndWhomTheyReach) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.gql_search_by_project(
                ProjectID(_project(laid).id), AdminSearchUsersInput()
            )


def _domain_and_project(laid: AnAskerAndWhomTheyReach) -> UserScope:
    return UserScope(
        domain=[UUIDScope(value=laid.domain.id)],
        project=[UUIDScope(value=_project(laid).id)],
    )


@dataclass(frozen=True)
class ScopedSearchingDomainAndProject(When[AnAskerAndWhomTheyReach, UserAdapter, Answer]):
    """첫 도메인과 프로젝트, 두 스코프를 함께 주고 훑는다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: AnAskerAndWhomTheyReach) -> str:
        return (
            f"{laid.caller.username}이 {laid.domain.name}과 {_project(laid).name} 두 스코프로 조회"
        )

    @override
    async def call(self, adapter: UserAdapter, laid: AnAskerAndWhomTheyReach) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchUsersInput(scope=_domain_and_project(laid))
            )


@dataclass(frozen=True)
class GqlScopedSearchingDomainAndProject(When[AnAskerAndWhomTheyReach, UserAdapter, Answer]):
    """첫 도메인과 프로젝트, 두 스코프를 함께 주고 GQL로 훑는다."""

    @override
    def operation(self) -> str:
        return "gql_scoped_search"

    @override
    def describe(self, laid: AnAskerAndWhomTheyReach) -> str:
        return (
            f"{laid.caller.username}이 {laid.domain.name}과 {_project(laid).name} "
            "두 스코프로 GQL 조회"
        )

    @override
    async def call(self, adapter: UserAdapter, laid: AnAskerAndWhomTheyReach) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.gql_scoped_search(
                _domain_and_project(laid), AdminSearchUsersInput()
            )


@dataclass(frozen=True)
class ScopedSearchingTheDomain(When[AnAskerAndWhomTheyReach, UserAdapter, Answer]):
    """도메인 스코프 하나를 페이지 인자 없이 주고 훑는다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: AnAskerAndWhomTheyReach) -> str:
        return f"{laid.caller.username}이 페이지 인자 없이 {laid.domain.name} 스코프로 조회"

    @override
    async def call(self, adapter: UserAdapter, laid: AnAskerAndWhomTheyReach) -> Answer:
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchUsersInput(scope=UserScope(domain=[UUIDScope(value=laid.domain.id)]))
            )


@dataclass(frozen=True)
class DrawnFrom(Condition[list[str]]):
    """모든 이름이 심은 사용자 중에서 온다."""

    names: tuple[str, ...]

    @override
    def says(self) -> str:
        return "모두 심은 사용자 중에서 온다"

    @override
    def holds(self, got: list[str]) -> bool:
        return set(got) <= set(self.names)


@dataclass(frozen=True)
class NewestFirst(Condition[list[datetime | None]]):
    """생성 시각이 모두 있고 내림차순으로 놓여 있다."""

    @override
    def says(self) -> str:
        return "생성 시각 내림차순"

    @override
    def holds(self, got: list[datetime | None]) -> bool:
        return all(
            later is not None and earlier is not None and later >= earlier
            for later, earlier in pairwise(got)
        )


@dataclass(frozen=True)
class TheOffsetPage(Then[AnAskerAndWhomTheyReach, Answer]):
    """닿는 사용자가 모두, 그리고 페이지 정보가 온다."""

    limit: int = 50
    offset: int = 0

    @override
    def says(self) -> str:
        return "닿는 사용자가 모두 오고 페이지 정보가 실린다"

    @override
    def look(self, laid: AnAskerAndWhomTheyReach, answered: Answered[Answer]) -> list[Verdict]:
        page = answered.response
        if not isinstance(page, SearchUsersPayload):
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Same(
                "items(이름순)",
                sorted(str(one.basic_info.username) for one in page.items),
                _names(laid.reached),
            ),
            Same("pagination.total", page.pagination.total, len(laid.reached)),
            Same("pagination.offset", page.pagination.offset, self.offset),
            Same("pagination.limit", page.pagination.limit, self.limit),
        ]


@dataclass(frozen=True)
class TheCursorPage(Then[AnAskerAndWhomTheyReach, Answer]):
    """닿는 사용자가 모두 한 페이지에 오고, 앞뒤 페이지가 없다."""

    @override
    def says(self) -> str:
        return "닿는 사용자가 모두 한 페이지로 온다"

    @override
    def look(self, laid: AnAskerAndWhomTheyReach, answered: Answered[Answer]) -> list[Verdict]:
        page = answered.response
        if not isinstance(page, AdminSearchUsersPayload):
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            Same(
                "items(이름순)",
                sorted(str(one.basic_info.username) for one in page.items),
                _names(laid.reached),
            ),
            Same("total_count", page.total_count, len(laid.reached)),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheNewestTen(Then[AnAskerAndWhomTheyReach, Answer]):
    """심은 사용자 중 열 명이 최근순으로 오고, 다음 페이지가 있다."""

    @override
    def says(self) -> str:
        return "심은 사용자 중 열 명이 최근순으로 오고 다음 페이지가 있다"

    @override
    def look(self, laid: AnAskerAndWhomTheyReach, answered: Answered[Answer]) -> list[Verdict]:
        page = answered.response
        if not isinstance(page, AdminSearchUsersPayload):
            return [Refused(InsufficientPrivilege, answered.raised)]
        names = [str(one.basic_info.username) for one in page.items]
        created = [one.timestamps.created_at for one in page.items]
        return [
            Same("items.length", len(page.items), 10),
            Held("items(이름)", names, DrawnFrom(tuple(_names(laid.reached)))),
            Held("items(생성 시각)", created, NewestFirst()),
            Same("total_count", page.total_count, len(laid.reached)),
            Same("has_next_page", page.has_next_page, True),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheRoleHolderOnly(Then[AnAskerAndWhomTheyReach, Answer]):
    """역할을 받은 사람만 온다."""

    @override
    def says(self) -> str:
        return "역할을 받은 사람만 온다"

    @override
    def look(self, laid: AnAskerAndWhomTheyReach, answered: Answered[Answer]) -> list[Verdict]:
        return TheOffsetPage().look(laid, answered)


@dataclass(frozen=True)
class TheOffsetPageWithStatuses(Then[AnAskerAndWhomTheyReach, Answer]):
    """닿는 사용자가 상태와 함께 모두 오고, 기본 페이지 정보가 실린다."""

    @override
    def says(self) -> str:
        return "삭제 상태를 포함해 심은 사용자가 모두 온다"

    @override
    def look(self, laid: AnAskerAndWhomTheyReach, answered: Answered[Answer]) -> list[Verdict]:
        page = answered.response
        if not isinstance(page, SearchUsersPayload):
            return [Refused(InsufficientPrivilege, answered.raised)]
        got = sorted((one.basic_info.username, str(one.status.status)) for one in page.items)
        return [
            Same(
                "items(이름순, 이름과 상태)",
                got,
                sorted((one.username, str(one.status)) for one in laid.reached),
            ),
            Same("pagination.total", page.pagination.total, 3),
            Same("pagination.offset", page.pagination.offset, 0),
            Same("pagination.limit", page.pagination.limit, 50),
        ]


@dataclass(frozen=True)
class TheSuperadminCountsDeletedUsersToo(Scenario[SeedingSession, Any, UserAdapter, Answer]):
    @override
    def summary(self) -> str:
        return "the-superadmin-searching-every-user-counts-deleted-ones-too"

    @override
    def describe(self) -> str:
        return (
            "전역 역할이 문인 검색에서 슈퍼관리자가 필터 없이 훑으면, "
            "삭제 상태 사용자를 포함해 심은 사용자가 모두 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, Any]:
        return AnActiveAndADeletedUser()

    @override
    def when(self) -> When[Any, UserAdapter, Answer]:
        return SearchingEveryone()

    @override
    def then(self) -> Then[Any, Answer]:
        return TheOffsetPageWithStatuses()


@dataclass(frozen=True)
class TheSuperadminSearchesEveryUserWithoutPaging(
    Scenario[SeedingSession, Any, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-gql-search-without-page-arguments-answers-the-newest-ten"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 커서와 페이지 인자를 모두 생략하고 훑으면, "
            "생성 시각 내림차순으로 열 명까지 오고 다음 페이지 여부가 함께 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, Any]:
        return ManyUsersAndTheSuperadmin(count=11)

    @override
    def when(self) -> When[Any, UserAdapter, Answer]:
        return GqlSearchingEveryone()

    @override
    def then(self) -> Then[Any, Answer]:
        return TheNewestTen()


@dataclass(frozen=True)
class OnlyTheSuperadminSearchesEveryUser(Scenario[SeedingSession, Any, UserAdapter, Answer]):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-every-user"

    @override
    def describe(self) -> str:
        return "도메인 스코프 권한을 받은 사용자라도 전체 검색을 하려 하면, 전역 역할 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, Any]:
        return SomeoneInADomain(granted=True)

    @override
    def when(self) -> When[Any, UserAdapter, Answer]:
        return SearchingEveryone()

    @override
    def then(self) -> Then[Any, Answer]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class OnlyTheSuperadminSearchesEveryUserByGql(Scenario[SeedingSession, Any, UserAdapter, Answer]):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-gql-search-every-user"

    @override
    def describe(self) -> str:
        return "권한 받은 사용자가 GQL 전체 검색을 하려 하면, 전역 역할 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, Any]:
        return SomeoneInADomain(granted=True)

    @override
    def when(self) -> When[Any, UserAdapter, Answer]:
        return GqlSearchingEveryone()

    @override
    def then(self) -> Then[Any, Answer]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class TheSuperadminSearchesByRole(Scenario[SeedingSession, Any, UserAdapter, Answer]):
    @override
    def summary(self) -> str:
        return "the-superadmin-searching-by-role-finds-only-its-holders"

    @override
    def describe(self) -> str:
        return (
            "전역 역할이 문인 역할 검색에서 슈퍼관리자가 역할 하나를 주면, "
            "그 역할을 배정받은 사용자만 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, Any]:
        return TwoUsersOneHoldingARole(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[Any, UserAdapter, Answer]:
        return SearchingByRole()

    @override
    def then(self) -> Then[Any, Answer]:
        return TheRoleHolderOnly()


@dataclass(frozen=True)
class OnlyTheSuperadminSearchesByRole(Scenario[SeedingSession, Any, UserAdapter, Answer]):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-by-role"

    @override
    def describe(self) -> str:
        return (
            "그 역할의 스코프 권한을 받은 사용자라도 역할 검색을 하려 하면, 전역 역할 문이 막는다"
        )

    @override
    def given(self) -> Given[SeedingSession, Any]:
        return TwoUsersOneHoldingARole(role=UserRole.USER)

    @override
    def when(self) -> When[Any, UserAdapter, Answer]:
        return SearchingByRole()

    @override
    def then(self) -> Then[Any, Answer]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class AGrantedUserSearchesTheirDomain(Scenario[SeedingSession, Any, UserAdapter, Answer]):
    @override
    def summary(self) -> str:
        return "a-user-granted-on-a-domain-searching-it-by-name-finds-only-its-users"

    @override
    def describe(self) -> str:
        return (
            "도메인 스코프에서 사용자 READ를 받은 사용자가 도메인 이름으로 훑으면, "
            "다른 도메인 사용자는 빠진다"
        )

    @override
    def given(self) -> Given[SeedingSession, Any]:
        return SomeoneInADomain(granted=True, with_neighbours=True)

    @override
    def when(self) -> When[Any, UserAdapter, Answer]:
        return SearchingTheDomain()

    @override
    def then(self) -> Then[Any, Answer]:
        return TheOffsetPage()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearchADomain(Scenario[SeedingSession, Any, UserAdapter, Answer]):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-a-domain-by-name"

    @override
    def describe(self) -> str:
        return "역할을 받지 않은 사용자가 도메인 이름으로 훑으려 하면, 스코프 권한 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, Any]:
        return SomeoneInADomain()

    @override
    def when(self) -> When[Any, UserAdapter, Answer]:
        return SearchingTheDomain()

    @override
    def then(self) -> Then[Any, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ADomainNameNothingAnswersToIsNotFound(Scenario[SeedingSession, Any, UserAdapter, Answer]):
    @override
    def summary(self) -> str:
        return "searching-a-domain-name-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return (
            "권한 받은 사용자가 없는 도메인 이름으로 훑으려 하면, "
            "스코프 검사 전에 이름 조회 단계가 대상 없음으로 막는다"
        )

    @override
    def given(self) -> Given[SeedingSession, Any]:
        return SomeoneInADomain(granted=True)

    @override
    def when(self) -> When[Any, UserAdapter, Answer]:
        return SearchingTheDomain(named=NO_SUCH_DOMAIN)

    @override
    def then(self) -> Then[Any, Answer]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AGrantedUserSearchesTheirDomainByGql(Scenario[SeedingSession, Any, UserAdapter, Answer]):
    @override
    def summary(self) -> str:
        return "a-user-granted-on-a-domain-gql-searching-it-finds-only-its-users"

    @override
    def describe(self) -> str:
        return "같은 권한으로 GQL 도메인 검색을 하면, 그 도메인 사용자만 커서 답으로 온다"

    @override
    def given(self) -> Given[SeedingSession, Any]:
        return SomeoneInADomain(granted=True, with_neighbours=True)

    @override
    def when(self) -> When[Any, UserAdapter, Answer]:
        return GqlSearchingTheDomain()

    @override
    def then(self) -> Then[Any, Answer]:
        return TheCursorPage()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotGqlSearchADomain(Scenario[SeedingSession, Any, UserAdapter, Answer]):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-gql-search-a-domain"

    @override
    def describe(self) -> str:
        return "역할 없이 GQL 도메인 검색을 하면, 스코프 권한 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, Any]:
        return SomeoneInADomain()

    @override
    def when(self) -> When[Any, UserAdapter, Answer]:
        return GqlSearchingTheDomain()

    @override
    def then(self) -> Then[Any, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearchAProject(Scenario[SeedingSession, Any, UserAdapter, Answer]):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-a-project"

    @override
    def describe(self) -> str:
        return "역할 없이 프로젝트 검색을 하면, 스코프 권한 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, Any]:
        return AProjectAndSomeone()

    @override
    def when(self) -> When[Any, UserAdapter, Answer]:
        return SearchingTheProject()

    @override
    def then(self) -> Then[Any, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotGqlSearchAProject(
    Scenario[SeedingSession, Any, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-gql-search-a-project"

    @override
    def describe(self) -> str:
        return "역할 없이 GQL 프로젝트 검색을 하면, 스코프 권한 문이 막는다"

    @override
    def given(self) -> Given[SeedingSession, Any]:
        return AProjectAndSomeone()

    @override
    def when(self) -> When[Any, UserAdapter, Answer]:
        return GqlSearchingTheProject()

    @override
    def then(self) -> Then[Any, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class OneUngrantedScopeRefusesTheScopedSearch(Scenario[SeedingSession, Any, UserAdapter, Answer]):
    @override
    def summary(self) -> str:
        return "one-scope-without-a-grant-refuses-the-whole-scoped-search"

    @override
    def describe(self) -> str:
        return "첫 스코프에만 READ를 받은 사용자가 두 스코프를 함께 주면, 스코프 권한 문이 전체를 막는다"

    @override
    def given(self) -> Given[SeedingSession, Any]:
        return TwoScopes(both=False)

    @override
    def when(self) -> When[Any, UserAdapter, Answer]:
        return ScopedSearchingDomainAndProject()

    @override
    def then(self) -> Then[Any, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class OneUngrantedScopeRefusesTheGqlScopedSearch(
    Scenario[SeedingSession, Any, UserAdapter, Answer]
):
    @override
    def summary(self) -> str:
        return "one-scope-without-a-grant-refuses-the-whole-gql-scoped-search"

    @override
    def describe(self) -> str:
        return (
            "한 스코프에만 READ를 받고 GQL 스코프 검색에 둘을 주면, 스코프 권한 문이 전체를 막는다"
        )

    @override
    def given(self) -> Given[SeedingSession, Any]:
        return TwoScopes(both=False)

    @override
    def when(self) -> When[Any, UserAdapter, Answer]:
        return GqlScopedSearchingDomainAndProject()

    @override
    def then(self) -> Then[Any, Answer]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AScopedSearchWithoutPagingAnswersFifty(Scenario[SeedingSession, Any, UserAdapter, Answer]):
    @override
    def summary(self) -> str:
        return "a-scoped-search-without-page-arguments-answers-up-to-fifty"

    @override
    def describe(self) -> str:
        return "권한 받은 사용자가 페이지 인자 없이 스코프 검색을 하면, limit 50 offset 0이 답에 실린다"

    @override
    def given(self) -> Given[SeedingSession, Any]:
        return SomeoneInADomain(granted=True)

    @override
    def when(self) -> When[Any, UserAdapter, Answer]:
        return ScopedSearchingTheDomain()

    @override
    def then(self) -> Then[Any, Answer]:
        return TheOffsetPage(limit=50, offset=0)


@dataclass(frozen=True)
class AGrantedUserSearchesTheRoster(Scenario[SeedingSession, Any, UserAdapter, Answer]):
    @override
    def summary(self) -> str:
        return "a-user-granted-on-a-project-searching-it-finds-only-its-roster"

    @override
    def describe(self) -> str:
        return (
            "프로젝트 스코프에서 사용자 READ를 받은 사용자가 그 프로젝트로 훑으면, "
            "명부에 오른 사용자만 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, Any]:
        return AProjectWithAMember()

    @override
    def when(self) -> When[Any, UserAdapter, Answer]:
        return SearchingTheProject()

    @override
    def then(self) -> Then[Any, Answer]:
        return TheOffsetPage()


@dataclass(frozen=True)
class AGrantedUserSearchesTheRosterByGql(Scenario[SeedingSession, Any, UserAdapter, Answer]):
    @override
    def summary(self) -> str:
        return "a-user-granted-on-a-project-gql-searching-it-finds-only-its-roster"

    @override
    def describe(self) -> str:
        return "같은 권한으로 GQL 프로젝트 검색을 하면, 명부의 사용자만 커서 답으로 온다"

    @override
    def given(self) -> Given[SeedingSession, Any]:
        return AProjectWithAMember()

    @override
    def when(self) -> When[Any, UserAdapter, Answer]:
        return GqlSearchingTheProject()

    @override
    def then(self) -> Then[Any, Answer]:
        return TheCursorPage()


@dataclass(frozen=True)
class TwoGrantedScopesAreJoined(Scenario[SeedingSession, Any, UserAdapter, Answer]):
    @override
    def summary(self) -> str:
        return "a-scoped-search-over-two-granted-scopes-joins-their-users"

    @override
    def describe(self) -> str:
        return (
            "도메인과 프로젝트 스코프 모두에서 READ를 받은 사용자가 두 스코프를 함께 주면, "
            "두 스코프의 사용자가 중복 없이 합쳐진다"
        )

    @override
    def given(self) -> Given[SeedingSession, Any]:
        return TwoScopes(both=True)

    @override
    def when(self) -> When[Any, UserAdapter, Answer]:
        return ScopedSearchingDomainAndProject()

    @override
    def then(self) -> Then[Any, Answer]:
        return TheOffsetPage()


@dataclass(frozen=True)
class TwoGrantedScopesAreJoinedByGql(Scenario[SeedingSession, Any, UserAdapter, Answer]):
    @override
    def summary(self) -> str:
        return "a-gql-scoped-search-over-two-granted-scopes-joins-their-users"

    @override
    def describe(self) -> str:
        return "같은 권한으로 GQL 스코프 검색을 하면, 두 스코프 사용자가 커서 답으로 온다"

    @override
    def given(self) -> Given[SeedingSession, Any]:
        return TwoScopes(both=True)

    @override
    def when(self) -> When[Any, UserAdapter, Answer]:
        return GqlScopedSearchingDomainAndProject()

    @override
    def then(self) -> Then[Any, Answer]:
        return TheCursorPage()


SCENARIOS: list[SearchStep] = [
    AGrantedUserSearchesTheRoster(),
    AGrantedUserSearchesTheRosterByGql(),
    TwoGrantedScopesAreJoined(),
    TwoGrantedScopesAreJoinedByGql(),
    TheSuperadminCountsDeletedUsersToo(),
    OnlyTheSuperadminSearchesEveryUser(),
    TheSuperadminSearchesEveryUserWithoutPaging(),
    OnlyTheSuperadminSearchesEveryUserByGql(),
    TheSuperadminSearchesByRole(),
    OnlyTheSuperadminSearchesByRole(),
    AGrantedUserSearchesTheirDomain(),
    AUserGrantedNothingMayNotSearchADomain(),
    ADomainNameNothingAnswersToIsNotFound(),
    AGrantedUserSearchesTheirDomainByGql(),
    AUserGrantedNothingMayNotGqlSearchADomain(),
    AUserGrantedNothingMayNotSearchAProject(),
    AUserGrantedNothingMayNotGqlSearchAProject(),
    OneUngrantedScopeRefusesTheScopedSearch(),
    OneUngrantedScopeRefusesTheGqlScopedSearch(),
    AScopedSearchWithoutPagingAnswersFifty(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchStep, adapter: UserAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
