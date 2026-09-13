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
from decimal import Decimal
from typing import Any, override
from uuid import UUID

from bai_scenario.components.domain import WAS_HERE, WrittenByThisRun
from bai_scenario.seeds.domain.domain import SeedDomain
from bai_scenario.seeds.keypair.keypair import SeedKeypair
from bai_scenario.seeds.rbac.role import SeedPermission, SeedRole
from bai_scenario.seeds.resource_policy.keypair import SeedKeypairPolicy
from bai_scenario.seeds.resource_policy.project import SeedProjectPolicy
from bai_scenario.seeds.resource_policy.user import SeedUserPolicy
from bai_scenario.seeds.seeder import Laid, Seeder, SeedNest, SeedRow
from bai_scenario.seeds.user.user import SeedUserOf

from ai.backend.common.data.entity.resource_policy import (
    KeyPairResourcePolicyEntityType,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.defs.session import SESSION_PRIORITY_MAX
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.common import (
    ResourceSlotEntryInput,
    VFolderHostPermissionEntryInput,
)
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    AdminSearchKeypairResourcePoliciesInput,
    CreateKeypairResourcePolicyInput,
    DeleteKeypairResourcePolicyInput,
    KeypairResourcePolicyFilter,
    KeypairResourcePolicyKeypairNestedFilter,
    UpdateKeypairResourcePolicyInput,
)
from ai.backend.common.dto.manager.v2.resource_policy.response import (
    KeypairResourcePolicyNode,
    SearchKeypairResourcePoliciesPayload,
)
from ai.backend.common.types import (
    DefaultForUnspecified,
    VFolderHostPermission,
)
from ai.backend.manager.api.adapters.resource_policy.adapter import ResourcePolicyAdapter
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.types import Permission
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

type Searched = SearchKeypairResourcePoliciesPayload

VFOLDER_HOST = "local:volume1"


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
    """생성 요청 하나와, 그 요청이 응답에 남겨야 하는 값."""

    asked: Any
    says: str
    expects: Mapping[str, Any]


@dataclass(frozen=True)
class Edit:
    """수정 요청 하나와, 그 요청이 바꿔야 하는 필드."""

    asked: Any
    says: str
    changed: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LaidHolder:
    """정책이 할당된 사용자 한 명과, 그 사용자에게 할당된 정책들의 참조."""

    domain: Laid[DomainData]
    user: Laid[UserData]
    user_policy: Laid[UserResourcePolicyData]
    keypair_policy: Laid[KeyPairResourcePolicyData]
    project_policy: Laid[ProjectResourcePolicyData]


class Family[PolicyData, PolicyNode](ABC):
    """정책 한 종류. 어떻게 미리 만들어 두고, 어댑터의 어느 호출로 읽고 쓰며, 응답의 어느 필드를 검사하는지."""

    @property
    @abstractmethod
    def label(self) -> str:
        """kebab-case 영문. 시나리오 요약에 붙는다."""
        raise NotImplementedError

    @property
    @abstractmethod
    def kind(self) -> str:
        """레포트에서 이 정책 종류를 가리키는 이름."""
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
        """이름과 시각을 제외하고 응답에 담기는 필드."""
        raise NotImplementedError

    @abstractmethod
    def seed(
        self, name_hint: str = "policy", *, holding_optional: bool = False
    ) -> SeedRow[PolicyData]:
        """정책 하나. ``holding_optional``이면 비울 수 있는 항목에도 값을 넣는다."""
        raise NotImplementedError

    @abstractmethod
    def own_of(self, holder: LaidHolder) -> Laid[PolicyData]:
        """그 사용자에게 할당된, 이 종류의 정책."""
        raise NotImplementedError

    @abstractmethod
    def view(self, node: PolicyNode) -> dict[str, Any]:
        """응답의 필드들을 비교 가능한 값으로 바꾼다."""
        raise NotImplementedError

    @abstractmethod
    def seeded_view(self, seeded: PolicyData) -> dict[str, Any]:
        """미리 만들어 둔 데이터를 응답과 같은 필드 구성으로 바꾼다."""
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
        """응답의 모든 필드를 검사한다. 이름은 id 필드에도 그대로 담긴다."""
        got = self.view(node)
        out: list[Verdict] = [
            Same("id", node.id, wanted["name"]),
            Same("name", node.name, wanted["name"]),
            Held("created_at", node.created_at, WrittenByThisRun(started)),
        ]
        out.extend(Same(one, got[one], wanted[one]) for one in self.fields)
        return out


