"""역할 배정 검색 — 전역, 내 배정, 역할 하나의 배정."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.entity.role import RoleEntityType, RoleID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.rbac.request import SearchRoleAssignmentsInput
from ai.backend.common.dto.manager.v2.rbac.response import RoleAssignmentNode
from ai.backend.manager.api.adapters.rbac.adapter import RBACAdapter
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.rbac_models.user_role.scopes import RoleRoleAssignmentTarget
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
    RolesAndACaller,
    RolesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type AssignmentPage = SearchResult[RoleAssignmentNode]
type AssignmentStep = Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, AssignmentPage]


def _in_seeded_order(
    laid: RolesAndACaller, nodes: list[RoleAssignmentNode]
) -> list[RoleAssignmentNode]:
    order = {user.id: index for index, user in enumerate(laid.assignees)}
    return sorted(nodes, key=lambda node: order.get(node.user_id, len(order)))


def _checked_assignees(
    started: datetime, laid: RolesAndACaller, page: AssignmentPage
) -> list[Verdict]:
    verdicts: list[Verdict] = [
        Same("items count", len(page.items), len(laid.assignees)),
        Same("total_count", page.total_count, len(laid.assignees)),
        Same("has_next_page", page.has_next_page, False),
        Same("has_previous_page", page.has_previous_page, False),
    ]
    look = AssignmentLook(started)
    for i, (node, user) in enumerate(
        zip(_in_seeded_order(laid, page.items), laid.assignees, strict=False)
    ):
        verdicts += look.verdicts(f"items[{i}].", node, user.id, laid.role.id, None)
    return verdicts


@dataclass(frozen=True)
class SearchingEveryAssignment(When[RolesAndACaller, RBACAdapter, AssignmentPage]):
    @override
    def operation(self) -> str:
        return "admin_search_role_assignments"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 모든 역할 배정을 검색합니다",
            english=f"{laid.caller.username} searches every role assignment",
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> AssignmentPage:
        with ActingAs(laid.caller):
            return await adapter.admin_search_role_assignments(SearchRoleAssignmentsInput())


@dataclass(frozen=True)
class SearchingMyAssignments(When[RolesAndACaller, RBACAdapter, AssignmentPage]):
    @override
    def operation(self) -> str:
        return "my_search_role_assignments"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 자기의 역할 배정을 검색합니다",
            english=f"{laid.caller.username} searches their own role assignments",
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> AssignmentPage:
        with ActingAs(laid.caller):
            return await adapter.my_search_role_assignments(SearchRoleAssignmentsInput())


@dataclass(frozen=True)
class SearchingTheAssignmentsOfTheRole(When[RolesAndACaller, RBACAdapter, AssignmentPage]):
    @override
    def operation(self) -> str:
        return "search_role_assignments_in_scope"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.role.name} 의 역할 배정을 검색합니다",
            english=f"{laid.caller.username} searches the assignments of {laid.role.name}",
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> AssignmentPage:
        with ActingAs(laid.caller):
            return await adapter.search_role_assignments_in_scope(
                [RoleRoleAssignmentTarget(role_id=RoleID(laid.role.id))],
                SearchRoleAssignmentsInput(),
            )


@dataclass(frozen=True)
class EveryAssignmentOfTheRole(Then[RolesAndACaller, AssignmentPage]):
    """미리 저장한 사람들이 그 역할을 받은 배정이 모두 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 사람들의 역할 배정이 모두 옵니다",
            english="the assignment of every user seeded in advance comes back",
        )

    @override
    def look(self, laid: RolesAndACaller, answered: Answered[AssignmentPage]) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(InsufficientPrivilege, answered.raised)]
        return _checked_assignees(self.started, laid, page)


@dataclass(frozen=True)
class TheAssignmentsOfTheRole(Then[RolesAndACaller, AssignmentPage]):
    """그 역할을 받은 사람들의 배정이 모두 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "그 역할을 받은 사람들의 배정이 모두 옵니다",
            english="the assignment of every user holding that role comes back",
        )

    @override
    def look(self, laid: RolesAndACaller, answered: Answered[AssignmentPage]) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        return _checked_assignees(self.started, laid, page)


@dataclass(frozen=True)
class TheAssignmentIHold(Then[RolesAndACaller, AssignmentPage]):
    """호출자가 가진 역할의 배정 하나가 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "호출자가 가진 역할의 배정 하나가 옵니다",
            english="the one assignment of the role the caller holds comes back",
        )

    @override
    def look(self, laid: RolesAndACaller, answered: Answered[AssignmentPage]) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(NotEnoughPermission, answered.raised)]
        if laid.self_role is None:
            raise AssertionError("this row needs the role the caller holds")
        verdicts: list[Verdict] = [
            Same("items count", len(page.items), 1),
            Same("total_count", page.total_count, 1),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]
        if page.items:
            verdicts += AssignmentLook(self.started).verdicts(
                "items[0].", page.items[0], laid.caller.id, laid.self_role.id, None
            )
        return verdicts


