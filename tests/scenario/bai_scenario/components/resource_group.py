"""What a resource group scenario table says besides the call.

A group is created in no scope and is its own scope, so a role sitting on the group is
how a user other than the superadmin reaches it. A table needs the caller, the group or
groups the call reads, and for the allow lists the domain or project on the other side
of the link.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType, ResourceGroupID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_group.response import (
    AllowedDomainsPayload,
    AllowedProjectsPayload,
    AllowedResourceGroupsPayload,
    FairShareResourceGroupSpecInfo,
    ResourceGroupDetailNode,
    ResourceInfoNode,
)
from ai.backend.common.dto.manager.v2.resource_group.types import (
    PreemptionModeDTO,
    SchedulerTypeDTO,
)
from ai.backend.common.types import PreemptionOrder, PreemptionVictimScope
from ai.backend.manager.api.adapters.resource_group.adapter import ResourceGroupSearchPayload
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Skipped,
    Then,
    Verdict,
)
from bai_scenario.components.domain import WAS_HERE, SomeoneOf, WrittenByThisRun
from bai_scenario.components.system import KEPT, Kept, role_named
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.project.project import SeedProject
from bai_scenario.seeds.rbac.role import SeedPermission, SeedRole
from bai_scenario.seeds.resource_group.resource_group import (
    LinkToDomain,
    LinkToProject,
    SeedResourceGroup,
)
from bai_scenario.seeds.resource_policy.project import SeedProjectPolicy
from bai_scenario.seeds.seeder import Laid, Seeder, SeedNest

type Loaded = list[ResourceGroupDetailNode | Exception | None]

SCHEDULER = "fifo"


# ------------------------------------------------------------------ situations


@dataclass(frozen=True)
class AGroupAndACaller:
    """리소스 그룹 하나와, 그것을 호출할 사용자."""

    group: ResourceGroupData
    caller: UserData


@dataclass(frozen=True)
class ManyGroupsAndACaller:
    """검색 대상 그룹 여럿과, 검색을 호출할 사용자. ``laid``는 응답에 나와야 하는 것만이고 ``named``는 그중 하나다."""

    laid: tuple[ResourceGroupData, ...]
    named: ResourceGroupData
    caller: UserData


@dataclass(frozen=True)
class ADomainGroupsAndACaller:
    """도메인 하나, 그 도메인에 건 그룹과 걸지 않은 그룹, 그리고 호출할 사용자."""

    domain: DomainData
    linked: ResourceGroupData
    other: ResourceGroupData
    caller: UserData


@dataclass(frozen=True)
class AProjectAGroupAndACaller:
    """프로젝트 하나와 그룹 하나, 그리고 호출할 사용자."""

    project: ProjectData
    group: ResourceGroupData
    caller: UserData


@dataclass(frozen=True)
class SomeoneGrantedOnTheGroup(SeedNest[Laid[None]]):
    """그 그룹에 앉힌 역할로 권한 하나를 받은 사용자."""

    group: Laid[ResourceGroupData]
    user: Laid[UserData]
    permission: Permission

    @override
    def kind(self) -> str:
        return f"리소스 그룹 범위의 {self.permission.name} 역할을 받은 사용자 준비"

    @override
    def lay(self, seed: Seeder) -> Laid[None]:
        role = seed.creating_from(
            SeedRole(lambda g: ResourceGroupID(g.id), name_hint="group-role"), self.group
        )
        seed.adding(
            SeedPermission(entity_type=ResourceGroupEntityType(), permission=self.permission),
            role,
        )
        return seed.granting(
            role, self.user, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id)
        )


@dataclass(frozen=True)
class SomeoneReadingGroupsInTheDomain(SeedNest[Laid[None]]):
    """그 도메인 범위에서 리소스 그룹을 읽을 수 있는 사용자."""

    domain: Laid[DomainData]
    user: Laid[UserData]

    @override
    def kind(self) -> str:
        return "도메인 범위의 리소스 그룹 읽기 역할을 받은 사용자 준비"

    @override
    def lay(self, seed: Seeder) -> Laid[None]:
        role = seed.creating_from(SeedRole(lambda d: d.id, name_hint="group-reader"), self.domain)
        seed.adding(
            SeedPermission(entity_type=ResourceGroupEntityType(), permission=Permission.READ),
            role,
        )
        return seed.granting(
            role, self.user, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id)
        )


@dataclass(frozen=True)
class AGroupAndSomeone(Given[Any, AGroupAndACaller]):
    """그룹 하나와 사용자 한 명. ``granted``를 주면 그 그룹에 앉힌 역할로 그 권한을 받는다."""

    role: UserRole = UserRole.USER
    granted: Permission | None = None
    description: str | None = None
    is_active: bool = True
    is_default: bool = False

    @override
    def describe(self) -> str:
        who = role_named(self.role)
        if self.granted is not None:
            who = f"그 그룹 범위의 {self.granted.name} 역할을 받은 {who}"
        return f"리소스 그룹 하나와, {who} 한 명"

    @override
    async def lay(self, seeding: Any) -> AGroupAndACaller:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        group = await seeding.creating(
            SeedResourceGroup(
                description=self.description, is_active=self.is_active, is_default=self.is_default
            )
        )
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        if self.granted is not None:
            await seeding.within(SomeoneGrantedOnTheGroup(group, caller, self.granted))
        return AGroupAndACaller(seeding.made(group), seeding.made(caller))


@dataclass(frozen=True)
class AGroupBesideTheDefaultAndSomeone(Given[Any, AGroupAndACaller]):
    """기본 그룹이 따로 있을 때의 그룹 하나와 사용자 한 명. ``group``은 기본이 아닌 쪽이다."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return (
            f"기본 리소스 그룹 하나와 기본이 아닌 그룹 하나, 그리고 {role_named(self.role)} 한 명"
        )

    @override
    async def lay(self, seeding: Any) -> AGroupAndACaller:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        await seeding.creating(SeedResourceGroup(name_hint="default-group", is_default=True))
        group = await seeding.creating(SeedResourceGroup())
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        return AGroupAndACaller(seeding.made(group), seeding.made(caller))