class OwnFamily[PolicyData, PolicyNode](Family[PolicyData, PolicyNode]):
    """호출자 자신의 정책을 읽는 호출이 있고, 생략하거나 비울 수 있는 항목이 있는 정책."""

    @property
    @abstractmethod
    def mine(self) -> str:
        """호출자 자신의 정책을 읽는 호출의 이름."""
        raise NotImplementedError

    @abstractmethod
    def only_required(self, name: str) -> Ask:
        raise NotImplementedError

    @abstractmethod
    def clearing_a_nullable(self) -> Edit:
        raise NotImplementedError

    @abstractmethod
    async def read_mine(self, adapter: ResourcePolicyAdapter) -> PolicyNode:
        raise NotImplementedError


class KeypairPolicies(OwnFamily[KeyPairResourcePolicyData, KeypairResourcePolicyNode]):
    @property
    @override
    def label(self) -> str:
        return "keypair-policy"

    @property
    @override
    def kind(self) -> str:
        return "키페어 정책"

    @property
    @override
    def entity_type(self) -> EntityType:
        return KeyPairResourcePolicyEntityType()

    @property
    @override
    def calls(self) -> Calls:
        return Calls(
            create="admin_create_keypair_resource_policy",
            read="admin_get_keypair_resource_policy",
            search="admin_search_keypair_resource_policies",
            update="admin_update_keypair_resource_policy",
            delete="admin_delete_keypair_resource_policy",
        )

    @property
    @override
    def mine(self) -> str:
        return "get_my_keypair_resource_policy"

    @property
    @override
    def fields(self) -> tuple[str, ...]:
        return (
            "default_for_unspecified",
            "total_resource_slots",
            "max_session_lifetime",
            "max_concurrent_sessions",
            "max_pending_session_count",
            "max_priority",
            "max_pending_session_resource_slots",
            "max_concurrent_sftp_sessions",
            "max_containers_per_session",
            "idle_timeout",
            "allowed_vfolder_hosts",
        )

    @override
    def seed(
        self, name_hint: str = "keypair-policy", *, holding_optional: bool = False
    ) -> SeedRow[KeyPairResourcePolicyData]:
        return SeedKeypairPolicy(
            name_hint=name_hint, max_pending_session_count=2 if holding_optional else None
        )

    @override
    def own_of(self, holder: LaidHolder) -> Laid[KeyPairResourcePolicyData]:
        return holder.keypair_policy

    @override
    def view(self, node: KeypairResourcePolicyNode) -> dict[str, Any]:
        return {
            "name": node.name,
            "default_for_unspecified": node.default_for_unspecified,
            "total_resource_slots": [
                (one.resource_type, one.quantity, one.unlimited)
                for one in node.total_resource_slots
            ],
            "max_session_lifetime": node.max_session_lifetime,
            "max_concurrent_sessions": node.max_concurrent_sessions,
            "max_pending_session_count": node.max_pending_session_count,
            "max_priority": node.max_priority,
            "max_pending_session_resource_slots": (
                [
                    (one.resource_type, one.quantity, one.unlimited)
                    for one in node.max_pending_session_resource_slots
                ]
                if node.max_pending_session_resource_slots is not None
                else None
            ),
            "max_concurrent_sftp_sessions": node.max_concurrent_sftp_sessions,
            "max_containers_per_session": node.max_containers_per_session,
            "idle_timeout": node.idle_timeout,
            "allowed_vfolder_hosts": sorted(
                (one.host, sorted(one.permissions)) for one in node.allowed_vfolder_hosts
            ),
        }

    @override
    def seeded_view(self, seeded: KeyPairResourcePolicyData) -> dict[str, Any]:
        return {
            "name": seeded.name,
            "default_for_unspecified": seeded.default_for_unspecified,
            "total_resource_slots": [
                (key, value if value.is_finite() else None, not value.is_finite())
                for key, value in seeded.total_resource_slots.items()
            ],
            "max_session_lifetime": seeded.max_session_lifetime,
            "max_concurrent_sessions": seeded.max_concurrent_sessions,
            "max_pending_session_count": seeded.max_pending_session_count,
            "max_priority": seeded.max_priority,
            "max_pending_session_resource_slots": (
                [
                    (key, value if value.is_finite() else None, not value.is_finite())
                    for key, value in seeded.max_pending_session_resource_slots.items()
                ]
                if seeded.max_pending_session_resource_slots is not None
                else None
            ),
            "max_concurrent_sftp_sessions": seeded.max_concurrent_sftp_sessions,
            "max_containers_per_session": seeded.max_containers_per_session,
            "idle_timeout": seeded.idle_timeout,
            "allowed_vfolder_hosts": sorted(
                (host, sorted(one.value for one in perms))
                for host, perms in seeded.allowed_vfolder_hosts.items()
            ),
        }

    def _ask(
        self,
        name: str,
        says: str,
        *,
        cpu: str = "4",
        pending_count: int | None = 2,
        priority: int | None = 10,
        pending_cpu: str | None = "2",
    ) -> Ask:
        """요청과, 그 요청이 응답에 남겨야 하는 값을 같은 값에서 만든다."""
        asked = CreateKeypairResourcePolicyInput(
            name=name,
            default_for_unspecified=DefaultForUnspecified.LIMITED,
            total_resource_slots=[ResourceSlotEntryInput(resource_type="cpu", quantity=cpu)],
            max_session_lifetime=3600,
            max_concurrent_sessions=5,
            max_pending_session_count=pending_count,
            max_priority=priority,
            max_pending_session_resource_slots=(
                [ResourceSlotEntryInput(resource_type="cpu", quantity=pending_cpu)]
                if pending_cpu is not None
                else None
            ),
            max_concurrent_sftp_sessions=1,
            max_containers_per_session=1,
            idle_timeout=600,
            allowed_vfolder_hosts=[
                VFolderHostPermissionEntryInput(
                    host=VFOLDER_HOST, permissions=[VFolderHostPermission.MOUNT_IN_SESSION.value]
                )
            ],
        )
        unlimited = cpu == "Infinity"
        expects = {
            "name": name,
            "default_for_unspecified": DefaultForUnspecified.LIMITED,
            "total_resource_slots": [("cpu", None if unlimited else Decimal(cpu), unlimited)],
            "max_session_lifetime": 3600,
            "max_concurrent_sessions": 5,
            "max_pending_session_count": pending_count,
            "max_priority": priority,
            "max_pending_session_resource_slots": (
                [("cpu", Decimal(pending_cpu), False)] if pending_cpu is not None else None
            ),
            "max_concurrent_sftp_sessions": 1,
            "max_containers_per_session": 1,
            "idle_timeout": 600,
            "allowed_vfolder_hosts": [
                (VFOLDER_HOST, [VFolderHostPermission.MOUNT_IN_SESSION.value])
            ],
        }
        return Ask(asked, says, expects)

    @override
    def everything(self, name: str) -> Ask:
        return self._ask(name, "모든 값을 지정해")

    @override
    def only_required(self, name: str) -> Ask:
        return self._ask(
            name,
            "대기 세션 수·우선순위 상한·대기 자원 슬롯을 생략하고",
            pending_count=None,
            priority=None,
            pending_cpu=None,
        )

    def unlimited_slot(self, name: str) -> Ask:
        return self._ask(name, "cpu 슬롯을 무제한으로 지정해", cpu="Infinity")

    def priority_out_of_range(self, name: str) -> Ask:
        return self._ask(
            name,
            "우선순위 상한을 세션 우선순위 범위 밖 값으로 지정해",
            priority=SESSION_PRIORITY_MAX + 1,
        )

    @override
    def one_limit(self) -> Edit:
        return Edit(
            UpdateKeypairResourcePolicyInput(max_concurrent_sessions=7),
            "동시 세션 수 7로 변경",
            {"max_concurrent_sessions": 7},
        )

    @override
    def nothing(self) -> Edit:
        return Edit(UpdateKeypairResourcePolicyInput(), "빈 요청")

    @override
    def clearing_a_nullable(self) -> Edit:
        return Edit(
            UpdateKeypairResourcePolicyInput(max_pending_session_count=None),
            "대기 세션 수 비우기",
            {"max_pending_session_count": None},
        )

    @override
    def clearing_a_non_nullable(self) -> Edit:
        return Edit(
            UpdateKeypairResourcePolicyInput(max_concurrent_sessions=None),
            "동시 세션 수 비우기",
        )

    def priority_moved_out_of_range(self) -> Edit:
        return Edit(
            UpdateKeypairResourcePolicyInput(max_priority=SESSION_PRIORITY_MAX + 1),
            "우선순위 상한을 세션 우선순위 범위 밖으로 변경",
        )

    @override
    async def create(self, adapter: ResourcePolicyAdapter, asked: Any) -> KeypairResourcePolicyNode:
        payload = await adapter.admin_create_keypair_resource_policy(asked)
        return payload.keypair_resource_policy

    @override
    async def read(self, adapter: ResourcePolicyAdapter, name: str) -> KeypairResourcePolicyNode:
        return await adapter.admin_get_keypair_resource_policy(name)

    @override
    async def search(
        self, adapter: ResourcePolicyAdapter, named: str | None = None
    ) -> SearchKeypairResourcePoliciesPayload:
        chosen = (
            KeypairResourcePolicyFilter(name=StringFilter(equals=named))
            if named is not None
            else None
        )
        return await adapter.admin_search_keypair_resource_policies(
            AdminSearchKeypairResourcePoliciesInput(filter=chosen)
        )

    async def search_held_by(
        self, adapter: ResourcePolicyAdapter, user_id: UUID
    ) -> SearchKeypairResourcePoliciesPayload:
        """그 사용자의 키페어에 할당된 정책만 검색한다."""
        return await adapter.admin_search_keypair_resource_policies(
            AdminSearchKeypairResourcePoliciesInput(
                filter=KeypairResourcePolicyFilter(
                    keypair=KeypairResourcePolicyKeypairNestedFilter(
                        user_id=UUIDFilter(equals=user_id)
                    )
                )
            )
        )

    @override
    async def update(
        self, adapter: ResourcePolicyAdapter, name: str, asked: Any
    ) -> KeypairResourcePolicyNode:
        payload = await adapter.admin_update_keypair_resource_policy(name, asked)
        return payload.keypair_resource_policy

    @override
    async def delete(self, adapter: ResourcePolicyAdapter, name: str) -> str:
        payload = await adapter.admin_delete_keypair_resource_policy(
            DeleteKeypairResourcePolicyInput(name=name)
        )
        return payload.name

    @override
    async def read_mine(self, adapter: ResourcePolicyAdapter) -> KeypairResourcePolicyNode:
        return await adapter.get_my_keypair_resource_policy()


