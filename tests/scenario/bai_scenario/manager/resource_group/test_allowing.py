"""허용 목록 — 도메인 쪽, 프로젝트 쪽, 그룹 쪽에서 같은 관계를 쓰고 읽는 호출 여덟."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_group.request import (
    UpdateAllowedDomainsForResourceGroupInput,
    UpdateAllowedProjectsForResourceGroupInput,
    UpdateAllowedResourceGroupsForDomainInput,
    UpdateAllowedResourceGroupsForProjectInput,
)
from ai.backend.common.dto.manager.v2.resource_group.response import (
    AllowedDomainsPayload,
    AllowedProjectsPayload,
    AllowedResourceGroupsPayload,
)
from ai.backend.manager.api.adapters.resource_group.adapter import ResourceGroupAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.resource import ResourceGroupNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_group import (
    ADomainGroupsAndACaller,
    ADomainGroupsAndSomeone,
    AGroupAndACaller,
    AGroupAndSomeone,
    AProjectAGroupAndACaller,
    AProjectAGroupAndSomeone,
    NothingIsAllowed,
    TheAllowedDomainNames,
    TheAllowedProjectIds,
    TheGroupIsAllowedForTheProject,
    TheLinkedGroupIsAllowed,
    TheOtherGroupIsAllowed,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type AllowingStep = Scenario[SeedingSession, Any, ResourceGroupAdapter, Any]

UNKNOWN_GROUP = "no-such-group"
UNKNOWN_DOMAIN = "no-such-domain"


# ------------------------------------------------------------------ domain side


@dataclass(frozen=True)
class AllowingForTheDomain(
    When[ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload]
):
    """도메인의 허용 목록에 그룹을 더하거나 뺀다. ``unknown``이면 어느 행에도 없는 이름을 쓴다."""

    remove: bool = False
    unknown: bool = False

    @override
    def operation(self) -> str:
        return "update_allowed_resource_groups_for_domain"

    @override
    def describe(self, laid: ADomainGroupsAndACaller) -> str:
        what = (
            "없는 그룹 이름"
            if self.unknown
            else (laid.linked.name if self.remove else laid.other.name)
        )
        verb = "제거" if self.remove else "추가"
        return f"{laid.caller.username}이 도메인 {laid.domain.name}의 허용 목록에 {what} {verb}"

    @override
    async def call(
        self, adapter: ResourceGroupAdapter, laid: ADomainGroupsAndACaller
    ) -> AllowedResourceGroupsPayload:
        name = (
            UNKNOWN_GROUP
            if self.unknown
            else (laid.linked.name if self.remove else laid.other.name)
        )
        asked = UpdateAllowedResourceGroupsForDomainInput(
            domain_name=laid.domain.name,
            add=None if self.remove else [name],
            remove=[name] if self.remove else None,
        )
        with ActingAs(laid.caller):
            return await adapter.update_allowed_resource_groups_for_domain(asked)


@dataclass(frozen=True)
class ReadingTheDomainsAllowed(
    When[ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload]
):
    """도메인의 허용 목록을 읽는다. ``unknown``이면 어느 행에도 없는 도메인 이름을 쓴다."""

    unknown: bool = False

    @override
    def operation(self) -> str:
        return "get_allowed_resource_groups_for_domain"

    @override
    def describe(self, laid: ADomainGroupsAndACaller) -> str:
        target = "존재하지 않는 도메인" if self.unknown else f"도메인 {laid.domain.name}"
        return f"{laid.caller.username}이 {target}의 허용 목록 조회"

    @override
    async def call(
        self, adapter: ResourceGroupAdapter, laid: ADomainGroupsAndACaller
    ) -> AllowedResourceGroupsPayload:
        with ActingAs(laid.caller):
            return await adapter.get_allowed_resource_groups_for_domain(
                UNKNOWN_DOMAIN if self.unknown else laid.domain.name
            )


# ------------------------------------------------------------------ project side


@dataclass(frozen=True)
class AllowingForTheProject(
    When[AProjectAGroupAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload]
):
    """프로젝트의 허용 목록에 그룹을 더한다."""

    @override
    def operation(self) -> str:
        return "update_allowed_resource_groups_for_project"

    @override
    def describe(self, laid: AProjectAGroupAndACaller) -> str:
        return f"{laid.caller.username}이 프로젝트 {laid.project.name}의 허용 목록에 {laid.group.name} 추가"

    @override
    async def call(
        self, adapter: ResourceGroupAdapter, laid: AProjectAGroupAndACaller
    ) -> AllowedResourceGroupsPayload:
        with ActingAs(laid.caller):
            return await adapter.update_allowed_resource_groups_for_project(
                UpdateAllowedResourceGroupsForProjectInput(
                    project_id=laid.project.id, add=[laid.group.name]
                )
            )


@dataclass(frozen=True)
class ReadingTheProjectsAllowed(
    When[AProjectAGroupAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload]
):
    """프로젝트의 허용 목록을 읽는다."""

    @override
    def operation(self) -> str:
        return "get_allowed_resource_groups_for_project"

    @override
    def describe(self, laid: AProjectAGroupAndACaller) -> str:
        return f"{laid.caller.username}이 프로젝트 {laid.project.name}의 허용 목록 조회"

    @override
    async def call(
        self, adapter: ResourceGroupAdapter, laid: AProjectAGroupAndACaller
    ) -> AllowedResourceGroupsPayload:
        with ActingAs(laid.caller):
            return await adapter.get_allowed_resource_groups_for_project(laid.project.id)


# ------------------------------------------------------------------ group side


@dataclass(frozen=True)
class AllowingADomainForTheGroup(
    When[ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedDomainsPayload]
):
    """그룹의 허용 도메인에 도메인을 더하거나 뺀다. ``unknown``이면 어느 행에도 없는 도메인 이름을 쓴다."""

    remove: bool = False
    unknown: bool = False

    @override
    def operation(self) -> str:
        return "update_allowed_domains_for_resource_group"

    @override
    def describe(self, laid: ADomainGroupsAndACaller) -> str:
        what = "없는 도메인 이름" if self.unknown else laid.domain.name
        verb = "제거" if self.remove else "추가"
        return f"{laid.caller.username}이 {laid.other.name}의 허용 도메인에 {what} {verb}"

    @override
    async def call(
        self, adapter: ResourceGroupAdapter, laid: ADomainGroupsAndACaller
    ) -> AllowedDomainsPayload:
        name = UNKNOWN_DOMAIN if self.unknown else laid.domain.name
        with ActingAs(laid.caller):
            return await adapter.update_allowed_domains_for_resource_group(
                UpdateAllowedDomainsForResourceGroupInput(
                    resource_group_name=laid.other.name,
                    add=None if self.remove else [name],
                    remove=[name] if self.remove else None,
                )
            )


@dataclass(frozen=True)
class ReadingTheGroupsDomains(
    When[ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedDomainsPayload]
):
    """그룹의 허용 도메인을 읽는다. 도메인에 건 그룹을 읽는다."""

    @override
    def operation(self) -> str:
        return "get_allowed_domains_for_resource_group"

    @override
    def describe(self, laid: ADomainGroupsAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.linked.name}의 허용 도메인 조회"

    @override
    async def call(
        self, adapter: ResourceGroupAdapter, laid: ADomainGroupsAndACaller
    ) -> AllowedDomainsPayload:
        with ActingAs(laid.caller):
            return await adapter.get_allowed_domains_for_resource_group(laid.linked.name)


@dataclass(frozen=True)
class AllowingAProjectForTheGroup(
    When[AProjectAGroupAndACaller, ResourceGroupAdapter, AllowedProjectsPayload]
):
    """그룹의 허용 프로젝트에 프로젝트를 더한다."""

    @override
    def operation(self) -> str:
        return "update_allowed_projects_for_resource_group"

    @override
    def describe(self, laid: AProjectAGroupAndACaller) -> str:
        return (
            f"{laid.caller.username}이 {laid.group.name}의 허용 프로젝트에 {laid.project.name} 추가"
        )

    @override
    async def call(
        self, adapter: ResourceGroupAdapter, laid: AProjectAGroupAndACaller
    ) -> AllowedProjectsPayload:
        with ActingAs(laid.caller):
            return await adapter.update_allowed_projects_for_resource_group(
                UpdateAllowedProjectsForResourceGroupInput(
                    resource_group_name=laid.group.name, add=[laid.project.id]
                )
            )


@dataclass(frozen=True)
class ReadingTheGroupsProjects(
    When[AProjectAGroupAndACaller, ResourceGroupAdapter, AllowedProjectsPayload]
):
    """그룹의 허용 프로젝트를 읽는다."""

    @override
    def operation(self) -> str:
        return "get_allowed_projects_for_resource_group"

    @override
    def describe(self, laid: AProjectAGroupAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.group.name}의 허용 프로젝트 조회"

    @override
    async def call(
        self, adapter: ResourceGroupAdapter, laid: AProjectAGroupAndACaller
    ) -> AllowedProjectsPayload:
        with ActingAs(laid.caller):
            return await adapter.get_allowed_projects_for_resource_group(laid.group.name)


@dataclass(frozen=True)
class ReadingTheOwnGroupsDomains(
    When[AGroupAndACaller, ResourceGroupAdapter, AllowedDomainsPayload]
):
    """그룹의 허용 도메인을 읽는다."""

    @override
    def operation(self) -> str:
        return "get_allowed_domains_for_resource_group"

    @override
    def describe(self, laid: AGroupAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.group.name}의 허용 도메인 조회"

    @override
    async def call(
        self, adapter: ResourceGroupAdapter, laid: AGroupAndACaller
    ) -> AllowedDomainsPayload:
        with ActingAs(laid.caller):
            return await adapter.get_allowed_domains_for_resource_group(laid.group.name)


# ------------------------------------------------------------------ scenarios: domain side


@dataclass(frozen=True)
class TheSuperadminAllowsAGroupForADomain(
    Scenario[
        SeedingSession, ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-allows-a-resource-group-for-a-domain"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 도메인의 허용 목록에 그룹을 더하면 그 그룹 이름이 담긴 목록이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ADomainGroupsAndACaller]:
        return ADomainGroupsAndSomeone(role=UserRole.SUPERADMIN, linked=False)

    @override
    def when(
        self,
    ) -> When[ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload]:
        return AllowingForTheDomain()

    @override
    def then(self) -> Then[ADomainGroupsAndACaller, AllowedResourceGroupsPayload]:
        return TheOtherGroupIsAllowed()


@dataclass(frozen=True)
class TheSuperadminDisallowsAGroupForADomain(
    Scenario[
        SeedingSession, ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-disallows-a-resource-group-for-a-domain"

    @override
    def describe(self) -> str:
        return "도메인에 건 그룹을 슈퍼관리자가 허용 목록에서 빼면 빈 목록이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ADomainGroupsAndACaller]:
        return ADomainGroupsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload]:
        return AllowingForTheDomain(remove=True)

    @override
    def then(self) -> Then[ADomainGroupsAndACaller, AllowedResourceGroupsPayload]:
        return NothingIsAllowed()


@dataclass(frozen=True)
class AllowingAnUnknownGroupForADomainIsNotFound(
    Scenario[
        SeedingSession, ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "allowing-a-group-name-nothing-answers-to-for-a-domain-is-not-found"

    @override
    def describe(self) -> str:
        return "존재하지 않는 그룹 이름을 도메인의 허용 목록에 더하려 하면 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ADomainGroupsAndACaller]:
        return ADomainGroupsAndSomeone(role=UserRole.SUPERADMIN, linked=False)

    @override
    def when(
        self,
    ) -> When[ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload]:
        return AllowingForTheDomain(unknown=True)

    @override
    def then(self) -> Then[ADomainGroupsAndACaller, AllowedResourceGroupsPayload]:
        return TheCallIsRefused(ResourceGroupNotFound)


@dataclass(frozen=True)
class DisallowingAnUnknownGroupForADomainIsSkipped(
    Scenario[
        SeedingSession, ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "disallowing-a-group-name-nothing-answers-to-for-a-domain-is-skipped"

    @override
    def describe(self) -> str:
        return "존재하지 않는 그룹 이름을 도메인의 허용 목록에서 빼려 하면 그 이름은 건너뛰고 빈 목록이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ADomainGroupsAndACaller]:
        return ADomainGroupsAndSomeone(role=UserRole.SUPERADMIN, linked=False)

    @override
    def when(
        self,
    ) -> When[ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload]:
        return AllowingForTheDomain(remove=True, unknown=True)

    @override
    def then(self) -> Then[ADomainGroupsAndACaller, AllowedResourceGroupsPayload]:
        return NothingIsAllowed()


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotAllowForADomain(
    Scenario[
        SeedingSession, ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-allow-a-group-for-a-domain"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 아닌 사용자가 도메인의 허용 목록에 그룹을 더하려 하면 역할 부족으로 거부된다. "
            "그룹 이름을 id로 바꾸는 자리가 슈퍼관리자 검사를 거친다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADomainGroupsAndACaller]:
        return ADomainGroupsAndSomeone(linked=False)

    @override
    def when(
        self,
    ) -> When[ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload]:
        return AllowingForTheDomain()

    @override
    def then(self) -> Then[ADomainGroupsAndACaller, AllowedResourceGroupsPayload]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class TheSuperadminReadsADomainsAllowed(
    Scenario[
        SeedingSession, ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reads-the-groups-allowed-for-a-domain"

    @override
    def describe(self) -> str:
        return "도메인에 건 그룹과 걸지 않은 그룹이 있을 때 슈퍼관리자가 도메인의 허용 목록을 읽으면 건 그룹 이름만 담긴다"

    @override
    def given(self) -> Given[SeedingSession, ADomainGroupsAndACaller]:
        return ADomainGroupsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload]:
        return ReadingTheDomainsAllowed()

    @override
    def then(self) -> Then[ADomainGroupsAndACaller, AllowedResourceGroupsPayload]:
        return TheLinkedGroupIsAllowed()


@dataclass(frozen=True)
class AUserReadingInTheDomainReadsItsAllowed(
    Scenario[
        SeedingSession, ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-in-the-domain-reads-the-groups-allowed-for-it"

    @override
    def describe(self) -> str:
        return "도메인 범위에서 리소스 그룹 읽기 역할을 받은 사용자가 그 도메인의 허용 목록을 읽으면 건 그룹 이름만 담긴다"

    @override
    def given(self) -> Given[SeedingSession, ADomainGroupsAndACaller]:
        return ADomainGroupsAndSomeone(reading=True)

    @override
    def when(
        self,
    ) -> When[ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload]:
        return ReadingTheDomainsAllowed()

    @override
    def then(self) -> Then[ADomainGroupsAndACaller, AllowedResourceGroupsPayload]:
        return TheLinkedGroupIsAllowed()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadADomainsAllowed(
    Scenario[
        SeedingSession, ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-the-groups-allowed-for-a-domain"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 자기 도메인의 허용 목록을 읽으려 하면 권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADomainGroupsAndACaller]:
        return ADomainGroupsAndSomeone()

    @override
    def when(
        self,
    ) -> When[ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload]:
        return ReadingTheDomainsAllowed()

    @override
    def then(self) -> Then[ADomainGroupsAndACaller, AllowedResourceGroupsPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ReadingAnUnknownDomainsAllowedIsNotFound(
    Scenario[
        SeedingSession, ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "reading-the-groups-allowed-for-a-domain-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "존재하지 않는 도메인 이름의 허용 목록을 읽으려 하면 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ADomainGroupsAndACaller]:
        return ADomainGroupsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload]:
        return ReadingTheDomainsAllowed(unknown=True)

    @override
    def then(self) -> Then[ADomainGroupsAndACaller, AllowedResourceGroupsPayload]:
        return TheCallIsRefused(EntityNotFoundError)


# ------------------------------------------------------------------ scenarios: project side


@dataclass(frozen=True)
class TheSuperadminAllowsAGroupForAProject(
    Scenario[
        SeedingSession, AProjectAGroupAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-allows-a-resource-group-for-a-project"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 프로젝트의 허용 목록에 그룹을 더하면 그 그룹 이름이 담긴 목록이 반환된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AProjectAGroupAndACaller]:
        return AProjectAGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[AProjectAGroupAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload]:
        return AllowingForTheProject()

    @override
    def then(self) -> Then[AProjectAGroupAndACaller, AllowedResourceGroupsPayload]:
        return TheGroupIsAllowedForTheProject()


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotAllowForAProject(
    Scenario[
        SeedingSession, AProjectAGroupAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-allow-a-group-for-a-project"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 프로젝트의 허용 목록에 그룹을 더하려 하면 역할 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AProjectAGroupAndACaller]:
        return AProjectAGroupAndSomeone()

    @override
    def when(
        self,
    ) -> When[AProjectAGroupAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload]:
        return AllowingForTheProject()

    @override
    def then(self) -> Then[AProjectAGroupAndACaller, AllowedResourceGroupsPayload]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class TheSuperadminReadsAProjectsAllowed(
    Scenario[
        SeedingSession, AProjectAGroupAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reads-the-groups-allowed-for-a-project"

    @override
    def describe(self) -> str:
        return "프로젝트에 건 그룹이 있을 때 슈퍼관리자가 프로젝트의 허용 목록을 읽으면 건 그룹 이름이 담긴다"

    @override
    def given(self) -> Given[SeedingSession, AProjectAGroupAndACaller]:
        return AProjectAGroupAndSomeone(role=UserRole.SUPERADMIN, linked=True)

    @override
    def when(
        self,
    ) -> When[AProjectAGroupAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload]:
        return ReadingTheProjectsAllowed()

    @override
    def then(self) -> Then[AProjectAGroupAndACaller, AllowedResourceGroupsPayload]:
        return TheGroupIsAllowedForTheProject()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadAProjectsAllowed(
    Scenario[
        SeedingSession, AProjectAGroupAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-the-groups-allowed-for-a-project"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 프로젝트의 허용 목록을 읽으려 하면 권한 부족으로 거부된다. "
            "자기 도메인, 그 프로젝트, 자기 자신 세 스코프 모두에서 읽을 수 있어야 한다"
        )

    @override
    def given(self) -> Given[SeedingSession, AProjectAGroupAndACaller]:
        return AProjectAGroupAndSomeone(linked=True)

    @override
    def when(
        self,
    ) -> When[AProjectAGroupAndACaller, ResourceGroupAdapter, AllowedResourceGroupsPayload]:
        return ReadingTheProjectsAllowed()

    @override
    def then(self) -> Then[AProjectAGroupAndACaller, AllowedResourceGroupsPayload]:
        return TheCallIsRefused(NotEnoughPermission)


# ------------------------------------------------------------------ scenarios: group side


@dataclass(frozen=True)
class TheSuperadminAllowsADomainForAGroup(
    Scenario[SeedingSession, ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedDomainsPayload]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-allows-a-domain-for-a-resource-group"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 그룹의 허용 도메인에 도메인을 더하면 그 도메인 이름이 담긴 목록이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, ADomainGroupsAndACaller]:
        return ADomainGroupsAndSomeone(role=UserRole.SUPERADMIN, linked=False)

    @override
    def when(self) -> When[ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedDomainsPayload]:
        return AllowingADomainForTheGroup()

    @override
    def then(self) -> Then[ADomainGroupsAndACaller, AllowedDomainsPayload]:
        return TheAllowedDomainNames()


@dataclass(frozen=True)
class AllowingAnUnknownDomainForAGroupIsNotFound(
    Scenario[SeedingSession, ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedDomainsPayload]
):
    @override
    def summary(self) -> str:
        return "allowing-a-domain-name-nothing-answers-to-for-a-group-is-not-found"

    @override
    def describe(self) -> str:
        return "존재하지 않는 도메인 이름을 그룹의 허용 도메인에 더하려 하면 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ADomainGroupsAndACaller]:
        return ADomainGroupsAndSomeone(role=UserRole.SUPERADMIN, linked=False)

    @override
    def when(self) -> When[ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedDomainsPayload]:
        return AllowingADomainForTheGroup(unknown=True)

    @override
    def then(self) -> Then[ADomainGroupsAndACaller, AllowedDomainsPayload]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class DisallowingAnUnknownDomainForAGroupIsNotFound(
    Scenario[SeedingSession, ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedDomainsPayload]
):
    @override
    def summary(self) -> str:
        return "disallowing-a-domain-name-nothing-answers-to-for-a-group-is-not-found"

    @override
    def describe(self) -> str:
        return (
            "존재하지 않는 도메인 이름을 그룹의 허용 도메인에서 빼려 하면 건너뛰지 않고 대상을 찾을 수 "
            "없다는 이유로 거부된다. 도메인 쪽에서 없는 그룹 이름을 빼는 것은 건너뛴다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADomainGroupsAndACaller]:
        return ADomainGroupsAndSomeone(role=UserRole.SUPERADMIN, linked=False)

    @override
    def when(self) -> When[ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedDomainsPayload]:
        return AllowingADomainForTheGroup(remove=True, unknown=True)

    @override
    def then(self) -> Then[ADomainGroupsAndACaller, AllowedDomainsPayload]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotAllowADomainForAGroup(
    Scenario[SeedingSession, ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedDomainsPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-allow-a-domain-for-a-resource-group"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 그룹의 허용 도메인에 도메인을 더하려 하면 권한 부족으로 거부된다. "
            "관계를 쓰는 자리가 양쪽 스코프의 권한을 검사한다"
        )

    @override
    def given(self) -> Given[SeedingSession, ADomainGroupsAndACaller]:
        return ADomainGroupsAndSomeone(linked=False)

    @override
    def when(self) -> When[ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedDomainsPayload]:
        return AllowingADomainForTheGroup()

    @override
    def then(self) -> Then[ADomainGroupsAndACaller, AllowedDomainsPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminReadsAGroupsDomains(
    Scenario[SeedingSession, ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedDomainsPayload]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reads-the-domains-allowed-for-a-resource-group"

    @override
    def describe(self) -> str:
        return "도메인에 건 그룹의 허용 도메인을 슈퍼관리자가 읽으면 그 도메인 이름이 담긴다"

    @override
    def given(self) -> Given[SeedingSession, ADomainGroupsAndACaller]:
        return ADomainGroupsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedDomainsPayload]:
        return ReadingTheGroupsDomains()

    @override
    def then(self) -> Then[ADomainGroupsAndACaller, AllowedDomainsPayload]:
        return TheAllowedDomainNames()


@dataclass(frozen=True)
class AUserGrantedReadOnTheGroupReadsItsDomains(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, AllowedDomainsPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-on-the-group-reads-the-domains-allowed-for-it"

    @override
    def describe(self) -> str:
        return "그 그룹에 앉힌 역할로 읽기 권한을 받은 사용자가 그룹의 허용 도메인을 읽으면 걸린 도메인이 없어 빈 목록이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(granted=Permission.READ)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, AllowedDomainsPayload]:
        return ReadingTheOwnGroupsDomains()

    @override
    def then(self) -> Then[AGroupAndACaller, AllowedDomainsPayload]:
        return NothingIsAllowed()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadAGroupsDomains(
    Scenario[SeedingSession, AGroupAndACaller, ResourceGroupAdapter, AllowedDomainsPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-the-domains-allowed-for-a-resource-group"

    @override
    def describe(self) -> str:
        return "아무 권한도 없는 사용자가 그룹의 허용 도메인을 읽으려 하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone()

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, AllowedDomainsPayload]:
        return ReadingTheOwnGroupsDomains()

    @override
    def then(self) -> Then[AGroupAndACaller, AllowedDomainsPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminAllowsAProjectForAGroup(
    Scenario[SeedingSession, AProjectAGroupAndACaller, ResourceGroupAdapter, AllowedProjectsPayload]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-allows-a-project-for-a-resource-group"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 그룹의 허용 프로젝트에 프로젝트를 더하면 그 프로젝트 id가 담긴 목록이 반환된다"

    @override
    def given(self) -> Given[SeedingSession, AProjectAGroupAndACaller]:
        return AProjectAGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AProjectAGroupAndACaller, ResourceGroupAdapter, AllowedProjectsPayload]:
        return AllowingAProjectForTheGroup()

    @override
    def then(self) -> Then[AProjectAGroupAndACaller, AllowedProjectsPayload]:
        return TheAllowedProjectIds()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotAllowAProjectForAGroup(
    Scenario[SeedingSession, AProjectAGroupAndACaller, ResourceGroupAdapter, AllowedProjectsPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-allow-a-project-for-a-resource-group"

    @override
    def describe(self) -> str:
        return "아무 권한도 없는 사용자가 그룹의 허용 프로젝트에 프로젝트를 더하려 하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AProjectAGroupAndACaller]:
        return AProjectAGroupAndSomeone()

    @override
    def when(self) -> When[AProjectAGroupAndACaller, ResourceGroupAdapter, AllowedProjectsPayload]:
        return AllowingAProjectForTheGroup()

    @override
    def then(self) -> Then[AProjectAGroupAndACaller, AllowedProjectsPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminReadsAGroupsProjects(
    Scenario[SeedingSession, AProjectAGroupAndACaller, ResourceGroupAdapter, AllowedProjectsPayload]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reads-the-projects-allowed-for-a-resource-group"

    @override
    def describe(self) -> str:
        return "프로젝트에 건 그룹의 허용 프로젝트를 슈퍼관리자가 읽으면 그 프로젝트 id가 담긴다"

    @override
    def given(self) -> Given[SeedingSession, AProjectAGroupAndACaller]:
        return AProjectAGroupAndSomeone(role=UserRole.SUPERADMIN, linked=True)

    @override
    def when(self) -> When[AProjectAGroupAndACaller, ResourceGroupAdapter, AllowedProjectsPayload]:
        return ReadingTheGroupsProjects()

    @override
    def then(self) -> Then[AProjectAGroupAndACaller, AllowedProjectsPayload]:
        return TheAllowedProjectIds()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadAGroupsProjects(
    Scenario[SeedingSession, AProjectAGroupAndACaller, ResourceGroupAdapter, AllowedProjectsPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-the-projects-allowed-for-a-resource-group"

    @override
    def describe(self) -> str:
        return "아무 권한도 없는 사용자가 그룹의 허용 프로젝트를 읽으려 하면 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AProjectAGroupAndACaller]:
        return AProjectAGroupAndSomeone(linked=True)

    @override
    def when(self) -> When[AProjectAGroupAndACaller, ResourceGroupAdapter, AllowedProjectsPayload]:
        return ReadingTheGroupsProjects()

    @override
    def then(self) -> Then[AProjectAGroupAndACaller, AllowedProjectsPayload]:
        return TheCallIsRefused(NotEnoughPermission)


SCENARIOS: list[AllowingStep] = [
    TheSuperadminAllowsAGroupForADomain(),
    TheSuperadminDisallowsAGroupForADomain(),
    AllowingAnUnknownGroupForADomainIsNotFound(),
    DisallowingAnUnknownGroupForADomainIsSkipped(),
    AUserWhoIsNotTheSuperadminMayNotAllowForADomain(),
    TheSuperadminReadsADomainsAllowed(),
    AUserReadingInTheDomainReadsItsAllowed(),
    AUserGrantedNothingMayNotReadADomainsAllowed(),
    ReadingAnUnknownDomainsAllowedIsNotFound(),
    TheSuperadminAllowsAGroupForAProject(),
    AUserWhoIsNotTheSuperadminMayNotAllowForAProject(),
    TheSuperadminReadsAProjectsAllowed(),
    AUserGrantedNothingMayNotReadAProjectsAllowed(),
    TheSuperadminAllowsADomainForAGroup(),
    AllowingAnUnknownDomainForAGroupIsNotFound(),
    DisallowingAnUnknownDomainForAGroupIsNotFound(),
    AUserGrantedNothingMayNotAllowADomainForAGroup(),
    TheSuperadminReadsAGroupsDomains(),
    AUserGrantedReadOnTheGroupReadsItsDomains(),
    AUserGrantedNothingMayNotReadAGroupsDomains(),
    TheSuperadminAllowsAProjectForAGroup(),
    AUserGrantedNothingMayNotAllowAProjectForAGroup(),
    TheSuperadminReadsAGroupsProjects(),
    AUserGrantedNothingMayNotReadAGroupsProjects(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_allowing(
    scenario: AllowingStep, adapter: ResourceGroupAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
