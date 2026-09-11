"""What a domain scenario table says besides the call.

How the adapter is built lives in the tables' own conftest, and the rows a scenario
lays come from ``seeds``. This holds what is left: the type a domain table is written
against, and the situations worth naming more than once.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, override

from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.rbac.role import SeedPermission, SeedRole
from bai_scenario.seeds.resource_policy.keypair import SeedKeypairPolicy
from bai_scenario.seeds.resource_policy.project import SeedProjectPolicy
from bai_scenario.seeds.resource_policy.user import SeedUserPolicy
from bai_scenario.seeds.seeder import Laid, Seeder, SeedNest
from bai_scenario.seeds.user.user import SeedUserOf

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.domain.response import DomainNode
from ai.backend.common.types import VFolderHostPermission
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.testutils.scenario_steps import (
    Answered,
    Condition,
    Given,
    Held,
    Refused,
    Same,
    Skipped,
    Then,
    Verdict,
)

WAS_HERE = "이미 있던 도메인"
"""시드가 심는 도메인의 설명. 시나리오가 기대값으로 다시 쓰므로 한 자리에 둔다."""

SKEW = timedelta(seconds=30)
"""두 시계가 어긋나 있어도 봐주는 폭."""


@dataclass(frozen=True)
class ADomainAndACaller:
    """도메인 하나와, 그것을 부를 사람."""

    domain: DomainData
    caller: UserData


@dataclass(frozen=True)
class ADomainAndSomeone(Given[Any, ADomainAndACaller]):
    """도메인 하나와 그 도메인에 속한 사용자 한 명."""

    role: UserRole = UserRole.USER
    name_hint: str = "host"

    @override
    def describe(self) -> str:
        return f"도메인 하나와, 그 도메인에 속한 {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> ADomainAndACaller:
        domain = await seeding.creating(SeedDomain(name_hint=self.name_hint, description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(domain, role=self.role))
        return ADomainAndACaller(seeding.made(domain), seeding.made(caller))


@dataclass(frozen=True)
class ATargetAndSomeone(Given[Any, ADomainAndACaller]):
    """건드릴 도메인 하나와, 다른 도메인에 사는 사람 한 명.

    건드리는 대상이 부르는 사람의 집이면 안 되는 자리에 쓴다. 완전히 지우는 요청이 그렇다.
    """

    role: UserRole = UserRole.USER
    name_hint: str = "target"

    @override
    def describe(self) -> str:
        return f"건드릴 도메인 하나와, 다른 도메인에 사는 {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> ADomainAndACaller:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        target = await seeding.creating(SeedDomain(name_hint=self.name_hint, description=WAS_HERE))
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        return ADomainAndACaller(seeding.made(target), seeding.made(caller))


@dataclass(frozen=True)
class ManyDomainsAndACaller:
    """훑을 도메인 여럿과, 훑을 사람. `named`는 그중 골라낼 하나다."""

    laid: tuple[DomainData, ...]
    named: DomainData
    caller: UserData


@dataclass(frozen=True)
class ManyDomainsAndSomeone(Given[Any, ManyDomainsAndACaller]):
    """도메인 여럿과 그중 한 도메인에 속한 사용자 한 명."""

    role: UserRole = UserRole.USER
    besides: int = 2

    @override
    def describe(self) -> str:
        return f"도메인 {self.besides + 2}개와, 그중 하나에 속한 {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> ManyDomainsAndACaller:
        home = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
        wanted = await seeding.creating(SeedDomain(name_hint="wanted", description=WAS_HERE))
        others = [
            await seeding.creating(SeedDomain(name_hint="other", description=WAS_HERE))
            for _ in range(self.besides)
        ]
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        return ManyDomainsAndACaller(
            laid=tuple(seeding.made(one) for one in [home, wanted, *others]),
            named=seeding.made(wanted),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class WrittenByThisRun(Condition[datetime | None]):
    """이 실행이 쓴 시각. 값 자체는 실행마다 달라 레포트에 넣지 않는다."""

    started: datetime

    @override
    def says(self) -> str:
        return "이 실행이 쓴 시각"

    @override
    def holds(self, got: datetime | None) -> bool:
        if got is None or got.tzinfo is None:
            return False
        return self.started - SKEW <= got <= datetime.now(UTC) + SKEW


@dataclass(frozen=True)
class TheDomainNode(Then[ADomainAndACaller, DomainNode]):
    """도메인 노드 하나가 통째로 온다.

    이름은 심은 것에서 읽는다. 시나리오가 정한 값만 여기로 받는다. 답이 노드를 감싸고
    있으면 `when`이 벗겨서 준다.
    """

    started: datetime
    described: str | None = WAS_HERE
    active: bool = True

    @override
    def says(self) -> str:
        return "심은 도메인 전체가 온다"

    @override
    def look(self, laid: ADomainAndACaller, answered: Answered[DomainNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        written = WrittenByThisRun(self.started)
        return [
            Same("name", node.basic_info.name, laid.domain.name),
            Same("description", node.basic_info.description, self.described),
            Same("integration_name", node.basic_info.integration_name, None),
            Same("allowed_docker_registries", node.registry.allowed_docker_registries, []),
            Same("is_active", node.lifecycle.is_active, self.active),
            Same("is_default", node.lifecycle.is_default, False),
            Skipped("id", "데이터베이스가 만든다"),
            Held("created_at", node.lifecycle.created_at, written),
            Held("modified_at", node.lifecycle.modified_at, written),
        ]


@dataclass(frozen=True)
class TheNewDomainNode(Then[Any, DomainNode]):
    """방금 만든 도메인이 통째로 온다. 이름과 설명은 시나리오가 정한 것이다."""

    started: datetime
    named: str
    described: str | None

    @override
    def says(self) -> str:
        return "만든 도메인 전체가 온다"

    @override
    def look(self, laid: Any, answered: Answered[DomainNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        written = WrittenByThisRun(self.started)
        return [
            Same("name", node.basic_info.name, self.named),
            Same("description", node.basic_info.description, self.described),
            Same("integration_name", node.basic_info.integration_name, None),
            Same("allowed_docker_registries", node.registry.allowed_docker_registries, []),
            Same("is_active", node.lifecycle.is_active, True),
            Same("is_default", node.lifecycle.is_default, False),
            Skipped("id", "데이터베이스가 만든다"),
            Held("created_at", node.lifecycle.created_at, written),
            Held("modified_at", node.lifecycle.modified_at, written),
        ]


@dataclass(frozen=True)
class TheCallIsRefused(Then[Any, Any]):
    """이 이름으로 거부된다."""

    expected: type[BaseException]

    @override
    def says(self) -> str:
        return "거부된다"

    @override
    def look(self, laid: Any, answered: Answered[Any]) -> list[Verdict]:
        return [Refused(self.expected, answered.raised)]


@dataclass(frozen=True)
class GrantedUser:
    """A user and the grant they hold, answered apart.

    The row beside it that wants the same user without the grant simply does not ask
    for one, so the two never travel as an inseparable pair.
    """

    user: Laid[UserData]
    grant: Laid[None]


@dataclass(frozen=True)
class SomeoneOf(SeedNest[Laid[UserData]]):
    """그 도메인에 속한 사용자 한 명. 매니저가 사용자를 만드는 경로를 그대로 탄다.

    그 경로가 인증에 쓰는 키와, 자기 폴더가 사는 개인 프로젝트까지 함께 만든다. 둘 다
    장식이 아니다. 호출자를 찾는 요청이나 자기 폴더를 만드는 요청은 그 둘이 없으면 권한을
    보기도 전에 실패한다.
    """

    domain: Laid[DomainData]
    role: UserRole = UserRole.USER
    name_hint: str = "user"
    """이 사람이 그 시나리오에서 무엇인지. 레포트가 이 이름으로 부른다."""
    vfolder_hosts: Sequence[str] = ()
    max_vfolder_count: int = 10
    host_permissions: Sequence[VFolderHostPermission] = tuple(VFolderHostPermission)

    @override
    def kind(self) -> str:
        return "도메인에 속한 사용자 한 명 준비"

    @override
    def lay(self, seed: Seeder) -> Laid[UserData]:
        seed.once(SeedProjectPolicy())
        policy = seed.creating(SeedUserPolicy(max_vfolder_count=self.max_vfolder_count))
        key_policy = seed.creating(
            SeedKeypairPolicy(
                vfolder_hosts=self.vfolder_hosts, host_permissions=self.host_permissions
            )
        )
        return seed.provisioning(
            SeedUserOf(role=self.role, name_hint=self.name_hint), self.domain, policy, key_policy
        )


@dataclass(frozen=True)
class SomeoneReadingDomains(SeedNest[GrantedUser]):
    """그 도메인 범위에서 도메인을 읽을 수 있는 사용자."""

    domain: Laid[DomainData]

    @override
    def kind(self) -> str:
        return "도메인 조회 권한을 받은 사용자 준비"

    @override
    def lay(self, seed: Seeder) -> GrantedUser:
        someone = seed.within(SomeoneOf(self.domain))
        role = seed.creating_from(SeedRole(lambda d: d.id, name_hint="domain-reader"), self.domain)
        seed.adding(
            SeedPermission(entity_type=DomainEntityType(), permission=Permission.READ), role
        )
        grant = seed.granting(role, someone, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id))
        return GrantedUser(someone, grant)