KEYPAIR = KeypairPolicies()

FAMILIES: tuple[Family[Any, Any], ...] = (KEYPAIR,)
OWN_FAMILIES: tuple[OwnFamily[Any, Any], ...] = (KEYPAIR,)


@dataclass(frozen=True)
class APolicyAndACaller[PolicyData]:
    """정책 하나와, 그것을 호출할 사용자."""

    policy: PolicyData
    caller: UserData


@dataclass(frozen=True)
class ManyPoliciesAndACaller[PolicyData]:
    """검색 대상 정책 여럿과, 검색을 호출할 사용자.

    ``named``는 그중 이름 필터로 골라낼 하나, ``held``는 호출자 자신에게 할당된 하나다.
    """

    laid: tuple[PolicyData, ...]
    named: PolicyData
    held: PolicyData
    caller: UserData


@dataclass(frozen=True)
class SomeoneHeldToPolicies(SeedNest[LaidHolder]):
    """정책들이 할당된 사용자 한 명. 매니저가 사용자를 만드는 경로를 그대로 사용한다.

    그 경로는 사용자 정책과 키페어 정책의 이름을 사용자 행에 기록하고, 함께 생성되는 개인
    프로젝트는 매니저가 정해 둔 이름의 프로젝트 정책을 찾는다. 시나리오가 그 정책들을 읽고
    삭제하므로 참조를 함께 반환한다.
    """

    domain: Laid[DomainData]
    role: UserRole = UserRole.USER
    active: bool = True

    @override
    def kind(self) -> str:
        return "정책이 할당된 사용자 한 명 준비"

    @override
    def lay(self, seed: Seeder) -> LaidHolder:
        project_policy = seed.once(SeedProjectPolicy())
        user_policy = seed.creating(SeedUserPolicy())
        keypair_policy = seed.creating(SeedKeypairPolicy())
        user = seed.provisioning(
            SeedUserOf(role=self.role, is_active=self.active),
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


@dataclass(frozen=True)
class ReadingOwnPolicies(SeedNest[Laid[None]]):
    """자기 스코프에서 그 정책을 읽을 수 있게 하는 역할과, 그 역할의 부여."""

    user: Laid[UserData]
    entity_type: EntityType

    @override
    def kind(self) -> str:
        return f"자기 스코프에서 {self.entity_type} 읽기 권한을 주는 역할 부여"

    @override
    def lay(self, seed: Seeder) -> Laid[None]:
        role = seed.creating_from(
            SeedRole(lambda u: UserID(u.id), name_hint="policy-reader"), self.user
        )
        seed.adding(SeedPermission(entity_type=self.entity_type, permission=Permission.READ), role)
        return seed.granting(
            role, self.user, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id)
        )


