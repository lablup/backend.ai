"""도메인 search — 딸린 프로젝트와 사용자로 거르고, 그 이름으로 세우기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.domain.request import (
    AdminSearchDomainsInput,
    DomainFilter,
    DomainOrder,
)
from ai.backend.common.dto.manager.v2.domain.response import AdminSearchDomainsPayload
from ai.backend.common.dto.manager.v2.domain.types import (
    DomainOrderField,
    DomainUserFilter,
    OrderDirection,
)
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.user.types import UserData, UserStatus
from ai.backend.manager.errors.auth import InsufficientPrivilege
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
from bai_scenario.components.domain import WAS_HERE, SomeoneOf
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.domain.domain import TestSeedDomain
from bai_scenario.seeds.project.project import TestSeedProject
from bai_scenario.seeds.resource_policy.keypair import TestSeedKeypairPolicy
from bai_scenario.seeds.resource_policy.project import TestSeedProjectPolicy
from bai_scenario.seeds.resource_policy.user import TestSeedUserPolicy
from bai_scenario.seeds.seeder import Laid, TestSeeder, TestSeedNest
from bai_scenario.seeds.user.user import TestSeedUserOf

type Searched = AdminSearchDomainsPayload


@dataclass(frozen=True)
class ThreeDomainsAndTheirRows:
    """딸린 행으로 거르고 세울 도메인 셋과, 그리고 훑을 사람."""

    first: DomainData
    second: DomainData
    third: DomainData
    caller: UserData


@dataclass(frozen=True)
class ThreeDomainsWithProjectsAndUsers(Given[Any, ThreeDomainsAndTheirRows]):
    """도메인 셋. 첫째와 둘째는 이름이 다른 프로젝트 하나와 활성 사용자 하나를 갖고,
    셋째는 비활성 사용자 하나만 갖는다. 첫째에는 superadmin 이 한 명 더 산다.
    """

    @override
    def describe(self) -> str:
        return Says(
            "도메인 셋, 첫째와 둘째는 이름이 다른 프로젝트 하나와 활성 사용자 하나를, "
            "셋째는 비활성 사용자 하나를 갖고, 첫째에 superadmin 이 한 명 더 있습니다",
            english=(
                "three domains: the first and second hold one project of a different name "
                "and one active user, the third holds one inactive user, and the first "
                "holds one more superadmin"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> ThreeDomainsAndTheirRows:
        projects = await seeding.once(TestSeedProjectPolicy())
        first = await seeding.creating(TestSeedDomain(name_hint="first", description=WAS_HERE))
        second = await seeding.creating(TestSeedDomain(name_hint="second", description=WAS_HERE))
        third = await seeding.creating(TestSeedDomain(name_hint="third", description=WAS_HERE))
        await seeding.creating_from_two(TestSeedProject(name_hint="alpha-team"), first, projects)
        await seeding.creating_from_two(TestSeedProject(name_hint="beta-team"), second, projects)
        await seeding.within(SomeoneOf(first))
        await seeding.within(SomeoneOf(second))
        await seeding.within(AnInactiveUserOf(third))
        caller = await seeding.within(SomeoneOf(first, role=UserRole.SUPERADMIN))
        return ThreeDomainsAndTheirRows(
            seeding.made(first),
            seeding.made(second),
            seeding.made(third),
            seeding.made(caller),
        )


@dataclass(frozen=True)
class AnInactiveUserOf(TestSeedNest[Laid[UserData]]):
    """그 도메인에 사는 비활성 사용자 한 명. 매니저가 사용자를 만드는 경로를 그대로 탄다."""

    domain: Laid[DomainData]

    @override
    def kind(self) -> str:
        return Says(
            "도메인에 속한 비활성 사용자 한 명 준비",
            english="Prepare one inactive user in the domain",
        )

    @override
    def lay(self, seed: TestSeeder) -> Laid[UserData]:
        seed.once(TestSeedProjectPolicy())
        policy = seed.creating(TestSeedUserPolicy())
        key_policy = seed.creating(TestSeedKeypairPolicy())
        return seed.provisioning(
            TestSeedUserOf(is_active=False, status=UserStatus.INACTIVE),
            self.domain,
            policy,
            key_policy,
        )


@dataclass(frozen=True)
class FilteringActiveUsersAndOrderingByProjectName(
    When[ThreeDomainsAndTheirRows, DomainAdapter, Searched]
):
    """활성 사용자가 사는 도메인을 프로젝트 이름순으로 세우고 첫 쪽 하나만 가져온다."""

    @override
    def operation(self) -> str:
        return "global_search"

    @override
    def describe(self, laid: ThreeDomainsAndTheirRows) -> str:
        return Says(
            f"{laid.caller.username}이 활성 사용자가 사는 도메인을 프로젝트 이름순으로 세워 "
            "첫 쪽 하나만 조회합니다",
            english=(
                f"{laid.caller.username} searches the domains holding an active user, "
                "ordered by project name, taking only the first page"
            ),
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: ThreeDomainsAndTheirRows) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.global_search(
                AdminSearchDomainsInput(
                    filter=DomainFilter(user=DomainUserFilter(is_active=True)),
                    order=[
                        DomainOrder(
                            field=DomainOrderField.PROJECT_NAME, direction=OrderDirection.ASC
                        )
                    ],
                    limit=1,
                )
            )


@dataclass(frozen=True)
class TheFirstInOrderIsLeft(Then[ThreeDomainsAndTheirRows, Searched]):
    """프로젝트 이름이 앞서는 첫째 하나만 오고, 활성 사용자가 없는 셋째는 빠진다."""

    @override
    def says(self) -> str:
        return Says(
            "프로젝트 이름이 앞서는 첫째 도메인 하나만 오고, 활성 사용자가 없는 셋째는 빠집니다",
            english=(
                "only the first domain, whose project name comes first, comes back, and the "
                "third domain holding no active user is left out"
            ),
        )

    @override
    def look(self, laid: ThreeDomainsAndTheirRows, answered: Answered[Searched]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(InsufficientPrivilege, answered.raised)]
        return [
            Same("items", [one.basic_info.name for one in payload.items], [laid.first.name]),
            Same("total_count", payload.total_count, 2),
            Same("has_next_page", payload.has_next_page, True),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class AFilterOnNestedFieldsNarrowsAndOrders(
    Scenario[TestSeedingSession, ThreeDomainsAndTheirRows, DomainAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-nested-user-filter-and-project-name-order-narrow-the-first-page"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 활성 사용자가 사는 도메인을 프로젝트 이름순으로 세워 첫 쪽 하나만 "
            "조회하면, 이름이 앞서는 첫째 도메인 하나와 나머지 수가 오고, 활성 사용자가 없는 "
            "셋째는 빠집니다. 전역 역할이 superadmin 만 통과시킵니다",
            english=(
                "when the superadmin, the only caller the global role admits, searches the "
                "domains holding an active user ordered by project name and takes only the "
                "first page, the first domain alone comes back with the remaining count and "
                "the third domain holding no active user is left out"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ThreeDomainsAndTheirRows]:
        return ThreeDomainsWithProjectsAndUsers()

    @override
    def when(self) -> When[ThreeDomainsAndTheirRows, DomainAdapter, Searched]:
        return FilteringActiveUsersAndOrderingByProjectName()

    @override
    def then(self) -> Then[ThreeDomainsAndTheirRows, Searched]:
        return TheFirstInOrderIsLeft()


SCENARIOS: list[Scenario[TestSeedingSession, ThreeDomainsAndTheirRows, DomainAdapter, Searched]] = [
    AFilterOnNestedFieldsNarrowsAndOrders(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_nested_searching(
    scenario: Scenario[TestSeedingSession, ThreeDomainsAndTheirRows, DomainAdapter, Searched],
    adapter: DomainAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
