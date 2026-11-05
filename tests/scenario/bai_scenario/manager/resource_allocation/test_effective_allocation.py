"""유효 자원 할당 — 호출자 경로와 관리자 경로, 그리고 표시 설정이 무엇을 담는가."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_allocation.request import (
    AdminEffectiveResourceAllocationInput,
    EffectiveResourceAllocationInput,
)
from ai.backend.common.dto.manager.v2.resource_allocation.response import (
    EffectiveResourceAllocationPayload,
)
from ai.backend.manager.api.adapters.resource_allocation.adapter import (
    ResourceAllocationAdapter,
)
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.resource import DomainNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Configured,
    Given,
    Says,
    Scenario,
    Then,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.resource_allocation_usage import (
    APlaceAndSomeone,
    AUsagePlace,
    TheEffectiveAllocation,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

GROUP_RESOURCE_VISIBILITY = "api.resources.group_resource_visibility"
HIDE_AGENTS = "manager.hide_agents"

type AskingStep = Scenario[
    TestSeedingSession, AUsagePlace, ResourceAllocationAdapter, EffectiveResourceAllocationPayload
]


@dataclass(frozen=True)
class AskingForMyEffectiveAllocation(
    When[AUsagePlace, ResourceAllocationAdapter, EffectiveResourceAllocationPayload]
):
    """호출자 자신의 키페어로 유효 할당을 읽는다."""

    @override
    def operation(self) -> str:
        return "effective_allocation_for_current_user"

    @override
    def describe(self, laid: AUsagePlace) -> str:
        return Says(
            f"{laid.caller.username}이 자기 유효 할당을 조회합니다",
            english=f"{laid.caller.username} reads their own effective allocation",
        )

    @override
    async def call(
        self, adapter: ResourceAllocationAdapter, laid: AUsagePlace
    ) -> EffectiveResourceAllocationPayload:
        with ActingAs(laid.caller):
            return await adapter.effective_allocation_for_current_user(
                EffectiveResourceAllocationInput(
                    project_id=laid.project.id, resource_group_name=laid.group.name
                )
            )


@dataclass(frozen=True)
class AskingForTheEffectiveAllocation(
    When[AUsagePlace, ResourceAllocationAdapter, EffectiveResourceAllocationPayload]
):
    """미리 만들어 둔 키페어의 접근 키와 정책으로 유효 할당을 읽는다."""

    @override
    def operation(self) -> str:
        return "effective_allocation"

    @override
    def describe(self, laid: AUsagePlace) -> str:
        return Says(
            f"{laid.caller.username}이 프로젝트 {laid.project.name}의 유효 할당을 조회합니다",
            english=(
                f"{laid.caller.username} reads the effective allocation of the project "
                f"{laid.project.name}"
            ),
        )

    @override
    async def call(
        self, adapter: ResourceAllocationAdapter, laid: AUsagePlace
    ) -> EffectiveResourceAllocationPayload:
        with ActingAs(laid.caller):
            return await adapter.effective_allocation(
                input=EffectiveResourceAllocationInput(
                    project_id=laid.project.id, resource_group_name=laid.group.name
                ),
                access_key=str(laid.access_key),
                resource_policy=laid.resource_policy,
            )


@dataclass(frozen=True)
class AskingAsAdminResolved(
    When[AUsagePlace, ResourceAllocationAdapter, EffectiveResourceAllocationPayload]
):
    """대상 사용자 id 로 관리자 경로의 유효 할당을 읽는다."""

    @override
    def operation(self) -> str:
        return "admin_effective_allocation_resolved"

    @override
    def describe(self, laid: AUsagePlace) -> str:
        return Says(
            f"{laid.caller.username}이 사용자 {laid.caller.username}의 유효 할당을 관리자 "
            "경로로 조회합니다",
            english=(
                f"{laid.caller.username} reads the effective allocation of "
                f"{laid.caller.username} by the admin path"
            ),
        )

    @override
    async def call(
        self, adapter: ResourceAllocationAdapter, laid: AUsagePlace
    ) -> EffectiveResourceAllocationPayload:
        with ActingAs(laid.caller):
            return await adapter.admin_effective_allocation_resolved(
                AdminEffectiveResourceAllocationInput(
                    user_id=laid.caller.id,
                    project_id=laid.project.id,
                    resource_group_name=laid.group.name,
                )
            )


@dataclass(frozen=True)
class AskingAsAdmin(
    When[AUsagePlace, ResourceAllocationAdapter, EffectiveResourceAllocationPayload]
):
    """대상 사용자의 접근 키와 정책을 직접 주어 관리자 경로의 유효 할당을 읽는다."""

    @override
    def operation(self) -> str:
        return "admin_effective_allocation"

    @override
    def describe(self, laid: AUsagePlace) -> str:
        return Says(
            f"{laid.caller.username}이 관리자 경로로 유효 할당을 조회합니다",
            english=f"{laid.caller.username} reads the effective allocation by the admin path",
        )

    @override
    async def call(
        self, adapter: ResourceAllocationAdapter, laid: AUsagePlace
    ) -> EffectiveResourceAllocationPayload:
        with ActingAs(laid.caller):
            return await adapter.admin_effective_allocation(
                input=AdminEffectiveResourceAllocationInput(
                    user_id=laid.caller.id,
                    project_id=laid.project.id,
                    resource_group_name=laid.group.name,
                ),
                access_key=str(laid.access_key),
                resource_policy=laid.resource_policy,
            )


@dataclass(frozen=True)
class TheSuperadminReadsTheirEffectiveAllocation(
    Scenario[
        TestSeedingSession,
        AUsagePlace,
        ResourceAllocationAdapter,
        EffectiveResourceAllocationPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reads-their-own-effective-allocation"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 자기 유효 할당을 읽으면, 프로젝트와 자원 그룹 범위가 모두 담겨 "
            "반환됩니다",
            english=(
                "when the superadmin reads their own effective allocation, both the project and "
                "the resource group scopes are included"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AUsagePlace]:
        return APlaceAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[AUsagePlace, ResourceAllocationAdapter, EffectiveResourceAllocationPayload]:
        return AskingForMyEffectiveAllocation()

    @override
    def then(
        self,
    ) -> Then[AUsagePlace, EffectiveResourceAllocationPayload]:
        return TheEffectiveAllocation(project=True, resource_group=True)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadTheirEffectiveAllocation(
    Scenario[
        TestSeedingSession,
        AUsagePlace,
        ResourceAllocationAdapter,
        EffectiveResourceAllocationPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-their-own-effective-allocation"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 자기 유효 할당을 읽으려 하면 권한 부족으로 거부됩니다",
            english=(
                "a user granted nothing reading their own effective allocation is rejected for "
                "not enough permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AUsagePlace]:
        return APlaceAndSomeone()

    @override
    def when(
        self,
    ) -> When[AUsagePlace, ResourceAllocationAdapter, EffectiveResourceAllocationPayload]:
        return AskingForMyEffectiveAllocation()

    @override
    def then(self) -> Then[AUsagePlace, EffectiveResourceAllocationPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserReadingSessionsReadsTheEffectiveAllocation(
    Scenario[
        TestSeedingSession,
        AUsagePlace,
        ResourceAllocationAdapter,
        EffectiveResourceAllocationPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-reading-sessions-reads-the-effective-allocation"

    @override
    def describe(self) -> str:
        return Says(
            "프로젝트 범위에서 세션을 읽을 수 있는 사용자가 유효 할당을 읽으면, 기본 설정에서는 "
            "프로젝트 범위가 담기지 않고 자원 그룹 범위가 담깁니다",
            english=(
                "a user who can read sessions in the project scope reading the effective "
                "allocation gets the resource group scope but not the project scope under the "
                "default settings"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AUsagePlace]:
        return APlaceAndSomeone(sessions_read=True)

    @override
    def when(
        self,
    ) -> When[AUsagePlace, ResourceAllocationAdapter, EffectiveResourceAllocationPayload]:
        return AskingForTheEffectiveAllocation()

    @override
    def then(self) -> Then[AUsagePlace, EffectiveResourceAllocationPayload]:
        return TheEffectiveAllocation(project=False, resource_group=True)


@dataclass(frozen=True)
class TurningVisibilityOnShowsTheProject(
    Scenario[
        TestSeedingSession,
        AUsagePlace,
        ResourceAllocationAdapter,
        EffectiveResourceAllocationPayload,
    ],
    Configured,
):
    @override
    def summary(self) -> str:
        return "turning-group-resource-visibility-on-shows-the-project-scope"

    @override
    def describe(self) -> str:
        return Says(
            "자원 그룹 가시성을 켜면, 프로젝트 범위에서 세션을 읽을 수 있는 사용자의 유효 할당에 "
            "프로젝트 범위가 담깁니다",
            english=(
                "turning group resource visibility on puts the project scope into the effective "
                "allocation of a user who can read sessions in the project scope"
            ),
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {GROUP_RESOURCE_VISIBILITY: True}

    @override
    def given(self) -> Given[TestSeedingSession, AUsagePlace]:
        return APlaceAndSomeone(sessions_read=True)

    @override
    def when(
        self,
    ) -> When[AUsagePlace, ResourceAllocationAdapter, EffectiveResourceAllocationPayload]:
        return AskingForTheEffectiveAllocation()

    @override
    def then(self) -> Then[AUsagePlace, EffectiveResourceAllocationPayload]:
        return TheEffectiveAllocation(project=True, resource_group=True)


@dataclass(frozen=True)
class HidingAgentsDropsTheResourceGroup(
    Scenario[
        TestSeedingSession,
        AUsagePlace,
        ResourceAllocationAdapter,
        EffectiveResourceAllocationPayload,
    ],
    Configured,
):
    @override
    def summary(self) -> str:
        return "hiding-agents-drops-the-resource-group-scope"

    @override
    def describe(self) -> Says:
        return Says(
            "에이전트를 숨기면, 프로젝트 범위에서 세션을 읽을 수 있는 사용자의 유효 할당에서 "
            "자원 그룹 범위가 빠집니다",
            english=(
                "hiding agents drops the resource group scope from the effective allocation of a "
                "user who can read sessions in the project scope"
            ),
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {HIDE_AGENTS: True}

    @override
    def given(self) -> Given[TestSeedingSession, AUsagePlace]:
        return APlaceAndSomeone(sessions_read=True)

    @override
    def when(
        self,
    ) -> When[AUsagePlace, ResourceAllocationAdapter, EffectiveResourceAllocationPayload]:
        return AskingForTheEffectiveAllocation()

    @override
    def then(self) -> Then[AUsagePlace, EffectiveResourceAllocationPayload]:
        return TheEffectiveAllocation(project=False, resource_group=False)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadTheEffectiveAllocation(
    Scenario[
        TestSeedingSession,
        AUsagePlace,
        ResourceAllocationAdapter,
        EffectiveResourceAllocationPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-the-effective-allocation"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 사용자가 프로젝트의 유효 할당을 읽으려 하면 권한 부족으로 "
            "거부됩니다",
            english=(
                "a user granted nothing reading a project's effective allocation is rejected for "
                "not enough permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AUsagePlace]:
        return APlaceAndSomeone()

    @override
    def when(
        self,
    ) -> When[AUsagePlace, ResourceAllocationAdapter, EffectiveResourceAllocationPayload]:
        return AskingForTheEffectiveAllocation()

    @override
    def then(self) -> Then[AUsagePlace, EffectiveResourceAllocationPayload]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheAdminPathCannotReadWithoutADomain(
    Scenario[
        TestSeedingSession,
        AUsagePlace,
        ResourceAllocationAdapter,
        EffectiveResourceAllocationPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "the-admin-path-reading-a-users-effective-allocation-finds-no-domain"

    @override
    def describe(self) -> str:
        return Says(
            "대상 사용자 id 로 관리자 경로의 유효 할당을 읽으면, 도메인 이름을 비운 채 조회하므로 "
            "도메인을 찾을 수 없다는 것으로 거부됩니다",
            english=(
                "reading a user's effective allocation by the admin path is rejected as no such "
                "domain, because the call reads with an empty domain name"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AUsagePlace]:
        return APlaceAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[AUsagePlace, ResourceAllocationAdapter, EffectiveResourceAllocationPayload]:
        return AskingAsAdminResolved()

    @override
    def then(self) -> Then[AUsagePlace, EffectiveResourceAllocationPayload]:
        return TheCallIsRefused(DomainNotFound)


@dataclass(frozen=True)
class TheAdminPathWithAGivenKeyFindsNoDomain(
    Scenario[
        TestSeedingSession,
        AUsagePlace,
        ResourceAllocationAdapter,
        EffectiveResourceAllocationPayload,
    ]
):
    @override
    def summary(self) -> str:
        return "the-admin-path-with-a-given-key-finds-no-domain"

    @override
    def describe(self) -> str:
        return Says(
            "접근 키와 정책을 주어 관리자 경로의 유효 할당을 읽으면, 도메인 이름을 비운 채 "
            "조회하므로 도메인을 찾을 수 없다는 것으로 거부됩니다",
            english=(
                "reading the effective allocation by the admin path with a given key is rejected "
                "as no such domain, because the call reads with an empty domain name"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AUsagePlace]:
        return APlaceAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(
        self,
    ) -> When[AUsagePlace, ResourceAllocationAdapter, EffectiveResourceAllocationPayload]:
        return AskingAsAdmin()

    @override
    def then(self) -> Then[AUsagePlace, EffectiveResourceAllocationPayload]:
        return TheCallIsRefused(DomainNotFound)


SCENARIOS: list[AskingStep] = [
    TheSuperadminReadsTheirEffectiveAllocation(),
    AUserGrantedNothingMayNotReadTheirEffectiveAllocation(),
    AUserReadingSessionsReadsTheEffectiveAllocation(),
    TurningVisibilityOnShowsTheProject(),
    HidingAgentsDropsTheResourceGroup(),
    AUserGrantedNothingMayNotReadTheEffectiveAllocation(),
    TheAdminPathCannotReadWithoutADomain(),
    TheAdminPathWithAGivenKeyFindsNoDomain(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_effective_allocation(
    scenario: AskingStep, adapter: ResourceAllocationAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