async def lay_a_holder(seeding: Any, *, role: UserRole, active: bool = True) -> LaidHolder:
    """도메인 하나와, 그 도메인에 속하며 정책이 할당된 사용자 한 명."""
    domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
    holder: LaidHolder = await seeding.within(
        SomeoneHeldToPolicies(domain, role=role, active=active)
    )
    return holder


@dataclass(frozen=True)
class APolicyAndSomeone(Given[Any, APolicyAndACaller[Any]]):
    """정책 하나와, 다른 정책이 할당된 사용자 한 명. 대상 정책은 아무도 사용하지 않는다."""

    family: Family[Any, Any]
    role: UserRole = UserRole.USER
    holding_optional: bool = False

    @override
    def describe(self) -> str:
        return f"아무도 사용하지 않는 {self.family.kind} 하나와, {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> APolicyAndACaller[Any]:
        holder = await lay_a_holder(seeding, role=self.role)
        target = await seeding.creating(self.family.seed(holding_optional=self.holding_optional))
        return APolicyAndACaller(seeding.made(target), seeding.made(holder.user))


@dataclass(frozen=True)
class AHeldPolicyAndSomeone(Given[Any, APolicyAndACaller[Any]]):
    """호출자 자신에게 할당된 정책. 그 사용자의 키페어·사용자 행·개인 프로젝트가 아직 이 이름을 참조한다."""

    family: Family[Any, Any]
    role: UserRole = UserRole.SUPERADMIN

    @override
    def describe(self) -> str:
        return f"{self.role.value} 한 명과, 그 사용자에게 아직 할당된 {self.family.kind}"

    @override
    async def lay(self, seeding: Any) -> APolicyAndACaller[Any]:
        holder = await lay_a_holder(seeding, role=self.role)
        return APolicyAndACaller(
            seeding.made(self.family.own_of(holder)), seeding.made(holder.user)
        )


