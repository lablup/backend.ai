"""감사 기록 전체 검색 — 슈퍼관리자인지 검사하지만, 읽기 연산이라 모니터 역할도 통과한다.

모니터 역할은 통과하지만 슈퍼관리자가 아닌 사용자는 거부된다. 이 검색은 권한 그래프가 아니라
슈퍼관리자 검사로 보호된다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.audit_log.request import (
    AdminSearchAuditLogsInput,
    AuditLogFilter,
    AuditLogStatusFilter,
)
from ai.backend.common.dto.manager.v2.audit_log.response import SearchAuditLogsPayload
from ai.backend.common.dto.manager.v2.audit_log.types import AuditLogStatus
from ai.backend.manager.api.adapters.audit_log.adapter import AuditLogAdapter
from ai.backend.manager.errors.api import InvalidCursor, InvalidGraphQLParameters
from ai.backend.manager.errors.auth import InsufficientPrivilege
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
from bai_scenario.components.audit_log import (
    ManyRecordsGlobally,
    MixedStatusGlobally,
    OneRunGlobally,
    RecordsAndACaller,
    ThePageIsCapped,
    TheRecordsAnswered,
    TwoActorsGlobally,
    TwoRecordsGlobally,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Searched = SearchAuditLogsPayload
type SearchingStep = Scenario[TestSeedingSession, RecordsAndACaller, AuditLogAdapter, Searched]
ENFORCEMENT = "manager.rbac.enforcement_enabled"


@dataclass(frozen=True)
class SearchingEverything(When[RecordsAndACaller, AuditLogAdapter, Searched]):
    """필터 없이 전체를 검색한다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: RecordsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 필터 없이 전체 검색합니다",
            english=f"{laid.caller.username} searches everything without a filter",
        )

    @override
    async def call(self, adapter: AuditLogAdapter, laid: RecordsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(AdminSearchAuditLogsInput())


@dataclass(frozen=True)
class SearchingBySuccess(When[RecordsAndACaller, AuditLogAdapter, Searched]):
    """성공한 기록만 상태 필터로 검색한다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: RecordsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 성공 상태 필터로 검색합니다",
            english=f"{laid.caller.username} searches with a success status filter",
        )

    @override
    async def call(self, adapter: AuditLogAdapter, laid: RecordsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                AdminSearchAuditLogsInput(
                    filter=AuditLogFilter(
                        status=AuditLogStatusFilter(equals=AuditLogStatus.SUCCESS)
                    )
                )
            )


@dataclass(frozen=True)
class SearchingByTriggeredUser(When[RecordsAndACaller, AuditLogAdapter, Searched]):
    """실행한 사용자를 필터로 검색한다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: RecordsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 실행한 사용자 필터로 검색합니다",
            english=f"{laid.caller.username} searches with a triggered-user filter",
        )

    @override
    async def call(self, adapter: AuditLogAdapter, laid: RecordsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                AdminSearchAuditLogsInput(
                    filter=AuditLogFilter(
                        triggered_by=StringFilter(equals=str(laid.filter_triggered))
                    )
                )
            )


