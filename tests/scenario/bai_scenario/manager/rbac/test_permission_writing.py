"""권한 쓰기 — 만들기, 고치기, 지우기, 역할 전체 바꾸기, 일괄 더하기와 빼기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import UUID

import pytest

from ai.backend.common.data.entity.domain import DomainEntityType
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.v2.rbac.request import (
    BulkAddRolePermissionsInput,
    BulkRemoveRolePermissionsInput,
    CreatePermissionInput,
    ReplaceRolePermissionsInput,
    UpdatePermissionInput,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    BulkAddRolePermissionsPayload,
    BulkRemoveRolePermissionsPayload,
    DeletePermissionPayload,
    PermissionNode,
    ReplaceRolePermissionsPayload,
)
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO
from ai.backend.manager.api.adapters.rbac.adapter import RBACAdapter
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.errors.permission import (
    NotEnoughPermission,
    ReplaceRolePermissionRoleIdMismatch,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Refused,
    Same,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.domain import Mentions, TheCallIsRefused
from bai_scenario.components.rbac import (
    Granted,
    PermissionLook,
    RolesAndACaller,
    RolesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type PermissionStep = Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, Any]

WRITING = (
    Granted(RoleEntityType(), Permission.READ),
    Granted(RoleEntityType(), Permission.UPDATE),
)
SEEDED = (
    Granted(SessionEntityType(), Permission.READ),
    Granted(VFolderEntityType(), Permission.UPDATE),
)
NEW_ONE = Granted(DomainEntityType(), Permission.CREATE)
NEW_TWO = Granted(ProjectEntityType(), Permission.READ)


def _by_value(
    nodes: list[PermissionNode],
) -> list[PermissionNode]:
    return sorted(nodes, key=lambda node: (str(node.entity_type), node.permission))


def _verdicts_of(
    started: datetime, laid: RolesAndACaller, nodes: list[PermissionNode], granted: list[Granted]
) -> list[Verdict]:
    expected = sorted(
        granted,
        key=lambda one: (str(one.entity_type), PermissionBitDTO.of(one.permission)),
    )
    look = PermissionLook(started)
    verdicts: list[Verdict] = [Same("items count", len(nodes), len(expected))]
    for i, (node, one) in enumerate(zip(_by_value(nodes), expected, strict=False)):
        verdicts += look.verdicts(f"items[{i}].", node, laid.role, one.entity_type, one.permission)
    return verdicts


@dataclass(frozen=True)
class CreatingAPermission(When[RolesAndACaller, RBACAdapter, PermissionNode]):
    @override
    def operation(self) -> str:
        return "create_permission"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.role.name} 에 세션 soft delete 권한을 더합니다",
            english=(
                f"{laid.caller.username} adds a session soft delete permission to {laid.role.name}"
            ),
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> PermissionNode:
        with ActingAs(laid.caller):
            return await adapter.create_permission(
                CreatePermissionInput(
                    role_id=laid.role.id,
                    entity_type=SessionEntityType(),
                    permission=PermissionBitDTO.SOFT_DELETE,
                )
            )


@dataclass(frozen=True)
class UpdatingAPermission(When[RolesAndACaller, RBACAdapter, PermissionNode]):
    @override
    def operation(self) -> str:
        return "update_permission"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.role.name} 의 첫 권한을 soft delete 로 바꿉니다",
            english=(
                f"{laid.caller.username} changes the first permission of {laid.role.name} to "
                "soft delete"
            ),
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> PermissionNode:
        with ActingAs(laid.caller):
            return await adapter.update_permission(
                UpdatePermissionInput(
                    id=laid.permissions[0].id, permission=PermissionBitDTO.SOFT_DELETE
                )
            )


@dataclass(frozen=True)
class PurgingAPermission(When[RolesAndACaller, RBACAdapter, DeletePermissionPayload]):
    @override
    def operation(self) -> str:
        return "purge_permission"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.role.name} 의 첫 권한을 purge 합니다",
            english=f"{laid.caller.username} purges the first permission of {laid.role.name}",
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> DeletePermissionPayload:
        with ActingAs(laid.caller):
            return await adapter.purge_permission(laid.permissions[0].id)


@dataclass(frozen=True)
class AddingSeveralPermissions(When[RolesAndACaller, RBACAdapter, BulkAddRolePermissionsPayload]):
    @override
    def operation(self) -> str:
        return "bulk_add_role_permissions"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.role.name} 에 도메인 만들기와 프로젝트 읽기 권한을 "
            "한 번에 더합니다",
            english=(
                f"{laid.caller.username} adds domain create and project read permissions to "
                f"{laid.role.name} in one call"
            ),
        )

    @override
    async def call(
        self, adapter: RBACAdapter, laid: RolesAndACaller
    ) -> BulkAddRolePermissionsPayload:
        with ActingAs(laid.caller):
            return await adapter.bulk_add_role_permissions(
                BulkAddRolePermissionsInput(
                    permissions=[
                        CreatePermissionInput(
                            role_id=laid.role.id,
                            entity_type=one.entity_type,
                            permission=PermissionBitDTO.of(one.permission),
                        )
                        for one in (NEW_ONE, NEW_TWO)
                    ]
                )
            )


@dataclass(frozen=True)
class AddingOneAlreadyHeld(When[RolesAndACaller, RBACAdapter, BulkAddRolePermissionsPayload]):
    @override
    def operation(self) -> str:
        return "bulk_add_role_permissions"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.role.name} 에 이미 가진 세션 읽기 권한과 도메인 "
            "만들기 권한을 한 번에 더합니다",
            english=(
                f"{laid.caller.username} adds a session read permission the role already holds "
                f"and a domain create permission to {laid.role.name} in one call"
            ),
        )

    @override
    async def call(
        self, adapter: RBACAdapter, laid: RolesAndACaller
    ) -> BulkAddRolePermissionsPayload:
        with ActingAs(laid.caller):
            return await adapter.bulk_add_role_permissions(
                BulkAddRolePermissionsInput(
                    permissions=[
                        CreatePermissionInput(
                            role_id=laid.role.id,
                            entity_type=laid.permissions[0].entity_type,
                            permission=PermissionBitDTO.of(laid.permissions[0].permission),
                        ),
                        CreatePermissionInput(
                            role_id=laid.role.id,
                            entity_type=NEW_ONE.entity_type,
                            permission=PermissionBitDTO.of(NEW_ONE.permission),
                        ),
                    ]
                )
            )


@dataclass(frozen=True)
class RemovingSeveralPermissions(
    When[RolesAndACaller, RBACAdapter, BulkRemoveRolePermissionsPayload]
):
    @override
    def operation(self) -> str:
        return "bulk_remove_role_permissions"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.role.name} 의 권한 둘을 한 번에 뺍니다",
            english=f"{laid.caller.username} removes both permissions of {laid.role.name} in one call",
        )

    @override
    async def call(
        self, adapter: RBACAdapter, laid: RolesAndACaller
    ) -> BulkRemoveRolePermissionsPayload:
        with ActingAs(laid.caller):
            return await adapter.bulk_remove_role_permissions(
                BulkRemoveRolePermissionsInput(permission_ids=[one.id for one in laid.permissions])
            )


@dataclass(frozen=True)
class ReplacingThePermissions(When[RolesAndACaller, RBACAdapter, ReplaceRolePermissionsPayload]):
    @override
    def operation(self) -> str:
        return "replace_role_permissions"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.role.name} 의 권한을 도메인 만들기와 프로젝트 "
            "읽기로 바꿉니다",
            english=(
                f"{laid.caller.username} replaces the permissions of {laid.role.name} with "
                "domain create and project read"
            ),
        )

    @override
    async def call(
        self, adapter: RBACAdapter, laid: RolesAndACaller
    ) -> ReplaceRolePermissionsPayload:
        with ActingAs(laid.caller):
            return await adapter.replace_role_permissions(
                ReplaceRolePermissionsInput(
                    role_id=laid.role.id,
                    permissions=[
                        CreatePermissionInput(
                            role_id=laid.role.id,
                            entity_type=one.entity_type,
                            permission=PermissionBitDTO.of(one.permission),
                        )
                        for one in (NEW_ONE, NEW_TWO)
                    ],
                )
            )


@dataclass(frozen=True)
class ReplacingWithAnotherRolesEntry(
    When[RolesAndACaller, RBACAdapter, ReplaceRolePermissionsPayload]
):
    @override
    def operation(self) -> str:
        return "replace_role_permissions"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.role.name} 의 권한을 다른 역할의 id 를 단 항목으로 "
            "바꾸려 합니다",
            english=(
                f"{laid.caller.username} tries to replace the permissions of {laid.role.name} "
                "with an entry naming another role"
            ),
        )

    @override
    async def call(
        self, adapter: RBACAdapter, laid: RolesAndACaller
    ) -> ReplaceRolePermissionsPayload:
        with ActingAs(laid.caller):
            return await adapter.replace_role_permissions(
                ReplaceRolePermissionsInput(
                    role_id=laid.role.id,
                    permissions=[
                        CreatePermissionInput(
                            role_id=laid.grant_role.id if laid.grant_role else laid.role.id,
                            entity_type=NEW_ONE.entity_type,
                            permission=PermissionBitDTO.of(NEW_ONE.permission),
                        )
                    ],
                )
            )


@dataclass(frozen=True)
class TheCreatedPermission(Then[RolesAndACaller, PermissionNode]):
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "만든 권한 행 전체가 옵니다",
            english="the whole permission row just created comes back",
        )

    @override
    def look(self, laid: RolesAndACaller, answered: Answered[PermissionNode]) -> list[Verdict]:
        node = answered.response
        if not isinstance(node, PermissionNode):
            return [Refused(NotEnoughPermission, answered.raised)]
        return PermissionLook(self.started).verdicts(
            "", node, laid.role, SessionEntityType(), Permission.SOFT_DELETE
        )


@dataclass(frozen=True)
class TheUpdatedPermission(Then[RolesAndACaller, PermissionNode]):
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "고친 권한 행 전체가 옵니다",
            english="the whole permission row just changed comes back",
        )

    @override
    def look(self, laid: RolesAndACaller, answered: Answered[PermissionNode]) -> list[Verdict]:
        node = answered.response
        if not isinstance(node, PermissionNode):
            return [Refused(NotEnoughPermission, answered.raised)]
        return PermissionLook(self.started).verdicts(
            "", node, laid.role, laid.permissions[0].entity_type, Permission.SOFT_DELETE
        )


@dataclass(frozen=True)
class ThePurgedPermission(Then[RolesAndACaller, DeletePermissionPayload]):
    @override
    def says(self) -> str:
        return Says(
            "purge 한 권한 행의 id 가 옵니다",
            english="the id of the purged permission row comes back",
        )

    @override
    def look(
        self, laid: RolesAndACaller, answered: Answered[DeletePermissionPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if not isinstance(payload, DeletePermissionPayload):
            return [Refused(NotEnoughPermission, answered.raised)]
        seeded = laid.permissions[0].id
        return [
            Held[UUID](
                "id",
                payload.id,
                SameAs(
                    seeded,
                    Says(
                        "미리 저장한 권한 행의 id",
                        english="the id of the permission row seeded in advance",
                    ),
                ),
            ),
            Held[UUID](
                "field_id",
                payload.field_id,
                SameAs(
                    seeded,
                    Says(
                        "미리 저장한 권한 행의 id",
                        english="the id of the permission row seeded in advance",
                    ),
                ),
            ),
        ]


@dataclass(frozen=True)
class EveryEntryAdded(Then[RolesAndACaller, BulkAddRolePermissionsPayload]):
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "더한 권한 행이 모두 오고 실패가 없습니다",
            english="every permission row added comes back and nothing failed",
        )

    @override
    def look(
        self, laid: RolesAndACaller, answered: Answered[BulkAddRolePermissionsPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if not isinstance(payload, BulkAddRolePermissionsPayload):
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            *_verdicts_of(self.started, laid, payload.items, [NEW_ONE, NEW_TWO]),
            Same("failed", payload.failed, []),
        ]


@dataclass(frozen=True)
class TheHeldEntryFails(Then[RolesAndACaller, BulkAddRolePermissionsPayload]):
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "새 권한만 더해지고 이미 가진 권한은 실패 목록에 옵니다",
            english="only the new permission is added and the one already held comes back failed",
        )

    @override
    def look(
        self, laid: RolesAndACaller, answered: Answered[BulkAddRolePermissionsPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if not isinstance(payload, BulkAddRolePermissionsPayload):
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            *_verdicts_of(self.started, laid, payload.items, [NEW_ONE]),
            Same("failed count", len(payload.failed), 1),
        ]
        for i, failure in enumerate(payload.failed):
            verdicts += [
                Same(
                    f"failed[{i}].entity_type",
                    failure.entity_type,
                    str(laid.permissions[0].entity_type),
                ),
                Same(
                    f"failed[{i}].permission",
                    failure.permission,
                    PermissionBitDTO.of(laid.permissions[0].permission),
                ),
                Held(f"failed[{i}].message", failure.message, Mentions("Duplicate permission")),
            ]
        return verdicts


@dataclass(frozen=True)
class EveryEntryRemoved(Then[RolesAndACaller, BulkRemoveRolePermissionsPayload]):
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "뺀 권한 행이 모두 오고 실패가 없습니다",
            english="every permission row removed comes back and nothing failed",
        )

    @override
    def look(
        self, laid: RolesAndACaller, answered: Answered[BulkRemoveRolePermissionsPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if not isinstance(payload, BulkRemoveRolePermissionsPayload):
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            *_verdicts_of(self.started, laid, payload.items, list(SEEDED)),
            Same("failed", payload.failed, []),
        ]


@dataclass(frozen=True)
class TheNewPermissionSet(Then[RolesAndACaller, ReplaceRolePermissionsPayload]):
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "바꾼 권한 행이 모두 오고 실패가 없습니다",
            english="the whole permission set that took over comes back and nothing failed",
        )

    @override
    def look(
        self, laid: RolesAndACaller, answered: Answered[ReplaceRolePermissionsPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if not isinstance(payload, ReplaceRolePermissionsPayload):
            return [Refused(NotEnoughPermission, answered.raised)]
        return [
            *_verdicts_of(self.started, laid, payload.items, [NEW_ONE, NEW_TWO]),
            Same("failed", payload.failed, []),
        ]


def _given(granted: bool) -> RolesAndSomeone:
    return RolesAndSomeone(
        permissions=SEEDED,
        grant=WRITING if granted else (),
    )


@dataclass(frozen=True)
class AUserGrantedRoleWriteCreatesAPermission(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, PermissionNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-role-write-creates-a-permission"

    @override
    def describe(self) -> str:
        return Says(
            "대상 도메인에서 역할 읽기와 수정 권한을 받은 사용자가 권한을 만들면, "
            "만든 권한 행 전체가 옵니다",
            english=(
                "when a user granted role read and update permissions in a domain creates a "
                "permission, the whole permission row just created comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return _given(True)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, PermissionNode]:
        return CreatingAPermission()

    @override
    def then(self) -> Then[RolesAndACaller, PermissionNode]:
        return TheCreatedPermission(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotCreateAPermission(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, PermissionNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-create-a-permission"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자는 권한을 만들 수 없습니다",
            english="a user granted nothing cannot create a permission",
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return _given(False)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, PermissionNode]:
        return CreatingAPermission()

    @override
    def then(self) -> Then[RolesAndACaller, PermissionNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedRoleWriteUpdatesAPermission(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, PermissionNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-role-write-updates-a-permission"

    @override
    def describe(self) -> str:
        return Says(
            "대상 도메인에서 역할 읽기와 수정 권한을 받은 사용자가 권한을 고치면, "
            "고친 권한 행 전체가 옵니다",
            english=(
                "when a user granted role read and update permissions in a domain changes a "
                "permission, the whole permission row just changed comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return _given(True)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, PermissionNode]:
        return UpdatingAPermission()

    @override
    def then(self) -> Then[RolesAndACaller, PermissionNode]:
        return TheUpdatedPermission(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotUpdateAPermission(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, PermissionNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-update-a-permission"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자는 권한을 고칠 수 없습니다",
            english="a user granted nothing cannot change a permission",
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return _given(False)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, PermissionNode]:
        return UpdatingAPermission()

    @override
    def then(self) -> Then[RolesAndACaller, PermissionNode]:
        return TheCallIsRefused(GenericBadRequest)


@dataclass(frozen=True)
class AUserGrantedRoleWritePurgesAPermission(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, DeletePermissionPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-role-write-purges-a-permission"

    @override
    def describe(self) -> str:
        return Says(
            "대상 도메인에서 역할 읽기와 수정 권한을 받은 사용자가 권한을 purge 하면, "
            "그 권한 행의 id 가 옵니다",
            english=(
                "when a user granted role read and update permissions in a domain purges a "
                "permission, the id of that permission row comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return _given(True)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, DeletePermissionPayload]:
        return PurgingAPermission()

    @override
    def then(self) -> Then[RolesAndACaller, DeletePermissionPayload]:
        return ThePurgedPermission()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotPurgeAPermission(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, DeletePermissionPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-purge-a-permission"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자는 권한을 purge 할 수 없습니다",
            english="a user granted nothing cannot purge a permission",
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return _given(False)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, DeletePermissionPayload]:
        return PurgingAPermission()

    @override
    def then(self) -> Then[RolesAndACaller, DeletePermissionPayload]:
        return TheCallIsRefused(GenericBadRequest)


@dataclass(frozen=True)
class AUserGrantedRoleWriteAddsSeveralPermissions(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, BulkAddRolePermissionsPayload]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-role-write-adds-several-permissions"

    @override
    def describe(self) -> str:
        return Says(
            "대상 도메인에서 역할 읽기와 수정 권한을 받은 사용자가 권한 둘을 한 번에 더하면, "
            "더한 권한 행이 모두 오고 실패가 없습니다",
            english=(
                "when a user granted role read and update permissions in a domain adds two "
                "permissions in one call, every row added comes back and nothing failed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return _given(True)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, BulkAddRolePermissionsPayload]:
        return AddingSeveralPermissions()

    @override
    def then(self) -> Then[RolesAndACaller, BulkAddRolePermissionsPayload]:
        return EveryEntryAdded(started=self.started)


@dataclass(frozen=True)
class AUserGrantedRoleWriteAddsOneAlreadyHeld(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, BulkAddRolePermissionsPayload]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-role-write-adds-one-permission-it-already-holds"

    @override
    def describe(self) -> str:
        return Says(
            "대상 도메인에서 역할 읽기와 수정 권한을 받은 사용자가 이미 가진 권한과 새 권한을 "
            "한 번에 더하면, 새 권한만 더해지고 이미 가진 권한은 실패 목록에 옵니다",
            english=(
                "when a user granted role read and update permissions in a domain adds a "
                "permission the role already holds and a new one in one call, only the new one "
                "is added and the one already held comes back failed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return _given(True)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, BulkAddRolePermissionsPayload]:
        return AddingOneAlreadyHeld()

    @override
    def then(self) -> Then[RolesAndACaller, BulkAddRolePermissionsPayload]:
        return TheHeldEntryFails(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotAddPermissions(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, BulkAddRolePermissionsPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-add-permissions"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자는 권한을 한 번에 더할 수 없습니다",
            english="a user granted nothing cannot add permissions in one call",
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return _given(False)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, BulkAddRolePermissionsPayload]:
        return AddingSeveralPermissions()

    @override
    def then(self) -> Then[RolesAndACaller, BulkAddRolePermissionsPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedRoleWriteRemovesSeveralPermissions(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, BulkRemoveRolePermissionsPayload]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-role-write-removes-several-permissions"

    @override
    def describe(self) -> str:
        return Says(
            "대상 도메인에서 역할 읽기와 수정 권한을 받은 사용자가 권한 둘을 한 번에 빼면, "
            "뺀 권한 행이 모두 오고 실패가 없습니다",
            english=(
                "when a user granted role read and update permissions in a domain removes two "
                "permissions in one call, every row removed comes back and nothing failed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return _given(True)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, BulkRemoveRolePermissionsPayload]:
        return RemovingSeveralPermissions()

    @override
    def then(self) -> Then[RolesAndACaller, BulkRemoveRolePermissionsPayload]:
        return EveryEntryRemoved(started=self.started)


@dataclass(frozen=True)
class AUserGrantedRoleWriteReplacesThePermissions(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, ReplaceRolePermissionsPayload]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-role-write-replaces-the-permissions"

    @override
    def describe(self) -> str:
        return Says(
            "대상 도메인에서 역할 읽기와 수정 권한을 받은 사용자가 역할의 권한을 통째로 바꾸면, "
            "새 권한 행이 모두 오고 실패가 없습니다",
            english=(
                "when a user granted role read and update permissions in a domain replaces the "
                "permission set of a role, every new permission row comes back and nothing failed"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return _given(True)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, ReplaceRolePermissionsPayload]:
        return ReplacingThePermissions()

    @override
    def then(self) -> Then[RolesAndACaller, ReplaceRolePermissionsPayload]:
        return TheNewPermissionSet(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReplaceThePermissions(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, ReplaceRolePermissionsPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-replace-the-permissions"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자는 역할의 권한을 통째로 바꿀 수 없습니다",
            english="a user granted nothing cannot replace the permission set of a role",
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return _given(False)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, ReplaceRolePermissionsPayload]:
        return ReplacingThePermissions()

    @override
    def then(self) -> Then[RolesAndACaller, ReplaceRolePermissionsPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ReplacingWithAnEntryOfAnotherRoleIsRefused(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, ReplaceRolePermissionsPayload]
):
    @override
    def summary(self) -> str:
        return "replacing-with-an-entry-of-another-role-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "요청한 역할과 다른 역할의 id 를 단 항목으로 권한을 바꾸려 하면, 요청 전체가 "
            "거부됩니다",
            english=(
                "when the request names one role and an entry names another, the whole request "
                "is rejected"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return _given(True)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, ReplaceRolePermissionsPayload]:
        return ReplacingWithAnotherRolesEntry()

    @override
    def then(self) -> Then[RolesAndACaller, ReplaceRolePermissionsPayload]:
        return TheCallIsRefused(ReplaceRolePermissionRoleIdMismatch)


@dataclass(frozen=True)
class ANothingGrantedUserRemovesNone(Then[RolesAndACaller, BulkRemoveRolePermissionsPayload]):
    @override
    def says(self) -> str:
        return Says(
            "아무 권한 행도 빠지지 않고 대상이 모두 실패 목록에 옵니다",
            english="no permission row is removed and every target comes back in the failed list",
        )

    @override
    def look(
        self, laid: RolesAndACaller, answered: Answered[BulkRemoveRolePermissionsPayload]
    ) -> list[Verdict]:
        payload = answered.response
        if not isinstance(payload, BulkRemoveRolePermissionsPayload):
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [
            Same("items", payload.items, []),
            Same("failed count", len(payload.failed), len(laid.permissions)),
        ]
        for i, (failure, seeded) in enumerate(zip(payload.failed, laid.permissions, strict=False)):
            verdicts += [
                Held[UUID](
                    f"failed[{i}].permission_id",
                    failure.permission_id,
                    SameAs(
                        seeded.id,
                        Says(
                            "미리 저장한 권한 행의 id",
                            english="the id of the permission row seeded in advance",
                        ),
                    ),
                ),
                Held(f"failed[{i}].message", failure.message, Mentions("permission")),
            ]
        return verdicts


@dataclass(frozen=True)
class AUserGrantedNothingRemovesNoPermission(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, BulkRemoveRolePermissionsPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-removes-no-permission"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 권한 둘을 한 번에 빼면, 하나도 빠지지 않고 모두 "
            "실패 목록에 옵니다",
            english=(
                "when a user granted nothing removes two permissions in one call, none is removed "
                "and both come back in the failed list"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return _given(False)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, BulkRemoveRolePermissionsPayload]:
        return RemovingSeveralPermissions()

    @override
    def then(self) -> Then[RolesAndACaller, BulkRemoveRolePermissionsPayload]:
        return ANothingGrantedUserRemovesNone()


SCENARIOS: list[PermissionStep] = [
    AUserGrantedRoleWriteCreatesAPermission(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotCreateAPermission(),
    AUserGrantedRoleWriteUpdatesAPermission(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotUpdateAPermission(),
    AUserGrantedRoleWritePurgesAPermission(),
    AUserGrantedNothingMayNotPurgeAPermission(),
    AUserGrantedRoleWriteAddsSeveralPermissions(started=datetime.now(UTC)),
    AUserGrantedRoleWriteAddsOneAlreadyHeld(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotAddPermissions(),
    AUserGrantedRoleWriteRemovesSeveralPermissions(started=datetime.now(UTC)),
    AUserGrantedNothingRemovesNoPermission(),
    AUserGrantedRoleWriteReplacesThePermissions(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotReplaceThePermissions(),
    ReplacingWithAnEntryOfAnotherRoleIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_permission_writing(
    scenario: PermissionStep, adapter: RBACAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