@dataclass(frozen=True)
class ManyPoliciesAndSomeone(Given[Any, ManyPoliciesAndACaller[Any]]):
    """정책 여럿과, 그중 하나가 할당된 사용자 한 명."""

    family: Family[Any, Any]
    role: UserRole = UserRole.USER
    besides: int = 1

    @override
    def describe(self) -> str:
        return (
            f"{self.family.kind} {self.besides + 2}개와, 그중 하나가 할당된 {self.role.value} 한 명"
        )

    @override
    async def lay(self, seeding: Any) -> ManyPoliciesAndACaller[Any]:
        holder = await lay_a_holder(seeding, role=self.role)
        wanted = await seeding.creating(self.family.seed("wanted"))
        others = [await seeding.creating(self.family.seed("other")) for _ in range(self.besides)]
        held = self.family.own_of(holder)
        return ManyPoliciesAndACaller(
            laid=tuple(seeding.made(one) for one in [held, wanted, *others]),
            named=seeding.made(wanted),
            held=seeding.made(held),
            caller=seeding.made(holder.user),
        )


@dataclass(frozen=True)
class SomeoneHeldToTheirPolicy(Given[Any, APolicyAndACaller[Any]]):
    """자기 정책을 조회할 사용자. 반환되는 정책은 그 사용자에게 할당된 것이다."""

    family: OwnFamily[Any, Any]
    granted: bool = True

    @override
    def describe(self) -> str:
        if self.granted:
            return f"{self.family.kind}이 할당된 사용자 한 명, 자기 스코프에서 그 정책을 읽을 권한 있음"
        return f"{self.family.kind}이 할당된 사용자 한 명, 아무 권한도 없음"

    @override
    async def lay(self, seeding: Any) -> APolicyAndACaller[Any]:
        holder = await lay_a_holder(seeding, role=UserRole.USER)
        if self.granted:
            await seeding.within(ReadingOwnPolicies(holder.user, self.family.entity_type))
        return APolicyAndACaller(
            seeding.made(self.family.own_of(holder)), seeding.made(holder.user)
        )