@dataclass(frozen=True)
class TheSuperadminSearchesEveryAssignment(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, AssignmentPage]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-searches-every-role-assignment"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 모든 역할 배정을 검색하면, 미리 저장한 사람들의 배정이 모두 옵니다",
            english=(
                "when the superadmin searches every role assignment, the assignment of every "
                "user seeded in advance comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(role=UserRole.SUPERADMIN, assignees=2, assigned=2)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, AssignmentPage]:
        return SearchingEveryAssignment()

    @override
    def then(self) -> Then[RolesAndACaller, AssignmentPage]:
        return EveryAssignmentOfTheRole(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearchEveryAssignment(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, AssignmentPage]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-every-role-assignment"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자는 모든 역할 배정을 검색할 수 없습니다",
            english="a user granted nothing cannot search every role assignment",
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(assignees=1, assigned=1)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, AssignmentPage]:
        return SearchingEveryAssignment()

    @override
    def then(self) -> Then[RolesAndACaller, AssignmentPage]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class AUserHoldingARoleSearchesItsAssignment(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, AssignmentPage]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-holding-a-role-searches-their-assignment"

    @override
    def describe(self) -> str:
        return Says(
            "자기 스코프의 역할 읽기 권한을 가진 역할을 가진 사용자가 자기의 역할 배정을 "
            "검색하면, 그 배정이 옵니다",
            english=(
                "when a user holding a role with role read permission in their own scope "
                "searches their own role assignments, that assignment comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(self_grant=(Permission.READ,))

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, AssignmentPage]:
        return SearchingMyAssignments()

    @override
    def then(self) -> Then[RolesAndACaller, AssignmentPage]:
        return TheAssignmentIHold(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearchTheirAssignment(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, AssignmentPage]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-their-role-assignment"

    @override
    def describe(self) -> str:
        return Says(
            "아무 역할도 가진 것이 없는 사용자는 자기의 역할 배정을 검색할 수 없습니다",
            english="a user holding no role cannot search their own role assignments",
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone()

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, AssignmentPage]:
        return SearchingMyAssignments()

    @override
    def then(self) -> Then[RolesAndACaller, AssignmentPage]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedRoleReadSearchesTheAssignmentsOfARole(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, AssignmentPage]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-role-read-searches-the-assignments-of-a-role"

    @override
    def describe(self) -> str:
        return Says(
            "대상 도메인에서 역할 읽기 권한을 받은 사용자가 역할 하나의 배정을 검색하면, "
            "그 역할을 받은 사람들의 배정이 모두 옵니다",
            english=(
                "when a user granted role read permission in a domain searches the assignments "
                "of one role, the assignment of every user holding it comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(
            assignees=2,
            assigned=2,
            grant=(Granted(RoleEntityType(), Permission.READ),),
        )

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, AssignmentPage]:
        return SearchingTheAssignmentsOfTheRole()

    @override
    def then(self) -> Then[RolesAndACaller, AssignmentPage]:
        return TheAssignmentsOfTheRole(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearchTheAssignmentsOfARole(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, AssignmentPage]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-the-assignments-of-a-role"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자는 역할 하나의 배정을 검색할 수 없습니다",
            english="a user granted nothing cannot search the assignments of a role",
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(assignees=1, assigned=1)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, AssignmentPage]:
        return SearchingTheAssignmentsOfTheRole()

    @override
    def then(self) -> Then[RolesAndACaller, AssignmentPage]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[AssignmentStep] = [
    TheSuperadminSearchesEveryAssignment(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotSearchEveryAssignment(),
    AUserHoldingARoleSearchesItsAssignment(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotSearchTheirAssignment(),
    AUserGrantedRoleReadSearchesTheAssignmentsOfARole(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotSearchTheAssignmentsOfARole(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching_assignments(
    scenario: AssignmentStep, adapter: RBACAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
