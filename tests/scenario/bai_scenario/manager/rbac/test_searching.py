"""역할 검색 — 전역, 내가 가진 역할, 스코프."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.entity.user import UserEntityType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.rbac.request import SearchRolesInput
from ai.backend.common.dto.manager.v2.rbac.response import RoleNode
from ai.backend.manager.api.adapters.rbac.adapter import RBACAdapter
from ai.backend.manager.data.common.types import SearchResult
from ai.backend.manager.data.permission.role import RoleData
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.rbac_models.role.scopes import ScopedRoleTarget
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
    RoleLook,
    RolesAndACaller,
    RolesAndSomeone,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type RolePage = SearchResult[RoleNode]
type RoleStep = Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, RolePage]


def _by_name(roles: list[RoleData]) -> list[RoleData]:
    return sorted(roles, key=lambda role: role.name)


def _checked(
    started: datetime, laid: RolesAndACaller, page: RolePage, roles: list[RoleData]
) -> list[Verdict]:
    expected = _by_name(roles)
    verdicts: list[Verdict] = [
        Same("items count", len(page.items), len(expected)),
        Same("total_count", page.total_count, len(expected)),
        Same("has_next_page", page.has_next_page, False),
        Same("has_previous_page", page.has_previous_page, False),
    ]
    look = RoleLook(started)
    for i, (node, role) in enumerate(
        zip(sorted(page.items, key=lambda n: n.name), expected, strict=False)
    ):
        verdicts += look.verdicts(f"items[{i}].", node, role, laid.domain.id)
    return verdicts


@dataclass(frozen=True)
class SearchingEveryRole(When[RolesAndACaller, RBACAdapter, RolePage]):
    """전역에서 역할을 검색한다."""

    @override
    def operation(self) -> str:
        return "admin_search_roles_gql"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 모든 역할을 검색합니다",
            english=f"{laid.caller.username} searches every role",
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> RolePage:
        with ActingAs(laid.caller):
            return await adapter.admin_search_roles_gql(SearchRolesInput())


@dataclass(frozen=True)
class SearchingTheRolesIHold(When[RolesAndACaller, RBACAdapter, RolePage]):
    """호출자가 가진 역할을 검색한다."""

    @override
    def operation(self) -> str:
        return "my_search_roles"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 자기가 가진 역할을 검색합니다",
            english=f"{laid.caller.username} searches the roles they hold",
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> RolePage:
        with ActingAs(laid.caller):
            return await adapter.my_search_roles(SearchRolesInput())


@dataclass(frozen=True)
class SearchingTheDomain(When[RolesAndACaller, RBACAdapter, RolePage]):
    """대상 도메인의 역할을 검색한다."""

    @override
    def operation(self) -> str:
        return "search_roles_in_scope"

    @override
    def describe(self, laid: RolesAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 도메인 {laid.domain.name} 의 역할을 검색합니다",
            english=f"{laid.caller.username} searches the roles of domain {laid.domain.name}",
        )

    @override
    async def call(self, adapter: RBACAdapter, laid: RolesAndACaller) -> RolePage:
        with ActingAs(laid.caller):
            return await adapter.search_roles_in_scope(
                [ScopedRoleTarget(scope=DomainID(laid.domain.id))], SearchRolesInput()
            )


@dataclass(frozen=True)
class EveryRoleInNameOrder(Then[RolesAndACaller, RolePage]):
    """미리 저장한 역할이 이름 순으로 모두 온다."""

    started: datetime
    with_grant: bool = False

    @override
    def says(self) -> str:
        return Says(
            "미리 저장한 역할이 이름 순으로 모두 옵니다",
            english="every role seeded in advance comes back in name order",
        )

    @override
    def look(self, laid: RolesAndACaller, answered: Answered[RolePage]) -> list[Verdict]:
        page = answered.response
        if page is None:
            return [Refused(InsufficientPrivilege, answered.raised)]
        roles = list(laid.roles)
        if self.with_grant and laid.grant_role is not None:
            roles.append(laid.grant_role)
        return _checked(self.started, laid, page, roles)


@dataclass(frozen=True)
class TheRoleIHold(Then[RolesAndACaller, RolePage]):
    """호출자가 가진 역할 하나가 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return Says(
            "호출자가 가진 역할 하나가 옵니다",
            english="the one role the caller holds comes back",
        )

    @override
    def look(self, laid: RolesAndACaller, answered: Answered[RolePage]) -> list[Verdict]:
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
            verdicts += RoleLook(self.started, scope_type=UserEntityType()).verdicts(
                "items[0].",
                page.items[0],
                laid.self_role,
                laid.caller.id,
                Says("호출자의 id", english="the id of the caller"),
            )
        return verdicts