@dataclass(frozen=True)
class SomeoneWithAnotherKey(Given[Any, APolicyAndACaller[Any]]):
    """키페어를 하나 더 가진 사용자. 두 키페어에는 서로 다른 키페어 정책이 할당돼 있다.

    사용자와 함께 만들어진 키페어가 기본 키페어다. 사용자가 활성이면 기본 키페어의 정책이
    반환되고, 비활성이면 기본 키페어도 비활성이므로 추가한 키페어의 정책이 반환된다.
    """

    active: bool = True

    @override
    def describe(self) -> str:
        if self.active:
            return "기본 키페어 외에 다른 키페어 정책이 할당된 활성 키페어를 하나 더 가진 사용자, 읽기 권한 있음"
        return "기본 키페어는 비활성이고 다른 키페어 정책이 할당된 활성 키페어를 하나 더 가진 사용자, 읽기 권한 있음"

    @override
    async def lay(self, seeding: Any) -> APolicyAndACaller[Any]:
        holder = await lay_a_holder(seeding, role=UserRole.USER, active=self.active)
        other = await seeding.creating(SeedKeypairPolicy(name_hint="other"))
        await seeding.adding(SeedKeypair(resource_policy=seeding.made(other).name), holder.user)
        await seeding.within(ReadingOwnPolicies(holder.user, KEYPAIR.entity_type))
        expected = holder.keypair_policy if self.active else other
        return APolicyAndACaller(seeding.made(expected), seeding.made(holder.user))


@dataclass(frozen=True)
class SomeoneWithNoActiveKey(Given[Any, APolicyAndACaller[Any]]):
    """비활성 사용자라 활성 키페어가 하나도 없는 사용자. 정책은 할당돼 있지만 키페어를 거쳐 도달할 수 없다."""

    @override
    def describe(self) -> str:
        return "활성 키페어가 없는 사용자, 자기 스코프에서 키페어 정책 읽기 권한 있음"

    @override
    async def lay(self, seeding: Any) -> APolicyAndACaller[Any]:
        holder = await lay_a_holder(seeding, role=UserRole.USER, active=False)
        await seeding.within(ReadingOwnPolicies(holder.user, KEYPAIR.entity_type))
        return APolicyAndACaller(seeding.made(holder.keypair_policy), seeding.made(holder.user))


@dataclass(frozen=True)
class ThePolicyNode(Then[APolicyAndACaller[Any], Any]):
    """미리 만들어 둔 정책이 통째로 반환된다. 기대값은 미리 만들어 둔 데이터에서 읽는다.

    수정 요청이 이 검사를 쓸 때는 바뀌어야 하는 필드만 ``changed``로 받는다. 나머지 필드가
    함께 바뀌면 그 필드에서 불일치가 드러난다.
    """

    family: Family[Any, Any]
    started: datetime
    changed: Mapping[str, Any] = field(default_factory=dict)

    @override
    def says(self) -> str:
        return f"미리 만들어 둔 {self.family.kind} 전체가 반환된다"

    @override
    def look(self, laid: APolicyAndACaller[Any], answered: Answered[Any]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        wanted = {**self.family.seeded_view(laid.policy), **self.changed}
        return self.family.verdicts(node, wanted, self.started)


@dataclass(frozen=True)
class TheNewPolicyNode(Then[Any, Any]):
    """방금 생성한 정책이 통째로 반환된다. 기대값은 요청이 지정한 값에서 읽는다."""

    family: Family[Any, Any]
    started: datetime
    ask: Ask

    @override
    def says(self) -> str:
        return f"생성한 {self.family.kind} 전체가 반환된다"

    @override
    def look(self, laid: Any, answered: Answered[Any]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return self.family.verdicts(node, self.ask.expects, self.started)


@dataclass(frozen=True)
class EveryLaidPolicyIsFound(Then[ManyPoliciesAndACaller[Any], Searched]):
    """미리 만들어 둔 정책이 모두, 그리고 그것만 반환된다."""

    family: Family[Any, Any]

    @override
    def says(self) -> str:
        return f"미리 만들어 둔 {self.family.kind}이 모두, 그리고 그것만 반환된다"

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
    """필터에 맞는 그 하나만 반환된다."""

    family: Family[Any, Any]

    @override
    def says(self) -> str:
        return f"필터에 맞는 {self.family.kind} 하나만 반환된다"

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
