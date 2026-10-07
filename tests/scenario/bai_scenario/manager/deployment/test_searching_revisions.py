"""리비전 훑기 — 한 배포 안을 훑는 문과 리비전 하나의 자원 슬롯을 훑는 문은 그 배포의
읽기 권한이, 전체 리비전을 훑는 문은 역할이 지킨다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.entity.deployment_revision import DeploymentRevisionID
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import IntFilter
from ai.backend.common.dto.manager.v2.deployment.request import (
    AdminSearchRevisionsInput,
    RevisionFilter,
)
from ai.backend.common.dto.manager.v2.deployment.response import AdminSearchRevisionsPayload
from ai.backend.common.dto.manager.v2.resource_slot.request import (
    SearchAllocatedResourceSlotsInput,
)
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    SearchAllocatedResourceSlotsPayload,
)
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.data.deployment.types import RevisionOperationScope
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.deployment_revision import (
    ADeploymentToRevise,
    EveryLaidRevisionIsCounted,
    EveryRevisionSlotIsCounted,
    RevisionsAndACaller,
    RevisionsInTwoProjects,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

type Searched = AdminSearchRevisionsPayload
type Slots = SearchAllocatedResourceSlotsPayload
type SearchingStep = Scenario[SeedingSession, RevisionsAndACaller, DeploymentAdapter, Searched]
type SlotStep = Scenario[SeedingSession, RevisionsAndACaller, DeploymentAdapter, Slots]


@dataclass(frozen=True)
class SearchingTheDeployment(When[RevisionsAndACaller, DeploymentAdapter, Searched]):
    """부를 배포 하나의 리비전을 훑는다. ``number``를 대면 그 번호로 거른다."""

    number: int | None = None

    @override
    def operation(self) -> str:
        return "search_revisions"

    @override
    def describe(self, laid: RevisionsAndACaller) -> str:
        filtered = f" 번호 {self.number}로 걸러" if self.number is not None else ""
        return f"{laid.caller.username}이 {laid.deployment.metadata.name}의 리비전을{filtered} 조회"

    @override
    async def call(self, adapter: DeploymentAdapter, laid: RevisionsAndACaller) -> Searched:
        wanted = (
            RevisionFilter(revision_number=IntFilter(equals=self.number))
            if self.number is not None
            else None
        )
        with ActingAs(laid.caller):
            return await adapter.search_revisions(
                RevisionOperationScope(deployment_id=laid.deployment.id),
                AdminSearchRevisionsInput(filter=wanted),
            )


@dataclass(frozen=True)
class SearchingEveryRevision(When[RevisionsAndACaller, DeploymentAdapter, Searched]):
    """필터 없이 모든 배포의 리비전을 훑는다."""

    @override
    def operation(self) -> str:
        return "admin_search_revisions"

    @override
    def describe(self, laid: RevisionsAndACaller) -> str:
        return f"{laid.caller.username}이 필터 없이 모든 리비전을 조회"

    @override
    async def call(self, adapter: DeploymentAdapter, laid: RevisionsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search_revisions(AdminSearchRevisionsInput())


@dataclass(frozen=True)
class SearchingTheSlots(When[RevisionsAndACaller, DeploymentAdapter, Slots]):
    """심은 첫 리비전이 잡은 자원 슬롯을 훑는다."""

    @override
    def operation(self) -> str:
        return "search_revision_resource_slots"

    @override
    def describe(self, laid: RevisionsAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.deployment.metadata.name}의 첫 리비전의 슬롯을 조회"

    @override
    async def call(self, adapter: DeploymentAdapter, laid: RevisionsAndACaller) -> Slots:
        with ActingAs(laid.caller):
            return await adapter.search_revision_resource_slots(
                DeploymentRevisionID(laid.revisions[0].id),
                SearchAllocatedResourceSlotsInput(),
            )


@dataclass(frozen=True)
class TheGrantedUserCountsTheDeploymentsRevisions(
    Scenario[SeedingSession, RevisionsAndACaller, DeploymentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-counts-every-revision-of-a-deployment"

    @override
    def describe(self) -> str:
        return (
            "리비전 셋이 딸린 배포에 읽기 권한을 받은 사용자가 그 배포의 리비전을 훑으면, "
            "셋을 모두 센다"
        )

    @override
    def given(self) -> Given[SeedingSession, RevisionsAndACaller]:
        return ADeploymentToRevise(granted=(Permission.READ,), revisions=3)

    @override
    def when(self) -> When[RevisionsAndACaller, DeploymentAdapter, Searched]:
        return SearchingTheDeployment()

    @override
    def then(self) -> Then[RevisionsAndACaller, Searched]:
        return EveryLaidRevisionIsCounted()


@dataclass(frozen=True)
class FilteringByNumberLeavesThatOne(
    Scenario[SeedingSession, RevisionsAndACaller, DeploymentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "filtering-revisions-by-number-leaves-only-that-one"

    @override
    def describe(self) -> str:
        return "리비전 셋이 딸린 배포의 리비전을 번호로 걸러 훑으면, 그 번호의 것만 남는다"

    @override
    def given(self) -> Given[SeedingSession, RevisionsAndACaller]:
        return ADeploymentToRevise(granted=(Permission.READ,), revisions=3)

    @override
    def when(self) -> When[RevisionsAndACaller, DeploymentAdapter, Searched]:
        return SearchingTheDeployment(number=2)

    @override
    def then(self) -> Then[RevisionsAndACaller, Searched]:
        return EveryLaidRevisionIsCounted(number=2)


@dataclass(frozen=True)
class AnotherDeploymentsRevisionsStayOut(
    Scenario[SeedingSession, RevisionsAndACaller, DeploymentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "another-deployments-revisions-stay-out-of-a-deployment-search"

    @override
    def describe(self) -> str:
        return (
            "두 프로젝트의 배포에 리비전이 나뉘어 있고 한쪽에만 읽기 권한을 받은 사용자가 "
            "그쪽 배포의 리비전을 훑으면, 그쪽 것만 나온다"
        )

    @override
    def given(self) -> Given[SeedingSession, RevisionsAndACaller]:
        return RevisionsInTwoProjects(granted=(Permission.READ,), named=2, elsewhere=1)

    @override
    def when(self) -> When[RevisionsAndACaller, DeploymentAdapter, Searched]:
        return SearchingTheDeployment()

    @override
    def then(self) -> Then[RevisionsAndACaller, Searched]:
        return EveryLaidRevisionIsCounted()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearchIt(
    Scenario[SeedingSession, RevisionsAndACaller, DeploymentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-a-deployments-revisions"

    @override
    def describe(self) -> str:
        return "아무 배포 권한도 받지 않은 사용자가 배포의 리비전을 훑으면, 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, RevisionsAndACaller]:
        return ADeploymentToRevise(revisions=1)

    @override
    def when(self) -> When[RevisionsAndACaller, DeploymentAdapter, Searched]:
        return SearchingTheDeployment()

    @override
    def then(self) -> Then[RevisionsAndACaller, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminCountsEveryRevision(
    Scenario[SeedingSession, RevisionsAndACaller, DeploymentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-counts-every-revision"

    @override
    def describe(self) -> str:
        return (
            "두 프로젝트의 배포에 리비전이 나뉘어 있고 슈퍼관리자가 필터 없이 전체를 훑으면, "
            "둘의 것을 모두 센다. 이 문은 역할이 지킨다"
        )

    @override
    def given(self) -> Given[SeedingSession, RevisionsAndACaller]:
        return RevisionsInTwoProjects(role=UserRole.SUPERADMIN, named=2, elsewhere=1)

    @override
    def when(self) -> When[RevisionsAndACaller, DeploymentAdapter, Searched]:
        return SearchingEveryRevision()

    @override
    def then(self) -> Then[RevisionsAndACaller, Searched]:
        return EveryLaidRevisionIsCounted(elsewhere_too=True)


@dataclass(frozen=True)
class AReadGrantDoesNotOpenTheGlobalDoor(
    Scenario[SeedingSession, RevisionsAndACaller, DeploymentAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-may-not-search-every-revision"

    @override
    def describe(self) -> str:
        return (
            "모든 배포에 읽기 권한을 받았지만 슈퍼관리자가 아닌 사용자가 전체 리비전을 훑으면, "
            "역할로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, RevisionsAndACaller]:
        return ADeploymentToRevise(granted=(Permission.READ,), revisions=1)

    @override
    def when(self) -> When[RevisionsAndACaller, DeploymentAdapter, Searched]:
        return SearchingEveryRevision()

    @override
    def then(self) -> Then[RevisionsAndACaller, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class TheGrantedUserCountsARevisionsSlots(
    Scenario[SeedingSession, RevisionsAndACaller, DeploymentAdapter, Slots]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-counts-every-slot-a-revision-allocates"

    @override
    def describe(self) -> str:
        return (
            "슬롯 둘을 잡은 리비전이 딸린 배포에 읽기 권한을 받은 사용자가 그 리비전의 슬롯을 "
            "훑으면, 둘을 모두 센다"
        )

    @override
    def given(self) -> Given[SeedingSession, RevisionsAndACaller]:
        return ADeploymentToRevise(granted=(Permission.READ,), revisions=1)

    @override
    def when(self) -> When[RevisionsAndACaller, DeploymentAdapter, Slots]:
        return SearchingTheSlots()

    @override
    def then(self) -> Then[RevisionsAndACaller, Slots]:
        return EveryRevisionSlotIsCounted()


@dataclass(frozen=True)
class AUserGrantedNothingMayNotSearchTheSlots(
    Scenario[SeedingSession, RevisionsAndACaller, DeploymentAdapter, Slots]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-search-a-revisions-slots"

    @override
    def describe(self) -> str:
        return (
            "아무 배포 권한도 받지 않은 사용자가 배포의 리비전의 슬롯을 훑으면, "
            "리비전을 찾을 수 없다는 답으로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, RevisionsAndACaller]:
        return ADeploymentToRevise(revisions=1)

    @override
    def when(self) -> When[RevisionsAndACaller, DeploymentAdapter, Slots]:
        return SearchingTheSlots()

    @override
    def then(self) -> Then[RevisionsAndACaller, Slots]:
        return TheCallIsRefused(GenericBadRequest)


SCENARIOS: list[SearchingStep] = [
    TheGrantedUserCountsTheDeploymentsRevisions(),
    FilteringByNumberLeavesThatOne(),
    AnotherDeploymentsRevisionsStayOut(),
    AUserGrantedNothingMayNotSearchIt(),
    TheSuperadminCountsEveryRevision(),
    AReadGrantDoesNotOpenTheGlobalDoor(),
]

SLOT_SCENARIOS: list[SlotStep] = [
    TheGrantedUserCountsARevisionsSlots(),
    AUserGrantedNothingMayNotSearchTheSlots(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching_revisions(
    scenario: SearchingStep, adapter: DeploymentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)


@pytest.mark.parametrize("scenario", SLOT_SCENARIOS, ids=lambda s: s.summary())
async def test_searching_revision_slots(
    scenario: SlotStep, adapter: DeploymentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
