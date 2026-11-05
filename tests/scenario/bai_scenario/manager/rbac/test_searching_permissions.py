"""권한 검색 — 전역, 역할 하나가 가진 권한."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.rbac.request import AdminSearchPermissionsGQLInput
from ai.backend.common.dto.manager.v2.rbac.response import PermissionNode
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO
from ai.backend.manager.api.adapters.rbac.adapter import RBACAdapter
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.errors.auth import InsufficientPrivilege
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
    Granted,
    PermissionLook,
    RolesAndACaller,
    RolesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type PermissionPage = SearchResult[PermissionNode]
type PermissionStep = Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, PermissionPage]

SESSION_READ = Granted(SessionEntityType(), Permission.READ)
VFOLDER_UPDATE = Granted(VFolderEntityType(), Permission.UPDATE)


def _expected(laid: RolesAndACaller) -> list[PermissionData]:
    """미리 저장한 권한 행을 실은 값 순으로 돌려준다."""
    return sorted(
        laid.permissions,
        key=lambda one: (str(one.entity_type), PermissionBitDTO.of(one.permission)),
    )


def _checked(started: datetime, laid: RolesAndACaller, page: PermissionPage) -> list[Verdict]:
    expected = _expected(laid)
    verdicts: list[Verdict] = [
        Same("items count", len(page.items), len(expected)),
        Same("total_count", page.total_count, len(expected)),
        Same("has_next_page", page.has_next_page, False),
        Same("has_previous_page", page.has_previous_page, False),
    ]
    nodes = sorted(page.items, key=lambda node: (str(node.entity_type), node.permission))
    look = PermissionLook(started)
    for i, (node, data) in enumerate(zip(nodes, expected, strict=False)):
        verdicts += look.verdicts(
            f"items[{i}].", node, laid.role, data.entity_type, data.permission
        )
    return verdicts


@dataclass(frozen=True)
class SearchingEveryPermission(When[RolesAndACaller, RBACAdapter, PermissionPage]):
    @override
    def operation(self) -> str:
        return "admin_search_permissions_gql"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 모든 권한을 검색합니다",
            english=f"{laid.caller.username} searches every permission",
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> PermissionPage:
        with ActingAs(laid.caller):
            return await adapter.admin_search_permissions_gql(AdminSearchPermissionsGQLInput())


@dataclass(frozen=True)
class SearchingTheRolePermissions(When[RolesAndACaller, RBACAdapter, PermissionPage]):
    @override
    def operation(self) -> str:
        return "search_role_permissions"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.role.name} 이 가진 권한을 검색합니다",
            english=f"{laid.caller.username} searches the permissions {laid.role.name} holds",
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> PermissionPage:
        with ActingAs(laid.caller):
            return await adapter.search_role_permissions(
                laid.role.id, AdminSearchPermissionsGQLInput()
            )


@dataclass(frozen=True)
class TheSeededPermissions(Then[RolesAndACaller, PermissionPage]):
    """미리 저장한 권한 행이 모두 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 권한 행이 모두 옵니다",
            english="every permission row seeded in advance comes back",
        )

    @override
    def look(self, laid: RolesAndACaller, answered: Answered[PermissionPage]) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(InsufficientPrivilege, answered.raised)]
        return _checked(self.started, laid, page)


@dataclass(frozen=True)
class TheRolePermissions(Then[RolesAndACaller, PermissionPage]):
    """그 역할이 가진 권한 행이 모두 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "그 역할이 가진 권한 행이 모두 옵니다",
            english="every permission row that role holds comes back",
        )

    @override
    def look(self, laid: RolesAndACaller, answered: Answered[PermissionPage]) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return _checked(self.started, laid, page)


@dataclass(frozen=True)
class TheSuperadminSearchesEveryPermission(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, PermissionPage]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-searches-every-permission"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 모든 권한을 검색하면, 미리 저장한 권한 행이 모두 옵니다",
            english=(
                "when the superadmin searches every permission, every permission row seeded in "
                "advance comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(role=UserRole.SUPERADMIN, permissions=(SESSION_READ, VFOLDER_UPDATE))

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, PermissionPage]:
        return SearchingEveryPermission()

    @override
    def then(self) -> Then[RolesAndACaller, PermissionPage]:
        return TheSeededPermissions(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearchEveryPermission(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, PermissionPage]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-every-permission"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자는 모든 권한을 검색할 수 없습니다",
            english="a user granted nothing cannot search every permission",
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(permissions=(SESSION_READ,))

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, PermissionPage]:
        return SearchingEveryPermission()

    @override
    def then(self) -> Then[RolesAndACaller, PermissionPage]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class AUserGrantedRoleReadSearchesItsPermissions(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, PermissionPage]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-role-read-searches-the-permissions-of-a-role"

    @override
    def describe(self) -> str:
        return Says(
            "대상 도메인에서 역할 읽기 권한을 받은 사용자가 역할이 가진 권한을 검색하면, "
            "그 역할의 권한 행이 모두 옵니다",
            english=(
                "when a user granted role read permission in a domain searches the permissions "
                "a role holds, every permission row of that role comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(
            permissions=(SESSION_READ, VFOLDER_UPDATE),
            grant=(Granted(RoleEntityType(), Permission.READ),),
        )

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, PermissionPage]:
        return SearchingTheRolePermissions()

    @override
    def then(self) -> Then[RolesAndACaller, PermissionPage]:
        return TheRolePermissions(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearchRolePermissions(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, PermissionPage]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-the-permissions-of-a-role"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자는 역할이 가진 권한을 검색할 수 없습니다",
            english="a user granted nothing cannot search the permissions a role holds",
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(permissions=(SESSION_READ,))

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, PermissionPage]:
        return SearchingTheRolePermissions()

    @override
    def then(self) -> Then[RolesAndACaller, PermissionPage]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[PermissionStep] = [
    TheSuperadminSearchesEveryPermission(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotSearchEveryPermission(),
    AUserGrantedRoleReadSearchesItsPermissions(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotSearchRolePermissions(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching_permissions(
    scenario: PermissionStep, adapter: RBACAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
