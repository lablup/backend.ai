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
from bai_scenario.seeds.resource_policy.project import SeedNamedProjectPolicy, SeedProjectPolicy
from bai_scenario.seeds.resource_policy.user import SeedUserPolicy
from bai_scenario.seeds.seeder import Laid, Seeder, SeedNest, SeedRow
from bai_scenario.seeds.user.user import SeedUserOf

from ai.backend.common.data.entity.resource_policy import (
    KeyPairResourcePolicyEntityType,
    ProjectResourcePolicyEntityType,
    UserResourcePolicyEntityType,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.defs.session import SESSION_PRIORITY_MAX
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.common import (
    BinarySizeInput,
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
    DeleteKeypairResourcePolicyInput,
    DeleteProjectResourcePolicyInput,
    DeleteUserResourcePolicyInput,
    KeypairResourcePolicyFilter,
    KeypairResourcePolicyKeypairNestedFilter,
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
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.resource.types import (
    KeyPairResourcePolicyData,
    ProjectResourcePolicyData,
    UserResourcePolicyData,
)
from ai.backend.manager.data.user.types import UserData
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    Then,
    Told,
    Verdict,
)

type Searched = (
    SearchKeypairResourcePoliciesPayload
    | SearchUserResourcePoliciesPayload
    | SearchProjectResourcePoliciesPayload
)

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
    def seed(
        self, name_hint: str = "policy", *, holding_optional: bool = False
    ) -> SeedRow[PolicyData]:
        """정책 하나. ``holding_optional``이면 비울 수 있는 항목에 값을 둔다."""
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


class OwnFamily[PolicyData, PolicyNode](Family[PolicyData, PolicyNode]):
    """부르는 사람 자신의 것을 읽는 호출이 있고, 생략하거나 비울 수 있는 항목이 있는 정책."""

    @property
    @abstractmethod
    def mine(self) -> str:
        """자기 것을 읽는 호출의 이름."""
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
        return SeedKeypairPolicy(name_hint=name_hint, max_priority=10 if holding_optional else None)

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
        """요청과, 그 요청이 답에 남겨야 하는 것을 같은 값에서 짓는다."""
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
        return self._ask(name, "모든 값을 주고")

    @override
    def only_required(self, name: str) -> Ask:
        return self._ask(
            name,
            "대기 세션 수와 우선순위 상한과 대기 자원 슬롯을 빼고",
            pending_count=None,
            priority=None,
            pending_cpu=None,
        )

    def unlimited_slot(self, name: str) -> Ask:
        return self._ask(name, "cpu 슬롯을 무한으로 주고", cpu="Infinity")

    def priority_out_of_range(self, name: str) -> Ask:
        return self._ask(
            name,
            "우선순위 상한을 세션이 가질 수 있는 범위 밖으로 주고",
            priority=SESSION_PRIORITY_MAX + 1,
        )

    @override
    def one_limit(self) -> Edit:
        return Edit(
            UpdateKeypairResourcePolicyInput(max_concurrent_sessions=7),
            "동시 세션 수를 7로",
            {"max_concurrent_sessions": 7},
        )

    @override
    def nothing(self) -> Edit:
        return Edit(UpdateKeypairResourcePolicyInput(), "아무것도 대지 않고")

    @override
    def clearing_a_nullable(self) -> Edit:
        return Edit(
            UpdateKeypairResourcePolicyInput(max_priority=None),
            "우선순위 상한을 비우도록",
            {"max_priority": None},
        )

    @override
    def clearing_a_non_nullable(self) -> Edit:
        return Edit(
            UpdateKeypairResourcePolicyInput(max_concurrent_sessions=None),
            "동시 세션 수를 비우도록",
        )

    def priority_moved_out_of_range(self) -> Edit:
        return Edit(
            UpdateKeypairResourcePolicyInput(max_priority=SESSION_PRIORITY_MAX + 1),
            "우선순위 상한을 세션이 가질 수 있는 범위 밖으로",
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
        """그 사용자의 키페어가 매인 정책만."""
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


class UserPolicies(OwnFamily[UserResourcePolicyData, UserResourcePolicyNode]):
    @property
    @override
    def label(self) -> str:
        return "user-policy"

    @property
    @override
    def kind(self) -> str:
        return "사용자 정책"

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
            update="admin_update_user_resource_policy",
            delete="admin_delete_user_resource_policy",
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
    ) -> SeedRow[UserResourcePolicyData]:
        return SeedUserPolicy(
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
        """요청과, 그 요청이 답에 남겨야 하는 것을 같은 값에서 짓는다."""
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
        return self._ask(name, "모든 값을 주고", logins=3)

    @override
    def only_required(self, name: str) -> Ask:
        return self._ask(name, "동시 로그인 수를 빼고", logins=None)

    @override
    def one_limit(self) -> Edit:
        return Edit(
            UpdateUserResourcePolicyInput(max_vfolder_count=20),
            "폴더 수를 20으로",
            {"max_vfolder_count": 20},
        )

    @override
    def nothing(self) -> Edit:
        return Edit(UpdateUserResourcePolicyInput(), "아무것도 대지 않고")

    @override
    def clearing_a_nullable(self) -> Edit:
        return Edit(
            UpdateUserResourcePolicyInput(max_concurrent_logins=None),
            "동시 로그인 수를 비우도록",
            {"max_concurrent_logins": None},
        )

    @override
    def clearing_a_non_nullable(self) -> Edit:
        return Edit(UpdateUserResourcePolicyInput(max_vfolder_count=None), "폴더 수를 비우도록")

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
    async def update(
        self, adapter: ResourcePolicyAdapter, name: str, asked: Any
    ) -> UserResourcePolicyNode:
        payload = await adapter.admin_update_user_resource_policy(name, asked)
        return payload.user_resource_policy

    @override
    async def delete(self, adapter: ResourcePolicyAdapter, name: str) -> str:
        payload = await adapter.admin_delete_user_resource_policy(
            DeleteUserResourcePolicyInput(name=name)
        )
        return payload.name

    @override
    async def read_mine(self, adapter: ResourcePolicyAdapter) -> UserResourcePolicyNode:
        return await adapter.get_my_user_resource_policy()


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
    def seed(
        self, name_hint: str = "project-policy", *, holding_optional: bool = False
    ) -> SeedRow[ProjectResourcePolicyData]:
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


KEYPAIR = KeypairPolicies()
USER = UserPolicies()
PROJECT = ProjectPolicies()

FAMILIES: tuple[Family[Any, Any], ...] = (KEYPAIR, USER, PROJECT)
OWN_FAMILIES: tuple[OwnFamily[Any, Any], ...] = (KEYPAIR, USER)


@dataclass(frozen=True)
class APolicyAndACaller[PolicyData]:
    """정책 하나와, 그것을 부를 사람."""

    policy: PolicyData
    caller: UserData


@dataclass(frozen=True)
class ManyPoliciesAndACaller[PolicyData]:
    """검색할 정책 여럿과, 검색할 사람.

    ``named``는 그중 이름으로 골라낼 하나, ``held``는 부르는 사람 자신이 매인 하나다.
    """

    laid: tuple[PolicyData, ...]
    named: PolicyData
    held: PolicyData
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
    active: bool = True

    @override
    def kind(self) -> str:
        return "정책에 매인 사용자 한 명 준비"

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
    """자기 스코프에서 그 정책을 읽을 수 있게 하는 역할과 그 부여."""

    user: Laid[UserData]
    entity_type: EntityType

    @override
    def kind(self) -> str:
        return f"자기 스코프에서 {self.entity_type}을 읽을 수 있게 준비"

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
    """도메인 하나와, 그 안에 정책에 매인 사용자 한 명."""
    domain = await seeding.creating(SeedDomain(name_hint="home", description=WAS_HERE))
    holder: LaidHolder = await seeding.within(
        SomeoneHeldToPolicies(domain, role=role, active=active)
    )
    return holder


@dataclass(frozen=True)
class APolicyAndSomeone(Given[Any, APolicyAndACaller[Any]]):
    """정책 하나와, 다른 정책에 매인 사용자 한 명. 지목하는 정책을 아무도 쓰지 않는다."""

    family: Family[Any, Any]
    role: UserRole = UserRole.USER
    holding_optional: bool = False

    @override
    def describe(self) -> str:
        return f"아무도 쓰지 않는 {self.family.kind} 하나와, {self.role.value} 한 명"

    @override
    async def lay(self, seeding: Any) -> APolicyAndACaller[Any]:
        holder = await lay_a_holder(seeding, role=self.role)
        target = await seeding.creating(self.family.seed(holding_optional=self.holding_optional))
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
        held = self.family.own_of(holder)
        return ManyPoliciesAndACaller(
            laid=tuple(seeding.made(one) for one in [held, wanted, *others]),
            named=seeding.made(wanted),
            held=seeding.made(held),
            caller=seeding.made(holder.user),
        )


@dataclass(frozen=True)
class SomeoneHeldToTheirPolicy(Given[Any, APolicyAndACaller[Any]]):
    """자기 정책을 읽을 사람. 답으로 오는 정책은 그 사람이 매인 것이다."""

    family: OwnFamily[Any, Any]
    granted: bool = True

    @override
    def describe(self) -> str:
        if self.granted:
            return f"{self.family.kind}에 매인 사용자 한 명, 자기 스코프에서 그것을 읽을 수 있음"
        return f"{self.family.kind}에 매인 사용자 한 명, 아무 권한도 받지 않음"

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
    """키를 하나 더 가진 사람. 두 키가 다른 키페어 정책에 매여 있다.

    함께 만들어진 키가 기본 표시를 갖는다. 그 사람이 활성이면 그 키의 정책이 답이고,
    비활성이면 그 키도 비활성이라 더한 키의 정책이 답이다.
    """

    active: bool = True

    @override
    def describe(self) -> str:
        if self.active:
            return "기본 키 외에 다른 키페어 정책의 활성 키를 하나 더 가진 사용자, 읽을 수 있음"
        return "기본 키가 비활성이고 다른 키페어 정책의 활성 키를 하나 더 가진 사용자, 읽을 수 있음"

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
    """비활성이라 활성 키가 하나도 없는 사람. 정책은 매여 있지만 키를 거쳐 닿지 못한다."""

    @override
    def describe(self) -> str:
        return "활성 키가 없는 사용자, 자기 스코프에서 키페어 정책을 읽을 수 있음"

    @override
    async def lay(self, seeding: Any) -> APolicyAndACaller[Any]:
        holder = await lay_a_holder(seeding, role=UserRole.USER, active=False)
        await seeding.within(ReadingOwnPolicies(holder.user, KEYPAIR.entity_type))
        return APolicyAndACaller(seeding.made(holder.keypair_policy), seeding.made(holder.user))


@dataclass(frozen=True)
class NoAnswer(Verdict):
    """답이 와야 하는 자리에 거부가 왔다."""

    raised: BaseException | None

    @override
    def told(self) -> Told:
        refused = type(self.raised).__name__ if self.raised is not None else "아무것도 없음"
        return Told("답이 온다", problems=(f"답이 와야 하는데 {refused}",))


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
            return [NoAnswer(answered.raised)]
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
            return [NoAnswer(answered.raised)]
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
            return [NoAnswer(answered.raised)]
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
            return [NoAnswer(answered.raised)]
        return [
            Same("items", [one.name for one in payload.items], [laid.named.name]),
            Same("total_count", payload.total_count, 1),
        ]
