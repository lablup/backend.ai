"""기록 하나의 범위 검색 — 그 기록의 소유자 중 하나라도 읽을 수 있으면 그 기록이 남긴 범위를 모두 읽는다.

소유자는 기록이 대상으로 한 엔티티, 기록이 남긴 범위, 기록을 실행한 사용자다. 기록 하나만
지정하므로 부분 성공은 없다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.entity.audit_log import AuditLogID
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.audit_log.request import (
    AuditLogScopeFilter,
    AuditLogScopeOrder,
    SearchAuditLogScopesInput,
)
from ai.backend.common.dto.manager.v2.audit_log.response import SearchAuditLogScopesPayload
from ai.backend.common.dto.manager.v2.audit_log.types import (
    AuditLogScopeOrderField,
    OrderDirection,
)
from ai.backend.manager.api.adapters.audit_log.adapter import AuditLogAdapter
from ai.backend.manager.errors.base.field import FieldNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Says, Scenario, Then, When
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.audit_log import (
    ARecordWithoutScopes,
    AScopedRecord,
    NoRecordToSearch,
    ScopesToSearch,
    TheScopesAnswered,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type ScopesSearched = SearchAuditLogScopesPayload
type ScopeStep = Scenario[TestSeedingSession, ScopesToSearch, AuditLogAdapter, ScopesSearched]
ENFORCEMENT = "manager.rbac.enforcement_enabled"


@dataclass(frozen=True)
class SearchingTheScopes(When[ScopesToSearch, AuditLogAdapter, ScopesSearched]):
    """기록 하나의 범위를 범위 종류 순으로 검색한다. ``narrow``가 조건을 고른다."""

    narrow: str = "all"

    @override
    def operation(self) -> str:
        return "search_scopes"

    @override
    def describe(self, laid: ScopesToSearch) -> str:
        how = {
            "all": ("", ""),
            "project": (" 프로젝트 종류만 지정해", ", naming only the project type"),
            "user": (" 범위 하나의 식별자를 지정해", ", naming the identifier of one scope"),
        }[self.narrow]
        return Says(
            f"{laid.caller.username}이 기록 하나의 범위를{how[0]} 검색합니다",
            english=f"{laid.caller.username} searches the scopes of one record{how[1]}",
        )

    @override
    async def call(self, adapter: AuditLogAdapter, laid: ScopesToSearch) -> ScopesSearched:
        narrowed: AuditLogScopeFilter | None
        match self.narrow:
            case "project":
                narrowed = AuditLogScopeFilter(
                    scope_type=StringFilter(equals=ProjectEntityType.name())
                )
            case "user":
                narrowed = AuditLogScopeFilter(scope_id=UUIDFilter(equals=laid.narrow_id))
            case _:
                narrowed = None
        with ActingAs(laid.caller):
            return await adapter.search_scopes(
                AuditLogID(laid.record),
                SearchAuditLogScopesInput(
                    filter=narrowed,
                    order=[
                        AuditLogScopeOrder(
                            field=AuditLogScopeOrderField.SCOPE_TYPE,
                            direction=OrderDirection.ASC,
                        )
                    ],
                ),
            )


@dataclass(frozen=True)
class TheSuperadminSearchesTheScopes(
    Scenario[TestSeedingSession, ScopesToSearch, AuditLogAdapter, ScopesSearched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-reads-every-scope-a-record-recorded"

    @override
    def describe(self) -> str:
        return Says(
            "범위 둘을 남긴 기록을 superadmin 이 검색하면, 범위 둘이 반환됩니다",
            english=(
                "when the superadmin searches a record that left two scopes, both scopes come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ScopesToSearch]:
        return AScopedRecord(reader="superadmin")

    @override
    def when(self) -> When[ScopesToSearch, AuditLogAdapter, ScopesSearched]:
        return SearchingTheScopes()

    @override
    def then(self) -> Then[ScopesToSearch, ScopesSearched]:
        return TheScopesAnswered()


@dataclass(frozen=True)
class AReaderOfOneScopeReadsEveryScope(
    Scenario[TestSeedingSession, ScopesToSearch, AuditLogAdapter, ScopesSearched]
):
    @override
    def summary(self) -> str:
        return "a-reader-of-one-scope-reads-every-scope-of-the-record"

    @override
    def describe(self) -> str:
        return Says(
            "기록이 남긴 범위 하나에만 읽기 권한을 받은 사용자가 검색하면, 그 기록이 남긴 범위가 "
            "모두 반환됩니다",
            english=(
                "when a user granted read on only one scope a record left searches, every "
                "scope that record left comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ScopesToSearch]:
        return AScopedRecord(reader="scope")

    @override
    def when(self) -> When[ScopesToSearch, AuditLogAdapter, ScopesSearched]:
        return SearchingTheScopes()

    @override
    def then(self) -> Then[ScopesToSearch, ScopesSearched]:
        return TheScopesAnswered()


@dataclass(frozen=True)
class AReaderOfTheTargetReadsTheScopes(
    Scenario[TestSeedingSession, ScopesToSearch, AuditLogAdapter, ScopesSearched]
):
    @override
    def summary(self) -> str:
        return "a-reader-of-the-entity-a-record-is-about-reads-its-scopes"

    @override
    def describe(self) -> str:
        return Says(
            "기록의 대상 엔티티에만 읽기 권한을 받은 사용자가 검색하면, 그 기록의 범위가 반환됩니다",
            english=(
                "when a user granted read only on the entity a record is about searches, the "
                "scopes of that record come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ScopesToSearch]:
        return AScopedRecord(reader="about")

    @override
    def when(self) -> When[ScopesToSearch, AuditLogAdapter, ScopesSearched]:
        return SearchingTheScopes()

    @override
    def then(self) -> Then[ScopesToSearch, ScopesSearched]:
        return TheScopesAnswered()


@dataclass(frozen=True)
class AReaderOfTheTriggerReadsTheScopes(
    Scenario[TestSeedingSession, ScopesToSearch, AuditLogAdapter, ScopesSearched]
):
    @override
    def summary(self) -> str:
        return "a-reader-of-the-user-who-triggered-a-record-reads-its-scopes"

    @override
    def describe(self) -> str:
        return Says(
            "기록을 실행한 사용자에만 읽기 권한을 받은 사용자가 검색하면, 그 기록의 범위가 "
            "반환됩니다",
            english=(
                "when a user granted read only on the user who triggered a record searches, "
                "the scopes of that record come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ScopesToSearch]:
        return AScopedRecord(reader="trigger")

    @override
    def when(self) -> When[ScopesToSearch, AuditLogAdapter, ScopesSearched]:
        return SearchingTheScopes()

    @override
    def then(self) -> Then[ScopesToSearch, ScopesSearched]:
        return TheScopesAnswered()


@dataclass(frozen=True)
class ARecordWithoutScopesAnswersEmpty(
    Scenario[TestSeedingSession, ScopesToSearch, AuditLogAdapter, ScopesSearched]
):
    @override
    def summary(self) -> str:
        return "a-record-that-recorded-no-scope-answers-an-empty-page"

    @override
    def describe(self) -> str:
        return Says(
            "범위를 남기지 않은 기록을 그 대상에 읽기 권한을 받은 사용자가 검색하면, 빈 페이지가 "
            "반환됩니다",
            english=(
                "when a user granted read on the target of a record that left no scope "
                "searches, an empty page comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ScopesToSearch]:
        return ARecordWithoutScopes()

    @override
    def when(self) -> When[ScopesToSearch, AuditLogAdapter, ScopesSearched]:
        return SearchingTheScopes()

    @override
    def then(self) -> Then[ScopesToSearch, ScopesSearched]:
        return TheScopesAnswered()


@dataclass(frozen=True)
class AScopeTypeFilterNarrowsTheScopes(
    Scenario[TestSeedingSession, ScopesToSearch, AuditLogAdapter, ScopesSearched]
):
    @override
    def summary(self) -> str:
        return "a-scope-type-filter-narrows-the-answer-to-that-type"

    @override
    def describe(self) -> str:
        return Says(
            "범위 둘을 남긴 기록을 프로젝트 종류만 지정해 검색하면, 프로젝트 범위만 반환됩니다",
            english=(
                "when a record that left two scopes is searched naming only the project type, "
                "only the project scope comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ScopesToSearch]:
        return AScopedRecord(reader="superadmin", narrow="project")

    @override
    def when(self) -> When[ScopesToSearch, AuditLogAdapter, ScopesSearched]:
        return SearchingTheScopes(narrow="project")

    @override
    def then(self) -> Then[ScopesToSearch, ScopesSearched]:
        return TheScopesAnswered()


@dataclass(frozen=True)
class AScopeIdFilterNarrowsTheScopes(
    Scenario[TestSeedingSession, ScopesToSearch, AuditLogAdapter, ScopesSearched]
):
    @override
    def summary(self) -> str:
        return "a-scope-id-filter-narrows-the-answer-to-that-scope"

    @override
    def describe(self) -> str:
        return Says(
            "범위 둘을 남긴 기록을 범위 하나의 식별자를 지정해 검색하면, 그 범위만 반환됩니다",
            english=(
                "when a record that left two scopes is searched naming the identifier of one "
                "scope, only that scope comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ScopesToSearch]:
        return AScopedRecord(reader="superadmin", narrow="user")

    @override
    def when(self) -> When[ScopesToSearch, AuditLogAdapter, ScopesSearched]:
        return SearchingTheScopes(narrow="user")

    @override
    def then(self) -> Then[ScopesToSearch, ScopesSearched]:
        return TheScopesAnswered()


@dataclass(frozen=True)
class AUserReachingNoOwnerIsRefused(
    Scenario[TestSeedingSession, ScopesToSearch, AuditLogAdapter, ScopesSearched]
):
    @override
    def summary(self) -> str:
        return "a-user-who-can-read-no-owner-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "기록의 소유자를 하나도 읽을 수 없는 사용자가 검색하면, 권한 부족으로 거부됩니다",
            english=(
                "when a user who can read none of the owners of a record searches, it is "
                "rejected for lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ScopesToSearch]:
        return AScopedRecord(reader="nobody")

    @override
    def when(self) -> When[ScopesToSearch, AuditLogAdapter, ScopesSearched]:
        return SearchingTheScopes()

    @override
    def then(self) -> Then[ScopesToSearch, ScopesSearched]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheMonitorRoleWithoutAGrantIsRefused(
    Scenario[TestSeedingSession, ScopesToSearch, AuditLogAdapter, ScopesSearched]
):
    @override
    def summary(self) -> str:
        return "the-monitor-role-without-a-grant-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 모니터 역할 사용자가 검색하면, 권한 부족으로 거부됩니다. 이 "
            "검색은 권한 그래프로 보호됩니다",
            english=(
                "when a monitor-role user granted nothing searches, it is rejected for lack "
                "of permission. This search is protected by the permission graph"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ScopesToSearch]:
        return AScopedRecord(reader="monitor")

    @override
    def when(self) -> When[ScopesToSearch, AuditLogAdapter, ScopesSearched]:
        return SearchingTheScopes()

    @override
    def then(self) -> Then[ScopesToSearch, ScopesSearched]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnAbsentRecordIsNotFound(
    Scenario[TestSeedingSession, ScopesToSearch, AuditLogAdapter, ScopesSearched]
):
    @override
    def summary(self) -> str:
        return "searching-a-record-that-does-not-exist-is-not-found"

    @override
    def describe(self) -> str:
        return Says(
            "어느 기록에도 해당하지 않는 id 로 superadmin 이 검색하면, 찾을 수 없음으로 거부됩니다",
            english=(
                "when the superadmin searches with an id that matches no record, it is "
                "rejected as not found"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ScopesToSearch]:
        return NoRecordToSearch()

    @override
    def when(self) -> When[ScopesToSearch, AuditLogAdapter, ScopesSearched]:
        return SearchingTheScopes()

    @override
    def then(self) -> Then[ScopesToSearch, ScopesSearched]:
        return TheCallIsRefused(FieldNotFoundError)


@dataclass(frozen=True)
class TurningEnforcementOffReadsWithoutAGrant(
    Scenario[TestSeedingSession, ScopesToSearch, AuditLogAdapter, ScopesSearched], Configured
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-reads-the-scopes-without-a-grant"

    @override
    def describe(self) -> str:
        return Says(
            "권한 검사를 끄면 아무 권한도 없는 사용자도 기록의 범위를 검색할 수 있습니다",
            english=(
                "turning the permission check off lets even a user granted nothing search "
                "the scopes of a record"
            ),
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[TestSeedingSession, ScopesToSearch]:
        return AScopedRecord(reader="nobody")

    @override
    def when(self) -> When[ScopesToSearch, AuditLogAdapter, ScopesSearched]:
        return SearchingTheScopes()

    @override
    def then(self) -> Then[ScopesToSearch, ScopesSearched]:
        return TheScopesAnswered()


SCENARIOS: list[ScopeStep] = [
    TheSuperadminSearchesTheScopes(),
    AReaderOfOneScopeReadsEveryScope(),
    AReaderOfTheTargetReadsTheScopes(),
    AReaderOfTheTriggerReadsTheScopes(),
    ARecordWithoutScopesAnswersEmpty(),
    AScopeTypeFilterNarrowsTheScopes(),
    AScopeIdFilterNarrowsTheScopes(),
    AUserReachingNoOwnerIsRefused(),
    TheMonitorRoleWithoutAGrantIsRefused(),
    AnAbsentRecordIsNotFound(),
    TurningEnforcementOffReadsWithoutAGrant(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_scope_searching(
    scenario: ScopeStep, adapter: AuditLogAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
