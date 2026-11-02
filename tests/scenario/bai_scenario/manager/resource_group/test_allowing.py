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
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
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
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type AllowingStep = Scenario[TestSeedingSession, Any, ResourceGroupAdapter, Any]

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
        if self.unknown:
            what_ko = "없는 자원 그룹 이름을"
            what_en = "an unknown resource group name"
        else:
            name = laid.linked.name if self.remove else laid.other.name
            what_ko = f"{name} 을"
            what_en = name
        if self.remove:
            verb_ko = "제거합니다"
            verb_en = "removes"
        else:
            verb_ko = "추가합니다"
            verb_en = "adds"
        return Says(
            f"{laid.caller.username}이 도메인 {laid.domain.name}의 허용 목록에 {what_ko} {verb_ko}",
            english=(
                f"{laid.caller.username} {verb_en} {what_en} in the allow list of "
                f"domain {laid.domain.name}"
            ),
        )

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
        target_ko = "존재하지 않는 도메인" if self.unknown else f"도메인 {laid.domain.name}"
        target_en = "a domain that does not exist" if self.unknown else f"domain {laid.domain.name}"
        return Says(
            f"{laid.caller.username}이 {target_ko}의 허용 목록을 조회합니다",
            english=f"{laid.caller.username} reads the allow list of {target_en}",
        )

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
        return Says(
            f"{laid.caller.username}이 프로젝트 {laid.project.name}의 허용 목록에 "
            f"{laid.group.name} 을 추가합니다",
            english=(
                f"{laid.caller.username} adds {laid.group.name} to the allow list of "
                f"project {laid.project.name}"
            ),
        )

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
        return Says(
            f"{laid.caller.username}이 프로젝트 {laid.project.name}의 허용 목록을 조회합니다",
            english=(f"{laid.caller.username} reads the allow list of project {laid.project.name}"),
        )

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
        what_ko = "없는 도메인 이름을" if self.unknown else f"{laid.domain.name} 을"
        what_en = "an unknown domain name" if self.unknown else laid.domain.name
        if self.remove:
            verb_ko = "제거합니다"
            verb_en = "removes"
        else:
            verb_ko = "추가합니다"
            verb_en = "adds"
        return Says(
            f"{laid.caller.username}이 {laid.other.name}의 허용 도메인에 {what_ko} {verb_ko}",
            english=(
                f"{laid.caller.username} {verb_en} {what_en} in the allowed domains of "
                f"{laid.other.name}"
            ),
        )

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
        return Says(
            f"{laid.caller.username}이 {laid.linked.name}의 허용 도메인을 조회합니다",
            english=(f"{laid.caller.username} reads the allowed domains of {laid.linked.name}"),
        )

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
        return Says(
            f"{laid.caller.username}이 {laid.group.name}의 허용 프로젝트에 "
            f"{laid.project.name} 을 추가합니다",
            english=(
                f"{laid.caller.username} adds {laid.project.name} to the allowed projects of "
                f"{laid.group.name}"
            ),
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
        return Says(
            f"{laid.caller.username}이 {laid.group.name}의 허용 프로젝트를 조회합니다",
            english=(f"{laid.caller.username} reads the allowed projects of {laid.group.name}"),
        )

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
        return Says(
            f"{laid.caller.username}이 {laid.group.name}의 허용 도메인을 조회합니다",
            english=f"{laid.caller.username} reads the allowed domains of {laid.group.name}",
        )

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
        TestSeedingSession,
        ADomainGroupsAndACaller,
        ResourceGroupAdapter,
        AllowedResourceGroupsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-allows-a-resource-group-for-a-domain"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 도메인의 허용 목록에 자원 그룹을 추가하면 그 그룹 이름이 담긴 목록이 반환됩니다",
            english=(
                "when the superadmin adds a resource group to the allow list of a domain, "
                "the list holding that group name comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainGroupsAndACaller]:
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
        TestSeedingSession,
        ADomainGroupsAndACaller,
        ResourceGroupAdapter,
        AllowedResourceGroupsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-disallows-a-resource-group-for-a-domain"

    @override
    def describe(self) -> str:
        return Says(
            "도메인에 건 자원 그룹을 superadmin 이 허용 목록에서 제거하면 빈 목록이 반환됩니다",
            english=(
                "when the superadmin removes the resource group linked to a domain from the "
                "allow list, an empty list comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainGroupsAndACaller]:
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
        TestSeedingSession,
        ADomainGroupsAndACaller,
        ResourceGroupAdapter,
        AllowedResourceGroupsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "allowing-a-group-name-nothing-answers-to-for-a-domain-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "존재하지 않는 자원 그룹 이름을 도메인의 허용 목록에 추가하려 하면 "
            "대상을 찾을 수 없다는 이유로 거부됩니다",
            english=(
                "adding a resource group name nothing answers to to the allow list of a "
                "domain is rejected because no target answers to it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainGroupsAndACaller]:
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
        TestSeedingSession,
        ADomainGroupsAndACaller,
        ResourceGroupAdapter,
        AllowedResourceGroupsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "disallowing-a-group-name-nothing-answers-to-for-a-domain-is-skipped"

    @override
    def describe(self) -> str:
        return Says(
            "존재하지 않는 자원 그룹 이름을 도메인의 허용 목록에서 제거하려 하면 그 이름은 "
            "건너뛰고 빈 목록이 반환됩니다",
            english=(
                "removing a resource group name nothing answers to from the allow list of a "
                "domain skips that name and an empty list comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainGroupsAndACaller]:
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
        TestSeedingSession,
        ADomainGroupsAndACaller,
        ResourceGroupAdapter,
        AllowedResourceGroupsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-allow-a-group-for-a-domain"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 도메인의 허용 목록에 자원 그룹을 추가하려 하면 "
            "역할 부족으로 거부됩니다. 자원 그룹 이름을 id 로 바꾸는 단계가 superadmin 검사를 "
            "거칩니다",
            english=(
                "when a user who is not the superadmin tries to add a resource group to the "
                "allow list of a domain, the call is rejected for lacking the role. the step "
                "that turns the resource group name into an id goes through the superadmin check"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainGroupsAndACaller]:
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
        TestSeedingSession,
        ADomainGroupsAndACaller,
        ResourceGroupAdapter,
        AllowedResourceGroupsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reads-the-groups-allowed-for-a-domain"

    @override
    def describe(self) -> str:
        return Says(
            "도메인에 건 자원 그룹과 걸지 않은 자원 그룹이 있을 때 superadmin 이 도메인의 허용 "
            "목록을 읽으면 건 자원 그룹 이름만 담깁니다",
            english=(
                "when one resource group is linked to a domain and one is not, reading the "
                "allow list of that domain as the superadmin answers only the linked group name"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainGroupsAndACaller]:
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
        TestSeedingSession,
        ADomainGroupsAndACaller,
        ResourceGroupAdapter,
        AllowedResourceGroupsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-in-the-domain-reads-the-groups-allowed-for-it"

    @override
    def describe(self) -> str:
        return Says(
            "도메인 범위에서 자원 그룹 읽기 역할을 받은 사용자가 그 도메인의 허용 목록을 읽으면 "
            "건 자원 그룹 이름만 담깁니다",
            english=(
                "a user granted the resource group read role in the domain scope reading the "
                "allow list of that domain gets only the linked group name"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainGroupsAndACaller]:
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
        TestSeedingSession,
        ADomainGroupsAndACaller,
        ResourceGroupAdapter,
        AllowedResourceGroupsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-the-groups-allowed-for-a-domain"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 자기 도메인의 허용 목록을 읽으려 하면 권한 부족으로 "
            "거부됩니다",
            english=(
                "a user granted nothing trying to read the allow list of their own domain is "
                "rejected for not enough permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainGroupsAndACaller]:
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
        TestSeedingSession,
        ADomainGroupsAndACaller,
        ResourceGroupAdapter,
        AllowedResourceGroupsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "reading-the-groups-allowed-for-a-domain-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "존재하지 않는 도메인 이름의 허용 목록을 읽으려 하면 대상을 찾을 수 없다는 이유로 "
            "거부됩니다",
            english=(
                "reading the allow list of a domain name nothing answers to is rejected "
                "because no target answers to it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainGroupsAndACaller]:
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
        TestSeedingSession,
        AProjectAGroupAndACaller,
        ResourceGroupAdapter,
        AllowedResourceGroupsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-allows-a-resource-group-for-a-project"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 프로젝트의 허용 목록에 자원 그룹을 추가하면 그 그룹 이름이 담긴 "
            "목록이 반환됩니다",
            english=(
                "when the superadmin adds a resource group to the allow list of a project, "
                "the list holding that group name comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AProjectAGroupAndACaller]:
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
        TestSeedingSession,
        AProjectAGroupAndACaller,
        ResourceGroupAdapter,
        AllowedResourceGroupsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-allow-a-group-for-a-project"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 프로젝트의 허용 목록에 자원 그룹을 추가하려 하면 "
            "역할 부족으로 거부됩니다",
            english=(
                "when a user who is not the superadmin tries to add a resource group to the "
                "allow list of a project, the call is rejected for lacking the role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AProjectAGroupAndACaller]:
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
        TestSeedingSession,
        AProjectAGroupAndACaller,
        ResourceGroupAdapter,
        AllowedResourceGroupsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reads-the-groups-allowed-for-a-project"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트에 건 자원 그룹이 있을 때 superadmin 이 프로젝트의 허용 목록을 읽으면 "
            "건 자원 그룹 이름이 담깁니다",
            english=(
                "when a resource group is linked to a project, reading the allow list of that "
                "project as the superadmin answers the linked group name"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AProjectAGroupAndACaller]:
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
        TestSeedingSession,
        AProjectAGroupAndACaller,
        ResourceGroupAdapter,
        AllowedResourceGroupsPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-the-groups-allowed-for-a-project"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 프로젝트의 허용 목록을 읽으려 하면 권한 부족으로 "
            "거부됩니다. 자기 도메인, 그 프로젝트, 자기 자신 세 스코프 모두에서 읽을 수 있어야 "
            "합니다",
            english=(
                "a user granted nothing trying to read the allow list of a project is rejected "
                "for not enough permission. reading has to be allowed in all three scopes, the "
                "caller's domain, the project and the caller themself"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AProjectAGroupAndACaller]:
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
    Scenario[
        TestSeedingSession, ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedDomainsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-allows-a-domain-for-a-resource-group"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 자원 그룹의 허용 도메인에 도메인을 추가하면 그 도메인 이름이 담긴 "
            "목록이 반환됩니다",
            english=(
                "when the superadmin adds a domain to the allowed domains of a resource group, "
                "the list holding that domain name comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainGroupsAndACaller]:
        return ADomainGroupsAndSomeone(role=UserRole.SUPERADMIN, linked=False)

    @override
    def when(self) -> When[ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedDomainsPayload]:
        return AllowingADomainForTheGroup()

    @override
    def then(self) -> Then[ADomainGroupsAndACaller, AllowedDomainsPayload]:
        return TheAllowedDomainNames()


@dataclass(frozen=True)
class AllowingAnUnknownDomainForAGroupIsNotFound(
    Scenario[
        TestSeedingSession, ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedDomainsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "allowing-a-domain-name-nothing-answers-to-for-a-group-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "존재하지 않는 도메인 이름을 자원 그룹의 허용 도메인에 추가하려 하면 대상을 찾을 수 "
            "없다는 이유로 거부됩니다",
            english=(
                "adding a domain name nothing answers to to the allowed domains of a resource "
                "group is rejected because no target answers to it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainGroupsAndACaller]:
        return ADomainGroupsAndSomeone(role=UserRole.SUPERADMIN, linked=False)

    @override
    def when(self) -> When[ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedDomainsPayload]:
        return AllowingADomainForTheGroup(unknown=True)

    @override
    def then(self) -> Then[ADomainGroupsAndACaller, AllowedDomainsPayload]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class DisallowingAnUnknownDomainForAGroupIsNotFound(
    Scenario[
        TestSeedingSession, ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedDomainsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "disallowing-a-domain-name-nothing-answers-to-for-a-group-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "존재하지 않는 도메인 이름을 자원 그룹의 허용 도메인에서 제거하려 하면 건너뛰지 않고 "
            "대상을 찾을 수 없다는 이유로 거부됩니다. 도메인 쪽에서 없는 자원 그룹 이름을 "
            "제거하는 것은 건너뜁니다",
            english=(
                "removing a domain name nothing answers to from the allowed domains of a "
                "resource group is rejected because no target answers to it instead of being "
                "skipped. removing an unknown resource group name on the domain side is skipped"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainGroupsAndACaller]:
        return ADomainGroupsAndSomeone(role=UserRole.SUPERADMIN, linked=False)

    @override
    def when(self) -> When[ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedDomainsPayload]:
        return AllowingADomainForTheGroup(remove=True, unknown=True)

    @override
    def then(self) -> Then[ADomainGroupsAndACaller, AllowedDomainsPayload]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotAllowADomainForAGroup(
    Scenario[
        TestSeedingSession, ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedDomainsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-allow-a-domain-for-a-resource-group"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 자원 그룹의 허용 도메인에 도메인을 추가하려 하면 권한 "
            "부족으로 거부됩니다. 관계를 쓰는 단계가 양쪽 스코프의 권한을 검사합니다",
            english=(
                "a user granted nothing trying to add a domain to the allowed domains of a "
                "resource group is rejected for not enough permission. the step that writes "
                "the relation checks the permission of both scopes"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainGroupsAndACaller]:
        return ADomainGroupsAndSomeone(linked=False)

    @override
    def when(self) -> When[ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedDomainsPayload]:
        return AllowingADomainForTheGroup()

    @override
    def then(self) -> Then[ADomainGroupsAndACaller, AllowedDomainsPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminReadsAGroupsDomains(
    Scenario[
        TestSeedingSession, ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedDomainsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reads-the-domains-allowed-for-a-resource-group"

    @override
    def describe(self) -> str:
        return Says(
            "도메인에 건 자원 그룹의 허용 도메인을 superadmin 이 읽으면 그 도메인 이름이 담깁니다",
            english=(
                "when the superadmin reads the allowed domains of a resource group linked to a "
                "domain, that domain name comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ADomainGroupsAndACaller]:
        return ADomainGroupsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ADomainGroupsAndACaller, ResourceGroupAdapter, AllowedDomainsPayload]:
        return ReadingTheGroupsDomains()

    @override
    def then(self) -> Then[ADomainGroupsAndACaller, AllowedDomainsPayload]:
        return TheAllowedDomainNames()


@dataclass(frozen=True)
class AUserGrantedReadOnTheGroupReadsItsDomains(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, AllowedDomainsPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-on-the-group-reads-the-domains-allowed-for-it"

    @override
    def describe(self) -> str:
        return Says(
            "그 자원 그룹에 부여된 역할로 읽기 권한을 받은 사용자가 자원 그룹의 허용 도메인을 "
            "읽으면 걸린 도메인이 없어 빈 목록이 반환됩니다",
            english=(
                "a user granted read through the role granted on the resource group reading the "
                "allowed domains of the group gets an empty list because no domain is linked"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone(granted=Permission.READ)

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, AllowedDomainsPayload]:
        return ReadingTheOwnGroupsDomains()

    @override
    def then(self) -> Then[AGroupAndACaller, AllowedDomainsPayload]:
        return NothingIsAllowed()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadAGroupsDomains(
    Scenario[TestSeedingSession, AGroupAndACaller, ResourceGroupAdapter, AllowedDomainsPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-the-domains-allowed-for-a-resource-group"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 자원 그룹의 허용 도메인을 읽으려 하면 권한 부족으로 "
            "거부됩니다",
            english=(
                "a user granted nothing trying to read the allowed domains of a resource group "
                "is rejected for not enough permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AGroupAndACaller]:
        return AGroupAndSomeone()

    @override
    def when(self) -> When[AGroupAndACaller, ResourceGroupAdapter, AllowedDomainsPayload]:
        return ReadingTheOwnGroupsDomains()

    @override
    def then(self) -> Then[AGroupAndACaller, AllowedDomainsPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminAllowsAProjectForAGroup(
    Scenario[
        TestSeedingSession, AProjectAGroupAndACaller, ResourceGroupAdapter, AllowedProjectsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-allows-a-project-for-a-resource-group"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 자원 그룹의 허용 프로젝트에 프로젝트를 추가하면 그 프로젝트 id 가 "
            "담긴 목록이 반환됩니다",
            english=(
                "when the superadmin adds a project to the allowed projects of a resource "
                "group, the list holding that project id comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AProjectAGroupAndACaller]:
        return AProjectAGroupAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AProjectAGroupAndACaller, ResourceGroupAdapter, AllowedProjectsPayload]:
        return AllowingAProjectForTheGroup()

    @override
    def then(self) -> Then[AProjectAGroupAndACaller, AllowedProjectsPayload]:
        return TheAllowedProjectIds()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotAllowAProjectForAGroup(
    Scenario[
        TestSeedingSession, AProjectAGroupAndACaller, ResourceGroupAdapter, AllowedProjectsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-allow-a-project-for-a-resource-group"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 자원 그룹의 허용 프로젝트에 프로젝트를 추가하려 하면 "
            "권한 부족으로 거부됩니다",
            english=(
                "a user granted nothing trying to add a project to the allowed projects of a "
                "resource group is rejected for not enough permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AProjectAGroupAndACaller]:
        return AProjectAGroupAndSomeone()

    @override
    def when(self) -> When[AProjectAGroupAndACaller, ResourceGroupAdapter, AllowedProjectsPayload]:
        return AllowingAProjectForTheGroup()

    @override
    def then(self) -> Then[AProjectAGroupAndACaller, AllowedProjectsPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminReadsAGroupsProjects(
    Scenario[
        TestSeedingSession, AProjectAGroupAndACaller, ResourceGroupAdapter, AllowedProjectsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reads-the-projects-allowed-for-a-resource-group"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트에 건 자원 그룹의 허용 프로젝트를 superadmin 이 읽으면 그 프로젝트 id 가 "
            "담깁니다",
            english=(
                "when the superadmin reads the allowed projects of a resource group linked to a "
                "project, that project id comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AProjectAGroupAndACaller]:
        return AProjectAGroupAndSomeone(role=UserRole.SUPERADMIN, linked=True)

    @override
    def when(self) -> When[AProjectAGroupAndACaller, ResourceGroupAdapter, AllowedProjectsPayload]:
        return ReadingTheGroupsProjects()

    @override
    def then(self) -> Then[AProjectAGroupAndACaller, AllowedProjectsPayload]:
        return TheAllowedProjectIds()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadAGroupsProjects(
    Scenario[
        TestSeedingSession, AProjectAGroupAndACaller, ResourceGroupAdapter, AllowedProjectsPayload
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-the-projects-allowed-for-a-resource-group"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 자원 그룹의 허용 프로젝트를 읽으려 하면 권한 부족으로 "
            "거부됩니다",
            english=(
                "a user granted nothing trying to read the allowed projects of a resource group "
                "is rejected for not enough permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AProjectAGroupAndACaller]:
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
