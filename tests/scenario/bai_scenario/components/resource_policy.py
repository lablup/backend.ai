"""What a resource policy scenario table says besides the call.

One adapter answers for three policies of the same shape, so a table is written once
and run against each. What tells the three apart — the seed that lays one, the calls
that read and write one, the places a node has — is gathered here as one class per
policy, and a row names the one it runs against.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.global_entity import GlobalEntityName
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_policy import (
    KeyPairResourcePolicyEntityType,
    KeyPairResourcePolicyUUID,
    ProjectResourcePolicyEntityType,
    ProjectResourcePolicyUUID,
    UserResourcePolicyEntityType,
    UserResourcePolicyUUID,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.defs.session import SESSION_PRIORITY_MAX
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.common import (
    BinarySizeInput,
    PartialBulkPayload,
    ResourceSlotEntryInput,
    VFolderHostPermissionEntryInput,
)
from ai.backend.common.dto.manager.v2.resource_policy.request import (
    AdminSearchKeypairResourcePoliciesInput,
    AdminSearchProjectResourcePoliciesInput,
    AdminSearchUserResourcePoliciesInput,
    CreateKeypairResourcePolicyInput,
    CreateProjectResourcePolicyInput,
    CreateUserResourcePolicyInput,
    KeypairResourcePolicyFilter,
    KeypairResourcePolicyKeypairNestedFilter,
    PartialBulkPurgeKeypairResourcePoliciesInput,
    PartialBulkPurgeProjectResourcePoliciesInput,
    PartialBulkPurgeUserResourcePoliciesInput,
    PartialBulkUpdateKeypairResourcePoliciesInput,
    PartialBulkUpdateKeypairResourcePolicyItemInput,
    PartialBulkUpdateProjectResourcePoliciesInput,
    PartialBulkUpdateProjectResourcePolicyItemInput,
    PartialBulkUpdateUserResourcePoliciesInput,
    PartialBulkUpdateUserResourcePolicyItemInput,
    ProjectResourcePolicyFilter,
    UpdateKeypairResourcePolicyInput,
    UpdateProjectResourcePolicyInput,
    UpdateUserResourcePolicyInput,
    UserResourcePolicyFilter,
)
from ai.backend.common.dto.manager.v2.resource_policy.response import (
    KeypairResourcePolicyNode,
    ProjectResourcePolicyNode,
    SearchKeypairResourcePoliciesPayload,
    SearchProjectResourcePoliciesPayload,
    SearchUserResourcePoliciesPayload,
    UserResourcePolicyNode,
)
from ai.backend.common.types import (
    BinarySize,
    DefaultForUnspecified,
    VFolderHostPermission,
)
from ai.backend.manager.api.adapters.resource_policy.adapter import ResourcePolicyAdapter
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.global_entity import global_entity_id
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.resource.types import (
    KeyPairResourcePolicyData,
    ProjectResourcePolicyData,
    UserResourcePolicyData,
)
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Language,
    Refused,
    Same,
    SameAs,
    Says,
    Skipped,
    Then,
    Verdict,
    in_language,
)
from bai_scenario.components.answers import MissingResponse
from bai_scenario.components.domain import WAS_HERE, Mentions, SomeoneOf, WrittenByThisRun
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.keypair.keypair import TestSeedKeypair
from bai_scenario.seeds.project.project import TestSeedProject
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole
from bai_scenario.seeds.resource_policy.keypair import TestSeedKeypairPolicy
from bai_scenario.seeds.resource_policy.project import (
    TestSeedNamedProjectPolicy,
    TestSeedProjectPolicy,
)
from bai_scenario.seeds.resource_policy.user import TestSeedUserPolicy
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest, TestSeedRow
from bai_scenario.seeds.user.user import TestSeedUserOf

type Searched = (
    SearchProjectResourcePoliciesPayload
    | SearchKeypairResourcePoliciesPayload
    | SearchUserResourcePoliciesPayload
)

VFOLDER_HOST = "local:volume1"


@dataclass(frozen=True)
class Calls:
    """The adapter calls one policy answers to, by the names the report counts."""

    create: str
    read: str
    search: str
    update: str
    purge: str
    partial_bulk_update: str
    partial_bulk_purge: str
    lookup: str
    bulk_get: str
    bulk_lookup: str


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
    ) -> TestSeedRow[PolicyData]:
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
    async def lookup(self, adapter: ResourcePolicyAdapter, name: str) -> UUID:
        """이름으로 id 를 찾는다. 인증만 확인하고 권한은 그 id 를 받는 호출이 본다."""
        raise NotImplementedError

    @abstractmethod
    async def bulk_get(self, adapter: ResourcePolicyAdapter, ids: list[UUID]) -> list[Any]:
        """id 여럿을 한 번에 읽는다. 자리마다 노드나 거부가 온다."""
        raise NotImplementedError

    @abstractmethod
    async def bulk_lookup(
        self, adapter: ResourcePolicyAdapter, names: list[str]
    ) -> Sequence[UUID | None]:
        """이름 여럿을 id 로 한 번에 바꾼다. 없는 이름의 자리는 비어 있다."""
        raise NotImplementedError

    @abstractmethod
    async def update(self, adapter: ResourcePolicyAdapter, name: str, asked: Any) -> PolicyNode:
        """이름으로 id 를 찾고, 그 id 로 수정한다."""
        raise NotImplementedError

    @abstractmethod
    async def purge(self, adapter: ResourcePolicyAdapter, name: str) -> str:
        """이름으로 id 를 찾고, 그 id 로 삭제한다. 삭제한 이름을 답한다."""
        raise NotImplementedError

    @abstractmethod
    async def partial_bulk_update(
        self, adapter: ResourcePolicyAdapter, ids: list[UUID], asked: Any
    ) -> PartialBulkPayload[Any]:
        """같은 수정을 여러 정책에 한 번에 건다."""
        raise NotImplementedError

    @abstractmethod
    async def partial_bulk_purge(
        self, adapter: ResourcePolicyAdapter, ids: list[UUID]
    ) -> PartialBulkPayload[Any]:
        raise NotImplementedError

    def verdicts(
        self,
        node: Any,
        wanted: Mapping[str, Any],
        started: datetime,
        prefix: str = "",
        *,
        entity_id: UUID | None = None,
    ) -> list[Verdict]:
        """응답의 모든 필드를 검사한다. 이름은 id 필드에도 그대로 담긴다."""
        got = self.view(node)
        out: list[Verdict] = [
            Same(f"{prefix}id", node.id, wanted["name"]),
            (
                Held[UUID](
                    f"{prefix}entity_id",
                    node.entity_id,
                    SameAs(
                        entity_id,
                        Says(
                            "미리 저장한 정책의 id",
                            english="the id of the policy seeded in advance",
                        ),
                    ),
                )
                if entity_id is not None
                else Skipped(f"{prefix}entity_id", "the database generates it")
            ),
            Same(f"{prefix}name", node.name, wanted["name"]),
            Held(f"{prefix}created_at", node.created_at, WrittenByThisRun(started)),
        ]
        out.extend(Same(f"{prefix}{one}", got[one], wanted[one]) for one in self.fields)
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


class ProjectPolicies(Family[ProjectResourcePolicyData, ProjectResourcePolicyNode]):
    @property
    @override
    def label(self) -> str:
        return "project-policy"

    @property
    @override
    def kind(self) -> str:
        return Says("프로젝트 정책", english="project policy")

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
            update="update_project_resource_policy",
            purge="purge_project_resource_policy",
            partial_bulk_update="partial_bulk_update_project_resource_policies",
            partial_bulk_purge="partial_bulk_purge_project_resource_policies",
            lookup="lookup_project_resource_policy",
            bulk_get="bulk_get_project_resource_policy_ids",
            bulk_lookup="bulk_lookup_project_resource_policy_names",
        )

    @property
    @override
    def fields(self) -> tuple[str, ...]:
        return ("max_vfolder_count", "max_quota_scope_size", "max_network_count")

    @override
    def seed(
        self, name_hint: str = "project-policy", *, holding_optional: bool = False
    ) -> TestSeedRow[ProjectResourcePolicyData]:
        return TestSeedNamedProjectPolicy(name_hint=name_hint)

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
            Says("모든 값을 지정해", english="all values given"),
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
            Says("vfolder 수 20으로 변경", english="the vfolder count changed to 20"),
            {"max_vfolder_count": 20},
        )

    @override
    def nothing(self) -> Edit:
        return Edit(UpdateProjectResourcePolicyInput(), Says("빈 요청", english="an empty request"))

    @override
    def clearing_a_non_nullable(self) -> Edit:
        return Edit(
            UpdateProjectResourcePolicyInput(max_vfolder_count=None),
            Says("vfolder 수 비우기", english="the vfolder count cleared"),
        )

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
    async def lookup(self, adapter: ResourcePolicyAdapter, name: str) -> UUID:
        return await adapter.lookup_project_resource_policy(name)

    @override
    async def bulk_get(self, adapter: ResourcePolicyAdapter, ids: list[UUID]) -> list[Any]:
        return await adapter.bulk_get_project_resource_policy_ids([
            ProjectResourcePolicyUUID(one) for one in ids
        ])

    @override
    async def bulk_lookup(
        self, adapter: ResourcePolicyAdapter, names: list[str]
    ) -> Sequence[UUID | None]:
        return await adapter.bulk_lookup_project_resource_policy_names(names)

    @override
    async def update(
        self, adapter: ResourcePolicyAdapter, name: str, asked: Any
    ) -> ProjectResourcePolicyNode:
        policy_id = await adapter.lookup_project_resource_policy(name)
        payload = await adapter.update_project_resource_policy(policy_id, asked)
        return payload.project_resource_policy

    @override
    async def purge(self, adapter: ResourcePolicyAdapter, name: str) -> str:
        policy_id = await adapter.lookup_project_resource_policy(name)
        payload = await adapter.purge_project_resource_policy(policy_id)
        return payload.name

    @override
    async def partial_bulk_update(
        self, adapter: ResourcePolicyAdapter, ids: list[UUID], asked: Any
    ) -> PartialBulkPayload[ProjectResourcePolicyNode]:
        return await adapter.partial_bulk_update_project_resource_policies(
            PartialBulkUpdateProjectResourcePoliciesInput(
                items=[
                    PartialBulkUpdateProjectResourcePolicyItemInput(id=policy_id, input=asked)
                    for policy_id in ids
                ]
            )
        )

    @override
    async def partial_bulk_purge(
        self, adapter: ResourcePolicyAdapter, ids: list[UUID]
    ) -> PartialBulkPayload[ProjectResourcePolicyNode]:
        return await adapter.partial_bulk_purge_project_resource_policies(
            PartialBulkPurgeProjectResourcePoliciesInput(ids=ids)
        )


class KeypairPolicies(OwnFamily[KeyPairResourcePolicyData, KeypairResourcePolicyNode]):
    @property
    @override
    def label(self) -> str:
        return "keypair-policy"

    @property
    @override
    def kind(self) -> str:
        return Says("키페어 정책", english="keypair policy")

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
            update="update_keypair_resource_policy",
            purge="purge_keypair_resource_policy",
            partial_bulk_update="partial_bulk_update_keypair_resource_policies",
            partial_bulk_purge="partial_bulk_purge_keypair_resource_policies",
            lookup="lookup_keypair_resource_policy",
            bulk_get="bulk_get_keypair_resource_policy_ids",
            bulk_lookup="bulk_lookup_keypair_resource_policy_names",
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
    ) -> TestSeedRow[KeyPairResourcePolicyData]:
        return TestSeedKeypairPolicy(
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
        return self._ask(name, Says("모든 값을 지정해", english="all values given"))

    @override
    def only_required(self, name: str) -> Ask:
        return self._ask(
            name,
            Says(
                "대기 세션 수, 우선순위 상한, 대기 자원 슬롯을 생략하고",
                english=(
                    "the pending session count, the priority cap and the pending resource "
                    "slots left out"
                ),
            ),
            pending_count=None,
            priority=None,
            pending_cpu=None,
        )

    def unlimited_slot(self, name: str) -> Ask:
        return self._ask(
            name,
            Says("cpu 슬롯을 무제한으로 지정해", english="the cpu slot set to unlimited"),
            cpu="Infinity",
        )

    def priority_out_of_range(self, name: str) -> Ask:
        return self._ask(
            name,
            Says(
                "우선순위 상한을 세션 우선순위 범위 밖 값으로 지정해",
                english="the priority cap set to a value outside the session priority range",
            ),
            priority=SESSION_PRIORITY_MAX + 1,
        )

    @override
    def one_limit(self) -> Edit:
        return Edit(
            UpdateKeypairResourcePolicyInput(max_concurrent_sessions=7),
            Says("동시 세션 수 7 로 변경", english="the concurrent session count changed to 7"),
            {"max_concurrent_sessions": 7},
        )

    @override
    def nothing(self) -> Edit:
        return Edit(UpdateKeypairResourcePolicyInput(), Says("빈 요청", english="an empty request"))

    @override
    def clearing_a_nullable(self) -> Edit:
        return Edit(
            UpdateKeypairResourcePolicyInput(max_pending_session_count=None),
            Says("대기 세션 수 비우기", english="the pending session count cleared"),
            {"max_pending_session_count": None},
        )

    @override
    def clearing_a_non_nullable(self) -> Edit:
        return Edit(
            UpdateKeypairResourcePolicyInput(max_concurrent_sessions=None),
            Says("동시 세션 수 비우기", english="the concurrent session count cleared"),
        )

    def priority_moved_out_of_range(self) -> Edit:
        return Edit(
            UpdateKeypairResourcePolicyInput(max_priority=SESSION_PRIORITY_MAX + 1),
            Says(
                "우선순위 상한을 세션 우선순위 범위 밖으로 변경",
                english="the priority cap changed to a value outside the session priority range",
            ),
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

    @override
    async def lookup(self, adapter: ResourcePolicyAdapter, name: str) -> UUID:
        return await adapter.lookup_keypair_resource_policy(name)

    @override
    async def bulk_get(self, adapter: ResourcePolicyAdapter, ids: list[UUID]) -> list[Any]:
        return await adapter.bulk_get_keypair_resource_policy_ids([
            KeyPairResourcePolicyUUID(one) for one in ids
        ])

    @override
    async def bulk_lookup(
        self, adapter: ResourcePolicyAdapter, names: list[str]
    ) -> Sequence[UUID | None]:
        return await adapter.bulk_lookup_keypair_resource_policy_names(names)

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
        policy_id = await adapter.lookup_keypair_resource_policy(name)
        payload = await adapter.update_keypair_resource_policy(policy_id, asked)
        return payload.keypair_resource_policy

    @override
    async def purge(self, adapter: ResourcePolicyAdapter, name: str) -> str:
        policy_id = await adapter.lookup_keypair_resource_policy(name)
        payload = await adapter.purge_keypair_resource_policy(policy_id)
        return payload.name

    @override
    async def partial_bulk_update(
        self, adapter: ResourcePolicyAdapter, ids: list[UUID], asked: Any
    ) -> PartialBulkPayload[KeypairResourcePolicyNode]:
        return await adapter.partial_bulk_update_keypair_resource_policies(
            PartialBulkUpdateKeypairResourcePoliciesInput(
                items=[
                    PartialBulkUpdateKeypairResourcePolicyItemInput(id=policy_id, input=asked)
                    for policy_id in ids
                ]
            )
        )

    @override
    async def partial_bulk_purge(
        self, adapter: ResourcePolicyAdapter, ids: list[UUID]
    ) -> PartialBulkPayload[KeypairResourcePolicyNode]:
        return await adapter.partial_bulk_purge_keypair_resource_policies(
            PartialBulkPurgeKeypairResourcePoliciesInput(ids=ids)
        )

    @override
    async def read_mine(self, adapter: ResourcePolicyAdapter) -> KeypairResourcePolicyNode:
        return await adapter.get_my_keypair_resource_policy()


class UserPolicies(OwnFamily[UserResourcePolicyData, UserResourcePolicyNode]):
    @property
    @override
    def label(self) -> str:
        return "user-policy"

    @property
    @override
    def kind(self) -> str:
        return Says("사용자 정책", english="user policy")

    @property
    @override
    def entity_type(self) -> EntityType:
        return UserResourcePolicyEntityType()

    @property
    @override
    def calls(self) -> Calls:
        return Calls(
            create="admin_create_user_resource_policy",
            read="admin_get_user_resource_policy",
            search="admin_search_user_resource_policies",
            update="update_user_resource_policy",
            purge="purge_user_resource_policy",
            partial_bulk_update="partial_bulk_update_user_resource_policies",
            partial_bulk_purge="partial_bulk_purge_user_resource_policies",
            lookup="lookup_user_resource_policy",
            bulk_get="bulk_get_user_resource_policy_ids",
            bulk_lookup="bulk_lookup_user_resource_policy_names",
        )

    @property
    @override
    def mine(self) -> str:
        return "get_my_user_resource_policy"

    @property
    @override
    def fields(self) -> tuple[str, ...]:
        return (
            "max_vfolder_count",
            "max_concurrent_logins",
            "max_quota_scope_size",
            "max_session_count_per_model_session",
            "max_customized_image_count",
        )

    @override
    def seed(
        self, name_hint: str = "user-policy", *, holding_optional: bool = False
    ) -> TestSeedRow[UserResourcePolicyData]:
        return TestSeedUserPolicy(
            name_hint=name_hint, max_concurrent_logins=3 if holding_optional else None
        )

    @override
    def own_of(self, holder: LaidHolder) -> Laid[UserResourcePolicyData]:
        return holder.user_policy

    @override
    def view(self, node: UserResourcePolicyNode) -> dict[str, Any]:
        return {
            "name": node.name,
            "max_vfolder_count": node.max_vfolder_count,
            "max_concurrent_logins": node.max_concurrent_logins,
            "max_quota_scope_size": (
                node.max_quota_scope_size.expr,
                node.max_quota_scope_size.display,
            ),
            "max_session_count_per_model_session": node.max_session_count_per_model_session,
            "max_customized_image_count": node.max_customized_image_count,
        }

    @override
    def seeded_view(self, seeded: UserResourcePolicyData) -> dict[str, Any]:
        return {
            "name": seeded.name,
            "max_vfolder_count": seeded.max_vfolder_count,
            "max_concurrent_logins": seeded.max_concurrent_logins,
            "max_quota_scope_size": (
                str(seeded.max_quota_scope_size),
                f"{BinarySize(seeded.max_quota_scope_size):s}",
            ),
            "max_session_count_per_model_session": seeded.max_session_count_per_model_session,
            "max_customized_image_count": seeded.max_customized_image_count,
        }

    def _ask(self, name: str, says: str, *, logins: int | None) -> Ask:
        """요청과, 그 요청이 응답에 남겨야 하는 값을 같은 값에서 만든다."""
        asked = CreateUserResourcePolicyInput(
            name=name,
            max_vfolder_count=20,
            max_concurrent_logins=logins,
            max_quota_scope_size=BinarySizeInput(expr="1g"),
            max_session_count_per_model_session=4,
            max_customized_image_count=2,
        )
        expects = {
            "name": name,
            "max_vfolder_count": 20,
            "max_concurrent_logins": logins,
            "max_quota_scope_size": ("1073741824", "1g"),
            "max_session_count_per_model_session": 4,
            "max_customized_image_count": 2,
        }
        return Ask(asked, says, expects)

    @override
    def everything(self, name: str) -> Ask:
        return self._ask(name, Says("모든 값을 지정해", english="all values given"), logins=3)

    @override
    def only_required(self, name: str) -> Ask:
        return self._ask(
            name,
            Says("동시 로그인 수를 생략하고", english="the concurrent login count left out"),
            logins=None,
        )

    @override
    def one_limit(self) -> Edit:
        return Edit(
            UpdateUserResourcePolicyInput(max_vfolder_count=20),
            Says("vfolder 수 20으로 변경", english="the vfolder count changed to 20"),
            {"max_vfolder_count": 20},
        )

    @override
    def nothing(self) -> Edit:
        return Edit(UpdateUserResourcePolicyInput(), Says("빈 요청", english="an empty request"))

    @override
    def clearing_a_nullable(self) -> Edit:
        return Edit(
            UpdateUserResourcePolicyInput(max_concurrent_logins=None),
            Says("동시 로그인 수 비우기", english="the concurrent login count cleared"),
            {"max_concurrent_logins": None},
        )

    @override
    def clearing_a_non_nullable(self) -> Edit:
        return Edit(
            UpdateUserResourcePolicyInput(max_vfolder_count=None),
            Says("vfolder 수 비우기", english="the vfolder count cleared"),
        )

    @override
    async def create(self, adapter: ResourcePolicyAdapter, asked: Any) -> UserResourcePolicyNode:
        payload = await adapter.admin_create_user_resource_policy(asked)
        return payload.user_resource_policy

    @override
    async def read(self, adapter: ResourcePolicyAdapter, name: str) -> UserResourcePolicyNode:
        return await adapter.admin_get_user_resource_policy(name)

    @override
    async def search(
        self, adapter: ResourcePolicyAdapter, named: str | None = None
    ) -> SearchUserResourcePoliciesPayload:
        chosen = (
            UserResourcePolicyFilter(name=StringFilter(equals=named)) if named is not None else None
        )
        return await adapter.admin_search_user_resource_policies(
            AdminSearchUserResourcePoliciesInput(filter=chosen)
        )

    @override
    async def lookup(self, adapter: ResourcePolicyAdapter, name: str) -> UUID:
        return await adapter.lookup_user_resource_policy(name)

    @override
    async def bulk_get(self, adapter: ResourcePolicyAdapter, ids: list[UUID]) -> list[Any]:
        return await adapter.bulk_get_user_resource_policy_ids([
            UserResourcePolicyUUID(one) for one in ids
        ])

    @override
    async def bulk_lookup(
        self, adapter: ResourcePolicyAdapter, names: list[str]
    ) -> Sequence[UUID | None]:
        return await adapter.bulk_lookup_user_resource_policy_names(names)

    @override
    async def update(
        self, adapter: ResourcePolicyAdapter, name: str, asked: Any
    ) -> UserResourcePolicyNode:
        policy_id = await adapter.lookup_user_resource_policy(name)
        payload = await adapter.update_user_resource_policy(policy_id, asked)
        return payload.user_resource_policy

    @override
    async def purge(self, adapter: ResourcePolicyAdapter, name: str) -> str:
        policy_id = await adapter.lookup_user_resource_policy(name)
        payload = await adapter.purge_user_resource_policy(policy_id)
        return payload.name

    @override
    async def partial_bulk_update(
        self, adapter: ResourcePolicyAdapter, ids: list[UUID], asked: Any
    ) -> PartialBulkPayload[UserResourcePolicyNode]:
        return await adapter.partial_bulk_update_user_resource_policies(
            PartialBulkUpdateUserResourcePoliciesInput(
                items=[
                    PartialBulkUpdateUserResourcePolicyItemInput(id=policy_id, input=asked)
                    for policy_id in ids
                ]
            )
        )

    @override
    async def partial_bulk_purge(
        self, adapter: ResourcePolicyAdapter, ids: list[UUID]
    ) -> PartialBulkPayload[UserResourcePolicyNode]:
        return await adapter.partial_bulk_purge_user_resource_policies(
            PartialBulkPurgeUserResourcePoliciesInput(ids=ids)
        )

    @override
    async def read_mine(self, adapter: ResourcePolicyAdapter) -> UserResourcePolicyNode:
        return await adapter.get_my_user_resource_policy()


PROJECT = ProjectPolicies()
KEYPAIR = KeypairPolicies()
USER = UserPolicies()

FAMILIES: tuple[Family[Any, Any], ...] = (PROJECT, KEYPAIR, USER)
OWN_FAMILIES: tuple[OwnFamily[Any, Any], ...] = (KEYPAIR, USER)


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
class SeveralPoliciesAndACaller[PolicyData]:
    """한 번에 다룰 정책 여럿과, 그것을 호출할 사용자.

    ``held``는 대상 중 호출자에게 할당된 정책이고, 있으면 ``targets``의 맨 앞에 있다.
    """

    targets: tuple[PolicyData, ...]
    held: PolicyData | None
    caller: UserData

    def unused(self) -> tuple[PolicyData, ...]:
        """대상 중 아무도 사용하지 않는 정책들."""
        return self.targets if self.held is None else self.targets[1:]


@dataclass(frozen=True)
class SomeoneHeldToPolicies(TestSeedNest[LaidHolder]):
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
        return Says(
            "정책이 할당된 사용자 한 명 준비",
            english="Prepare one user with policies assigned",
        )

    @override
    def lay(self, seed: TestSeeder) -> LaidHolder:
        project_policy = seed.once(TestSeedProjectPolicy())
        user_policy = seed.creating(TestSeedUserPolicy())
        keypair_policy = seed.creating(TestSeedKeypairPolicy())
        # TODO(BA-7935): the report line for this user does not say it is inactive;
        # SeedUserOf.detail() reports only an explicit status.
        user = seed.provisioning(
            TestSeedUserOf(role=self.role, is_active=self.active),
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
class ReadingOwnPolicies(TestSeedNest[Laid[None]]):
    """자기 스코프에서 그 정책을 읽을 수 있게 하는 역할과, 그 역할의 부여."""

    user: Laid[UserData]
    entity_type: EntityType

    @override
    def kind(self) -> str:
        return Says(
            f"자기 스코프에서 {self.entity_type} 읽기 권한을 주는 역할 부여",
            english=(
                "Prepare the role assignment that grants read permission on "
                f"{self.entity_type} in the user's own scope"
            ),
        )

    @override
    def lay(self, seed: TestSeeder) -> Laid[None]:
        role = seed.creating_from(
            TestSeedRole(lambda u: UserID(u.id), name_hint="policy-reader"), self.user
        )
        seed.adding(
            TestSeedPermission(entity_type=self.entity_type, permission=Permission.READ), role
        )
        return seed.granting(
            role, self.user, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id)
        )


async def lay_a_holder(seeding: Any, *, role: UserRole, active: bool = True) -> LaidHolder:
    """도메인 하나와, 그 도메인에 속하며 정책이 할당된 사용자 한 명."""
    domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
    holder: LaidHolder = await seeding.within(
        SomeoneHeldToPolicies(domain, role=role, active=active)
    )
    return holder


@dataclass(frozen=True)
class ReadingPoliciesInGlobal(TestSeedNest[Laid[None]]):
    """global 스코프에서 그 정책을 읽을 수 있게 하는 역할과, 그 역할의 부여."""

    user: Laid[UserData]
    entity_type: EntityType

    @override
    def kind(self) -> str:
        return Says(
            f"global 스코프에서 {self.entity_type} 읽기 권한을 주는 역할 부여",
            english=(
                f"the role assignment granting read permission on {self.entity_type} "
                "in the global scope"
            ),
        )

    @override
    def lay(self, seed: TestSeeder) -> Laid[None]:
        role = seed.creating_from(
            TestSeedRole(
                lambda _: global_entity_id(GlobalEntityName.GLOBAL), name_hint="policy-reader"
            ),
            self.user,
        )
        seed.adding(
            TestSeedPermission(entity_type=self.entity_type, permission=Permission.READ), role
        )
        return seed.granting(
            role, self.user, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id)
        )


@dataclass(frozen=True)
class APolicyAndSomeone(Given[Any, APolicyAndACaller[Any]]):
    """정책 하나와, 다른 정책이 할당된 사용자 한 명. 대상 정책은 아무도 사용하지 않는다.

    ``granted`` 면 그 사용자가 global 스코프에서 그 정책을 읽을 수 있다.
    """

    family: Family[Any, Any]
    role: UserRole = UserRole.USER
    holding_optional: bool = False
    granted: bool = False

    @override
    def describe(self) -> str:
        kind = self.family.kind
        if self.granted:
            return Says(
                f"아무도 사용하지 않는 {kind} 하나와, global 스코프에서 그 정책을 읽을 수 있는 "
                f"{self.role.value} 한 명",
                english=(
                    f"one unused {in_language(kind, Language.ENGLISH)} and one {self.role.value} "
                    "who can read it in the global scope"
                ),
            )
        return Says(
            f"아무도 사용하지 않는 {kind} 하나와, {self.role.value} 한 명",
            english=(f"one unused {in_language(kind, Language.ENGLISH)} and one {self.role.value}"),
        )

    @override
    async def lay(self, seeding: Any) -> APolicyAndACaller[Any]:
        holder = await lay_a_holder(seeding, role=self.role)
        target = await seeding.creating(self.family.seed(holding_optional=self.holding_optional))
        if self.granted:
            await seeding.within(ReadingPoliciesInGlobal(holder.user, self.family.entity_type))
        return APolicyAndACaller(seeding.made(target), seeding.made(holder.user))


@dataclass(frozen=True)
class AHeldPolicyAndSomeone(Given[Any, APolicyAndACaller[Any]]):
    """호출자 자신에게 할당된 정책. 그 사용자의 키페어·사용자 행·개인 프로젝트가 아직 이 이름을 참조한다."""

    family: Family[Any, Any]
    role: UserRole = UserRole.SUPERADMIN

    @override
    def describe(self) -> str:
        kind = self.family.kind
        return Says(
            f"{self.role.value} 한 명과, 그 사용자에게 아직 할당된 {kind}",
            english=(
                f"one {self.role.value} and the {in_language(kind, Language.ENGLISH)} "
                "still assigned to that user"
            ),
        )

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
        kind = self.family.kind
        return Says(
            f"{kind} {self.besides + 2}개와, 그중 하나가 할당된 {self.role.value} 한 명",
            english=(
                f"{self.besides + 2} policies of the {in_language(kind, Language.ENGLISH)} "
                f"kind and one {self.role.value} with one of them assigned"
            ),
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
class SeveralPoliciesAndSomeone(Given[Any, SeveralPoliciesAndACaller[Any]]):
    """아무도 사용하지 않는 정책 여럿과 사용자 한 명. ``with_held``이면 그 사용자에게 할당된 정책도 대상에 넣는다."""

    family: Family[Any, Any]
    role: UserRole = UserRole.USER
    unused: int = 2
    with_held: bool = False

    @override
    def describe(self) -> str:
        kind = self.family.kind
        kind_en = in_language(kind, Language.ENGLISH)
        said_ko = f"아무도 사용하지 않는 {kind} {self.unused}개와, {self.role.value} 한 명"
        said_en = f"{self.unused} unused policies of the {kind_en} kind and one {self.role.value}"
        if self.with_held:
            return Says(
                f"{said_ko}, 그 사용자에게 할당된 {kind}도 대상에 넣음",
                english=(
                    f"{said_en}, with the {kind_en} assigned to that user also among the targets"
                ),
            )
        return Says(said_ko, english=said_en)

    @override
    async def lay(self, seeding: Any) -> SeveralPoliciesAndACaller[Any]:
        holder = await lay_a_holder(seeding, role=self.role)
        unused = [await seeding.creating(self.family.seed("target")) for _ in range(self.unused)]
        held = seeding.made(self.family.own_of(holder)) if self.with_held else None
        made = tuple(seeding.made(one) for one in unused)
        return SeveralPoliciesAndACaller(
            targets=made if held is None else (held, *made),
            held=held,
            caller=seeding.made(holder.user),
        )


@dataclass(frozen=True)
class SomeoneHeldToTheirPolicy(Given[Any, APolicyAndACaller[Any]]):
    """자기 정책을 조회할 사용자. 반환되는 정책은 그 사용자에게 할당된 것이다."""

    family: OwnFamily[Any, Any]
    granted: bool = True

    @override
    def describe(self) -> str:
        kind = self.family.kind
        kind_en = in_language(kind, Language.ENGLISH)
        if self.granted:
            return Says(
                f"{kind}이 할당된 사용자 한 명, 자기 스코프에서 그 정책을 읽을 권한 있음",
                english=(
                    f"one user with a {kind_en} assigned, allowed to read that policy "
                    "in their own scope"
                ),
            )
        return Says(
            f"{kind}이 할당된 사용자 한 명, 아무 권한도 없음",
            english=f"one user with a {kind_en} assigned and no permission",
        )

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
            return Says(
                "기본 키페어 외에 다른 키페어 정책이 할당된 활성 키페어를 하나 더 가진 사용자, "
                "읽기 권한 있음",
                english=(
                    "a user with one more active keypair, besides the default keypair, that "
                    "holds a different keypair policy, and with read permission"
                ),
            )
        return Says(
            "기본 키페어는 비활성이고 다른 키페어 정책이 할당된 활성 키페어를 하나 더 가진 사용자, "
            "읽기 권한 있음",
            english=(
                "a user whose default keypair is inactive and who has one more active keypair "
                "holding a different keypair policy, and with read permission"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> APolicyAndACaller[Any]:
        holder = await lay_a_holder(seeding, role=UserRole.USER, active=self.active)
        other = await seeding.creating(TestSeedKeypairPolicy(name_hint="other"))
        await seeding.adding(TestSeedKeypair(resource_policy=seeding.made(other).name), holder.user)
        await seeding.within(ReadingOwnPolicies(holder.user, KEYPAIR.entity_type))
        expected = holder.keypair_policy if self.active else other
        return APolicyAndACaller(seeding.made(expected), seeding.made(holder.user))


@dataclass(frozen=True)
class SomeoneWithNoActiveKey(Given[Any, APolicyAndACaller[Any]]):
    """비활성 사용자라 활성 키페어가 하나도 없는 사용자. 정책은 할당돼 있지만 키페어를 거쳐 도달할 수 없다."""

    @override
    def describe(self) -> str:
        return Says(
            "활성 키페어가 없는 사용자, 자기 스코프에서 키페어 정책 읽기 권한 있음",
            english=(
                "a user with no active keypair, allowed to read keypair policies in their own scope"
            ),
        )

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
        kind = self.family.kind
        return Says(
            f"미리 저장한 {kind} 전체가 반환됩니다",
            english=(
                f"the whole {in_language(kind, Language.ENGLISH)} seeded in advance comes back"
            ),
        )

    @override
    def look(self, laid: APolicyAndACaller[Any], answered: Answered[Any]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        wanted = {**self.family.seeded_view(laid.policy), **self.changed}
        return self.family.verdicts(node, wanted, self.started, entity_id=laid.policy.entity_id())


@dataclass(frozen=True)
class TheNewPolicyNode(Then[Any, Any]):
    """방금 생성한 정책이 통째로 반환된다. 기대값은 요청이 지정한 값에서 읽는다."""

    family: Family[Any, Any]
    started: datetime
    ask: Ask

    @override
    def says(self) -> str:
        kind = self.family.kind
        return Says(
            f"생성한 {kind} 전체가 반환됩니다",
            english=f"the whole {in_language(kind, Language.ENGLISH)} just created comes back",
        )

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
        kind = self.family.kind
        return Says(
            f"미리 저장한 {kind}이 모두, 그리고 그것만 반환됩니다",
            english=(
                f"every {in_language(kind, Language.ENGLISH)} seeded in advance comes back, "
                "and only those"
            ),
        )

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
        kind = self.family.kind
        return Says(
            f"필터에 맞는 {kind} 하나만 반환됩니다",
            english=(
                f"only the one {in_language(kind, Language.ENGLISH)} the filter names comes back"
            ),
        )

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


@dataclass(frozen=True)
class EveryUnusedTargetIsProcessed(Then[SeveralPoliciesAndACaller[Any], PartialBulkPayload[Any]]):
    """아무도 사용하지 않는 대상이 모두 처리된 목록에 온다. 기대값은 미리 만들어 둔 데이터에서 읽는다.

    ``changed``는 수정이 바꿔야 하는 필드다. ``missing``이 있으면 그 id 가, 대상 중 할당된
    정책이 있으면 그 정책이 실패 목록에 온다.
    """

    family: Family[Any, Any]
    started: datetime
    changed: Mapping[str, Any] = field(default_factory=dict)
    missing: UUID | None = None

    @override
    def says(self) -> str:
        kind = self.family.kind
        kind_en = in_language(kind, Language.ENGLISH)
        if self.missing is not None:
            return Says(
                f"대상 {kind}이 모두 처리된 목록에 오고, 없는 id 는 대상이 없다는 "
                "이유로 실패 목록에 옵니다",
                english=(
                    f"every target {kind_en} comes back in the processed list and an unknown "
                    "id comes back in the failed list because no target answers to it"
                ),
            )
        return Says(
            f"대상 {kind}이 모두 처리된 목록에 오고, 실패한 것은 없습니다",
            english=f"every target {kind_en} comes back in the processed list and nothing failed",
        )

    @override
    def look(
        self, laid: SeveralPoliciesAndACaller[Any], answered: Answered[PartialBulkPayload[Any]]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        targets = laid.unused()
        verdicts: list[Verdict] = [Same("successes count", len(payload.successes), len(targets))]
        for i, (node, policy) in enumerate(zip(payload.successes, targets, strict=False)):
            wanted = {**self.family.seeded_view(policy), **self.changed}
            verdicts += self.family.verdicts(
                node,
                wanted,
                self.started,
                prefix=f"successes[{i}].",
                entity_id=policy.entity_id(),
            )
        if self.missing is None:
            return [*verdicts, Same("failed", payload.failed, [])]
        verdicts.append(Same("failed count", len(payload.failed), 1))
        for failure in payload.failed:
            verdicts += [
                Held[UUID](
                    "failed[0].id",
                    failure.id,
                    SameAs(
                        self.missing,
                        Says("요청에 넣은 없는 id", english="the unknown id put in the request"),
                    ),
                ),
                Held("failed[0].message", failure.message, Mentions("not found")),
            ]
        return verdicts


@dataclass(frozen=True)
class OnlyTheHeldOneFails(Then[SeveralPoliciesAndACaller[Any], PartialBulkPayload[Any]]):
    """아무도 사용하지 않는 대상은 처리된 목록에, 아직 할당된 정책은 실패 목록에 온다."""

    family: Family[Any, Any]
    started: datetime
    reason: str

    @override
    def says(self) -> str:
        kind = self.family.kind
        kind_en = in_language(kind, Language.ENGLISH)
        return Says(
            f"아무도 사용하지 않는 {kind}은 처리된 목록에 오고, 아직 할당된 것은 "
            "참조 중이라는 이유로 실패 목록에 옵니다",
            english=(
                f"the unused {kind_en} comes back in the processed list and the one still "
                "assigned comes back in the failed list because it is still referenced"
            ),
        )

    @override
    def look(
        self, laid: SeveralPoliciesAndACaller[Any], answered: Answered[PartialBulkPayload[Any]]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None or laid.held is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        targets = laid.unused()
        verdicts: list[Verdict] = [Same("successes count", len(payload.successes), len(targets))]
        for i, (node, policy) in enumerate(zip(payload.successes, targets, strict=False)):
            verdicts += self.family.verdicts(
                node,
                self.family.seeded_view(policy),
                self.started,
                prefix=f"successes[{i}].",
                entity_id=policy.entity_id(),
            )
        verdicts.append(Same("failed count", len(payload.failed), 1))
        for failure in payload.failed:
            verdicts += [
                Held[UUID](
                    "failed[0].id",
                    failure.id,
                    SameAs(
                        laid.held.uuid,
                        Says(
                            "호출자에게 할당된 정책의 id",
                            english="the id of the policy assigned to the caller",
                        ),
                    ),
                ),
                Held("failed[0].message", failure.message, Mentions(self.reason)),
            ]
        return verdicts


@dataclass(frozen=True)
class NoTargetIsProcessed(Then[SeveralPoliciesAndACaller[Any], PartialBulkPayload[Any]]):
    """처리된 정책 없이, 대상이 모두 같은 이유로 실패 목록에 온다."""

    family: Family[Any, Any]
    reason: str

    @override
    def says(self) -> str:
        kind = self.family.kind
        return Says(
            f"처리된 {kind} 없이 대상이 모두 실패 목록에 옵니다",
            english=(
                f"no {in_language(kind, Language.ENGLISH)} is processed and every target "
                "comes back in the failed list"
            ),
        )

    @override
    def look(
        self, laid: SeveralPoliciesAndACaller[Any], answered: Answered[PartialBulkPayload[Any]]
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes", payload.successes, []),
            Same("failed count", len(payload.failed), len(laid.targets)),
        ]
        for i, (failure, policy) in enumerate(zip(payload.failed, laid.targets, strict=False)):
            verdicts += [
                Held[UUID](
                    f"failed[{i}].id",
                    failure.id,
                    SameAs(
                        policy.uuid, Says("대상 정책의 id", english="the id of the target policy")
                    ),
                ),
                Held(f"failed[{i}].message", failure.message, Mentions(self.reason)),
            ]
        return verdicts


@dataclass(frozen=True)
class ThePolicyId(Then[APolicyAndACaller[Any], UUID]):
    """이름을 푼 결과가 미리 만들어 둔 정책의 id 다."""

    @override
    def says(self) -> str:
        return Says(
            "그 정책의 id 가 반환됩니다",
            english="the id of that policy comes back",
        )

    @override
    def look(self, laid: APolicyAndACaller[Any], answered: Answered[UUID]) -> list[Verdict]:
        found = answered.response
        if found is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return [
            Held[UUID](
                "id",
                found,
                SameAs(
                    laid.policy.uuid,
                    Says(
                        "미리 저장한 정책의 id",
                        english="the id of the policy seeded in advance",
                    ),
                ),
            )
        ]


@dataclass(frozen=True)
class TheOnlyLoadedPolicy(Then[APolicyAndACaller[Any], list[Any]]):
    """물은 자리 하나에 미리 만들어 둔 정책 전체가 온다."""

    family: Family[Any, Any]
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "물은 항목에 미리 저장한 정책 전체가 응답으로 옵니다",
            english="the whole policy seeded in advance comes back for the item asked",
        )

    @override
    def look(self, laid: APolicyAndACaller[Any], answered: Answered[list[Any]]) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [MissingResponse(answered.raised)]
        if len(items) != 1:
            return [Same("len(items)", len(items), 1)]
        node = items[0]
        if not isinstance(
            node,
            (KeypairResourcePolicyNode, ProjectResourcePolicyNode, UserResourcePolicyNode),
        ):
            return [Same("items[0]", type(node).__name__, Says("노드", english="node"))]
        wanted = self.family.seeded_view(laid.policy)
        return [
            Same("len(items)", len(items), 1),
            *self.family.verdicts(
                node, wanted, self.started, prefix="items[0].", entity_id=laid.policy.entity_id()
            ),
        ]


@dataclass(frozen=True)
class TheOnlyTargetIsRefused(Then[APolicyAndACaller[Any], list[Any]]):
    """물은 자리 하나가 권한 부족으로 거부된다. 호출 전체는 답한다."""

    @override
    def says(self) -> str:
        return Says(
            "물은 항목이 권한 부족으로 거부됩니다",
            english="the item asked is rejected for not enough permission",
        )

    @override
    def look(self, laid: APolicyAndACaller[Any], answered: Answered[list[Any]]) -> list[Verdict]:
        items = answered.response
        if items is None:
            return [MissingResponse(answered.raised)]
        if len(items) != 1:
            return [Same("len(items)", len(items), 1)]
        got = items[0]
        return [
            Refused(
                NotEnoughPermission,
                got if isinstance(got, BaseException) else None,
            )
        ]


@dataclass(frozen=True)
class TheKnownNameHasAnId(Then[APolicyAndACaller[Any], Sequence[UUID | None]]):
    """있는 이름의 자리에 그 정책의 id 가, 없는 이름의 자리에 빈 값이 온다."""

    @override
    def says(self) -> str:
        return Says(
            "있는 이름의 항목에 그 정책의 id 가, 없는 이름의 항목에 빈 값이 응답으로 옵니다",
            english=(
                "the id of that policy comes back for the name that exists, and an empty value "
                "for the name that does not"
            ),
        )

    @override
    def look(
        self, laid: APolicyAndACaller[Any], answered: Answered[Sequence[UUID | None]]
    ) -> list[Verdict]:
        found = answered.response
        if found is None:
            return [MissingResponse(answered.raised)]
        if len(found) != 2:
            return [Same("len(ids)", len(found), 2)]
        return [
            Held[UUID | None](
                "[0]",
                found[0],
                SameAs(
                    laid.policy.uuid,
                    Says("미리 저장한 정책의 id", english="the id of the policy seeded in advance"),
                ),
            ),
            Same("[1]", found[1], None),
        ]


@dataclass(frozen=True)
class AProjectPolicyAndACaller:
    """프로젝트 하나와 그 프로젝트가 따르는 정책, 그리고 호출할 사용자."""

    project: ProjectData
    policy: ProjectResourcePolicyData
    caller: UserData


@dataclass(frozen=True)
class AProjectAndSomeone(Given[Any, AProjectPolicyAndACaller]):
    """프로젝트 하나와 사용자 한 명. ``granted``면 그 프로젝트 범위에서 프로젝트 정책 읽기 권한을 받는다."""

    granted: bool = True

    @override
    def describe(self) -> str:
        if self.granted:
            return Says(
                "프로젝트 하나와, 그 프로젝트 범위에서 프로젝트 정책 읽기 권한을 받은 일반 사용자 한 명",
                english=(
                    "one project and one regular user granted permission to read project resource "
                    "policies in that project's scope"
                ),
            )
        return Says(
            "프로젝트 하나와, 아무 권한도 받지 않은 일반 사용자 한 명",
            english="one project and one regular user granted nothing",
        )

    @override
    async def lay(self, seeding: Any) -> AProjectPolicyAndACaller:
        domain = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        policy = await seeding.once(TestSeedProjectPolicy())
        project = await seeding.creating_from_two(TestSeedProject(name_hint="team"), domain, policy)
        caller = await seeding.within(SomeoneOf(domain))
        if self.granted:
            role = await seeding.creating_from(
                TestSeedRole(lambda one: ProjectID(one.id), name_hint="policy-reader"), project
            )
            await seeding.adding(
                TestSeedPermission(
                    entity_type=ProjectResourcePolicyEntityType(), permission=Permission.READ
                ),
                role,
            )
            await seeding.granting(
                role, caller, role_id=lambda r: r.id, user_id=lambda u: UserID(u.id)
            )
        return AProjectPolicyAndACaller(
            project=seeding.made(project),
            policy=seeding.made(policy),
            caller=seeding.made(caller),
        )


@dataclass(frozen=True)
class TheProjectPolicyNode(Then[AProjectPolicyAndACaller, ProjectResourcePolicyNode]):
    """그 프로젝트가 따르는 정책 전체가 반환된다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "그 프로젝트가 따르는 프로젝트 정책 전체가 반환됩니다",
            english="the whole project policy that project follows comes back",
        )

    @override
    def look(
        self, laid: AProjectPolicyAndACaller, answered: Answered[ProjectResourcePolicyNode]
    ) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [MissingResponse(answered.raised)]
        wanted = PROJECT.seeded_view(laid.policy)
        return PROJECT.verdicts(node, wanted, self.started, entity_id=laid.policy.entity_id())
