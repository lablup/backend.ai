"""지목 검색 — 지목한 엔티티마다 걸린 읽기 권한이 지키고, 부분 성공하지 않는다.

볼 수 없는 것이 하나라도 섞이면 요청 전체가 거부된다. 지목하는 방법은 둘 — 기록의 대상
엔티티로, 또는 기록을 일으킨 사용자로. 권한은 앞은 그 엔티티에, 뒤는 그 사용자에 묻는다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

import pytest
from bai_scenario.components.answers import NothingIsFound, TheCallIsRefused
from bai_scenario.components.audit_log import (
    ActorRecords,
    OneProjectManyRecords,
    OneProjectMixedStatus,
    ProjectRecords,
    ScopedActors,
    ScopedEntities,
    ThePageIsCapped,
    TheRecordsAnswered,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.audit_log.request import (
    AuditLogFilter,
    AuditLogScope,
    AuditLogStatusFilter,
    ScopedSearchAuditLogsInput,
)
from ai.backend.common.dto.manager.v2.audit_log.response import SearchAuditLogsPayload
from ai.backend.common.dto.manager.v2.audit_log.types import AuditLogStatus
from ai.backend.common.dto.manager.v2.rbac.types import EntityTypeScope, UUIDScope
from ai.backend.manager.api.adapters.audit_log.adapter import AuditLogAdapter
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Configured,
    Given,
    Scenario,
    Then,
    When,
)

type Searched = SearchAuditLogsPayload
type EntityStep = Scenario[SeedingSession, ScopedEntities, AuditLogAdapter, Searched]
type ActorStep = Scenario[SeedingSession, ScopedActors, AuditLogAdapter, Searched]
ENFORCEMENT = "manager.rbac.enforcement_enabled"


@dataclass(frozen=True)
class ScopedSearchingEntities(When[ScopedEntities, AuditLogAdapter, Searched]):
    """지목한 엔티티의 기록을 검색한다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: ScopedEntities) -> str:
        return f"{laid.caller.username}이 엔티티를 지목해 검색"

    @override
    async def call(self, adapter: AuditLogAdapter, laid: ScopedEntities) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchAuditLogsInput(
                    scope=AuditLogScope(
                        entity=[
                            EntityTypeScope(entity_type=ProjectEntityType(), entity_id=str(one))
                            for one in laid.named
                        ]
                    )
                )
            )


@dataclass(frozen=True)
class ScopedSearchingEntitiesBySuccess(When[ScopedEntities, AuditLogAdapter, Searched]):
    """지목한 엔티티 안에서 성공한 것만 남도록 거른다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: ScopedEntities) -> str:
        return f"{laid.caller.username}이 엔티티를 지목하고 성공 상태로 걸러 검색"

    @override
    async def call(self, adapter: AuditLogAdapter, laid: ScopedEntities) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchAuditLogsInput(
                    scope=AuditLogScope(
                        entity=[
                            EntityTypeScope(entity_type=ProjectEntityType(), entity_id=str(one))
                            for one in laid.named
                        ]
                    ),
                    filter=AuditLogFilter(
                        status=AuditLogStatusFilter(equals=AuditLogStatus.SUCCESS)
                    ),
                )
            )


@dataclass(frozen=True)
class ScopedSearchingBadId(When[ScopedEntities, AuditLogAdapter, Searched]):
    """엔티티 id 자리에 id 꼴이 아닌 문자열을 넣는다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: ScopedEntities) -> str:
        return f"{laid.caller.username}이 id 꼴이 아닌 값을 지목해 검색"

    @override
    async def call(self, adapter: AuditLogAdapter, laid: ScopedEntities) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchAuditLogsInput(
                    scope=AuditLogScope(
                        entity=[
                            EntityTypeScope(entity_type=ProjectEntityType(), entity_id="not-a-uuid")
                        ]
                    )
                )
            )


