"""범위 지정 검색 — 지정한 엔티티마다 부여된 읽기 권한을 검사하고, 부분 성공하지 않는다.

볼 수 없는 것이 하나라도 섞이면 요청 전체가 거부된다. 범위를 지정하는 방법은 둘 — 기록의
대상 엔티티로, 또는 기록을 실행한 사용자로. 권한은 앞은 그 엔티티에, 뒤는 그 사용자에 대해
검사한다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import UUIDFilter
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
    Says,
    Scenario,
    Then,
    When,
)
from bai_scenario.components.answers import NothingIsFound, TheCallIsRefused
from bai_scenario.components.audit_log import (
    ActorRecords,
    ARecordScopedToAProject,
    OneProjectManyRecords,
    OneProjectMixedStatus,
    OneProjectOneRun,
    ProjectRecords,
    ScopedActors,
    ScopedEntities,
    ThePageIsCapped,
    TheRecordsAnswered,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Searched = SearchAuditLogsPayload
type EntityStep = Scenario[TestSeedingSession, ScopedEntities, AuditLogAdapter, Searched]
type ActorStep = Scenario[TestSeedingSession, ScopedActors, AuditLogAdapter, Searched]
ENFORCEMENT = "manager.rbac.enforcement_enabled"


@dataclass(frozen=True)
class ScopedSearchingEntities(When[ScopedEntities, AuditLogAdapter, Searched]):
    """지정한 엔티티의 기록을 검색한다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: ScopedEntities) -> str:
        return Says(
            f"{laid.caller.username}이 엔티티를 지정해 검색합니다",
            english=f"{laid.caller.username} searches naming an entity",
        )

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
    """지정한 엔티티 안에서 성공한 기록만 필터로 검색한다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: ScopedEntities) -> str:
        return Says(
            f"{laid.caller.username}이 엔티티를 지정하고 성공 상태 필터로 검색합니다",
            english=(
                f"{laid.caller.username} searches naming an entity with a success status filter"
            ),
        )

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
class ScopedSearchingEntitiesByRun(When[ScopedEntities, AuditLogAdapter, Searched]):
    """지정한 엔티티 안에서 한 실행의 기록을 필터로 검색한다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: ScopedEntities) -> str:
        return Says(
            f"{laid.caller.username}이 엔티티를 지정하고 실행 필터로 검색합니다",
            english=(f"{laid.caller.username} searches naming an entity with a run filter"),
        )

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
                    filter=AuditLogFilter(action_id=UUIDFilter(equals=laid.filter_action)),
                )
            )


