"""id 로 역할, 권한, 배정을 한 번에 읽기."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.permission import PermissionID
from ai.backend.common.data.entity.role import RoleEntityType, RoleID
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.rbac.request import SearchRoleAssignmentsInput
from ai.backend.common.dto.manager.v2.rbac.response import (
    PermissionNode,
    RoleAssignmentNode,
    RoleNode,
)
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO
from ai.backend.manager.api.adapters.rbac.adapter import RBACAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Same,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.domain import TheCallIsRefused
from bai_scenario.components.rbac import (
    AssignmentLook,
    Granted,
    PermissionLook,
    RoleLook,
    RolesAndACaller,
    RolesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type RolesLoaded = list[RoleNode | None]
type PermissionsLoaded = list[PermissionNode | None]
type PermissionListsLoaded = list[list[PermissionNode]]
type AssignmentsLoaded = list[RoleAssignmentNode | None]
type LoadStep = Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, Any]

PERMISSIONS = (
    Granted(SessionEntityType(), Permission.READ),
    Granted(VFolderEntityType(), Permission.UPDATE),
)


@dataclass(frozen=True)
class LoadingRoles(When[RolesAndACaller, RBACAdapter, RolesLoaded]):
    @override
    def operation(self) -> str:
        return "batch_load_roles_by_ids"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 역할 둘과 없는 id 하나를 한 번에 읽습니다",
            english=f"{laid.caller.username} loads two roles and one missing id in one call",
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> RolesLoaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_roles_by_ids([
                RoleID(laid.roles[0].id),
                RoleID(laid.roles[1].id),
                RoleID(uuid4()),
            ])


@dataclass(frozen=True)
class LoadingRolesWithAnUnreadableOne(When[RolesAndACaller, RBACAdapter, RolesLoaded]):
    @override
    def operation(self) -> str:
        return "batch_load_roles_by_ids"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 읽을 수 있는 역할 하나와 읽을 수 없는 역할 하나를 한 번에 읽습니다",
            english=(
                f"{laid.caller.username} loads one readable role and one unreadable role in one call"
            ),
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> RolesLoaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_roles_by_ids([
                RoleID(laid.roles[0].id),
                RoleID(laid.beyond_roles[0].id),
            ])


@dataclass(frozen=True)
class LoadingPermissions(When[RolesAndACaller, RBACAdapter, PermissionsLoaded]):
    @override
    def operation(self) -> str:
        return "batch_load_permissions_by_ids"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 권한 둘과 없는 id 하나를 한 번에 읽습니다",
            english=(
                f"{laid.caller.username} loads two permission rows and one missing id in one call"
            ),
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> PermissionsLoaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_permissions_by_ids([
                laid.permissions[0].id,
                laid.permissions[1].id,
                PermissionID(uuid4()),
            ])


@dataclass(frozen=True)
class LoadingPermissionsWithAnUnreadableOne(When[RolesAndACaller, RBACAdapter, PermissionsLoaded]):
    @override
    def operation(self) -> str:
        return "batch_load_permissions_by_ids"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 읽을 수 있는 권한 하나와 읽을 수 없는 권한 하나를 한 번에 읽습니다",
            english=(
                f"{laid.caller.username} loads one readable permission row and one unreadable "
                "permission row in one call"
            ),
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> PermissionsLoaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_permissions_by_ids([
                laid.permissions[0].id,
                laid.unreadable_permissions[0].id,
            ])


@dataclass(frozen=True)
class LoadingTheRolePermissions(When[RolesAndACaller, RBACAdapter, PermissionListsLoaded]):
    @override
    def operation(self) -> str:
        return "batch_load_permissions_by_role_ids"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.role.name} 이 가진 권한을 역할 id 로 한 번에 읽습니다",
            english=(
                f"{laid.caller.username} loads the permissions of {laid.role.name} by role id "
                "in one call"
            ),
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> PermissionListsLoaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_permissions_by_role_ids([RoleID(laid.role.id)])


@dataclass(frozen=True)
class LoadingTheRolePermissionsWithAnUnreadableRole(
    When[RolesAndACaller, RBACAdapter, PermissionListsLoaded]
):
    @override
    def operation(self) -> str:
        return "batch_load_permissions_by_role_ids"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 읽을 수 있는 역할과 읽을 수 없는 역할이 가진 권한을 "
            "역할 id 로 한 번에 읽습니다",
            english=(
                f"{laid.caller.username} loads the permissions of one readable role and one "
                "unreadable role by role id in one call"
            ),
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> PermissionListsLoaded:
        with ActingAs(laid.caller):
            return await adapter.batch_load_permissions_by_role_ids([
                RoleID(laid.roles[0].id),
                RoleID(laid.beyond_roles[0].id),
            ])


@dataclass(frozen=True)
class LoadingTheAssignments(When[RolesAndACaller, RBACAdapter, AssignmentsLoaded]):
    """배정 id 를 전역 검색으로 먼저 얻고, 그 id 들로 한 번에 읽는다."""

    @override
    def operation(self) -> str:
        return "batch_load_role_assignments_by_ids"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 미리 저장한 배정을 id 로 한 번에 읽습니다",
            english=(
                f"{laid.caller.username} loads the assignments seeded in advance by id in one call"
            ),
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> AssignmentsLoaded:
        with ActingAs(laid.caller):
            found = await adapter.admin_search_role_assignments(SearchRoleAssignmentsInput())
            ids = [node.id for node in found.items]
            ids.append(uuid4())
            return await adapter.batch_load_role_assignments_by_ids(ids)


@dataclass(frozen=True)
class TheTwoRolesAndAMiss(Then[RolesAndACaller, RolesLoaded]):
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 역할 둘은 노드로, 없는 id 자리는 빈 값으로 옵니다",
            english=(
                "the two roles seeded in advance come back as nodes and the missing id as an "
                "empty value"
            ),
        )

    @override
    def look(self, laid: RolesAndACaller, answered: Answered[RolesLoaded]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [Same("length", len(loaded), 3)]
        if len(loaded) != 3:
            return verdicts
        first, second, third = loaded
        look = RoleLook(self.started)
        if isinstance(first, RoleNode):
            verdicts += look.verdicts("[0].", first, laid.roles[0], laid.domain.id)
        else:
            verdicts.append(Same("[0]", type(first).__name__, "RoleNode"))
        if isinstance(second, RoleNode):
            verdicts += look.verdicts("[1].", second, laid.roles[1], laid.domain.id)
        else:
            verdicts.append(Same("[1]", type(second).__name__, "RoleNode"))
        verdicts.append(Same("[2]", third, None))
        return verdicts


@dataclass(frozen=True)
class TheReadableRoleAndAnEmptyOne(Then[RolesAndACaller, RolesLoaded]):
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "읽을 수 있는 역할은 노드로, 읽을 수 없는 역할 자리는 빈 값으로 옵니다",
            english=(
                "the readable role comes back as a node and the unreadable role as an empty value"
            ),
        )

    @override
    def look(self, laid: RolesAndACaller, answered: Answered[RolesLoaded]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [Same("length", len(loaded), 2)]
        if len(loaded) != 2:
            return verdicts
        first, second = loaded
        if isinstance(first, RoleNode):
            verdicts += RoleLook(self.started).verdicts(
                "[0].", first, laid.roles[0], laid.domain.id
            )
        else:
            verdicts.append(Same("[0]", type(first).__name__, "RoleNode"))
        verdicts.append(Same("[1]", second, None))
        return verdicts


@dataclass(frozen=True)
class TheTwoPermissionsAndAMiss(Then[RolesAndACaller, PermissionsLoaded]):
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 권한 둘은 노드로, 없는 id 자리는 빈 값으로 옵니다",
            english=(
                "the two permission rows seeded in advance come back as nodes and the missing id "
                "as an empty value"
            ),
        )

    @override
    def look(self, laid: RolesAndACaller, answered: Answered[PermissionsLoaded]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [Same("length", len(loaded), 3)]
        if len(loaded) != 3:
            return verdicts
        first, second, third = loaded
        look = PermissionLook(self.started)
        expected = laid.permissions
        if isinstance(first, PermissionNode):
            verdicts += look.verdicts(
                "[0].", first, laid.role, expected[0].entity_type, expected[0].permission
            )
        else:
            verdicts.append(Same("[0]", type(first).__name__, "PermissionNode"))
        if isinstance(second, PermissionNode):
            verdicts += look.verdicts(
                "[1].", second, laid.role, expected[1].entity_type, expected[1].permission
            )
        else:
            verdicts.append(Same("[1]", type(second).__name__, "PermissionNode"))
        verdicts.append(Same("[2]", third, None))
        return verdicts


@dataclass(frozen=True)
class TheReadablePermissionAndAnEmptyOne(Then[RolesAndACaller, PermissionsLoaded]):
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "읽을 수 있는 권한은 노드로, 읽을 수 없는 권한 자리는 빈 값으로 옵니다",
            english=(
                "the readable permission row comes back as a node and the unreadable row as an "
                "empty value"
            ),
        )

    @override
    def look(self, laid: RolesAndACaller, answered: Answered[PermissionsLoaded]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [Same("length", len(loaded), 2)]
        if len(loaded) != 2:
            return verdicts
        first, second = loaded
        one = laid.permissions[0]
        if isinstance(first, PermissionNode):
            verdicts += PermissionLook(self.started).verdicts(
                "[0].", first, laid.role, one.entity_type, one.permission
            )
        else:
            verdicts.append(Same("[0]", type(first).__name__, "PermissionNode"))
        verdicts.append(Same("[1]", second, None))
        return verdicts


@dataclass(frozen=True)
class ThePermissionsOfTheRole(Then[RolesAndACaller, PermissionListsLoaded]):
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "그 역할이 가진 권한이 역할 하나 몫으로 옵니다",
            english="the permissions that role holds come back as the one role's list",
        )

    @override
    def look(
        self, laid: RolesAndACaller, answered: Answered[PermissionListsLoaded]
    ) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [Same("length", len(loaded), 1)]
        if not loaded:
            return verdicts
        nodes = loaded[0]
        expected = sorted(
            laid.permissions,
            key=lambda one: (str(one.entity_type), PermissionBitDTO.of(one.permission)),
        )
        nodes = sorted(nodes, key=lambda node: (str(node.entity_type), node.permission))
        verdicts.append(Same("[0] length", len(nodes), len(expected)))
        look = PermissionLook(self.started)
        for i, (node, one) in enumerate(zip(nodes, expected, strict=False)):
            verdicts += look.verdicts(
                f"[0][{i}].", node, laid.role, one.entity_type, one.permission
            )
        return verdicts


@dataclass(frozen=True)
class TheLoadedAssignments(Then[RolesAndACaller, AssignmentsLoaded]):
    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 배정은 노드로, 없는 id 자리는 빈 값으로 옵니다",
            english=(
                "the assignments seeded in advance come back as nodes and the missing id as an "
                "empty value"
            ),
        )

    @override
    def look(self, laid: RolesAndACaller, answered: Answered[AssignmentsLoaded]) -> list[Verdict]:
        loaded = answered.response
        if loaded is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        verdicts: list[Verdict] = [Same("length", len(loaded), len(laid.assignees) + 1)]
        by_user = {user.id: user for user in laid.assignees}
        look = AssignmentLook(self.started)
        for i, node in enumerate(loaded[:-1]):
            if not isinstance(node, RoleAssignmentNode):
                verdicts.append(Same(f"[{i}]", type(node).__name__, "RoleAssignmentNode"))
                continue
            user = by_user.get(node.user_id)
            if user is None:
                verdicts.append(
                    Same(f"[{i}].user_id", str(node.user_id), "a user seeded in advance")
                )
                continue
            verdicts += look.verdicts(f"[{i}].", node, user.id, laid.role.id, None)
        verdicts.append(Same(f"[{len(laid.assignees)}]", loaded[-1], None))
        return verdicts


def _two(granted: bool, role: UserRole = UserRole.USER) -> RolesAndSomeone:
    return RolesAndSomeone(
        role=role,
        count=2,
        permissions=PERMISSIONS,
        assignees=2,
        assigned=2,
        grant=(Granted(RoleEntityType(), Permission.READ),) if granted else (),
    )


def _two_with_an_unreadable_one() -> RolesAndSomeone:
    return RolesAndSomeone(
        count=2,
        permissions=PERMISSIONS,
        grant=(Granted(RoleEntityType(), Permission.READ),),
        beyond=1,
        unreadable=PERMISSIONS,
    )


@dataclass(frozen=True)
class AUserGrantedRoleReadLoadsRoles(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, RolesLoaded]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-role-read-loads-two-roles-and-a-missing-id"

    @override
    def describe(self) -> str:
        return Says(
            "대상 도메인에서 역할 읽기 권한을 받은 사용자가 역할 둘과 없는 id 하나를 한 번에 "
            "읽으면, 역할 둘은 노드로, 없는 id 자리는 빈 값으로 옵니다",
            english=(
                "when a user granted role read permission in a domain loads two roles and one "
                "missing id in one call, the two roles come back as nodes and the missing id as "
                "an empty value"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return _two(True)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, RolesLoaded]:
        return LoadingRoles()

    @override
    def then(self) -> Then[RolesAndACaller, RolesLoaded]:
        return TheTwoRolesAndAMiss(started=self.started)


@dataclass(frozen=True)
class AUserGetsNothingForAnUnreadableRole(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, RolesLoaded]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-loads-an-unreadable-role-and-gets-an-empty-entry"

    @override
    def describe(self) -> str:
        return Says(
            "역할 읽기 권한을 받은 사용자가 읽을 수 있는 역할 하나와 읽을 권한이 없는 역할 하나를 "
            "한 번에 읽으면, 읽을 수 있는 역할만 노드로 오고 다른 자리는 빈 값으로 옵니다",
            english=(
                "when a user granted role read permission loads one readable role and one role "
                "it has no permission on in one call, only the readable role comes back as a node "
                "and the other entry comes back empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return _two_with_an_unreadable_one()

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, RolesLoaded]:
        return LoadingRolesWithAnUnreadableOne()

    @override
    def then(self) -> Then[RolesAndACaller, RolesLoaded]:
        return TheReadableRoleAndAnEmptyOne(started=self.started)


@dataclass(frozen=True)
class AUserGrantedRoleReadLoadsPermissions(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, PermissionsLoaded]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-role-read-loads-two-permissions-and-a-missing-id"

    @override
    def describe(self) -> str:
        return Says(
            "대상 도메인에서 역할 읽기 권한을 받은 사용자가 권한 둘과 없는 id 하나를 한 번에 "
            "읽으면, 권한 둘은 노드로, 없는 id 자리는 빈 값으로 옵니다",
            english=(
                "when a user granted role read permission in a domain loads two permission rows "
                "and one missing id in one call, the two rows come back as nodes and the missing "
                "id as an empty value"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return _two(True)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, PermissionsLoaded]:
        return LoadingPermissions()

    @override
    def then(self) -> Then[RolesAndACaller, PermissionsLoaded]:
        return TheTwoPermissionsAndAMiss(started=self.started)


@dataclass(frozen=True)
class AUserGetsNothingForAnUnreadablePermission(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, PermissionsLoaded]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-loads-an-unreadable-permission-and-gets-an-empty-entry"

    @override
    def describe(self) -> str:
        return Says(
            "역할 읽기 권한을 받은 사용자가 읽을 수 있는 권한 하나와 읽을 권한이 없는 권한 하나를 "
            "한 번에 읽으면, 읽을 수 있는 권한만 노드로 오고 다른 자리는 빈 값으로 옵니다",
            english=(
                "when a user granted role read permission loads one readable permission row and "
                "one row it has no permission on in one call, only the readable row comes back as "
                "a node and the other entry comes back empty"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return _two_with_an_unreadable_one()

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, PermissionsLoaded]:
        return LoadingPermissionsWithAnUnreadableOne()

    @override
    def then(self) -> Then[RolesAndACaller, PermissionsLoaded]:
        return TheReadablePermissionAndAnEmptyOne(started=self.started)


@dataclass(frozen=True)
class AUserGrantedRoleReadLoadsTheRolePermissions(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, PermissionListsLoaded]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-role-read-loads-the-permissions-of-a-role"

    @override
    def describe(self) -> str:
        return Says(
            "대상 도메인에서 역할 읽기 권한을 받은 사용자가 역할 id 로 권한을 한 번에 읽으면, "
            "그 역할이 가진 권한이 옵니다",
            english=(
                "when a user granted role read permission in a domain loads permissions by role "
                "id, the permissions that role holds come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return _two(True)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, PermissionListsLoaded]:
        return LoadingTheRolePermissions()

    @override
    def then(self) -> Then[RolesAndACaller, PermissionListsLoaded]:
        return ThePermissionsOfTheRole(started=self.started)


@dataclass(frozen=True)
class AUserMayNotLoadThePermissionsOfAnUnreadableRole(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, PermissionListsLoaded]
):
    @override
    def summary(self) -> str:
        return "a-user-may-not-load-the-permissions-of-an-unreadable-role-by-role-id"

    @override
    def describe(self) -> str:
        return Says(
            "역할 읽기 권한을 받은 사용자가 읽을 권한이 없는 역할을 하나 함께 넣어 역할 id 로 "
            "권한을 한 번에 읽으면, 호출 전체가 거부됩니다",
            english=(
                "when a user granted role read permission adds one role it has no permission on "
                "and loads permissions by role id, the whole call is refused"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return _two_with_an_unreadable_one()

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, PermissionListsLoaded]:
        return LoadingTheRolePermissionsWithAnUnreadableRole()

    @override
    def then(self) -> Then[RolesAndACaller, PermissionListsLoaded]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminLoadsAssignments(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, AssignmentsLoaded]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-loads-the-assignments-by-id"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 미리 저장한 배정과 없는 id 하나를 한 번에 읽으면, 배정은 노드로, "
            "없는 id 자리는 빈 값으로 옵니다. 배정 id 를 얻는 전역 검색을 전역 역할이 막으므로 "
            "superadmin 이 부릅니다. 읽기 자체는 인증만 거칩니다",
            english=(
                "when the superadmin loads the assignments seeded in advance and one missing id "
                "in one call, the assignments come back as nodes and the missing id as an empty "
                "value. The global role gates the search that collects the assignment ids, so the "
                "superadmin calls it. The load itself needs authentication only"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return _two(False, UserRole.SUPERADMIN)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, AssignmentsLoaded]:
        return LoadingTheAssignments()

    @override
    def then(self) -> Then[RolesAndACaller, AssignmentsLoaded]:
        return TheLoadedAssignments(started=self.started)


SCENARIOS: list[LoadStep] = [
    AUserGrantedRoleReadLoadsRoles(started=datetime.now(UTC)),
    AUserGetsNothingForAnUnreadableRole(started=datetime.now(UTC)),
    AUserGrantedRoleReadLoadsPermissions(started=datetime.now(UTC)),
    AUserGetsNothingForAnUnreadablePermission(started=datetime.now(UTC)),
    AUserGrantedRoleReadLoadsTheRolePermissions(started=datetime.now(UTC)),
    AUserMayNotLoadThePermissionsOfAnUnreadableRole(),
    TheSuperadminLoadsAssignments(started=datetime.now(UTC)),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_loading(
    scenario: LoadStep, adapter: RBACAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
