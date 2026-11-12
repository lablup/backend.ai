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
from ai.backend.testutils.scenario_steps import (
    Given,
    Language,
    Says,
    Scenario,
    Then,
    When,
    in_language,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.service_catalog import (
    EveryLaidServiceComesWhole,
    ManyServicesAndACaller,
    ManyServicesAndSomeone,
    OnlyTheNamedGroupIsLeft,
    OnlyTheServicesOfStatuses,
    ServicesOfEveryStatusAndSomeone,
    ServicesOfTwoGroupsAndSomeone,
    TheFirstPageOfServices,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario
from bai_scenario.seeds.service_catalog.service import STATUS_NAMES

DEFAULT_PAGE = 10

type Searched = AdminSearchServiceCatalogsPayload
type SearchingStep = Scenario[
    TestSeedingSession, ManyServicesAndACaller, ServiceCatalogAdapter, Searched
]


@dataclass(frozen=True)
class SearchingEveryService(When[ManyServicesAndACaller, ServiceCatalogAdapter, Searched]):
    """필터도 크기도 없이 전체를 검색한다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: ManyServicesAndACaller) -> str:
        return Says(
            f"{laid.caller.username} 이 필터 없이 전체를 조회합니다",
            english=f"{laid.caller.username} reads everything without a filter",
        )

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
        return Says(
            f"{laid.caller.username} 이 {laid.named.service_group} 그룹으로 필터 기반 조회합니다",
            english=(
                f"{laid.caller.username} reads filtered by the {laid.named.service_group} group"
            ),
        )

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
        status = STATUS_NAMES[self.status]
        return Says(
            f"{laid.caller.username} 이 상태가 {status} 인 것으로 필터 기반 조회합니다",
            english=(
                f"{laid.caller.username} reads filtered by the status "
                f"{in_language(status, Language.ENGLISH)}"
            ),
        )

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
        status = STATUS_NAMES[self.status]
        return Says(
            f"{laid.caller.username} 이 상태가 {status} 이 아닌 것으로 필터 기반 조회합니다",
            english=(
                f"{laid.caller.username} reads filtered by a status other than "
                f"{in_language(status, Language.ENGLISH)}"
            ),
        )

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
        listed_ko = ", ".join(str(STATUS_NAMES[one]) for one in self.statuses)
        listed_en = ", ".join(
            in_language(STATUS_NAMES[one], Language.ENGLISH) for one in self.statuses
        )
        return Says(
            f"{laid.caller.username} 이 상태가 {listed_ko} 중 하나인 것으로 필터 기반 조회합니다",
            english=(f"{laid.caller.username} reads filtered by one of the statuses {listed_en}"),
        )

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
        listed_ko = ", ".join(str(STATUS_NAMES[one]) for one in self.statuses)
        listed_en = ", ".join(
            in_language(STATUS_NAMES[one], Language.ENGLISH) for one in self.statuses
        )
        return Says(
            f"{laid.caller.username} 이 상태가 {listed_ko} 중 어느 것도 아닌 것으로 필터 기반 "
            "조회합니다",
            english=(
                f"{laid.caller.username} reads filtered by a status that is none of {listed_en}"
            ),
        )

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
class TheSuperadminCountsEveryServiceOnce(
    Scenario[TestSeedingSession, ManyServicesAndACaller, ServiceCatalogAdapter, Searched]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-superadmin-counts-every-service-laid-once"

    @override
    def describe(self) -> str:
        return Says(
            "서비스 둘 중 하나가 엔드포인트를 가질 때 superadmin 이 필터 없이 조회하면, "
            "둘 다 한 번씩 집계됩니다",
            english=(
                "when one of two services holds an endpoint and the superadmin reads without a "
                "filter, both are counted once"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyServicesAndACaller]:
        return ManyServicesAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyServicesAndACaller, ServiceCatalogAdapter, Searched]:
        return SearchingEveryService()

    @override
    def then(self) -> Then[ManyServicesAndACaller, Searched]:
        return EveryLaidServiceComesWhole(started=self.started)


@dataclass(frozen=True)
class AGroupFilterNarrows(
    Scenario[TestSeedingSession, ManyServicesAndACaller, ServiceCatalogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-group-filter-narrows-the-answer-to-the-services-of-that-group"

    @override
    def describe(self) -> str:
        return Says(
            "그룹이 다른 서비스 둘 중 한 그룹으로 필터 기반 조회하면, 응답에는 그 그룹의 서비스만 "
            "남습니다",
            english=(
                "when a read is filtered by one group among two services of different groups, "
                "only the services of that group remain in the answer"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyServicesAndACaller]:
        return ServicesOfTwoGroupsAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyServicesAndACaller, ServiceCatalogAdapter, Searched]:
        return SearchingByGroup()

    @override
    def then(self) -> Then[ManyServicesAndACaller, Searched]:
        return OnlyTheNamedGroupIsLeft()


@dataclass(frozen=True)
class AStatusEqualsFilterKeepsThatStatus(
    Scenario[TestSeedingSession, ManyServicesAndACaller, ServiceCatalogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-status-equals-filter-keeps-the-services-of-that-status"

    @override
    def describe(self) -> str:
        return Says(
            "상태마다 하나씩 있는 서비스를 비정상과 같은 것으로 필터 기반 조회하면 비정상 서비스만 "
            "반환됩니다",
            english=(
                "when services with one of each status are read filtered by unhealthy, only the "
                "unhealthy service comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyServicesAndACaller]:
        return ServicesOfEveryStatusAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyServicesAndACaller, ServiceCatalogAdapter, Searched]:
        return SearchingByStatusEquals(ServiceCatalogStatus.UNHEALTHY)

    @override
    def then(self) -> Then[ManyServicesAndACaller, Searched]:
        return OnlyTheServicesOfStatuses((ServiceCatalogStatus.UNHEALTHY,))


@dataclass(frozen=True)
class AStatusNotEqualsFilterDropsThatStatus(
    Scenario[TestSeedingSession, ManyServicesAndACaller, ServiceCatalogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-status-not-equals-filter-drops-the-services-of-that-status"

    @override
    def describe(self) -> str:
        return Says(
            "상태마다 하나씩 있는 서비스를 비정상과 다른 것으로 필터 기반 조회하면 "
            "정상과 등록 해제 서비스만 반환됩니다",
            english=(
                "when services with one of each status are read filtered by a status other than "
                "unhealthy, only the healthy and deregistered services come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyServicesAndACaller]:
        return ServicesOfEveryStatusAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyServicesAndACaller, ServiceCatalogAdapter, Searched]:
        return SearchingByStatusNotEquals(ServiceCatalogStatus.UNHEALTHY)

    @override
    def then(self) -> Then[ManyServicesAndACaller, Searched]:
        return OnlyTheServicesOfStatuses((
            ServiceCatalogStatus.HEALTHY,
            ServiceCatalogStatus.DEREGISTERED,
        ))


@dataclass(frozen=True)
class AStatusInFilterKeepsListedStatuses(
    Scenario[TestSeedingSession, ManyServicesAndACaller, ServiceCatalogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-status-in-filter-keeps-the-services-of-a-listed-status"

    @override
    def describe(self) -> str:
        return Says(
            "상태마다 하나씩 있는 서비스를 비정상, 등록 해제 목록에 든 것으로 필터 기반 조회하면 "
            "비정상과 등록 해제 서비스만 반환됩니다",
            english=(
                "when services with one of each status are read filtered by a status in the "
                "unhealthy and deregistered list, only the unhealthy and deregistered services "
                "come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyServicesAndACaller]:
        return ServicesOfEveryStatusAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyServicesAndACaller, ServiceCatalogAdapter, Searched]:
        return SearchingByStatusIn((
            ServiceCatalogStatus.UNHEALTHY,
            ServiceCatalogStatus.DEREGISTERED,
        ))

    @override
    def then(self) -> Then[ManyServicesAndACaller, Searched]:
        return OnlyTheServicesOfStatuses((
            ServiceCatalogStatus.UNHEALTHY,
            ServiceCatalogStatus.DEREGISTERED,
        ))


@dataclass(frozen=True)
class AStatusNotInFilterDropsListedStatuses(
    Scenario[TestSeedingSession, ManyServicesAndACaller, ServiceCatalogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-status-not-in-filter-drops-the-services-of-a-listed-status"

    @override
    def describe(self) -> str:
        return Says(
            "상태마다 하나씩 있는 서비스를 비정상, 등록 해제 목록에 들지 않은 것으로 필터 기반 "
            "조회하면 정상 서비스만 반환됩니다",
            english=(
                "when services with one of each status are read filtered by a status not in the "
                "unhealthy and deregistered list, only the healthy service comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyServicesAndACaller]:
        return ServicesOfEveryStatusAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[ManyServicesAndACaller, ServiceCatalogAdapter, Searched]:
        return SearchingByStatusNotIn((
            ServiceCatalogStatus.UNHEALTHY,
            ServiceCatalogStatus.DEREGISTERED,
        ))

    @override
    def then(self) -> Then[ManyServicesAndACaller, Searched]:
        return OnlyTheServicesOfStatuses((ServiceCatalogStatus.HEALTHY,))


@dataclass(frozen=True)
class OmittingThePageSizeGivesTen(
    Scenario[TestSeedingSession, ManyServicesAndACaller, ServiceCatalogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "omitting-the-page-size-answers-ten-services-and-a-next-page"

    @override
    def describe(self) -> str:
        return Says(
            "서비스 11개가 있을 때 크기 없이 조회하면 10건까지 반환되고 다음 페이지가 있다고 "
            "응답합니다",
            english=(
                "when eleven services exist and the read names no size, ten services come back "
                "and the answer says there is a next page"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyServicesAndACaller]:
        return ManyServicesAndSomeone(role=UserRole.SUPERADMIN, besides=DEFAULT_PAGE)

    @override
    def when(self) -> When[ManyServicesAndACaller, ServiceCatalogAdapter, Searched]:
        return SearchingEveryService()

    @override
    def then(self) -> Then[ManyServicesAndACaller, Searched]:
        return TheFirstPageOfServices(size=DEFAULT_PAGE)


@dataclass(frozen=True)
class TheMonitorSeesWhatTheSuperadminSees(
    Scenario[TestSeedingSession, ManyServicesAndACaller, ServiceCatalogAdapter, Searched]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "the-monitor-role-counts-every-service-as-the-superadmin-does"

    @override
    def describe(self) -> str:
        return Says(
            "모니터 역할이 필터 없이 조회하면 superadmin 과 같은 응답을 받습니다. "
            "이 검색은 읽기 연산이라 모니터 역할이 전역 역할 검사를 통과합니다",
            english=(
                "when the monitor role reads without a filter, it gets the same answer as the "
                "superadmin. This search is a read operation, so the monitor role passes the "
                "global role check"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyServicesAndACaller]:
        return ManyServicesAndSomeone(role=UserRole.MONITOR)

    @override
    def when(self) -> When[ManyServicesAndACaller, ServiceCatalogAdapter, Searched]:
        return SearchingEveryService()

    @override
    def then(self) -> Then[ManyServicesAndACaller, Searched]:
        return EveryLaidServiceComesWhole(started=self.started)


@dataclass(frozen=True)
class AUserWhoIsNotTheSuperadminMayNotSearch(
    Scenario[TestSeedingSession, ManyServicesAndACaller, ServiceCatalogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-services"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 아닌 사용자가 전체 조회를 요청하면 역할 부족으로 거부됩니다",
            english=(
                "when a user who is not the superadmin requests a global read, it is rejected "
                "for lack of role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ManyServicesAndACaller]:
        return ManyServicesAndSomeone()

    @override
    def when(self) -> When[ManyServicesAndACaller, ServiceCatalogAdapter, Searched]:
        return SearchingEveryService()

    @override
    def then(self) -> Then[ManyServicesAndACaller, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


SCENARIOS: list[SearchingStep] = [
    TheSuperadminCountsEveryServiceOnce(started=datetime.now(UTC)),
    AGroupFilterNarrows(),
    AStatusEqualsFilterKeepsThatStatus(),
    AStatusNotEqualsFilterDropsThatStatus(),
    AStatusInFilterKeepsListedStatuses(),
    AStatusNotInFilterDropsListedStatuses(),
    OmittingThePageSizeGivesTen(),
    TheMonitorSeesWhatTheSuperadminSees(started=datetime.now(UTC)),
    AUserWhoIsNotTheSuperadminMayNotSearch(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: ServiceCatalogAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