@dataclass(frozen=True)
class ScopedSearchingActors(When[ScopedActors, AuditLogAdapter, Searched]):
    """지목한 사용자가 일으킨 기록을 검색한다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: ScopedActors) -> str:
        return f"{laid.caller.username}이 일으킨 사용자를 지목해 검색"

    @override
    async def call(self, adapter: AuditLogAdapter, laid: ScopedActors) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchAuditLogsInput(
                    scope=AuditLogScope(triggered_user=[UUIDScope(value=one) for one in laid.named])
                )
            )


@dataclass(frozen=True)
class TheGrantedUserReadsAnEntity(
    Scenario[SeedingSession, ScopedEntities, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-on-an-entity-reads-only-that-entitys-records"

    @override
    def describe(self) -> str:
        return (
            "두 엔티티에 기록이 하나씩 있고 한쪽에만 읽기 권한을 받은 사용자가 그 엔티티를 "
            "지목해 검색하면, 그 엔티티의 기록만 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, ScopedEntities]:
        return ProjectRecords(grant_first=True, name="first")

    @override
    def when(self) -> When[ScopedEntities, AuditLogAdapter, Searched]:
        return ScopedSearchingEntities()

    @override
    def then(self) -> Then[ScopedEntities, Searched]:
        return TheRecordsAnswered()


@dataclass(frozen=True)
class NamingSeveralEntitiesMerges(
    Scenario[SeedingSession, ScopedEntities, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "naming-several-readable-entities-merges-their-records-newest-first"

    @override
    def describe(self) -> str:
        return (
            "두 엔티티에 모두 읽기 권한을 받은 사용자가 둘을 함께 지목해 검색하면, 두 기록이 "
            "다 오고 최근 것이 먼저다"
        )

    @override
    def given(self) -> Given[SeedingSession, ScopedEntities]:
        return ProjectRecords(grant_first=True, grant_second=True, name="both")

    @override
    def when(self) -> When[ScopedEntities, AuditLogAdapter, Searched]:
        return ScopedSearchingEntities()

    @override
    def then(self) -> Then[ScopedEntities, Searched]:
        return TheRecordsAnswered()


@dataclass(frozen=True)
class AStatusFilterNarrowsWithinScope(
    Scenario[SeedingSession, ScopedEntities, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-status-filter-narrows-within-the-named-scope"

    @override
    def describe(self) -> str:
        return (
            "한 엔티티에 성공 기록과 거부 기록이 있을 때 그것을 지목하고 성공 상태로 걸러 "
            "검색하면, 성공한 것만 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, ScopedEntities]:
        return OneProjectMixedStatus()

    @override
    def when(self) -> When[ScopedEntities, AuditLogAdapter, Searched]:
        return ScopedSearchingEntitiesBySuccess()

    @override
    def then(self) -> Then[ScopedEntities, Searched]:
        return TheRecordsAnswered()


@dataclass(frozen=True)
class OmittingThePageSizeCapsThePage(
    Scenario[SeedingSession, ScopedEntities, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "omitting-the-page-size-caps-a-scoped-page-and-says-more-follow"

    @override
    def describe(self) -> str:
        return "지목한 엔티티에 기록이 많고 페이지 크기를 대지 않으면, 열 건까지 오고 다음 페이지가 있다고 답한다"

    @override
    def given(self) -> Given[SeedingSession, ScopedEntities]:
        return OneProjectManyRecords(total=11)

    @override
    def when(self) -> When[ScopedEntities, AuditLogAdapter, Searched]:
        return ScopedSearchingEntities()

    @override
    def then(self) -> Then[ScopedEntities, Searched]:
        return ThePageIsCapped(size=10, total=11)


@dataclass(frozen=True)
class AnUnreadableEntityRefusesTheWhole(
    Scenario[SeedingSession, ScopedEntities, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "one-unreadable-entity-among-those-named-refuses-the-whole-read"

    @override
    def describe(self) -> str:
        return (
            "한쪽에만 읽기 권한을 받은 사용자가 두 엔티티를 함께 지목해 검색하면, 볼 수 있는 "
            "것만 주는 대신 요청 전체가 권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ScopedEntities]:
        return ProjectRecords(grant_first=True, name="both")

    @override
    def when(self) -> When[ScopedEntities, AuditLogAdapter, Searched]:
        return ScopedSearchingEntities()

    @override
    def then(self) -> Then[ScopedEntities, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotScopeSearch(
    Scenario[SeedingSession, ScopedEntities, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-scope-search-an-entity"

    @override
    def describe(self) -> str:
        return "아무 권한도 받지 않은 사용자가 엔티티를 지목해 검색하면, 권한 부족으로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ScopedEntities]:
        return ProjectRecords(name="first")

    @override
    def when(self) -> When[ScopedEntities, AuditLogAdapter, Searched]:
        return ScopedSearchingEntities()

    @override
    def then(self) -> Then[ScopedEntities, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheMonitorRoleGetsNoScopeForFree(
    Scenario[SeedingSession, ScopedEntities, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-monitor-role-without-a-grant-may-not-scope-search"

    @override
    def describe(self) -> str:
        return (
            "모니터 역할 사용자라도 권한 없이 엔티티를 지목해 검색하면, 권한 부족으로 거부된다. "
            "모니터가 지나는 것은 역할 문뿐이고 이 문은 권한 그래프가 지킨다"
        )

    @override
    def given(self) -> Given[SeedingSession, ScopedEntities]:
        return ProjectRecords(role=UserRole.MONITOR, name="first")

    @override
    def when(self) -> When[ScopedEntities, AuditLogAdapter, Searched]:
        return ScopedSearchingEntities()

    @override
    def then(self) -> Then[ScopedEntities, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class NamingAnUnknownEntityIsRefused(
    Scenario[SeedingSession, ScopedEntities, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "naming-an-entity-nothing-answers-to-is-refused-as-permission"

    @override
    def describe(self) -> str:
        return (
            "다른 엔티티에 읽기 권한을 받은 사용자가 아무것도 아닌 id를 지목해 검색하면, 그 id에 "
            "걸린 권한이 없어 권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, ScopedEntities]:
        return ProjectRecords(grant_first=True, name="unknown")

    @override
    def when(self) -> When[ScopedEntities, AuditLogAdapter, Searched]:
        return ScopedSearchingEntities()

    @override
    def then(self) -> Then[ScopedEntities, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminNamingAnUnknownEntitySeesNothing(
    Scenario[SeedingSession, ScopedEntities, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-naming-an-entity-nothing-answers-to-sees-an-empty-page"

    @override
    def describe(self) -> str:
        return (
            "슈퍼관리자가 아무것도 아닌 id를 지목해 검색하면, 권한 검사를 지나 빈 답을 본다. "
            "대상 없음으로 거부하는 자리가 아니다"
        )

    @override
    def given(self) -> Given[SeedingSession, ScopedEntities]:
        return ProjectRecords(role=UserRole.SUPERADMIN, name="unknown")

    @override
    def when(self) -> When[ScopedEntities, AuditLogAdapter, Searched]:
        return ScopedSearchingEntities()

    @override
    def then(self) -> Then[ScopedEntities, Searched]:
        return NothingIsFound()


@dataclass(frozen=True)
class EnforcementOffReadsWithoutAGrant(
    Scenario[SeedingSession, ScopedEntities, AuditLogAdapter, Searched], Configured
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-reads-a-named-entitys-records-without-a-grant"

    @override
    def describe(self) -> str:
        return (
            "엔티티 권한 집행을 끄면 아무 권한도 받지 않은 사용자도 엔티티를 지목해 그 기록을 "
            "읽는다. 이 문은 권한 그래프가 지키기 때문이다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, ScopedEntities]:
        return ProjectRecords(name="first")

    @override
    def when(self) -> When[ScopedEntities, AuditLogAdapter, Searched]:
        return ScopedSearchingEntities()

    @override
    def then(self) -> Then[ScopedEntities, Searched]:
        return TheRecordsAnswered()


@dataclass(frozen=True)
class ANonEntityIdIsRefused(Scenario[SeedingSession, ScopedEntities, AuditLogAdapter, Searched]):
    @override
    def summary(self) -> str:
        return "a-scope-id-that-is-not-an-entity-id-is-refused"

    @override
    def describe(self) -> str:
        return "지목한 id가 id 꼴이 아니면, 입력이 틀렸다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, ScopedEntities]:
        return ProjectRecords(grant_first=True, name="first")

    @override
    def when(self) -> When[ScopedEntities, AuditLogAdapter, Searched]:
        return ScopedSearchingBadId()

    @override
    def then(self) -> Then[ScopedEntities, Searched]:
        return TheCallIsRefused(InvalidAPIParameters)


@dataclass(frozen=True)
class TheGrantedReaderReadsByActor(
    Scenario[SeedingSession, ScopedActors, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-on-an-actor-reads-only-what-that-actor-triggered"

    @override
    def describe(self) -> str:
        return (
            "두 사용자가 각각 기록을 남겼고 한 사용자에 읽기 권한을 받은 사람이 그 사용자를 "
            "일으킨 사람으로 지목해 검색하면, 그 사용자가 일으킨 기록만 온다"
        )

    @override
    def given(self) -> Given[SeedingSession, ScopedActors]:
        return ActorRecords(grant=True)

    @override
    def when(self) -> When[ScopedActors, AuditLogAdapter, Searched]:
        return ScopedSearchingActors()

    @override
    def then(self) -> Then[ScopedActors, Searched]:
        return TheRecordsAnswered()


@dataclass(frozen=True)
class ReadingOnesOwnActorRecordsNeedsAGrant(
    Scenario[SeedingSession, ScopedActors, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-even-the-records-they-triggered"

    @override
    def describe(self) -> str:
        return (
            "자기 자신에 읽기 권한을 받지 않은 사용자가 자기를 일으킨 사람으로 지목해 검색하면, "
            "권한 부족으로 거부된다. 자기 기록을 읽는 문이 따로 없기 때문이다"
        )

    @override
    def given(self) -> Given[SeedingSession, ScopedActors]:
        return ActorRecords(caller_is_first=True)

    @override
    def when(self) -> When[ScopedActors, AuditLogAdapter, Searched]:
        return ScopedSearchingActors()

    @override
    def then(self) -> Then[ScopedActors, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


ENTITY_SCENARIOS: list[EntityStep] = [
    TheGrantedUserReadsAnEntity(),
    NamingSeveralEntitiesMerges(),
    AStatusFilterNarrowsWithinScope(),
    OmittingThePageSizeCapsThePage(),
    AnUnreadableEntityRefusesTheWhole(),
    AUserGrantedNothingMayNotScopeSearch(),
    TheMonitorRoleGetsNoScopeForFree(),
    NamingAnUnknownEntityIsRefused(),
    TheSuperadminNamingAnUnknownEntitySeesNothing(),
    EnforcementOffReadsWithoutAGrant(),
    ANonEntityIdIsRefused(),
]

ACTOR_SCENARIOS: list[ActorStep] = [
    TheGrantedReaderReadsByActor(),
    ReadingOnesOwnActorRecordsNeedsAGrant(),
]


@pytest.mark.parametrize("scenario", ENTITY_SCENARIOS, ids=lambda s: s.summary())
async def test_scoped_searching_by_entity(
    scenario: EntityStep, adapter: AuditLogAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)


@pytest.mark.parametrize("scenario", ACTOR_SCENARIOS, ids=lambda s: s.summary())
async def test_scoped_searching_by_actor(
    scenario: ActorStep, adapter: AuditLogAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
