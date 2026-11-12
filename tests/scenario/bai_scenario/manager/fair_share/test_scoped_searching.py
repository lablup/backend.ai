"""한 리소스 그룹 안의 fair share 검색하기. 그 그룹 범위의 fair share 읽기 권한이 막는다."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import pytest

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.v2.fair_share.request import (
    DomainFairShareDomainNestedFilter,
    DomainFairShareFilter,
    DomainFairShareOrder,
    ProjectFairShareFilter,
    ProjectFairShareOrder,
    ProjectFairShareProjectNestedFilter,
    SearchDomainFairSharesInput,
    SearchProjectFairSharesInput,
    SearchUserFairSharesInput,
    UserFairShareFilter,
    UserFairShareOrder,
    UserFairShareUserNestedFilter,
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
from ai.backend.manager.data.fair_share.types import ProjectFairShareData, UserFairShareData
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.fair_share import (
    AScopedWeightAndACaller,
    DomainsAndAWeightElsewhere,
    DomainsAroundAGroupAndACaller,
    MembersAroundAProject,
    ProjectsAroundADomain,
    TheSecondActiveDomainOnItsDefaults,
    TheSecondActiveMember,
    TheSecondActiveProject,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Laid = Any
type SearchingStep = Scenario[TestSeedingSession, Laid, FairShareAdapter, Any]


@dataclass(frozen=True)
class SearchingInTheGroup:
    """요청이 이름으로 가리키는 리소스 그룹. ``missing``이면 아무도 만들지 않은 이름이다."""

    missing: bool = False

    def name(self, laid: Laid) -> str:
        if self.missing:
            return f"{laid.group.name}-missing"
        return str(laid.group.name)

    def says(self, laid: Laid, scope_ko: str, scope_en: str, by_ko: str, by_en: str) -> str:
        if self.missing:
            where_ko = "없는 리소스 그룹 이름으로"
            where_en = "under a resource group name nobody created"
        else:
            where_ko = f"{laid.group.name} 안에서"
            where_en = f"in {laid.group.name}"
        return Says(
            (
                f"{laid.caller.username} 이 {where_ko} {scope_ko} 활성 필터, {by_ko} 오름차순으로 "
                "한 건을 건너뛰고 한 건을 조회합니다"
            ),
            english=(
                f"{laid.caller.username} searches {where_en} {scope_en} with the active filter, in "
                f"ascending {by_en} order, skipping one item and asking for one"
            ),
        )


@dataclass(frozen=True)
class SearchingDomains(When[DomainsAroundAGroupAndACaller, FairShareAdapter, Any]):
    """그룹 안 활성 도메인을 이름 순으로 둘째 한 건 검색한다."""

    group: SearchingInTheGroup

    @override
    def operation(self) -> str:
        return "search_rg_domain"

    @override
    def describe(self, laid: DomainsAroundAGroupAndACaller) -> str:
        return self.group.says(laid, "도메인을", "the domains", "도메인 이름", "domain name")

    @override
    async def call(
        self, adapter: FairShareAdapter, laid: DomainsAroundAGroupAndACaller
    ) -> SearchDomainFairSharesPayload:
        with ActingAs(laid.caller):
            return await adapter.search_rg_domain(
                SearchDomainFairSharesInput(
                    filter=DomainFairShareFilter(
                        domain=DomainFairShareDomainNestedFilter(is_active=True)
                    ),
                    order=[
                        DomainFairShareOrder(
                            field=DomainFairShareOrderField.DOMAIN_NAME,
                            direction=OrderDirection.ASC,
                        )
                    ],
                    limit=1,
                    offset=1,
                ),
                resource_group=self.group.name(laid),
            )


@dataclass(frozen=True)
class SearchingProjects(When[AScopedWeightAndACaller[ProjectFairShareData], FairShareAdapter, Any]):
    """그룹과 도메인 안 활성 프로젝트를 이름 순으로 둘째 한 건 검색한다."""

    group: SearchingInTheGroup

    @override
    def operation(self) -> str:
        return "search_rg_project"

    @override
    def describe(self, laid: AScopedWeightAndACaller[ProjectFairShareData]) -> str:
        return self.group.says(
            laid,
            f"도메인 {laid.domain.name}의 프로젝트를",
            f"the projects of domain {laid.domain.name}",
            "프로젝트 이름",
            "project name",
        )

    @override
    async def call(
        self, adapter: FairShareAdapter, laid: AScopedWeightAndACaller[ProjectFairShareData]
    ) -> SearchProjectFairSharesPayload:
        with ActingAs(laid.caller):
            return await adapter.search_rg_project(
                SearchProjectFairSharesInput(
                    filter=ProjectFairShareFilter(
                        project=ProjectFairShareProjectNestedFilter(is_active=True)
                    ),
                    order=[
                        ProjectFairShareOrder(
                            field=ProjectFairShareOrderField.PROJECT_NAME,
                            direction=OrderDirection.ASC,
                        )
                    ],
                    limit=1,
                    offset=1,
                ),
                resource_group=self.group.name(laid),
                domain_name=laid.domain.name,
            )


@dataclass(frozen=True)
class SearchingMembers(When[AScopedWeightAndACaller[UserFairShareData], FairShareAdapter, Any]):
    """그룹과 프로젝트 안 활성 멤버를 사용자 이름 순으로 둘째 한 건 검색한다."""

    group: SearchingInTheGroup

    @override
    def operation(self) -> str:
        return "search_rg_user"

    @override
    def describe(self, laid: AScopedWeightAndACaller[UserFairShareData]) -> str:
        return self.group.says(
            laid,
            f"프로젝트 {laid.project.name}의 멤버를",
            f"the members of project {laid.project.name}",
            "사용자 이름",
            "username",
        )

    @override
    async def call(
        self, adapter: FairShareAdapter, laid: AScopedWeightAndACaller[UserFairShareData]
    ) -> SearchUserFairSharesPayload:
        with ActingAs(laid.caller):
            return await adapter.search_rg_user(
                SearchUserFairSharesInput(
                    filter=UserFairShareFilter(user=UserFairShareUserNestedFilter(is_active=True)),
                    order=[
                        UserFairShareOrder(
                            field=UserFairShareOrderField.USER_USERNAME,
                            direction=OrderDirection.ASC,
                        )
                    ],
                    limit=1,
                    offset=1,
                ),
                resource_group=self.group.name(laid),
                domain_name=laid.domain.name,
                project_id=laid.project.id,
            )


@dataclass(frozen=True)
class Target:
    """검색할 fair share 의 종류와 그 종류의 준비, 호출, 검사."""

    key: str
    korean: str
    english: str
    scope_korean: str
    scope_english: str
    given: Callable[[Permission], Given[Any, Any]]
    when: Callable[[SearchingInTheGroup], When[Any, FairShareAdapter, Any]]
    then: Callable[[datetime], Then[Any, Any]]


DOMAIN = Target(
    "domain",
    "도메인",
    "domain",
    "다른 리소스 그룹에만 기록한 도메인은 이 그룹의 기본값으로 오고 비활성 도메인은 오지 않습니다",
    (
        "a domain recorded only in the other resource group comes back with this group's "
        "defaults and the inactive domain does not come back"
    ),
    DomainsAndAWeightElsewhere,
    SearchingDomains,
    TheSecondActiveDomainOnItsDefaults,
)
PROJECT = Target(
    "project",
    "프로젝트",
    "project",
    "다른 도메인의 프로젝트와 비활성 프로젝트는 오지 않습니다",
    "the project of another domain and the inactive project do not come back",
    ProjectsAroundADomain,
    SearchingProjects,
    TheSecondActiveProject,
)
USER = Target(
    "user",
    "사용자",
    "user",
    "다른 프로젝트의 멤버와 비활성 멤버는 오지 않습니다",
    "the member of another project and the inactive member do not come back",
    MembersAroundAProject,
    SearchingMembers,
    TheSecondActiveMember,
)


@dataclass(frozen=True)
class AReaderSearchesTheGroup(Scenario[TestSeedingSession, Laid, FairShareAdapter, Any]):
    target: Target
    started: datetime

    @override
    def summary(self) -> str:
        return f"a-user-granted-fair-share-read-on-the-group-searches-its-{self.target.key}-fair-shares"

    @override
    def describe(self) -> str:
        return Says(
            (
                "그 리소스 그룹 범위에서 fair share 읽기 역할을 받은 사용자가 그 그룹의 "
                f"{self.target.korean} fair share 를 활성 필터, 이름 순, 둘째 한 건으로 조회하면 "
                f"활성인 것 둘이 세어지고 둘째 것이 옵니다. {self.target.scope_korean}"
            ),
            english=(
                "when a user granted the fair share read role in the resource group scope "
                f"searches the {self.target.english} fair shares of that group with the active "
                "filter, by name, for the second item, the two active ones are counted and the "
                f"second comes back; {self.target.scope_english}"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return self.target.given(Permission.READ)

    @override
    def when(self) -> When[Laid, FairShareAdapter, Any]:
        return self.target.when(SearchingInTheGroup())

    @override
    def then(self) -> Then[Laid, Any]:
        return self.target.then(self.started)


@dataclass(frozen=True)
class AnUpdaterMayNotSearchTheGroup(Scenario[TestSeedingSession, Laid, FairShareAdapter, Any]):
    target: Target

    @override
    def summary(self) -> str:
        return f"a-user-granted-only-fair-share-update-may-not-search-{self.target.key}-fair-shares"

    @override
    def describe(self) -> str:
        return Says(
            (
                "그 리소스 그룹 범위에서 fair share 수정 역할만 받은 사용자가 그 그룹의 "
                f"{self.target.korean} fair share 를 검색하면 권한 부족으로 거부됩니다"
            ),
            english=(
                "when a user granted only the fair share update role in the resource group scope "
                f"searches the {self.target.english} fair shares of that group, it is rejected "
                "for a lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return self.target.given(Permission.UPDATE)

    @override
    def when(self) -> When[Laid, FairShareAdapter, Any]:
        return self.target.when(SearchingInTheGroup())

    @override
    def then(self) -> Then[Laid, Any]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnUnknownGroupFails(Scenario[TestSeedingSession, Laid, FairShareAdapter, Any]):
    target: Target

    @override
    def summary(self) -> str:
        return f"searching-{self.target.key}-fair-shares-in-an-unknown-resource-group-fails"

    @override
    def describe(self) -> str:
        return Says(
            (
                "fair share 읽기 역할을 받은 사용자가 없는 리소스 그룹 이름으로 "
                f"{self.target.korean} fair share 를 검색하면 리소스 그룹을 찾지 못해 실패합니다"
            ),
            english=(
                f"when a user granted the fair share read role searches the {self.target.english} "
                "fair shares under a resource group name nobody created, it fails because the "
                "resource group is not found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return self.target.given(Permission.READ)

    @override
    def when(self) -> When[Laid, FairShareAdapter, Any]:
        return self.target.when(SearchingInTheGroup(missing=True))

    @override
    def then(self) -> Then[Laid, Any]:
        return TheCallIsRefused(EntityNotFoundError)


SCENARIOS: list[SearchingStep] = [
    row
    for target in (DOMAIN, PROJECT, USER)
    for row in (
        AReaderSearchesTheGroup(target, started=datetime.now(UTC)),
        AnUpdaterMayNotSearchTheGroup(target),
        AnUnknownGroupFails(target),
    )
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_scoped_searching(
    scenario: SearchingStep, adapter: FairShareAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