@dataclass(frozen=True)
class TheSuperadminSearchesEveryRole(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, RolePage]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-searches-every-role"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 모든 역할을 검색하면, 미리 저장한 역할이 이름 순으로 모두 옵니다",
            english=(
                "when the superadmin searches every role, every role seeded in advance comes "
                "back in name order"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(role=UserRole.SUPERADMIN, count=2)

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, RolePage]:
        return SearchingEveryRole()

    @override
    def then(self) -> Then[RolesAndACaller, RolePage]:
        return EveryRoleInNameOrder(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearchEveryRole(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, RolePage]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-every-role"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자는 모든 역할을 검색할 수 없습니다",
            english="a user granted nothing cannot search every role",
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone()

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, RolePage]:
        return SearchingEveryRole()

    @override
    def then(self) -> Then[RolesAndACaller, RolePage]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class AUserHoldingARoleSearchesIt(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, RolePage]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-holding-a-role-searches-it"

    @override
    def describe(self) -> str:
        return Says(
            "자기 스코프의 역할 읽기 권한을 가진 역할을 가진 사용자가 가진 역할을 검색하면, "
            "그 역할이 옵니다",
            english=(
                "when a user holding a role with role read permission in their own scope "
                "searches the roles they hold, that role comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(self_grant=(Permission.READ,))

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, RolePage]:
        return SearchingTheRolesIHold()

    @override
    def then(self) -> Then[RolesAndACaller, RolePage]:
        return TheRoleIHold(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearchTheirRoles(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, RolePage]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-their-roles"

    @override
    def describe(self) -> str:
        return Says(
            "아무 역할도 가진 것이 없는 사용자는 자기가 가진 역할을 검색할 수 없습니다",
            english="a user holding no role cannot search the roles they hold",
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone()

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, RolePage]:
        return SearchingTheRolesIHold()

    @override
    def then(self) -> Then[RolesAndACaller, RolePage]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedRoleReadSearchesADomain(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, RolePage]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-user-granted-role-read-searches-a-domain"

    @override
    def describe(self) -> str:
        return Says(
            "대상 도메인에서 역할 읽기 권한을 받은 사용자가 그 도메인의 역할을 검색하면, "
            "그 도메인의 역할이 모두 옵니다",
            english=(
                "when a user granted role read permission in a domain searches the roles of that "
                "domain, every role of that domain comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone(count=2, grant=(Granted(RoleEntityType(), Permission.READ),))

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, RolePage]:
        return SearchingTheDomain()

    @override
    def then(self) -> Then[RolesAndACaller, RolePage]:
        return EveryRoleInNameOrder(started=self.started, with_grant=True)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearchADomain(
    Scenario[TestSeedingSession, RolesAndACaller, RBACAdapter, RolePage]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-a-domain"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자는 도메인의 역할을 검색할 수 없습니다",
            english="a user granted nothing cannot search the roles of a domain",
        )

    @override
    def given(self) -> Given[TestSeedingSession, RolesAndACaller]:
        return RolesAndSomeone()

    @override
    def when(self) -> When[RolesAndACaller, RBACAdapter, RolePage]:
        return SearchingTheDomain()

    @override
    def then(self) -> Then[RolesAndACaller, RolePage]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[RoleStep] = [
    TheSuperadminSearchesEveryRole(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotSearchEveryRole(),
    AUserHoldingARoleSearchesIt(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotSearchTheirRoles(),
    AUserGrantedRoleReadSearchesADomain(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotSearchADomain(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: RoleStep, adapter: RBACAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