@dataclass(frozen=True)
class TwoGroupsAndSomeone(Given[Any, ManyGroupsAndACaller]):
    """그룹 둘과 사용자 한 명. ``named``는 앞의 것이다."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"리소스 그룹 둘과, {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyGroupsAndACaller:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        wanted = await seeding.creating(SeedResourceGroup(name_hint="wanted"))
        other = await seeding.creating(SeedResourceGroup(name_hint="other"))
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        return ManyGroupsAndACaller(
            laid=(seeding.made(wanted), seeding.made(other)),
            named=seeding.made(wanted),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class AnActiveAndAnInactiveGroup(Given[Any, ManyGroupsAndACaller]):
    """활성 그룹 하나와 비활성 그룹 하나, 사용자 한 명. ``laid``는 활성인 것뿐이다."""

    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"활성 리소스 그룹 하나와 비활성 하나, 그리고 {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyGroupsAndACaller:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        active = await seeding.creating(SeedResourceGroup(name_hint="active"))
        await seeding.creating(SeedResourceGroup(name_hint="inactive", is_active=False))
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        return ManyGroupsAndACaller(
            laid=(seeding.made(active),),
            named=seeding.made(active),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class ADomainGroupsAndSomeone(Given[Any, ADomainGroupsAndACaller]):
    """호출자의 도메인에 건 그룹 하나와 걸지 않은 그룹 하나, 사용자 한 명.

    ``reading``이면 그 도메인 범위에서 리소스 그룹을 읽는 역할을 받는다. ``linked``가
    False면 어느 그룹도 걸지 않는다.
    """

    role: UserRole = UserRole.USER
    reading: bool = False
    linked: bool = True

    @override
    def describe(self) -> str:
        who = role_named(self.role)
        if self.reading:
            who = f"그 도메인 범위의 리소스 그룹 읽기 역할을 받은 {who}"
        groups = (
            "도메인에 건 리소스 그룹 하나와 걸지 않은 그룹 하나"
            if self.linked
            else "어느 것도 도메인에 걸지 않은 리소스 그룹 둘"
        )
        return f"도메인 하나, {groups}, 그리고 {who} 한 명"

    @override
    async def lay(self, seeding: Any) -> ADomainGroupsAndACaller:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        linked = await seeding.creating(SeedResourceGroup(name_hint="linked"))
        other = await seeding.creating(SeedResourceGroup(name_hint="other"))
        if self.linked:
            await seeding.linking(LinkToDomain(), home, linked)
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        if self.reading:
            await seeding.within(SomeoneReadingGroupsInTheDomain(home, caller))
        return ADomainGroupsAndACaller(
            seeding.made(home), seeding.made(linked), seeding.made(other), seeding.made(caller)
        )


@dataclass(frozen=True)
class AProjectAGroupAndSomeone(Given[Any, AProjectAGroupAndACaller]):
    """호출자의 도메인에 있는 프로젝트 하나와 그룹 하나, 사용자 한 명. ``linked``면 그룹을 프로젝트에 건다."""

    role: UserRole = UserRole.USER
    linked: bool = False

    @override
    def describe(self) -> str:
        group = "프로젝트에 건 리소스 그룹 하나" if self.linked else "리소스 그룹 하나"
        return f"프로젝트 하나와 {group}, 그리고 {role_named(self.role)} 한 명"

    @override
    async def lay(self, seeding: Any) -> AProjectAGroupAndACaller:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        policy = await seeding.once(SeedProjectPolicy())
        project = await seeding.creating_from_two(SeedProject(name_hint="team"), home, policy)
        group = await seeding.creating(SeedResourceGroup())
        if self.linked:
            await seeding.linking(LinkToProject(), project, group)
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        return AProjectAGroupAndACaller(
            seeding.made(project), seeding.made(group), seeding.made(caller)
        )


# ------------------------------------------------------------------ verdicts


@dataclass(frozen=True)
class GroupLook:
    """미리 만들어 둔 그룹이 응답에서 어떻게 보여야 하는지. 바뀐 자리만 값을 준다."""

    started: datetime
    named: str | Kept = KEPT
    described: str | None | Kept = KEPT
    is_active: bool | Kept = KEPT
    is_public: bool | Kept = KEPT
    is_default: bool | Kept = KEPT
    scheduler_type: SchedulerTypeDTO | Kept = KEPT
    wsproxy_addr: str | None | Kept = KEPT
    use_host_network: bool | Kept = KEPT
    preemption_enabled: bool | Kept = KEPT
    preemptible_priority: int | Kept = KEPT
    preemption_order: PreemptionOrder | Kept = KEPT
    preemption_mode: PreemptionModeDTO | Kept = KEPT
    preemption_min_runtime: float | Kept = KEPT
    victim_scope: PreemptionVictimScope | Kept = KEPT

    def verdicts(
        self, prefix: str, node: ResourceGroupDetailNode, seed: ResourceGroupData
    ) -> list[Verdict]:
        preemption = seed.scheduler.options.preemption
        return [
            Skipped(f"{prefix}id", "데이터베이스가 만든다"),
            Same(f"{prefix}name", node.name, _or(self.named, seed.name)),
            Same(
                f"{prefix}status.is_active",
                node.status.is_active,
                _or(self.is_active, seed.status.is_active),
            ),
            Same(
                f"{prefix}status.is_public",
                node.status.is_public,
                _or(self.is_public, seed.status.is_public),
            ),
            Same(
                f"{prefix}status.is_default",
                node.status.is_default,
                _or(self.is_default, seed.status.is_default),
            ),
            Same(
                f"{prefix}metadata.description",
                node.metadata.description,
                _or(self.described, seed.metadata.description or None),
            ),
            Held(
                f"{prefix}metadata.created_at",
                node.metadata.created_at,
                WrittenByThisRun(self.started),
            ),
            Same(
                f"{prefix}network.wsproxy_addr",
                node.network.wsproxy_addr,
                _or(self.wsproxy_addr, seed.network.wsproxy_addr or None),
            ),
            Same(
                f"{prefix}network.use_host_network",
                node.network.use_host_network,
                _or(self.use_host_network, seed.network.use_host_network),
            ),
            Same(
                f"{prefix}scheduler.type",
                node.scheduler.type,
                _or(self.scheduler_type, SchedulerTypeDTO(seed.scheduler.name.value)),
            ),
            Same(
                f"{prefix}scheduler.preemption.enabled",
                node.scheduler.preemption.enabled,
                _or(self.preemption_enabled, preemption.enabled),
            ),
            Same(
                f"{prefix}scheduler.preemption.preemptible_priority",
                node.scheduler.preemption.preemptible_priority,
                _or(self.preemptible_priority, preemption.preemptible_priority),
            ),
            Same(
                f"{prefix}scheduler.preemption.order",
                node.scheduler.preemption.order,
                _or(self.preemption_order, preemption.order),
            ),
            Same(
                f"{prefix}scheduler.preemption.mode",
                node.scheduler.preemption.mode,
                _or(self.preemption_mode, PreemptionModeDTO(preemption.mode.value)),
            ),
            Same(
                f"{prefix}scheduler.preemption.preemption_min_runtime",
                node.scheduler.preemption.preemption_min_runtime,
                _or(self.preemption_min_runtime, preemption.preemption_min_runtime.total_seconds()),
            ),
            Same(
                f"{prefix}scheduler.preemption.victim_scope",
                node.scheduler.preemption.victim_scope,
                _or(self.victim_scope, preemption.victim_scope),
            ),
            Skipped(f"{prefix}default_deployment_options", "설치본이 정한 기본값이다"),
            Skipped(f"{prefix}default_session_options", "설치본이 정한 기본값이다"),
        ]


def _or[V](asked: V | Kept, kept: V) -> V:
    return kept if isinstance(asked, Kept) else asked


@dataclass(frozen=True)
class TheNewGroupNode(Then[Any, ResourceGroupDetailNode]):
    """방금 만든 그룹이 통째로 반환된다. 기대값은 요청이 지정한 값과 코드의 기본값이다."""

    started: datetime
    named: str
    is_default: bool = False

    @override
    def says(self) -> str:
        return "만든 리소스 그룹 전체가 반환된다"

    @override
    def look(self, laid: Any, answered: Answered[ResourceGroupDetailNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Skipped("id", "데이터베이스가 만든다"),
            Same("name", node.name, self.named),
            Same("status.is_active", node.status.is_active, True),
            Same("status.is_public", node.status.is_public, True),
            Same("status.is_default", node.status.is_default, self.is_default),
            Same("metadata.description", node.metadata.description, None),
            Held("metadata.created_at", node.metadata.created_at, WrittenByThisRun(self.started)),
            Same("network.wsproxy_addr", node.network.wsproxy_addr, None),
            Same("network.use_host_network", node.network.use_host_network, False),
            Same("scheduler.type", node.scheduler.type, SchedulerTypeDTO.FIFO),
            Same("scheduler.preemption.enabled", node.scheduler.preemption.enabled, False),
            Same(
                "scheduler.preemption.preemptible_priority",
                node.scheduler.preemption.preemptible_priority,
                5,
            ),
            Same(
                "scheduler.preemption.order",
                node.scheduler.preemption.order,
                PreemptionOrder.OLDEST,
            ),
            Same(
                "scheduler.preemption.mode",
                node.scheduler.preemption.mode,
                PreemptionModeDTO.TERMINATE,
            ),
            Same(
                "scheduler.preemption.preemption_min_runtime",
                node.scheduler.preemption.preemption_min_runtime,
                0.0,
            ),
            Same(
                "scheduler.preemption.victim_scope",
                node.scheduler.preemption.victim_scope,
                PreemptionVictimScope.USER,
            ),
            Skipped("default_deployment_options", "설치본이 정한 기본값이다"),
            Skipped("default_session_options", "설치본이 정한 기본값이다"),
        ]


@dataclass(frozen=True)
class TheGroupNode(Then[AGroupAndACaller, ResourceGroupDetailNode]):
    """미리 만들어 둔 그룹이 통째로 반환된다. 수정 요청은 바뀌어야 하는 자리만 ``look``에 준다."""

    look_for: GroupLook

    @override
    def says(self) -> str:
        return "미리 만들어 둔 리소스 그룹 전체가 반환된다"

    @override
    def look(
        self, laid: AGroupAndACaller, answered: Answered[ResourceGroupDetailNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return self.look_for.verdicts("", node, laid.group)


@dataclass(frozen=True)
class TheLaidGroupsAreLeft(Then[ManyGroupsAndACaller, ResourceGroupSearchPayload]):
    """응답에 나와야 하는 그룹이 모두, 그리고 그것만 반환된다."""

    @override
    def says(self) -> str:
        return "응답에 나와야 하는 리소스 그룹만 반환된다"

    @override
    def look(
        self, laid: ManyGroupsAndACaller, answered: Answered[ResourceGroupSearchPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same(
                "items",
                sorted(one.name for one in page.items),
                sorted(one.name for one in laid.laid),
            ),
            Same("total_count", page.total_count, len(laid.laid)),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class OnlyTheNamedGroupIsLeft(Then[ManyGroupsAndACaller, ResourceGroupSearchPayload]):
    """필터에 맞는 그 하나만 반환된다."""

    @override
    def says(self) -> str:
        return "필터에 맞는 리소스 그룹 하나만 반환된다"

    @override
    def look(
        self, laid: ManyGroupsAndACaller, answered: Answered[ResourceGroupSearchPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same("items", [one.name for one in page.items], [laid.named.name]),
            Same("total_count", page.total_count, 1),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheFirstGroupPage(Then[ManyGroupsAndACaller, ResourceGroupSearchPayload]):
    """한 건짜리 첫 페이지. 한 건이 반환되고 다음 페이지가 있다고 응답한다."""

    @override
    def says(self) -> str:
        return "한 건짜리 첫 페이지가 반환된다"

    @override
    def look(
        self, laid: ManyGroupsAndACaller, answered: Answered[ResourceGroupSearchPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same("len(items)", len(page.items), 1),
            Same("total_count", page.total_count, len(laid.laid)),
            Same("has_next_page", page.has_next_page, True),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class OnlyTheLinkedGroupIsLeft(Then[ADomainGroupsAndACaller, ResourceGroupSearchPayload]):
    """도메인에 건 그룹 하나만 반환된다."""

    @override
    def says(self) -> str:
        return "도메인에 건 리소스 그룹 하나만 반환된다"

    @override
    def look(
        self, laid: ADomainGroupsAndACaller, answered: Answered[ResourceGroupSearchPayload]
    ) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same("items", [one.name for one in page.items], [laid.linked.name]),
            Same("total_count", page.total_count, 1),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheGroupsInTheOrderAsked(Then[ManyGroupsAndACaller, Loaded]):
    """요청한 순서대로 한 항목씩 반환된다. 미리 만들어 둔 것은 노드로, 없는 것은 빈 항목으로."""

    started: datetime

    @override
    def says(self) -> str:
        return "요청한 순서대로 반환되고, 없는 것에 해당하는 항목은 비어 있다"

    @override
    def look(self, laid: ManyGroupsAndACaller, answered: Answered[Loaded]) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        asked = len(laid.laid) + 1
        seen: list[Verdict] = [Same("len(items)", len(items), asked)]
        look = GroupLook(started=self.started)
        for i, expected in enumerate(laid.laid):
            got = items[i] if i < len(items) else None
            if not isinstance(got, ResourceGroupDetailNode):
                seen.append(Same(f"items[{i}]", got, "노드"))
                continue
            seen.extend(look.verdicts(f"items[{i}].", got, expected))
        last = items[asked - 1] if len(items) >= asked else "없음"
        seen.append(Same(f"items[{asked - 1}]", last, None))
        return seen


@dataclass(frozen=True)
class EachItemIsRefused(Then[Any, list[Any]]):
    """요청한 항목마다 권한 부족 거부가 담긴다."""

    asked: int

    @override
    def says(self) -> str:
        return "항목마다 권한 부족 거부가 담긴다"

    @override
    def look(self, laid: Any, answered: Answered[list[Any]]) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        seen: list[Verdict] = [Same("len(items)", len(items), self.asked)]
        for i in range(self.asked):
            got = items[i] if i < len(items) else None
            seen.append(
                Same(
                    f"items[{i}]",
                    type(got).__name__ if got is not None else None,
                    NotEnoughPermission.__name__,
                )
            )
        return seen


@dataclass(frozen=True)
class NothingComesBack(Then[Any, list[Any]]):
    """빈 응답이 반환된다."""

    @override
    def says(self) -> str:
        return "빈 응답이 반환된다"

    @override
    def look(self, laid: Any, answered: Answered[list[Any]]) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [Same("items", items, [])]


@dataclass(frozen=True)
class TheResourceInfoIsEmpty(Then[AGroupAndACaller, ResourceInfoNode]):
    """에이전트가 없어 용량·사용량·여유가 모두 비어 있다."""

    @override
    def says(self) -> str:
        return "용량·사용량·여유가 모두 비어 있다"

    @override
    def look(self, laid: AGroupAndACaller, answered: Answered[ResourceInfoNode]) -> list[Verdict]:
        info = answered.response
        if info is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same("capacity.entries", list(info.capacity.entries), []),
            Same("used.entries", list(info.used.entries), []),
            Same("free.entries", list(info.free.entries), []),
        ]


@dataclass(frozen=True)
class TheLinkedGroupIsAllowed(Then[ADomainGroupsAndACaller, AllowedResourceGroupsPayload]):
    """도메인에 건 그룹 이름만 담긴다."""

    @override
    def says(self) -> str:
        return "허용 목록에 건 리소스 그룹 이름만 담긴다"

    @override
    def look(
        self, laid: ADomainGroupsAndACaller, answered: Answered[AllowedResourceGroupsPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [Same("items", payload.items, [laid.linked.name])]


@dataclass(frozen=True)
class TheOtherGroupIsAllowed(Then[ADomainGroupsAndACaller, AllowedResourceGroupsPayload]):
    """걸지 않았던 그룹 이름만 담긴다. 그것을 방금 걸었을 때 본다."""

    @override
    def says(self) -> str:
        return "허용 목록에 방금 건 리소스 그룹 이름만 담긴다"

    @override
    def look(
        self, laid: ADomainGroupsAndACaller, answered: Answered[AllowedResourceGroupsPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [Same("items", payload.items, [laid.other.name])]


@dataclass(frozen=True)
class TheGroupIsAllowedForTheProject(Then[AProjectAGroupAndACaller, AllowedResourceGroupsPayload]):
    """그 그룹 이름만 담긴다."""

    @override
    def says(self) -> str:
        return "허용 목록에 건 리소스 그룹 이름만 담긴다"

    @override
    def look(
        self, laid: AProjectAGroupAndACaller, answered: Answered[AllowedResourceGroupsPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [Same("items", payload.items, [laid.group.name])]


@dataclass(frozen=True)
class NothingIsAllowed(Then[Any, Any]):
    """허용 목록이 비어 있다. 그룹·도메인·프로젝트 목록 모두 같은 자리 이름을 쓴다."""

    @override
    def says(self) -> str:
        return "허용 목록이 비어 있다"

    @override
    def look(self, laid: Any, answered: Answered[Any]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [Same("items", list(payload.items), [])]


@dataclass(frozen=True)
class TheAllowedDomainNames(Then[ADomainGroupsAndACaller, AllowedDomainsPayload]):
    """허용 도메인에 그 도메인 이름만 담긴다."""

    @override
    def says(self) -> str:
        return "허용 도메인에 건 도메인 이름만 담긴다"

    @override
    def look(
        self, laid: ADomainGroupsAndACaller, answered: Answered[AllowedDomainsPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [Same("items", payload.items, [laid.domain.name])]


@dataclass(frozen=True)
class TheAllowedProjectIds(Then[AProjectAGroupAndACaller, AllowedProjectsPayload]):
    """허용 프로젝트에 그 프로젝트 id만 담긴다."""

    @override
    def says(self) -> str:
        return "허용 프로젝트에 건 프로젝트 id만 담긴다"

    @override
    def look(
        self, laid: AProjectAGroupAndACaller, answered: Answered[AllowedProjectsPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Held[list[UUID]](
                "items", list(payload.items), SameAs[list[UUID]]([laid.project.id], "건 프로젝트")
            )
        ]


@dataclass(frozen=True)
class TheFairShareDefaults(Then[AGroupAndACaller, FairShareResourceGroupSpecInfo]):
    """코드가 정한 기본 fair share 설정. 에이전트가 없어 가중치 목록은 비어 있다."""

    @override
    def says(self) -> str:
        return "기본 fair share 설정이 반환되고 가중치 목록은 비어 있다"

    @override
    def look(
        self, laid: AGroupAndACaller, answered: Answered[FairShareResourceGroupSpecInfo]
    ) -> list[Verdict]:
        spec = answered.response
        if spec is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Same("half_life_days", spec.half_life_days, 7),
            Same("lookback_days", spec.lookback_days, 28),
            Same("decay_unit_days", spec.decay_unit_days, 1),
            Same("default_weight", str(spec.default_weight), "1.0"),
            Same("resource_weights", list(spec.resource_weights), []),
        ]