@dataclass(frozen=True)
class ScopedSearchingBadId(When[ScopedEntities, AuditLogAdapter, Searched]):
    """엔티티 id 필드에 id 형식이 아닌 문자열을 넣는다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: ScopedEntities) -> str:
        return Says(
            f"{laid.caller.username}이 id 형식이 아닌 값을 지정해 검색합니다",
            english=f"{laid.caller.username} searches naming a value that is not an id",
        )

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
    """지정한 사용자가 실행한 기록을 검색한다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: ScopedActors) -> str:
        return Says(
            f"{laid.caller.username}이 실행한 사용자를 지정해 검색합니다",
            english=f"{laid.caller.username} searches naming the user who triggered records",
        )

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
    Scenario[TestSeedingSession, ScopedEntities, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-on-an-entity-reads-only-that-entitys-records"

    @override
    def describe(self) -> str:
        return Says(
            "두 엔티티에 기록이 하나씩 있고 한쪽에만 읽기 권한을 받은 사용자가 그 엔티티를 "
            "지정해 검색하면, 그 엔티티의 기록만 반환됩니다",
            english=(
                "when each of two entities has one record and a user granted read on only "
                "one of them searches naming that entity, only the records of that entity "
                "come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ScopedEntities]:
        return ProjectRecords(grant_first=True, name="first")

    @override
    def when(self) -> When[ScopedEntities, AuditLogAdapter, Searched]:
        return ScopedSearchingEntities()

    @override
    def then(self) -> Then[ScopedEntities, Searched]:
        return TheRecordsAnswered()


@dataclass(frozen=True)
class NamingSeveralEntitiesMerges(
    Scenario[TestSeedingSession, ScopedEntities, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "naming-several-readable-entities-merges-their-records-newest-first"

    @override
    def describe(self) -> str:
        return Says(
            "두 엔티티에 모두 읽기 권한을 받은 사용자가 둘을 함께 지정해 검색하면, 두 기록이 "
            "다 반환되고 최근 것이 먼저입니다",
            english=(
                "when a user granted read on both of two entities searches naming both, both "
                "records come back with the newest first"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ScopedEntities]:
        return ProjectRecords(grant_first=True, grant_second=True, name="both")

    @override
    def when(self) -> When[ScopedEntities, AuditLogAdapter, Searched]:
        return ScopedSearchingEntities()

    @override
    def then(self) -> Then[ScopedEntities, Searched]:
        return TheRecordsAnswered()


@dataclass(frozen=True)
class AStatusFilterNarrowsWithinScope(
    Scenario[TestSeedingSession, ScopedEntities, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-status-filter-narrows-within-the-named-scope"

    @override
    def describe(self) -> str:
        return Says(
            "한 엔티티에 성공 기록과 거부 기록이 있을 때 그것을 지정하고 성공 상태 필터로 "
            "검색하면, 성공한 기록만 반환됩니다",
            english=(
                "when one entity holds a success record and a rejected record and it is "
                "searched with a success status filter, only the successful record comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ScopedEntities]:
        return OneProjectMixedStatus()

    @override
    def when(self) -> When[ScopedEntities, AuditLogAdapter, Searched]:
        return ScopedSearchingEntitiesBySuccess()

    @override
    def then(self) -> Then[ScopedEntities, Searched]:
        return TheRecordsAnswered()


@dataclass(frozen=True)
class ARunFilterNarrowsWithinScope(
    Scenario[TestSeedingSession, ScopedEntities, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-run-filter-narrows-within-the-named-scope"

    @override
    def describe(self) -> str:
        return Says(
            "한 엔티티에 두 실행이 남긴 기록이 있을 때 그것을 지정하고 한 실행 필터로 검색하면, "
            "그 실행이 남긴 기록만 모두 반환됩니다",
            english=(
                "when one entity holds records left by two runs and it is searched with one "
                "run filter, every record that run left comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ScopedEntities]:
        return OneProjectOneRun()

    @override
    def when(self) -> When[ScopedEntities, AuditLogAdapter, Searched]:
        return ScopedSearchingEntitiesByRun()

    @override
    def then(self) -> Then[ScopedEntities, Searched]:
        return TheRecordsAnswered()


@dataclass(frozen=True)
class OmittingThePageSizeCapsThePage(
    Scenario[TestSeedingSession, ScopedEntities, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "omitting-the-page-size-caps-a-scoped-page-and-says-more-follow"

    @override
    def describe(self) -> str:
        return Says(
            "지정한 엔티티에 기록이 많고 페이지 크기를 지정하지 않으면, 10건까지 반환되고 다음 "
            "페이지가 있다고 응답합니다",
            english=(
                "when the named entity holds many records and no page size is given, ten "
                "items come back and it answers that there is a next page"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ScopedEntities]:
        return OneProjectManyRecords(total=11)

    @override
    def when(self) -> When[ScopedEntities, AuditLogAdapter, Searched]:
        return ScopedSearchingEntities()

    @override
    def then(self) -> Then[ScopedEntities, Searched]:
        return ThePageIsCapped(size=10, total=11)


@dataclass(frozen=True)
class AnUnreadableEntityRefusesTheWhole(
    Scenario[TestSeedingSession, ScopedEntities, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "one-unreadable-entity-among-those-named-refuses-the-whole-read"

    @override
    def describe(self) -> str:
        return Says(
            "한쪽에만 읽기 권한을 받은 사용자가 두 엔티티를 함께 지정해 검색하면, 볼 수 있는 "
            "것만 주는 대신 요청 전체가 권한 부족으로 거부됩니다",
            english=(
                "when a user granted read on only one of two entities searches naming both, "
                "the whole request is rejected for lack of permission instead of giving only "
                "what is readable"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ScopedEntities]:
        return ProjectRecords(grant_first=True, name="both")

    @override
    def when(self) -> When[ScopedEntities, AuditLogAdapter, Searched]:
        return ScopedSearchingEntities()

    @override
    def then(self) -> Then[ScopedEntities, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotScopeSearch(
    Scenario[TestSeedingSession, ScopedEntities, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-scope-search-an-entity"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 없는 사용자가 엔티티를 지정해 검색하면, 권한 부족으로 거부됩니다",
            english=(
                "when a user granted nothing searches naming an entity, it is rejected for "
                "lack of permission"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ScopedEntities]:
        return ProjectRecords(name="first")

    @override
    def when(self) -> When[ScopedEntities, AuditLogAdapter, Searched]:
        return ScopedSearchingEntities()

    @override
    def then(self) -> Then[ScopedEntities, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheMonitorRoleGetsNoScopeForFree(
    Scenario[TestSeedingSession, ScopedEntities, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-monitor-role-without-a-grant-may-not-scope-search"

    @override
    def describe(self) -> str:
        return Says(
            "모니터 역할 사용자라도 권한 없이 엔티티를 지정해 검색하면, 권한 부족으로 거부됩니다. "
            "모니터가 통과하는 것은 superadmin 검사뿐이고 이 검색은 권한 그래프로 보호됩니다",
            english=(
                "even a monitor-role user is rejected for lack of permission when searching "
                "naming an entity without a grant. The monitor passes only the superadmin "
                "check, and this search is protected by the permission graph"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ScopedEntities]:
        return ProjectRecords(role=UserRole.MONITOR, name="first")

    @override
    def when(self) -> When[ScopedEntities, AuditLogAdapter, Searched]:
        return ScopedSearchingEntities()

    @override
    def then(self) -> Then[ScopedEntities, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class NamingAnUnknownEntityIsRefused(
    Scenario[TestSeedingSession, ScopedEntities, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "naming-an-entity-nothing-answers-to-is-refused-as-permission"

    @override
    def describe(self) -> str:
        return Says(
            "다른 엔티티에 읽기 권한을 받은 사용자가 어느 엔티티도 아닌 id 를 지정해 검색하면, 그 "
            "id 에 부여된 권한이 없어 권한 부족으로 거부됩니다",
            english=(
                "when a user granted read on another entity searches naming an id that is no "
                "entity, it is rejected for lack of permission because no permission is "
                "granted on that id"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ScopedEntities]:
        return ProjectRecords(grant_first=True, name="unknown")

    @override
    def when(self) -> When[ScopedEntities, AuditLogAdapter, Searched]:
        return ScopedSearchingEntities()

    @override
    def then(self) -> Then[ScopedEntities, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class TheSuperadminNamingAnUnknownEntityFindsNothing(
    Scenario[TestSeedingSession, ScopedEntities, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-naming-an-entity-nothing-answers-to-finds-nothing"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 어느 엔티티도 아닌 id 를 지정해 검색하면, 권한 검사를 지나가므로 "
            "거부되지 않고 빈 페이지가 옵니다",
            english=(
                "when the superadmin searches naming an id that is no entity, it passes the "
                "permission check and an empty page comes back instead of a rejection"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ScopedEntities]:
        return ProjectRecords(role=UserRole.SUPERADMIN, name="unknown")

    @override
    def when(self) -> When[ScopedEntities, AuditLogAdapter, Searched]:
        return ScopedSearchingEntities()

    @override
    def then(self) -> Then[ScopedEntities, Searched]:
        return NothingIsFound()


@dataclass(frozen=True)
class EnforcementOffReadsWithoutAGrant(
    Scenario[TestSeedingSession, ScopedEntities, AuditLogAdapter, Searched], Configured
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-reads-a-named-entitys-records-without-a-grant"

    @override
    def describe(self) -> str:
        return Says(
            "권한 검사를 끄면 아무 권한도 없는 사용자도 엔티티를 지정해 그 기록을 검색할 수 "
            "있습니다",
            english=(
                "turning the permission check off lets even a user granted nothing search the "
                "records of a named entity"
            ),
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[TestSeedingSession, ScopedEntities]:
        return ProjectRecords(name="first")

    @override
    def when(self) -> When[ScopedEntities, AuditLogAdapter, Searched]:
        return ScopedSearchingEntities()

    @override
    def then(self) -> Then[ScopedEntities, Searched]:
        return TheRecordsAnswered()


@dataclass(frozen=True)
class ANonEntityIdIsRefused(
    Scenario[TestSeedingSession, ScopedEntities, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-scope-id-that-is-not-an-entity-id-is-refused"

    @override
    def describe(self) -> str:
        return Says(
            "지정한 id 가 id 형식이 아니면, 잘못된 입력으로 거부됩니다",
            english=("when the named id is not in id form, it is rejected as invalid input"),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ScopedEntities]:
        return ProjectRecords(grant_first=True, name="first")

    @override
    def when(self) -> When[ScopedEntities, AuditLogAdapter, Searched]:
        return ScopedSearchingBadId()

    @override
    def then(self) -> Then[ScopedEntities, Searched]:
        return TheCallIsRefused(InvalidAPIParameters)


@dataclass(frozen=True)
class TheGrantedReaderReadsByActor(
    Scenario[TestSeedingSession, ScopedActors, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-read-on-an-actor-reads-only-what-that-actor-triggered"

    @override
    def describe(self) -> str:
        return Says(
            "두 사용자가 각각 기록을 남겼고 한 사용자에 읽기 권한을 받은 사용자가 그 사용자를 "
            "실행한 사용자로 지정해 검색하면, 그 사용자가 실행한 기록만 반환됩니다",
            english=(
                "when two users each left a record and a user granted read on one of them "
                "searches naming that user as the one who triggered records, only the records "
                "that user triggered come back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ScopedActors]:
        return ActorRecords(grant=True)

    @override
    def when(self) -> When[ScopedActors, AuditLogAdapter, Searched]:
        return ScopedSearchingActors()

    @override
    def then(self) -> Then[ScopedActors, Searched]:
        return TheRecordsAnswered()


@dataclass(frozen=True)
class ReadingOnesOwnActorRecordsNeedsAGrant(
    Scenario[TestSeedingSession, ScopedActors, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-even-the-records-they-triggered"

    @override
    def describe(self) -> str:
        return Says(
            "자기 자신에 읽기 권한을 받지 않은 사용자가 자기를 실행한 사용자로 지정해 검색하면, "
            "권한 부족으로 거부됩니다. 자기 기록을 조회하는 호출이 따로 없기 때문입니다",
            english=(
                "when a user granted no read on themselves searches naming themselves as the "
                "one who triggered records, it is rejected for lack of permission, because "
                "there is no separate call that reads one's own records"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ScopedActors]:
        return ActorRecords(caller_is_first=True)

    @override
    def when(self) -> When[ScopedActors, AuditLogAdapter, Searched]:
        return ScopedSearchingActors()

    @override
    def then(self) -> Then[ScopedActors, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ARecordIsFoundByItsScopeTag(
    Scenario[TestSeedingSession, ScopedEntities, AuditLogAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-record-tagged-with-a-scope-is-found-by-searching-that-scope"

    @override
    def describe(self) -> str:
        return Says(
            "다른 엔티티에 대한 기록이 한 프로젝트를 스코프로 달고 있을 때 그 프로젝트를 지정해 "
            "검색하면, 대상 엔티티가 그 프로젝트가 아니어도 그 기록이 반환됩니다",
            english=(
                "when a record about another entity carries a project as its scope and that "
                "project is named in a search, the record comes back even though its target "
                "entity is not that project"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, ScopedEntities]:
        return ARecordScopedToAProject()

    @override
    def when(self) -> When[ScopedEntities, AuditLogAdapter, Searched]:
        return ScopedSearchingEntities()

    @override
    def then(self) -> Then[ScopedEntities, Searched]:
        return TheRecordsAnswered()


ENTITY_SCENARIOS: list[EntityStep] = [
    TheGrantedUserReadsAnEntity(),
    ARecordIsFoundByItsScopeTag(),
    NamingSeveralEntitiesMerges(),
    AStatusFilterNarrowsWithinScope(),
    ARunFilterNarrowsWithinScope(),
    OmittingThePageSizeCapsThePage(),
    AnUnreadableEntityRefusesTheWhole(),
    AUserGrantedNothingMayNotScopeSearch(),
    TheMonitorRoleGetsNoScopeForFree(),
    NamingAnUnknownEntityIsRefused(),
    TheSuperadminNamingAnUnknownEntityFindsNothing(),
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
