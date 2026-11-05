"""What a role scenario table says besides the call.

How the adapter is built lives in the tables' own conftest, and the rows a scenario
lays come from ``seeds``. This holds the type a role table is written against and the
checks more than one table shares.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.permission.types import role_scope_types
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.rbac.response import (
    EntityOperationCombinationInfo,
    PermissionNode,
    RoleAssignmentNode,
    RoleNode,
    ScopeEntityCombinationInfo,
    ScopeEntityOperationCombinationInfo,
)
from ai.backend.common.dto.manager.v2.rbac.types import (
    PermissionBitDTO,
    RoleSourceDTO,
    RoleStatusDTO,
)
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.testutils.scenario_steps import (
    Answered,
    Condition,
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
from bai_scenario.components.domain import (
    WAS_HERE,
    Mentions,
    SomeoneOf,
    WrittenByThisRun,
)
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.rbac.role import TestSeedPermission, TestSeedRole

DOMAIN_OF_ROLE = Says("역할을 둔 도메인의 id", english="the id of the domain the role sits in")
USER_OF_ROLE = Says("역할을 둔 사용자의 id", english="the id of the user the role sits in")


@dataclass(frozen=True)
class RolesAndACaller:
    """역할 여럿과, 그것을 부를 사람. 역할은 호출자가 속하지 않은 도메인에 있다."""

    roles: tuple[RoleData, ...]
    domain: DomainData
    caller: UserData
    permissions: tuple[PermissionData, ...] = ()
    assignees: tuple[UserData, ...] = ()
    self_role: RoleData | None = None
    grant_role: RoleData | None = None

    @property
    def role(self) -> RoleData:
        """역할이 하나뿐인 행이 다루는 역할."""
        return self.roles[0]


@dataclass(frozen=True)
class Granted:
    """A permission a seeded role holds, and the entity type it holds it on."""

    entity_type: EntityType
    permission: Permission


@dataclass(frozen=True)
class RolesAndSomeone(Given[Any, RolesAndACaller]):
    """한 도메인에 둔 역할 여럿과, 다른 도메인에 사는 사람 한 명.

    ``permissions``는 첫 역할이 가진 권한 행, ``grant``는 호출자에게 준 역할의 권한,
    ``self_grant``는 호출자 자신의 스코프에 둔 역할의 권한이다. ``assignees``는 역할을
    받을 사람들이고, 그중 ``assigned``명은 미리 그 역할을 받아 둔다.
    """

    role: UserRole = UserRole.USER
    count: int = 1
    permissions: Sequence[Granted] = ()
    grant: Sequence[Granted] = ()
    self_grant: Sequence[Permission] = ()
    assignees: int = 0
    assigned: int = 0

    @override
    def describe(self) -> str:
        return Says(
            f"한 도메인에 둔 커스텀 역할 {self.count}개와, 다른 도메인에 사는 "
            f"{self.role.value} 한 명",
            english=(
                f"{self.count} custom roles in one domain and one {self.role.value} "
                "in another domain"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> RolesAndACaller:
        home = await seeding.creating(TestSeedDomain(name_hint="home", description=WAS_HERE))
        target = await seeding.creating(TestSeedDomain(name_hint="target", description=WAS_HERE))
        roles = [
            await seeding.creating_from(TestSeedRole(lambda d: d.id, name_hint="role"), target)
            for _ in range(self.count)
        ]
        permissions = [
            await seeding.adding(TestSeedPermission(one.entity_type, one.permission), roles[0])
            for one in self.permissions
        ]
        caller = await seeding.within(SomeoneOf(home, role=self.role))
        assignees = [await seeding.within(SomeoneOf(target)) for _ in range(self.assignees)]
        for one in assignees[: self.assigned]:
            await seeding.granting(
                roles[0],
                one,
                role_id=lambda role: role.id,
                user_id=lambda user: UserID(user.id),
            )
        grant_role = None
        if self.grant:
            grant_role = await seeding.creating_from(
                TestSeedRole(lambda d: d.id, name_hint="grant"), target
            )
            for one in self.grant:
                await seeding.adding(
                    TestSeedPermission(one.entity_type, one.permission), grant_role
                )
            await seeding.granting(
                grant_role,
                caller,
                role_id=lambda one: one.id,
                user_id=lambda one: UserID(one.id),
            )
        self_role = None
        if self.self_grant:
            self_role = await seeding.creating_from(
                TestSeedRole(lambda u: UserID(u.id), name_hint="self-role"), caller
            )
            for permission in self.self_grant:
                await seeding.adding(TestSeedPermission(RoleEntityType(), permission), self_role)
            await seeding.granting(
                self_role,
                caller,
                role_id=lambda one: one.id,
                user_id=lambda one: UserID(one.id),
            )
        return RolesAndACaller(
            roles=tuple(seeding.made(one) for one in roles),
            domain=seeding.made(target),
            caller=seeding.made(caller),
            permissions=tuple(seeding.made(one) for one in permissions),
            assignees=tuple(seeding.made(one) for one in assignees),
            self_role=seeding.made(self_role) if self_role is not None else None,
            grant_role=seeding.made(grant_role) if grant_role is not None else None,
        )


@dataclass(frozen=True)
class RoleLook:
    """미리 만든 역할의 노드가 어떤 값으로 와야 하는지. 이름은 미리 만든 것에서 읽는다."""

    started: datetime
    described: str | None = None
    status: RoleStatusDTO = RoleStatusDTO.ACTIVE
    scope_type: EntityType = field(default_factory=DomainEntityType)

    def verdicts(
        self,
        prefix: str,
        node: RoleNode,
        laid: RoleData,
        scope_id: UUID,
        scope_called: Says = DOMAIN_OF_ROLE,
    ) -> list[Verdict]:
        written = WrittenByThisRun(self.started)
        deleted_at: Verdict = (
            Held(f"{prefix}deleted_at", node.deleted_at, written)
            if self.status == RoleStatusDTO.DELETED
            else Same(f"{prefix}deleted_at", node.deleted_at, None)
        )
        return [
            Same(f"{prefix}name", node.name, laid.name),
            Same(f"{prefix}description", node.description, self.described),
            Same(f"{prefix}source", node.source, RoleSourceDTO.CUSTOM),
            Same(f"{prefix}status", node.status, self.status),
            Same(f"{prefix}auto_assign", node.auto_assign, False),
            Same(f"{prefix}scope_type", node.scope_type, self.scope_type),
            Held[UUID](f"{prefix}scope_id", node.scope_id, SameAs(scope_id, scope_called)),
            Same(f"{prefix}role_preset_id", node.role_preset_id, None),
            Skipped(
                f"{prefix}id",
                Says("데이터베이스가 생성합니다", english="the database generates it"),
            ),
            Held[UUID](
                f"{prefix}entity_id",
                node.entity_id,
                SameAs(
                    laid.id,
                    Says("미리 저장한 역할의 id", english="the id of the role seeded in advance"),
                ),
            ),
            Held(f"{prefix}created_at", node.created_at, written),
            Held(f"{prefix}updated_at", node.updated_at, written),
            deleted_at,
        ]


@dataclass(frozen=True)
class PermissionLook:
    """권한 행 하나가 어떤 값으로 와야 하는지. 시드한 역할과 권한에서 읽는다."""

    started: datetime

    def verdicts(
        self,
        prefix: str,
        node: PermissionNode,
        role: RoleData,
        entity_type: EntityType,
        permission: Permission,
    ) -> list[Verdict]:
        return [
            Skipped(
                f"{prefix}id",
                Says("데이터베이스가 생성합니다", english="the database generates it"),
            ),
            Skipped(
                f"{prefix}field_id",
                Says("데이터베이스가 생성합니다", english="the database generates it"),
            ),
            Held[UUID](
                f"{prefix}role_id",
                node.role_id,
                SameAs(
                    role.id,
                    Says("미리 저장한 역할의 id", english="the id of the role seeded in advance"),
                ),
            ),
            Same(f"{prefix}entity_type", node.entity_type, entity_type),
            Same(f"{prefix}permission", node.permission, PermissionBitDTO.of(permission)),
            Held(f"{prefix}created_at", node.created_at, WrittenByThisRun(self.started)),
        ]


@dataclass(frozen=True)
class AssignmentLook:
    """역할 배정 하나가 어떤 값으로 와야 하는지. 시드한 사람과 역할에서 읽는다."""

    started: datetime

    def verdicts(
        self,
        prefix: str,
        node: RoleAssignmentNode,
        user_id: UUID,
        role_id: UUID,
        granted_by: UUID | None,
    ) -> list[Verdict]:
        granted: Verdict = (
            Same(f"{prefix}granted_by", node.granted_by, None)
            if granted_by is None
            else Held[UUID | None](
                f"{prefix}granted_by",
                node.granted_by,
                SameAs(
                    granted_by,
                    Says("역할을 준 사람", english="the one who granted the role"),
                ),
            )
        )
        return [
            Skipped(
                f"{prefix}id",
                Says("데이터베이스가 생성합니다", english="the database generates it"),
            ),
            Held[UUID](
                f"{prefix}user_id",
                node.user_id,
                SameAs(
                    user_id,
                    Says("미리 저장한 사용자의 id", english="the id of the user seeded in advance"),
                ),
            ),
            Held[UUID](
                f"{prefix}role_id",
                node.role_id,
                SameAs(
                    role_id,
                    Says("미리 저장한 역할의 id", english="the id of the role seeded in advance"),
                ),
            ),
            granted,
            Held(f"{prefix}granted_at", node.granted_at, WrittenByThisRun(self.started)),
        ]


@dataclass(frozen=True)
class NothingIsProcessed(Then[RolesAndACaller, PartialBulkPayload[RoleNode]]):
    """처리된 역할 없이, 대상이 모두 같은 이유로 실패 목록에 온다."""

    reason: str

    @override
    def says(self) -> str:
        return Says(
            "처리된 역할 없이 대상이 모두 실패 목록에 옵니다",
            english="no role is processed and every target comes back in the failed list",
        )

    @override
    def look(
        self,
        laid: RolesAndACaller,
        answered: Answered[PartialBulkPayload[RoleNode]],
    ) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("successes", payload.successes, []),
            Same("failed count", len(payload.failed), len(laid.roles)),
        ]
        for i, (failure, role) in enumerate(zip(payload.failed, laid.roles, strict=False)):
            verdicts += [
                Held[UUID](
                    f"failed[{i}].id",
                    failure.id,
                    SameAs(role.id, Says("대상 역할의 id", english="the id of the target role")),
                ),
                Held(f"failed[{i}].message", failure.message, Mentions(self.reason)),
            ]
        return verdicts


@dataclass(frozen=True)
class ThePermissionMatrix(Condition[list[ScopeEntityOperationCombinationInfo]]):
    """배선이 정한 스코프와 엔티티, 연산을 모두 실은 표.

    스코프는 역할이 놓이는 셋 그대로이고, 모든 스코프가 같은 엔티티를 실으며, 엔티티와
    연산은 이름 순이다. 연산마다 요구 권한과 설명이 있다.
    """

    @override
    def says(self) -> Says:
        return Says(
            "배선된 스코프와 엔티티, 연산을 모두 실은 표",
            english="the table carrying every wired scope, entity and operation",
        )

    @override
    def holds(self, got: list[ScopeEntityOperationCombinationInfo]) -> bool:
        if [one.scope_type for one in got] != list(role_scope_types()):
            return False
        if not got:
            return False
        first = [entity.entity_type for entity in got[0].entities]
        for one in got:
            entities = [entity.entity_type for entity in one.entities]
            if entities != first or entities != sorted(entities):
                return False
            for entity in one.entities:
                names = [operation.operation for operation in entity.actions]
                if not names or names != sorted(names):
                    return False
                if any(not operation.description for operation in entity.actions):
                    return False
                if any(
                    not isinstance(operation.required_permission, PermissionBitDTO)
                    for operation in entity.actions
                ):
                    return False
        return True


@dataclass(frozen=True)
class TheEntityOperations(Condition[list[EntityOperationCombinationInfo]]):
    """역할이 허용할 수 있는 엔티티와 그 연산. 엔티티와 연산은 이름 순이다."""

    @override
    def says(self) -> Says:
        return Says(
            "배선된 엔티티와 그 연산을 모두 싣고 이름 순인 목록",
            english="every wired entity with its operations, each in name order",
        )

    @override
    def holds(self, got: list[EntityOperationCombinationInfo]) -> bool:
        entities = [one.entity_type for one in got]
        if not entities or entities != sorted(entities):
            return False
        for one in got:
            names = [operation.operation for operation in one.operations]
            if not names or names != sorted(names):
                return False
            if any(not operation.description for operation in one.operations):
                return False
        return True


@dataclass(frozen=True)
class TheScopeEntities(Condition[list[ScopeEntityCombinationInfo]]):
    """역할이 놓이는 스코프마다 권한이 지목할 수 있는 엔티티. 스코프와 엔티티는 이름 순이다."""

    @override
    def says(self) -> Says:
        return Says(
            "스코프마다 지목할 수 있는 엔티티를 모두 싣고 이름 순인 목록",
            english="every scope with the entities it may name, each in name order",
        )

    @override
    def holds(self, got: list[ScopeEntityCombinationInfo]) -> bool:
        if [one.scope_type for one in got] != list(role_scope_types()):
            return False
        first = list(got[0].valid_entity_types) if got else []
        for one in got:
            entities = list(one.valid_entity_types)
            if not entities or entities != sorted(entities):
                return False
            if entities != first:
                return False
        return True
