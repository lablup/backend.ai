"""도메인 search — 딸린 프로젝트와 사용자로 거르고, 그 이름으로 세우기."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.domain.request import (
    AdminSearchDomainsInput,
    DomainFilter,
    DomainOrder,
)
from ai.backend.common.dto.manager.v2.domain.response import AdminSearchDomainsPayload
from ai.backend.common.dto.manager.v2.domain.types import (
    DomainOrderField,
    DomainProjectFilter,
    DomainUserFilter,
    OrderDirection,
)
from ai.backend.manager.api.adapters.domain.adapter import DomainAdapter
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.data.project.types import ProjectData
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
class TwoDomainsAndTheirRows:
    """딸린 행으로 거를 도메인 둘과 그 행들, 그리고 훑을 사람."""

    first: DomainData
    second: DomainData
    first_project: ProjectData
    second_project: ProjectData
    first_user: UserData
    second_user: UserData
    caller: UserData


@dataclass(frozen=True)
class TwoDomainsWithProjectsAndUsers(Given[Any, TwoDomainsAndTheirRows]):
    """도메인 둘, 각각 이름이 다른 프로젝트 하나와 사용자 하나.

    첫째 도메인에는 superadmin 이 한 명 더 산다. ``second_user_inactive``면 둘째
    도메인의 사용자는 비활성 상태다.
    """

    second_user_inactive: bool = False

    @override
    def describe(self) -> str:
        if self.second_user_inactive:
            return Says(
                "도메인 둘, 각각 이름이 다른 프로젝트 하나와 사용자 하나, 둘째 도메인의 사용자는 "
                "비활성 상태이고 첫째 도메인에 superadmin 이 한 명 더 있습니다",
                english=(
                    "two domains, each holding one project of a different name and one user, "
                    "the user of the second is inactive, and the first holds one more "
                    "superadmin"
                ),
            )
        return Says(
            "도메인 둘, 각각 이름이 다른 프로젝트 하나와 사용자 하나, 첫째 도메인에 superadmin 이 "
            "한 명 더 있습니다",
            english=(
                "two domains, each holding one project of a different name and one user, "
                "and the first holds one more superadmin"
            ),
        )

    @override
    async def lay(self, seeding: Any) -> TwoDomainsAndTheirRows:
        projects = await seeding.once(TestSeedProjectPolicy())
        first = await seeding.creating(TestSeedDomain(name_hint="first", description=WAS_HERE))
        second = await seeding.creating(TestSeedDomain(name_hint="second", description=WAS_HERE))
        first_project = await seeding.creating_from_two(
            TestSeedProject(name_hint="alpha-team"), first, projects
        )
        second_project = await seeding.creating_from_two(
            TestSeedProject(name_hint="beta-team"), second, projects
        )
        first_user = await seeding.within(SomeoneOf(first))
        second_user = await seeding.within(
            AnInactiveUserOf(second) if self.second_user_inactive else SomeoneOf(second)
        )
        caller = await seeding.within(SomeoneOf(first, role=UserRole.SUPERADMIN))
        return TwoDomainsAndTheirRows(
            seeding.made(first),
            seeding.made(second),
            seeding.made(first_project),
            seeding.made(second_project),
            seeding.made(first_user),
            seeding.made(second_user),
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
class SearchingByTheFirstProjectName(When[TwoDomainsAndTheirRows, DomainAdapter, Searched]):
    """첫째 도메인이 가진 프로젝트의 이름으로 걸러 search 한다."""

    @override
    def operation(self) -> str:
        return "global_search"

    @override
    def describe(self, laid: TwoDomainsAndTheirRows) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.first_project.name}이라는 프로젝트를 가진 도메인을 "
            "찾습니다",
            english=(
                f"{laid.caller.username} searches for the domain holding the project named "
                f"{laid.first_project.name}"
            ),
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: TwoDomainsAndTheirRows) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.global_search(
                AdminSearchDomainsInput(
                    filter=DomainFilter(
                        project=DomainProjectFilter(
                            name=StringFilter(equals=laid.first_project.name)
                        )
                    )
                )
            )


@dataclass(frozen=True)
class SearchingByTheFirstUsername(When[TwoDomainsAndTheirRows, DomainAdapter, Searched]):
    """첫째 도메인에 사는 사용자의 이름으로 걸러 search 한다."""

    @override
    def operation(self) -> str:
        return "global_search"

    @override
    def describe(self, laid: TwoDomainsAndTheirRows) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.first_user.username}이 사는 도메인을 찾습니다",
            english=(
                f"{laid.caller.username} searches for the domain where "
                f"{laid.first_user.username} lives"
            ),
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: TwoDomainsAndTheirRows) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.global_search(
                AdminSearchDomainsInput(
                    filter=DomainFilter(
                        user=DomainUserFilter(
                            username=StringFilter(equals=laid.first_user.username)
                        )
                    )
                )
            )


@dataclass(frozen=True)
class SearchingByTheFirstEmail(When[TwoDomainsAndTheirRows, DomainAdapter, Searched]):
    """첫째 도메인에 사는 사용자의 이메일로 걸러 search 한다."""

    @override
    def operation(self) -> str:
        return "global_search"

    @override
    def describe(self, laid: TwoDomainsAndTheirRows) -> str:
        return Says(
            f"{laid.caller.username}이 {laid.first_user.email}을 쓰는 사용자가 사는 도메인을 "
            "찾습니다",
            english=(
                f"{laid.caller.username} searches for the domain where the user with the email "
                f"{laid.first_user.email} lives"
            ),
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: TwoDomainsAndTheirRows) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.global_search(
                AdminSearchDomainsInput(
                    filter=DomainFilter(
                        user=DomainUserFilter(email=StringFilter(equals=laid.first_user.email))
                    )
                )
            )


@dataclass(frozen=True)
class SearchingByAnInactiveUser(When[TwoDomainsAndTheirRows, DomainAdapter, Searched]):
    """비활성 사용자가 사는 도메인을 search 한다."""

    @override
    def operation(self) -> str:
        return "global_search"

    @override
    def describe(self, laid: TwoDomainsAndTheirRows) -> str:
        return Says(
            f"{laid.caller.username}이 비활성 사용자가 사는 도메인을 찾습니다",
            english=f"{laid.caller.username} searches for the domain where an inactive user lives",
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: TwoDomainsAndTheirRows) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.global_search(
                AdminSearchDomainsInput(filter=DomainFilter(user=DomainUserFilter(is_active=False)))
            )


@dataclass(frozen=True)
class OrderingByTheProjectName(When[TwoDomainsAndTheirRows, DomainAdapter, Searched]):
    """도메인이 가진 프로젝트의 이름으로 세워 search 한다."""

    @override
    def operation(self) -> str:
        return "global_search"

    @override
    def describe(self, laid: TwoDomainsAndTheirRows) -> str:
        return Says(
            f"{laid.caller.username}이 프로젝트 이름순으로 세워 전체를 조회합니다",
            english=f"{laid.caller.username} searches every domain ordered by project name",
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: TwoDomainsAndTheirRows) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.global_search(
                AdminSearchDomainsInput(
                    order=[
                        DomainOrder(
                            field=DomainOrderField.PROJECT_NAME, direction=OrderDirection.ASC
                        )
                    ]
                )
            )


@dataclass(frozen=True)
class OrderingByTheUsername(When[TwoDomainsAndTheirRows, DomainAdapter, Searched]):
    """도메인에 사는 사용자의 이름으로 세워 search 한다."""

    @override
    def operation(self) -> str:
        return "global_search"

    @override
    def describe(self, laid: TwoDomainsAndTheirRows) -> str:
        return Says(
            f"{laid.caller.username}이 사용자 이름순으로 세워 전체를 조회합니다",
            english=f"{laid.caller.username} searches every domain ordered by the username of its users",
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: TwoDomainsAndTheirRows) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.global_search(
                AdminSearchDomainsInput(
                    order=[
                        DomainOrder(
                            field=DomainOrderField.USER_USERNAME, direction=OrderDirection.ASC
                        )
                    ]
                )
            )


@dataclass(frozen=True)
class OrderingByTheEmail(When[TwoDomainsAndTheirRows, DomainAdapter, Searched]):
    """도메인에 사는 사용자의 이메일로 세워 search 한다."""

    @override
    def operation(self) -> str:
        return "global_search"

    @override
    def describe(self, laid: TwoDomainsAndTheirRows) -> str:
        return Says(
            f"{laid.caller.username}이 사용자 이메일순으로 세워 전체를 조회합니다",
            english=f"{laid.caller.username} searches every domain ordered by the email of its users",
        )

    @override
    async def call(self, adapter: DomainAdapter, laid: TwoDomainsAndTheirRows) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.global_search(
                AdminSearchDomainsInput(
                    order=[
                        DomainOrder(field=DomainOrderField.USER_EMAIL, direction=OrderDirection.ASC)
                    ]
                )
            )


@dataclass(frozen=True)
class OnlyOneDomainIsLeft(Then[TwoDomainsAndTheirRows, Searched]):
    """그 행을 가진 도메인 하나만 남는다. ``first``면 첫째, 아니면 둘째다."""

    first: bool = True

    @override
    def says(self) -> str:
        if self.first:
            return Says(
                "첫째 도메인 하나만 남습니다",
                english="only the first domain is left",
            )
        return Says(
            "둘째 도메인 하나만 남습니다",
            english="only the second domain is left",
        )

    @override
    def look(self, laid: TwoDomainsAndTheirRows, answered: Answered[Searched]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(InsufficientPrivilege, answered.raised)]
        expected = laid.first if self.first else laid.second
        return [
            Same("items", [one.basic_info.name for one in payload.items], [expected.name]),
            Same("total_count", payload.total_count, 1),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheDomainsInOrder(Then[TwoDomainsAndTheirRows, Searched]):
    """도메인이 프로젝트 이름순으로 온다."""

    @override
    def says(self) -> str:
        return Says(
            "도메인이 이름순으로 옵니다",
            english="the domains come back in name order",
        )

    @override
    def look(self, laid: TwoDomainsAndTheirRows, answered: Answered[Searched]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [Refused(InsufficientPrivilege, answered.raised)]
        return [
            Same(
                "items",
                [one.basic_info.name for one in payload.items],
                [laid.first.name, laid.second.name],
            ),
            Same("total_count", payload.total_count, 2),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


type NestedStep = Scenario[TestSeedingSession, TwoDomainsAndTheirRows, DomainAdapter, Searched]


@dataclass(frozen=True)
class AProjectNameFilterNarrows(
    Scenario[TestSeedingSession, TwoDomainsAndTheirRows, DomainAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-project-name-filter-narrows-the-answer-to-the-domain-holding-it"

    @override
    def describe(self) -> str:
        return Says(
            "도메인 둘 중 하나가 가진 프로젝트의 이름으로 걸러 조회하면, 그 프로젝트를 가진 도메인만 "
            "남습니다",
            english=(
                "when domains are searched with a filter on the name of a project one of them "
                "holds, only the domain holding that project is left"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, TwoDomainsAndTheirRows]:
        return TwoDomainsWithProjectsAndUsers()

    @override
    def when(self) -> When[TwoDomainsAndTheirRows, DomainAdapter, Searched]:
        return SearchingByTheFirstProjectName()

    @override
    def then(self) -> Then[TwoDomainsAndTheirRows, Searched]:
        return OnlyOneDomainIsLeft()


@dataclass(frozen=True)
class AUsernameFilterNarrows(
    Scenario[TestSeedingSession, TwoDomainsAndTheirRows, DomainAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-username-filter-narrows-the-answer-to-the-domain-the-user-lives-in"

    @override
    def describe(self) -> str:
        return Says(
            "도메인 둘 중 하나에 사는 사용자의 이름으로 걸러 조회하면, 그 사용자가 사는 도메인만 "
            "남습니다",
            english=(
                "when domains are searched with a filter on the username of a user living in "
                "one of them, only the domain that user lives in is left"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, TwoDomainsAndTheirRows]:
        return TwoDomainsWithProjectsAndUsers()

    @override
    def when(self) -> When[TwoDomainsAndTheirRows, DomainAdapter, Searched]:
        return SearchingByTheFirstUsername()

    @override
    def then(self) -> Then[TwoDomainsAndTheirRows, Searched]:
        return OnlyOneDomainIsLeft()


@dataclass(frozen=True)
class AnEmailFilterNarrows(
    Scenario[TestSeedingSession, TwoDomainsAndTheirRows, DomainAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "an-email-filter-narrows-the-answer-to-the-domain-the-user-lives-in"

    @override
    def describe(self) -> str:
        return Says(
            "도메인 둘 중 하나에 사는 사용자의 이메일로 걸러 조회하면, 그 사용자가 사는 도메인만 "
            "남습니다",
            english=(
                "when domains are searched with a filter on the email of a user living in one "
                "of them, only the domain that user lives in is left"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, TwoDomainsAndTheirRows]:
        return TwoDomainsWithProjectsAndUsers()

    @override
    def when(self) -> When[TwoDomainsAndTheirRows, DomainAdapter, Searched]:
        return SearchingByTheFirstEmail()

    @override
    def then(self) -> Then[TwoDomainsAndTheirRows, Searched]:
        return OnlyOneDomainIsLeft()


@dataclass(frozen=True)
class AnInactiveUserFilterNarrows(
    Scenario[TestSeedingSession, TwoDomainsAndTheirRows, DomainAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "an-inactive-user-filter-narrows-the-answer-to-the-domain-they-live-in"

    @override
    def describe(self) -> str:
        return Says(
            "비활성 사용자로 걸러 조회하면, 그 사용자가 사는 도메인만 남습니다",
            english=(
                "when domains are searched with a filter on inactive users, only the domain "
                "such a user lives in is left"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, TwoDomainsAndTheirRows]:
        return TwoDomainsWithProjectsAndUsers(second_user_inactive=True)

    @override
    def when(self) -> When[TwoDomainsAndTheirRows, DomainAdapter, Searched]:
        return SearchingByAnInactiveUser()

    @override
    def then(self) -> Then[TwoDomainsAndTheirRows, Searched]:
        return OnlyOneDomainIsLeft(first=False)


@dataclass(frozen=True)
class TheDomainsComeInProjectNameOrder(
    Scenario[TestSeedingSession, TwoDomainsAndTheirRows, DomainAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "ordering-by-the-project-name-puts-the-domains-in-that-order"

    @override
    def describe(self) -> str:
        return Says(
            "도메인 전체를 가진 프로젝트의 이름순으로 세워 조회하면, 이름이 앞서는 프로젝트를 가진 "
            "도메인이 먼저 옵니다",
            english=(
                "when every domain is searched ordered by the name of the project it holds, "
                "the domain holding the project whose name comes first comes first"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, TwoDomainsAndTheirRows]:
        return TwoDomainsWithProjectsAndUsers()

    @override
    def when(self) -> When[TwoDomainsAndTheirRows, DomainAdapter, Searched]:
        return OrderingByTheProjectName()

    @override
    def then(self) -> Then[TwoDomainsAndTheirRows, Searched]:
        return TheDomainsInOrder()


@dataclass(frozen=True)
class TheDomainsComeInUsernameOrder(
    Scenario[TestSeedingSession, TwoDomainsAndTheirRows, DomainAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "ordering-by-the-username-puts-the-domains-in-that-order"

    @override
    def describe(self) -> str:
        return Says(
            "도메인 전체를 사용자 이름순으로 세워 조회하면, 이름이 앞서는 사용자가 사는 도메인이 "
            "먼저 옵니다",
            english=(
                "when every domain is searched ordered by the username of its users, the "
                "domain whose user's name comes first comes first"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, TwoDomainsAndTheirRows]:
        return TwoDomainsWithProjectsAndUsers()

    @override
    def when(self) -> When[TwoDomainsAndTheirRows, DomainAdapter, Searched]:
        return OrderingByTheUsername()

    @override
    def then(self) -> Then[TwoDomainsAndTheirRows, Searched]:
        return TheDomainsInOrder()


@dataclass(frozen=True)
class TheDomainsComeInEmailOrder(
    Scenario[TestSeedingSession, TwoDomainsAndTheirRows, DomainAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "ordering-by-the-email-puts-the-domains-in-that-order"

    @override
    def describe(self) -> str:
        return Says(
            "도메인 전체를 사용자 이메일순으로 세워 조회하면, 이메일이 앞서는 사용자가 사는 도메인이 "
            "먼저 옵니다",
            english=(
                "when every domain is searched ordered by the email of its users, the domain "
                "whose user's email comes first comes first"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, TwoDomainsAndTheirRows]:
        return TwoDomainsWithProjectsAndUsers()

    @override
    def when(self) -> When[TwoDomainsAndTheirRows, DomainAdapter, Searched]:
        return OrderingByTheEmail()

    @override
    def then(self) -> Then[TwoDomainsAndTheirRows, Searched]:
        return TheDomainsInOrder()


SCENARIOS: list[NestedStep] = [
    AProjectNameFilterNarrows(),
    AUsernameFilterNarrows(),
    AnEmailFilterNarrows(),
    AnInactiveUserFilterNarrows(),
    TheDomainsComeInProjectNameOrder(),
    TheDomainsComeInUsernameOrder(),
    TheDomainsComeInEmailOrder(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_nested_searching(
    scenario: NestedStep, adapter: DomainAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
