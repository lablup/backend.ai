"""서비스 카탈로그 검색 — 필터가 무엇을 좁히고, 누가 물을 수 있는가."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.service_catalog.request import (
    AdminSearchServiceCatalogsInput,
    ServiceCatalogFilter,
)
from ai.backend.common.dto.manager.v2.service_catalog.response import (
    AdminSearchServiceCatalogsPayload,
)
from ai.backend.common.dto.manager.v2.service_catalog.types import ServiceCatalogStatusFilter
from ai.backend.common.types import ServiceCatalogStatus
from ai.backend.manager.api.adapters.service_catalog.adapter import ServiceCatalogAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Scenario, Then, When
from bai_scenario.components.answers import NothingIsFound, TheCallIsRefused
from bai_scenario.components.service_catalog import (
    EveryLaidServiceComesWhole,
    EveryLaidServiceIsCounted,
    ManyServicesAndACaller,
    ManyServicesAndSomeone,
    OnlyTheNamedGroupIsLeft,
    ServicesOfTwoGroupsAndSomeone,
    TheFirstPageOfServices,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

DEFAULT_PAGE = 10

type Searched = AdminSearchServiceCatalogsPayload
type SearchingStep = Scenario[
    SeedingSession, ManyServicesAndACaller, ServiceCatalogAdapter, Searched
]


@dataclass(frozen=True)
class SearchingEveryService(When[ManyServicesAndACaller, ServiceCatalogAdapter, Searched]):
    """필터도 크기도 없이 전체를 검색한다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyServicesAndACaller) -> str:
        return f"{laid.caller.username}이 필터 없이 전체 조회"

    @override
    async def call(self, adapter: ServiceCatalogAdapter, laid: ManyServicesAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(AdminSearchServiceCatalogsInput())


@dataclass(frozen=True)
class SearchingByGroup(When[ManyServicesAndACaller, ServiceCatalogAdapter, Searched]):
    """심은 것 중 하나의 그룹으로 걸러 검색한다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyServicesAndACaller) -> str:
        return f"{laid.caller.username}이 {laid.named.service_group} 그룹으로 걸러 조회"

    @override
    async def call(self, adapter: ServiceCatalogAdapter, laid: ManyServicesAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                AdminSearchServiceCatalogsInput(
                    filter=ServiceCatalogFilter(
                        service_group=StringFilter(equals=laid.named.service_group)
                    )
                )
            )


@dataclass(frozen=True)
class SearchingByStatusEquals(When[ManyServicesAndACaller, ServiceCatalogAdapter, Searched]):
    """상태가 이것인 서비스로 걸러 검색한다."""

    status: ServiceCatalogStatus

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyServicesAndACaller) -> str:
        return f"{laid.caller.username}이 상태가 {self.status.value}인 것으로 걸러 조회"

    @override
    async def call(self, adapter: ServiceCatalogAdapter, laid: ManyServicesAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                AdminSearchServiceCatalogsInput(
                    filter=ServiceCatalogFilter(
                        status=ServiceCatalogStatusFilter(equals=self.status)
                    )
                )
            )


@dataclass(frozen=True)
class SearchingByStatusNotEquals(When[ManyServicesAndACaller, ServiceCatalogAdapter, Searched]):
    """상태가 이것이 아닌 서비스로 걸러 검색한다."""

    status: ServiceCatalogStatus

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyServicesAndACaller) -> str:
        return f"{laid.caller.username}이 상태가 {self.status.value}이 아닌 것으로 걸러 조회"

    @override
    async def call(self, adapter: ServiceCatalogAdapter, laid: ManyServicesAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                AdminSearchServiceCatalogsInput(
                    filter=ServiceCatalogFilter(
                        status=ServiceCatalogStatusFilter(not_equals=self.status)
                    )
                )
            )


@dataclass(frozen=True)
class SearchingByStatusIn(When[ManyServicesAndACaller, ServiceCatalogAdapter, Searched]):
    """상태가 이 목록에 든 서비스로 걸러 검색한다."""

    statuses: tuple[ServiceCatalogStatus, ...]

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyServicesAndACaller) -> str:
        listed = ", ".join(one.value for one in self.statuses)
        return f"{laid.caller.username}이 상태가 {listed} 중 하나인 것으로 걸러 조회"

    @override
    async def call(self, adapter: ServiceCatalogAdapter, laid: ManyServicesAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                AdminSearchServiceCatalogsInput(
                    filter=ServiceCatalogFilter(
                        status=ServiceCatalogStatusFilter(in_=list(self.statuses))
                    )
                )
            )


@dataclass(frozen=True)
class SearchingByStatusNotIn(When[ManyServicesAndACaller, ServiceCatalogAdapter, Searched]):
    """상태가 이 목록에 들지 않은 서비스로 걸러 검색한다."""

    statuses: tuple[ServiceCatalogStatus, ...]

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyServicesAndACaller) -> str:
        listed = ", ".join(one.value for one in self.statuses)
        return f"{laid.caller.username}이 상태가 {listed} 중 어느 것도 아닌 것으로 걸러 조회"

    @override
    async def call(self, adapter: ServiceCatalogAdapter, laid: ManyServicesAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                AdminSearchServiceCatalogsInput(
                    filter=ServiceCatalogFilter(
                        status=ServiceCatalogStatusFilter(not_in=list(self.statuses))
                    )
                )
            )


@dataclass(frozen=True)
class TheSuperadminCountsEveryServiceWithItsEndpoints(
    Scenario[SeedingSession, ManyServicesAndACaller, ServiceCatalogAdapter, Searched]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-counts-every-service-laid-with-its-endpoints"

    @override
    def describe(self) -> str:
        return (
            "서비스 둘 중 하나가 엔드포인트를 가질 때 슈퍼관리자가 필터 없이 조회하면, "
            "둘 다 집계되고 엔드포인트가 함께 담긴다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyServicesAndACaller]:
        return ManyServicesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyServicesAndACaller, ServiceCatalogAdapter, Searched]:
        return SearchingEveryService()

    @override
    def then(self) -> Then[ManyServicesAndACaller, Searched]:
        return EveryLaidServiceComesWhole(started=self.started)


@dataclass(frozen=True)
class AGroupFilterNarrows(
    Scenario[SeedingSession, ManyServicesAndACaller, ServiceCatalogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-group-filter-narrows-the-answer-to-the-services-of-that-group"

    @override
    def describe(self) -> str:
        return (
            "그룹이 다른 서비스 둘 중 한 그룹으로 걸러 조회하면, 답에는 그 그룹의 서비스만 남는다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyServicesAndACaller]:
        return ServicesOfTwoGroupsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyServicesAndACaller, ServiceCatalogAdapter, Searched]:
        return SearchingByGroup()

    @override
    def then(self) -> Then[ManyServicesAndACaller, Searched]:
        return OnlyTheNamedGroupIsLeft()


@dataclass(frozen=True)
class AStatusEqualsFilterKeepsThatStatus(
    Scenario[SeedingSession, ManyServicesAndACaller, ServiceCatalogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-status-equals-filter-keeps-the-services-of-that-status"

    @override
    def describe(self) -> str:
        return "정상 상태의 서비스 둘을 그 상태와 같은 것으로 걸러 조회하면 둘 다 세어진다"

    @override
    def given(self) -> Given[SeedingSession, ManyServicesAndACaller]:
        return ManyServicesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyServicesAndACaller, ServiceCatalogAdapter, Searched]:
        return SearchingByStatusEquals(ServiceCatalogStatus.HEALTHY)

    @override
    def then(self) -> Then[ManyServicesAndACaller, Searched]:
        return EveryLaidServiceIsCounted()


@dataclass(frozen=True)
class AStatusNotEqualsFilterDropsThatStatus(
    Scenario[SeedingSession, ManyServicesAndACaller, ServiceCatalogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-status-not-equals-filter-drops-the-services-of-that-status"

    @override
    def describe(self) -> str:
        return "정상 상태의 서비스 둘을 그 상태와 다른 것으로 걸러 조회하면 아무것도 남지 않는다"

    @override
    def given(self) -> Given[SeedingSession, ManyServicesAndACaller]:
        return ManyServicesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyServicesAndACaller, ServiceCatalogAdapter, Searched]:
        return SearchingByStatusNotEquals(ServiceCatalogStatus.HEALTHY)

    @override
    def then(self) -> Then[ManyServicesAndACaller, Searched]:
        return NothingIsFound()


@dataclass(frozen=True)
class AStatusInFilterDropsUnlistedStatuses(
    Scenario[SeedingSession, ManyServicesAndACaller, ServiceCatalogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-status-in-filter-drops-the-services-of-no-listed-status"

    @override
    def describe(self) -> str:
        return "정상 상태의 서비스 둘을 다른 상태들의 목록에 든 것으로 걸러 조회하면 아무것도 남지 않는다"

    @override
    def given(self) -> Given[SeedingSession, ManyServicesAndACaller]:
        return ManyServicesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyServicesAndACaller, ServiceCatalogAdapter, Searched]:
        return SearchingByStatusIn((
            ServiceCatalogStatus.UNHEALTHY,
            ServiceCatalogStatus.DEREGISTERED,
        ))

    @override
    def then(self) -> Then[ManyServicesAndACaller, Searched]:
        return NothingIsFound()


@dataclass(frozen=True)
class AStatusNotInFilterKeepsUnlistedStatuses(
    Scenario[SeedingSession, ManyServicesAndACaller, ServiceCatalogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-status-not-in-filter-keeps-the-services-of-no-listed-status"

    @override
    def describe(self) -> str:
        return "정상 상태의 서비스 둘을 다른 상태들의 목록에 들지 않은 것으로 걸러 조회하면 둘 다 세어진다"

    @override
    def given(self) -> Given[SeedingSession, ManyServicesAndACaller]:
        return ManyServicesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyServicesAndACaller, ServiceCatalogAdapter, Searched]:
        return SearchingByStatusNotIn((
            ServiceCatalogStatus.UNHEALTHY,
            ServiceCatalogStatus.DEREGISTERED,
        ))

    @override
    def then(self) -> Then[ManyServicesAndACaller, Searched]:
        return EveryLaidServiceIsCounted()


@dataclass(frozen=True)
class OmittingThePageSizeGivesTen(
    Scenario[SeedingSession, ManyServicesAndACaller, ServiceCatalogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "omitting-the-page-size-answers-ten-services-and-a-next-page"

    @override
    def describe(self) -> str:
        return "서비스 11개가 있을 때 크기 없이 조회하면 10건까지 반환되고 다음 페이지가 있다고 응답한다"

    @override
    def given(self) -> Given[SeedingSession, ManyServicesAndACaller]:
        return ManyServicesAndSomeone(role=UserRole.SUPERADMIN, besides=DEFAULT_PAGE)

    @override
    def when(self) -> When[ManyServicesAndACaller, ServiceCatalogAdapter, Searched]:
        return SearchingEveryService()

    @override
    def then(self) -> Then[ManyServicesAndACaller, Searched]:
        return TheFirstPageOfServices(size=DEFAULT_PAGE)


@dataclass(frozen=True)
class TheMonitorSeesWhatTheSuperadminSees(
    Scenario[SeedingSession, ManyServicesAndACaller, ServiceCatalogAdapter, Searched]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-monitor-role-counts-every-service-as-the-superadmin-does"

    @override
    def describe(self) -> str:
        return (
            "모니터 역할이 필터 없이 조회하면 슈퍼관리자와 같은 답을 받는다. "
            "이 검색은 읽기 연산이라 모니터 역할이 전역 역할 검사를 통과한다"
        )

    @override
    def given(self) -> Given[SeedingSession, ManyServicesAndACaller]:
        return ManyServicesAndSomeone(role=UserRole.MONITOR)

    @override
    def when(self) -> When[ManyServicesAndACaller, ServiceCatalogAdapter, Searched]:
        return SearchingEveryService()

    @override
    def then(self) -> Then[ManyServicesAndACaller, Searched]:
        return EveryLaidServiceComesWhole(started=self.started)


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotSearch(
    Scenario[SeedingSession, ManyServicesAndACaller, ServiceCatalogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-services"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 아닌 사용자가 전체 조회를 요청하면 역할 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ManyServicesAndACaller]:
        return ManyServicesAndSomeone()

    @override
    def when(self) -> When[ManyServicesAndACaller, ServiceCatalogAdapter, Searched]:
        return SearchingEveryService()

    @override
    def then(self) -> Then[ManyServicesAndACaller, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchingStep] = [
    TheSuperadminCountsEveryServiceWithItsEndpoints(started=datetime.now(UTC)),
    AGroupFilterNarrows(),
    AStatusEqualsFilterKeepsThatStatus(),
    AStatusNotEqualsFilterDropsThatStatus(),
    AStatusInFilterDropsUnlistedStatuses(),
    AStatusNotInFilterKeepsUnlistedStatuses(),
    OmittingThePageSizeGivesTen(),
    TheMonitorSeesWhatTheSuperadminSees(started=datetime.now(UTC)),
    AUserWhoIsNotTheSuperadminMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: ServiceCatalogAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
