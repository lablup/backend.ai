"""리소스 그룹을 가리지 않고 fair share 기록 검색하기. 전역 역할이 막는다."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.fair_share.request import (
    DomainFairShareFilter,
    DomainFairShareOrder,
    ProjectFairShareFilter,
    ProjectFairShareOrder,
    SearchDomainFairSharesInput,
    SearchProjectFairSharesInput,
    SearchUserFairSharesInput,
    UserFairShareFilter,
    UserFairShareOrder,
)
from ai.backend.common.dto.manager.v2.fair_share.response import (
    SearchDomainFairSharesPayload,
    SearchProjectFairSharesPayload,
    SearchUserFairSharesPayload,
)
from ai.backend.common.dto.manager.v2.fair_share.types import (
    DomainFairShareOrderField,
    OrderDirection,
    ProjectFairShareOrderField,
    UserFairShareOrderField,
)
from ai.backend.manager.api.adapters.fair_share.adapter import FairShareAdapter
from ai.backend.manager.data.fair_share.types import (
    DomainFairShareData,
    ProjectFairShareData,
    UserFairShareData,
)
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.fair_share import (
    DomainWeightsInTwoGroups,
    ProjectWeightsInTwoGroups,
    TheFirstDomainOfTheGroup,
    TheFirstProjectOfTheGroup,
    TheFirstUserOfTheGroup,
    UserWeightsInTwoGroups,
    WeightsInTwoGroupsAndACaller,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Laid = WeightsInTwoGroupsAndACaller[Any]
type SearchingStep = Scenario[TestSeedingSession, Laid, FairShareAdapter, Any]


def _says_the_request(laid: Laid, by_ko: str, by_en: str) -> str:
    return Says(
        (
            f"{laid.caller.username} 이 리소스 그룹 {laid.group.name} 필터, {by_ko} 오름차순으로 "
            "앞에서 한 건을 조회합니다"
        ),
        english=(
            f"{laid.caller.username} asks for one item from the front with the resource group "
            f"{laid.group.name} filter, in ascending {by_en} order"
        ),
    )


@dataclass(frozen=True)
class SearchingDomains(
    When[
        WeightsInTwoGroupsAndACaller[DomainFairShareData],
        FairShareAdapter,
        SearchDomainFairSharesPayload,
    ]
):
    """한 그룹의 기록만 도메인 이름 순으로 한 건 검색한다."""

    @override
    def operation(self) -> str:
        return "search_domain"

    @override
    def describe(self, laid: WeightsInTwoGroupsAndACaller[DomainFairShareData]) -> str:
        return _says_the_request(laid, "도메인 이름", "domain name")

    @override
    async def call(
        self, adapter: FairShareAdapter, laid: WeightsInTwoGroupsAndACaller[DomainFairShareData]
    ) -> SearchDomainFairSharesPayload:
        with ActingAs(laid.caller):
            return await adapter.search_domain(
                SearchDomainFairSharesInput(
                    filter=DomainFairShareFilter(
                        resource_group=StringFilter(equals=laid.group.name)
                    ),
                    order=[
                        DomainFairShareOrder(
                            field=DomainFairShareOrderField.DOMAIN_NAME,
                            direction=OrderDirection.ASC,
                        )
                    ],
                    limit=1,
                )
            )


@dataclass(frozen=True)
class SearchingProjects(
    When[
        WeightsInTwoGroupsAndACaller[ProjectFairShareData],
        FairShareAdapter,
        SearchProjectFairSharesPayload,
    ]
):
    """한 그룹의 기록만 프로젝트 이름 순으로 한 건 검색한다."""

    @override
    def operation(self) -> str:
        return "search_project"

    @override
    def describe(self, laid: WeightsInTwoGroupsAndACaller[ProjectFairShareData]) -> str:
        return _says_the_request(laid, "프로젝트 이름", "project name")

    @override
    async def call(
        self, adapter: FairShareAdapter, laid: WeightsInTwoGroupsAndACaller[ProjectFairShareData]
    ) -> SearchProjectFairSharesPayload:
        with ActingAs(laid.caller):
            return await adapter.search_project(
                SearchProjectFairSharesInput(
                    filter=ProjectFairShareFilter(
                        resource_group=StringFilter(equals=laid.group.name)
                    ),
                    order=[
                        ProjectFairShareOrder(
                            field=ProjectFairShareOrderField.PROJECT_NAME,
                            direction=OrderDirection.ASC,
                        )
                    ],
                    limit=1,
                )
            )


@dataclass(frozen=True)
class SearchingUsers(
    When[
        WeightsInTwoGroupsAndACaller[UserFairShareData],
        FairShareAdapter,
        SearchUserFairSharesPayload,
    ]
):
    """한 그룹의 기록만 사용자 이름 순으로 한 건 검색한다."""

    @override
    def operation(self) -> str:
        return "search_user"

    @override
    def describe(self, laid: WeightsInTwoGroupsAndACaller[UserFairShareData]) -> str:
        return _says_the_request(laid, "사용자 이름", "username")

    @override
    async def call(
        self, adapter: FairShareAdapter, laid: WeightsInTwoGroupsAndACaller[UserFairShareData]
    ) -> SearchUserFairSharesPayload:
        with ActingAs(laid.caller):
            return await adapter.search_user(
                SearchUserFairSharesInput(
                    filter=UserFairShareFilter(resource_group=StringFilter(equals=laid.group.name)),
                    order=[
                        UserFairShareOrder(
                            field=UserFairShareOrderField.USER_USERNAME,
                            direction=OrderDirection.ASC,
                        )
                    ],
                    limit=1,
                )
            )


@dataclass(frozen=True)
class Target:
    """검색할 fair share 의 종류와 그 종류의 준비, 호출, 검사."""

    key: str
    korean: str
    english: str
    given: Callable[[UserRole], Given[Any, Any]]
    when: Callable[[], When[Any, FairShareAdapter, Any]]
    then: Callable[[datetime], Then[Any, Any]]


DOMAIN = Target(
    "domain",
    "도메인",
    "domain",
    DomainWeightsInTwoGroups,
    SearchingDomains,
    TheFirstDomainOfTheGroup,
)
PROJECT = Target(
    "project",
    "프로젝트",
    "project",
    ProjectWeightsInTwoGroups,
    SearchingProjects,
    TheFirstProjectOfTheGroup,
)
USER = Target(
    "user", "사용자", "user", UserWeightsInTwoGroups, SearchingUsers, TheFirstUserOfTheGroup
)


@dataclass(frozen=True)
class TheSuperadminSearchesOneGroup(Scenario[TestSeedingSession, Laid, FairShareAdapter, Any]):
    target: Target
    started: datetime

    @override
    def summary(self) -> str:
        return f"the-superadmin-searches-the-{self.target.key}-fair-shares-of-one-group"

    @override
    def describe(self) -> str:
        return Says(
            (
                f"전역 역할이 막는 검색입니다. superadmin 이 {self.target.korean} fair share 를 한 "
                "리소스 그룹 필터와 이름 순으로 한 건 조회하면, 그 그룹의 기록 둘이 세어지고 이름 "
                "순으로 앞선 기록이 오며 다른 그룹의 기록은 오지 않습니다"
            ),
            english=(
                "this search is gated by the global role. When the superadmin searches the "
                f"{self.target.english} fair shares with one resource group filter, by name, for "
                "one item, the two records of that group are counted, the record first by name "
                "comes back, and the record in the other group does not"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return self.target.given(UserRole.SUPERADMIN)

    @override
    def when(self) -> When[Laid, FairShareAdapter, Any]:
        return self.target.when()

    @override
    def then(self) -> Then[Laid, Any]:
        return self.target.then(self.started)


@dataclass(frozen=True)
class ARegularUserMayNotSearch(Scenario[TestSeedingSession, Laid, FairShareAdapter, Any]):
    target: Target

    @override
    def summary(self) -> str:
        return f"a-regular-user-may-not-search-{self.target.key}-fair-shares-across-groups"

    @override
    def describe(self) -> str:
        return Says(
            (
                f"일반 사용자가 리소스 그룹을 가리지 않고 {self.target.korean} fair share 를 "
                "검색하면 역할 부족으로 거부됩니다"
            ),
            english=(
                f"when a regular user searches the {self.target.english} fair shares across "
                "resource groups, it is rejected for lacking the role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return self.target.given(UserRole.USER)

    @override
    def when(self) -> When[Laid, FairShareAdapter, Any]:
        return self.target.when()

    @override
    def then(self) -> Then[Laid, Any]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchingStep] = [
    row
    for target in (DOMAIN, PROJECT, USER)
    for row in (
        TheSuperadminSearchesOneGroup(target, started=datetime.now(UTC)),
        ARegularUserMayNotSearch(target),
    )
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: FairShareAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
