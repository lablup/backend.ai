"""What a resource policy scenario table says besides the call.

One adapter answers for three policies of the same shape, so a table is written once
and run against each. What tells the three apart — the seed that lays one, the calls
that read and write one, the places a node has — is gathered here as one class per
policy, and a row names the one it runs against.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, override

from bai_scenario.components.domain import WAS_HERE, WrittenByThisRun
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.resource_policy.keypair import SeedKeypairPolicy
from bai_scenario.seeds.resource_policy.project import SeedNamedProjectPolicy, SeedProjectPolicy
from bai_scenario.seeds.resource_policy.user import SeedUserPolicy
from bai_scenario.seeds.seeder import Laid, Seeder, SeedNest, SeedRow
from bai_scenario.seeds.user.user import SeedUserOf

from ai.backend.common.data.entity.resource_policy import (
    ProjectResourcePolicyEntityType,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.common import (
    BinarySizeInput,
)
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    AdminSearchProjectResourcePoliciesInput,
    CreateProjectResourcePolicyInput,
    DeleteProjectResourcePolicyInput,
    ProjectResourcePolicyFilter,
    UpdateProjectResourcePolicyInput,
)
from ai.backend.common.dto.manager.v2.resource_policy.response import (
    ProjectResourcePolicyNode,
    SearchProjectResourcePoliciesPayload,
)
from ai.backend.common.types import BinarySize
from ai.backend.manager.api.adapters.resource_policy.adapter import ResourcePolicyAdapter
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.resource.types import (
    KeyPairResourcePolicyData,
    ProjectResourcePolicyData,
    UserResourcePolicyData,
)
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    Then,
    Verdict,
)

type Searched = SearchProjectResourcePoliciesPayload


@dataclass(frozen=True)
class Calls:
    """The adapter calls one policy answers to, by the names the report counts."""

    create: str
    read: str
    search: str
    update: str
    delete: str


@dataclass(frozen=True)
class Ask:
    """만들기 요청 하나와, 그 요청이 답에 남겨야 하는 것."""

    asked: Any
    says: str
    expects: Mapping[str, Any]


@dataclass(frozen=True)
class Edit:
    """고치기 요청 하나와, 그 요청이 바꿔야 하는 자리."""

    asked: Any
    says: str
    changed: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LaidHolder:
    """정책에 매인 사용자 한 명과 그 정책들의 손잡이."""

    domain: Laid[DomainData]
    user: Laid[UserData]
    user_policy: Laid[UserResourcePolicyData]
    keypair_policy: Laid[KeyPairResourcePolicyData]
    project_policy: Laid[ProjectResourcePolicyData]


class Family[PolicyData, PolicyNode](ABC):
    """정책 한 종류. 어떻게 심고, 어댑터의 어느 호출로 읽고 쓰고, 답의 어느 자리를 보는지."""

    @property
    @abstractmethod
    def label(self) -> str:
        """kebab 영문. 시나리오 요약에 붙는다."""
        raise NotImplementedError

    @property
    @abstractmethod
    def kind(self) -> str:
        """레포트가 이 정책을 부르는 이름."""
        raise NotImplementedError

    @property
    @abstractmethod
    def entity_type(self) -> EntityType:
        raise NotImplementedError

    @property
    @abstractmethod
    def calls(self) -> Calls:
        raise NotImplementedError

    @property
    @abstractmethod
    def fields(self) -> tuple[str, ...]:
        """이름과 시각 말고 답이 싣는 자리."""
        raise NotImplementedError

    @abstractmethod
    def seed(self, name_hint: str = "policy") -> SeedRow[PolicyData]:
        raise NotImplementedError

    @abstractmethod
    def own_of(self, holder: LaidHolder) -> Laid[PolicyData]:
        """그 사용자가 매인 이 종류의 정책."""
        raise NotImplementedError

    @abstractmethod
    def view(self, node: PolicyNode) -> dict[str, Any]:
        """답의 자리들을 견줄 수 있는 값으로."""
        raise NotImplementedError

    @abstractmethod
    def seeded_view(self, seeded: PolicyData) -> dict[str, Any]:
        """심은 것을 답과 같은 자리로."""
        raise NotImplementedError

    @abstractmethod
    def everything(self, name: str) -> Ask:
        raise NotImplementedError

    @abstractmethod
    def one_limit(self) -> Edit:
        raise NotImplementedError

    @abstractmethod
    def nothing(self) -> Edit:
        raise NotImplementedError

    @abstractmethod
    def clearing_a_non_nullable(self) -> Edit:
        raise NotImplementedError

    @abstractmethod
    async def create(self, adapter: ResourcePolicyAdapter, asked: Any) -> PolicyNode:
        raise NotImplementedError

    @abstractmethod
    async def read(self, adapter: ResourcePolicyAdapter, name: str) -> PolicyNode:
        raise NotImplementedError

    @abstractmethod
    async def search(self, adapter: ResourcePolicyAdapter, named: str | None = None) -> Searched:
        raise NotImplementedError

    @abstractmethod
    async def update(self, adapter: ResourcePolicyAdapter, name: str, asked: Any) -> PolicyNode:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, adapter: ResourcePolicyAdapter, name: str) -> str:
        raise NotImplementedError

    def verdicts(self, node: Any, wanted: Mapping[str, Any], started: datetime) -> list[Verdict]:
        """답의 모든 자리를 본다. 이름은 id 자리에도 실린다."""
        got = self.view(node)
        out: list[Verdict] = [
            Same("id", node.id, wanted["name"]),
            Same("name", node.name, wanted["name"]),
            Held("created_at", node.created_at, WrittenByThisRun(started)),
        ]
        out.extend(Same(one, got[one], wanted[one]) for one in self.fields)
        return out


class ProjectPolicies(Family[ProjectResourcePolicyData, ProjectResourcePolicyNode]):
    @property
    @override
    def label(self) -> str:
        return "project-policy"

    @property
    @override
    def kind(self) -> str:
        return "프로젝트 정책"

    @property
    @override
    def entity_type(self) -> EntityType:
        return ProjectResourcePolicyEntityType()

    @property
    @override
    def calls(self) -> Calls:
        return Calls(
            create="admin_create_project_resource_policy",
            read="admin_get_project_resource_policy",
            search="admin_search_project_resource_policies",
            update="admin_update_project_resource_policy",
            delete="admin_delete_project_resource_policy",
        )

    @property
    @override
    def fields(self) -> tuple[str, ...]:
        return ("max_vfolder_count", "max_quota_scope_size", "max_network_count")

    @override
    def seed(self, name_hint: str = "project-policy") -> SeedRow[ProjectResourcePolicyData]:
        return SeedNamedProjectPolicy(name_hint=name_hint)

    @override
    def own_of(self, holder: LaidHolder) -> Laid[ProjectResourcePolicyData]:
        return holder.project_policy

    @override
    def view(self, node: ProjectResourcePolicyNode) -> dict[str, Any]:
        return {
            "name": node.name,
            "max_vfolder_count": node.max_vfolder_count,
            "max_quota_scope_size": (
                node.max_quota_scope_size.expr,
                node.max_quota_scope_size.display,
            ),
            "max_network_count": node.max_network_count,
        }

    @override
    def seeded_view(self, seeded: ProjectResourcePolicyData) -> dict[str, Any]:
        return {
            "name": seeded.name,
            "max_vfolder_count": seeded.max_vfolder_count,
            "max_quota_scope_size": (
                str(seeded.max_quota_scope_size),
                f"{BinarySize(seeded.max_quota_scope_size):s}",
            ),
            "max_network_count": seeded.max_network_count,
        }

    @override
    def everything(self, name: str) -> Ask:
        return Ask(
            CreateProjectResourcePolicyInput(
                name=name,
                max_vfolder_count=20,
                max_quota_scope_size=BinarySizeInput(expr="1g"),
                max_network_count=5,
            ),
            "모든 값을 주고",
            {
                "name": name,
                "max_vfolder_count": 20,
                "max_quota_scope_size": ("1073741824", "1g"),
                "max_network_count": 5,
            },
        )

    @override
    def one_limit(self) -> Edit:
        return Edit(
            UpdateProjectResourcePolicyInput(max_vfolder_count=20),
            "폴더 수를 20으로",
            {"max_vfolder_count": 20},
        )

    @override
    def nothing(self) -> Edit:
        return Edit(UpdateProjectResourcePolicyInput(), "아무것도 대지 않고")

    @override
    def clearing_a_non_nullable(self) -> Edit:
        return Edit(UpdateProjectResourcePolicyInput(max_vfolder_count=None), "폴더 수를 비우도록")

    @override
    async def create(self, adapter: ResourcePolicyAdapter, asked: Any) -> ProjectResourcePolicyNode:
        payload = await adapter.admin_create_project_resource_policy(asked)
        return payload.project_resource_policy

    @override
    async def read(self, adapter: ResourcePolicyAdapter, name: str) -> ProjectResourcePolicyNode:
        return await adapter.admin_get_project_resource_policy(name)

    @override
    async def search(
        self, adapter: ResourcePolicyAdapter, named: str | None = None
    ) -> SearchProjectResourcePoliciesPayload:
        chosen = (
            ProjectResourcePolicyFilter(name=StringFilter(equals=named))
            if named is not None
            else None
        )
        return await adapter.admin_search_project_resource_policies(
            AdminSearchProjectResourcePoliciesInput(filter=chosen)
        )

    @override
    async def update(
        self, adapter: ResourcePolicyAdapter, name: str, asked: Any
    ) -> ProjectResourcePolicyNode:
        payload = await adapter.admin_update_project_resource_policy(name, asked)
        return payload.project_resource_policy

    @override
    async def delete(self, adapter: ResourcePolicyAdapter, name: str) -> str:
        payload = await adapter.admin_delete_project_resource_policy(
            DeleteProjectResourcePolicyInput(name=name)
        )
        return payload.name


PROJECT = ProjectPolicies()

FAMILIES: tuple[Family[Any, Any], ...] = (PROJECT,)


@dataclass(frozen=True)
class APolicyAndACaller[PolicyData]:
    """정책 하나와, 그것을 부를 사람."""

    policy: PolicyData
    caller: UserData


@dataclass(frozen=True)
class ManyPoliciesAndACaller[PolicyData]:
    """검색할 정책 여럿과, 검색할 사람. ``named``는 그중 골라낼 하나다."""

    laid: tuple[PolicyData, ...]
    named: PolicyData
    caller: UserData


@dataclass(frozen=True)
class SomeoneHeldToPolicies(SeedNest[LaidHolder]):
    """정책들에 매인 사용자 한 명. 매니저가 사용자를 만드는 경로를 그대로 탄다.

    그 경로가 사용자 정책과 키페어 정책의 이름을 행에 적고, 딸려 생기는 개인 프로젝트가
    매니저가 못박은 이름의 프로젝트 정책을 찾는다. 이 표가 그 정책들을 읽고 지우므로
    손잡이를 함께 답한다.
    """

    domain: Laid[DomainData]
    role: UserRole = UserRole.USER

    @override
    def kind(self) -> str:
        return "정책에 매인 사용자 한 명 준비"

    @override
    def lay(self, seed: Seeder) -> LaidHolder:
        project_policy = seed.once(SeedProjectPolicy())
        user_policy = seed.creating(SeedUserPolicy())
        keypair_policy = seed.creating(SeedKeypairPolicy())
        user = seed.provisioning(
            SeedUserOf(role=self.role),
            self.domain,
            user_policy,
            keypair_policy,
        )
        return LaidHolder(
            domain=self.domain,
            user=user,
            user_policy=user_policy,
            keypair_policy=keypair_policy,
            project_policy=project_policy,
        )


async def lay_a_holder(seeding: Any, *, role: UserRole) -> LaidHolder:
    """도메인 하나와, 그 안에 정책에 매인 사용자 한 명."""
    domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
    holder: LaidHolder = await seeding.within(SomeoneHeldToPolicies(domain, role=role))
    return holder


@dataclass(frozen=True)
class APolicyAndSomeone(Given[Any, APolicyAndACaller[Any]]):
    """정책 하나와, 다른 정책에 매인 사용자 한 명. 지목하는 정책을 아무도 쓰지 않는다."""

    family: Family[Any, Any]
    role: UserRole = UserRole.USER

    @override
    def describe(self) -> str:
        return f"아무도 쓰지 않는 {self.family.kind} 하나와, {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> APolicyAndACaller[Any]:
        holder = await lay_a_holder(seeding, role=self.role)
        target = await seeding.creating(self.family.seed())
        return APolicyAndACaller(seeding.made(target), seeding.made(holder.user))


@dataclass(frozen=True)
class AHeldPolicyAndSomeone(Given[Any, APolicyAndACaller[Any]]):
    """부르는 사람 자신이 매인 정책. 그 사람의 키페어·행·개인 프로젝트가 아직 이 이름을 가리킨다."""

    family: Family[Any, Any]
    role: UserRole = UserRole.SUPERADMIN

    @override
    def describe(self) -> str:
        return f"{self.role.value} 한 명과, 그 사람이 아직 매여 있는 {self.family.kind}"

    @override
    async def lay(self, seeding: Any) -> APolicyAndACaller[Any]:
        holder = await lay_a_holder(seeding, role=self.role)
        return APolicyAndACaller(
            seeding.made(self.family.own_of(holder)), seeding.made(holder.user)
        )


@dataclass(frozen=True)
class ManyPoliciesAndSomeone(Given[Any, ManyPoliciesAndACaller[Any]]):
    """정책 여럿과, 그중 하나에 매인 사용자 한 명."""

    family: Family[Any, Any]
    role: UserRole = UserRole.USER
    besides: int = 1

    @override
    def describe(self) -> str:
        return (
            f"{self.family.kind} {self.besides + 2}개와, 그중 하나에 매인 {self.role.value} 한 명"
        )

    @override
    async def lay(self, seeding: Any) -> ManyPoliciesAndACaller[Any]:
        holder = await lay_a_holder(seeding, role=self.role)
        wanted = await seeding.creating(self.family.seed("wanted"))
        others = [await seeding.creating(self.family.seed("other")) for _ in range(self.besides)]
        return ManyPoliciesAndACaller(
            laid=tuple(seeding.made(one) for one in [self.family.own_of(holder), wanted, *others]),
            named=seeding.made(wanted),
            caller=seeding.made(holder.user),
        )


@dataclass(frozen=True)
class ThePolicyNode(Then[APolicyAndACaller[Any], Any]):
    """심은 정책이 통째로 온다. 값은 심은 것에서 읽는다.

    바꾸는 요청이 이것을 쓸 때는 바뀌어야 하는 자리만 ``changed``로 받는다. 나머지가
    조용히 함께 움직이면 그 자리에서 어긋난다.
    """

    family: Family[Any, Any]
    started: datetime
    changed: Mapping[str, Any] = field(default_factory=dict)

    @override
    def says(self) -> str:
        return f"심은 {self.family.kind} 전체가 온다"

    @override
    def look(self, laid: APolicyAndACaller[Any], answered: Answered[Any]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        wanted = {**self.family.seeded_view(laid.policy), **self.changed}
        return self.family.verdicts(node, wanted, self.started)


@dataclass(frozen=True)
class TheNewPolicyNode(Then[Any, Any]):
    """방금 만든 정책이 통째로 온다. 요청이 정한 것만 여기로 받는다."""

    family: Family[Any, Any]
    started: datetime
    ask: Ask

    @override
    def says(self) -> str:
        return f"만든 {self.family.kind} 전체가 온다"

    @override
    def look(self, laid: Any, answered: Answered[Any]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return self.family.verdicts(node, self.ask.expects, self.started)


@dataclass(frozen=True)
class EveryLaidPolicyIsFound(Then[ManyPoliciesAndACaller[Any], Searched]):
    """심은 것이 모두, 그리고 그것만 온다."""

    family: Family[Any, Any]

    @override
    def says(self) -> str:
        return f"심은 {self.family.kind}이 모두, 그리고 그것만 온다"

    @override
    def look(
        self, laid: ManyPoliciesAndACaller[Any], answered: Answered[Searched]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(InsufficientPrivilege, answered.raised)]
        return [
            Same(
                "items",
                sorted(one.name for one in payload.items),
                sorted(one.name for one in laid.laid),
            ),
            Same("total_count", payload.total_count, len(laid.laid)),
        ]


@dataclass(frozen=True)
class OnlyTheNamedOneIsFound(Then[ManyPoliciesAndACaller[Any], Searched]):
    """걸러낸 그 하나만 온다."""

    family: Family[Any, Any]

    @override
    def says(self) -> str:
        return f"걸러낸 {self.family.kind} 하나만 온다"

    @override
    def look(
        self, laid: ManyPoliciesAndACaller[Any], answered: Answered[Searched]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(InsufficientPrivilege, answered.raised)]
        return [
            Same("items", [one.name for one in payload.items], [laid.named.name]),
            Same("total_count", payload.total_count, 1),
        ]