@dataclass(frozen=True)
class SearchingByRun(When[RecordsAndACaller, AuditLogAdapter, Searched]):
    """한 실행의 기록을 필터로 검색한다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: RecordsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 실행 필터로 검색합니다",
            english=f"{laid.caller.username} searches with a run filter",
        )

    @override
    async def call(self, adapter: AuditLogAdapter, laid: RecordsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                AdminSearchAuditLogsInput(
                    filter=AuditLogFilter(action_id=UUIDFilter(equals=laid.filter_action))
                )
            )


@dataclass(frozen=True)
class SearchingWithoutPageSize(When[RecordsAndACaller, AuditLogAdapter, Searched]):
    """페이지 크기를 지정하지 않고 검색한다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: RecordsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 크기 없이 검색합니다",
            english=f"{laid.caller.username} searches without a page size",
        )

    @override
    async def call(self, adapter: AuditLogAdapter, laid: RecordsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(AdminSearchAuditLogsInput())


@dataclass(frozen=True)
class SearchingWithMixedPagination(When[RecordsAndACaller, AuditLogAdapter, Searched]):
    """오프셋 방식과 커서 방식을 함께 지정한다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: RecordsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 두 페이지 방식을 함께 지정해 검색합니다",
            english=f"{laid.caller.username} searches naming both pagination modes at once",
        )

    @override
    async def call(self, adapter: AuditLogAdapter, laid: RecordsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(AdminSearchAuditLogsInput(first=1, limit=1))


@dataclass(frozen=True)
class SearchingWithBadCursor(When[RecordsAndACaller, AuditLogAdapter, Searched]):
    """해석할 수 없는 커서로 검색한다."""

    @override
    def operation(self) -> str:
        return "admin_search"

    @override
    def describe(self, laid: RecordsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 손상된 커서로 검색합니다",
            english=f"{laid.caller.username} searches with a broken cursor",
        )

    @override
    async def call(self, adapter: AuditLogAdapter, laid: RecordsAndACaller) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.admin_search(
                AdminSearchAuditLogsInput(first=1, after="not-a-valid-cursor")
            )


@dataclass(frozen=True)
class TheSuperadminSeesEveryRecord(
    Scenario[TestSeedingSession, RecordsAndACaller, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-searching-without-a-filter-sees-every-record-newest-first"

    @override
    def describe(self) -> str:
        return Says(
            "기록 둘이 있고 superadmin 이 필터 없이 검색하면, 둘 다 반환되고 최근 것이 먼저입니다",
            english=(
                "when there are two records and the superadmin searches without a filter, "
                "both come back with the newest first"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RecordsAndACaller]:
        return TwoRecordsGlobally(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[RecordsAndACaller, AuditLogAdapter, Searched]:
        return SearchingEverything()

    @override
    def then(self) -> Then[RecordsAndACaller, Searched]:
        return TheRecordsAnswered()


@dataclass(frozen=True)
class TheMonitorRoleSeesEveryRecord(
    Scenario[TestSeedingSession, RecordsAndACaller, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-monitor-role-searching-sees-the-same-records-as-the-superadmin"

    @override
    def describe(self) -> str:
        return Says(
            "검색은 읽기 연산이므로 모니터 역할 사용자도 superadmin 검사를 통과해 superadmin 과 "
            "같은 응답을 받습니다",
            english=(
                "because searching is a read operation, a monitor-role user also passes the "
                "superadmin check and gets the same response as the superadmin"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RecordsAndACaller]:
        return TwoRecordsGlobally(role=UserRole.MONITOR)

    @override
    def when(self) -> When[RecordsAndACaller, AuditLogAdapter, Searched]:
        return SearchingEverything()

    @override
    def then(self) -> Then[RecordsAndACaller, Searched]:
        return TheRecordsAnswered()


@dataclass(frozen=True)
class APlainUserMayNotSearch(
    Scenario[TestSeedingSession, RecordsAndACaller, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-the-superadmin-may-not-search-every-record"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 도 모니터도 아닌 사용자가 전체를 검색하면, 역할 부족으로 거부됩니다",
            english=(
                "when a user who is neither the superadmin nor a monitor searches everything, "
                "it is rejected for lack of role"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RecordsAndACaller]:
        return TwoRecordsGlobally(role=UserRole.USER)

    @override
    def when(self) -> When[RecordsAndACaller, AuditLogAdapter, Searched]:
        return SearchingEverything()

    @override
    def then(self) -> Then[RecordsAndACaller, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class EnforcementOffStillNeedsTheRole(
    Scenario[TestSeedingSession, RecordsAndACaller, AuditLogAdapter, Searched], Configured
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-does-not-let-a-plain-user-search-every-record"

    @override
    def describe(self) -> str:
        return Says(
            "권한 검사를 꺼도 superadmin 이 아닌 사용자는 전체를 검색할 수 없습니다",
            english=(
                "turning the permission check off still does not let a user who is not the "
                "superadmin search everything"
            ),
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[TestSeedingSession, RecordsAndACaller]:
        return TwoRecordsGlobally(role=UserRole.USER)

    @override
    def when(self) -> When[RecordsAndACaller, AuditLogAdapter, Searched]:
        return SearchingEverything()

    @override
    def then(self) -> Then[RecordsAndACaller, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class OmittingThePageSizeCapsThePage(
    Scenario[TestSeedingSession, RecordsAndACaller, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "omitting-the-page-size-caps-the-page-and-says-more-follow"

    @override
    def describe(self) -> str:
        return Says(
            "페이지 크기를 지정하지 않고 검색하면, 10건까지 반환되고 다음 페이지가 있다고 "
            "응답합니다",
            english=(
                "when a search gives no page size, ten items come back and it answers that "
                "there is a next page"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RecordsAndACaller]:
        return ManyRecordsGlobally(total=11)

    @override
    def when(self) -> When[RecordsAndACaller, AuditLogAdapter, Searched]:
        return SearchingWithoutPageSize()

    @override
    def then(self) -> Then[RecordsAndACaller, Searched]:
        return ThePageIsCapped(size=10, total=11)


@dataclass(frozen=True)
class AStatusFilterNarrowsToSuccess(
    Scenario[TestSeedingSession, RecordsAndACaller, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-status-filter-narrows-the-answer-to-the-status-it-names"

    @override
    def describe(self) -> str:
        return Says(
            "성공 기록과 거부 기록이 섞여 있을 때 성공 상태 필터로 검색하면, 성공한 기록만 "
            "반환됩니다",
            english=(
                "when success records and rejected records are mixed and a success status "
                "filter is used, only the successful records come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RecordsAndACaller]:
        return MixedStatusGlobally()

    @override
    def when(self) -> When[RecordsAndACaller, AuditLogAdapter, Searched]:
        return SearchingBySuccess()

    @override
    def then(self) -> Then[RecordsAndACaller, Searched]:
        return TheRecordsAnswered()


@dataclass(frozen=True)
class AnActorFilterNarrowsToOneUser(
    Scenario[TestSeedingSession, RecordsAndACaller, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "an-actor-filter-narrows-the-answer-to-the-user-who-triggered-it"

    @override
    def describe(self) -> str:
        return Says(
            "두 사용자가 각각 기록을 남겼을 때 한 사용자 필터로 검색하면, 그 사용자가 실행한 "
            "기록만 반환됩니다",
            english=(
                "when two users each left records and one user filter is used, only the "
                "records that user triggered come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RecordsAndACaller]:
        return TwoActorsGlobally()

    @override
    def when(self) -> When[RecordsAndACaller, AuditLogAdapter, Searched]:
        return SearchingByTriggeredUser()

    @override
    def then(self) -> Then[RecordsAndACaller, Searched]:
        return TheRecordsAnswered()


@dataclass(frozen=True)
class ARunFilterNarrowsToOneRun(
    Scenario[TestSeedingSession, RecordsAndACaller, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-run-filter-answers-every-record-the-run-left-and-only-those"

    @override
    def describe(self) -> str:
        return Says(
            "한 실행이 여러 엔티티에 기록을 남겼을 때 그 실행 필터로 검색하면, 그 실행이 남긴 "
            "기록이 모두, 그리고 그것만 반환됩니다",
            english=(
                "when one run left records on several entities and its run filter is used, "
                "every record that run left comes back, and only those"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RecordsAndACaller]:
        return OneRunGlobally()

    @override
    def when(self) -> When[RecordsAndACaller, AuditLogAdapter, Searched]:
        return SearchingByRun()

    @override
    def then(self) -> Then[RecordsAndACaller, Searched]:
        return TheRecordsAnswered()


@dataclass(frozen=True)
class TwoPaginationModesAreRefused(
    Scenario[TestSeedingSession, RecordsAndACaller, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "naming-two-pagination-modes-at-once-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "오프셋 방식과 커서 방식을 함께 지정해 검색하면, 잘못된 입력으로 거부됩니다",
            english=(
                "when a search names both the offset and cursor pagination modes at once, it "
                "is rejected as invalid input"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RecordsAndACaller]:
        return TwoRecordsGlobally(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[RecordsAndACaller, AuditLogAdapter, Searched]:
        return SearchingWithMixedPagination()

    @override
    def then(self) -> Then[RecordsAndACaller, Searched]:
        return TheCallIsRefused(InvalidGraphQLParameters)


@dataclass(frozen=True)
class ABrokenCursorIsRefused(
    Scenario[TestSeedingSession, RecordsAndACaller, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-cursor-that-cannot-be-decoded-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "해석할 수 없는 커서로 검색하면, 잘못된 커서로 거부됩니다",
            english=(
                "when a search uses a cursor that cannot be decoded, it is rejected as a "
                "broken cursor"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RecordsAndACaller]:
        return TwoRecordsGlobally(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[RecordsAndACaller, AuditLogAdapter, Searched]:
        return SearchingWithBadCursor()

    @override
    def then(self) -> Then[RecordsAndACaller, Searched]:
        return TheCallIsRefused(InvalidCursor)


SCENARIOS: list[SearchingStep] = [
    TheSuperadminSeesEveryRecord(),
    TheMonitorRoleSeesEveryRecord(),
    APlainUserMayNotSearch(),
    EnforcementOffStillNeedsTheRole(),
    OmittingThePageSizeCapsThePage(),
    AStatusFilterNarrowsToSuccess(),
    AnActorFilterNarrowsToOneUser(),
    ARunFilterNarrowsToOneRun(),
    TwoPaginationModesAreRefused(),
    ABrokenCursorIsRefused(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: AuditLogAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
