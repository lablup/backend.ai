"""세션 그룹 전체 검색 — 슈퍼관리자에게만, 배포의 replica group이 가진 세션 그룹까지."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import NullableDateTimeFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.session_group.request import (
    AdminSearchSessionGroupsInput,
    SessionGroupFilter,
    SessionGroupOrder,
)
from ai.backend.common.dto.manager.v2.session_group.response import (
    AdminSearchSessionGroupsPayload,
)
from ai.backend.common.dto.manager.v2.session_group.types import (
    SessionGroupOrderField,
)
from ai.backend.manager.api.adapters.session_group.adapter import SessionGroupAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
    SameAs,
    Says,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import MissingResponse, TheCallIsRefused
from bai_scenario.components.session_group import (
    GrantedIn,
    SessionGroupsAndACaller,
    SessionGroupsAndARetiredOne,
    SessionGroupsInTwoProjects,
    SessionGroupsWithARetiredOne,
    TheseGroups,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Laid = SessionGroupsAndACaller
type RetiredLaid = SessionGroupsAndARetiredOne
type Searched = AdminSearchSessionGroupsPayload
type SearchingStep = Scenario[TestSeedingSession, Laid, SessionGroupAdapter, Searched]
type RetiredSearchingStep = Scenario[TestSeedingSession, RetiredLaid, SessionGroupAdapter, Searched]


@dataclass(frozen=True)
class SearchingTheProject(When[Laid, SessionGroupAdapter, Searched]):
    """세션 그룹들이 있는 프로젝트로 걸러 전체 검색한다."""

    @override
    def operation(self) -> str:
        return "global_search"

    @override
    def describe(self, laid: Laid) -> str:
        return Says(
            f"{laid.caller.username} 이 {laid.project.name} 프로젝트를 필터로 전체 검색합니다",
            english=(
                f"{laid.caller.username} searches everything filtered by the project "
                f"{laid.project.name}"
            ),
        )

    @override
    async def call(self, adapter: SessionGroupAdapter, laid: Laid) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.global_search(
                AdminSearchSessionGroupsInput(
                    filter=SessionGroupFilter(project_id=UUIDFilter(equals=laid.project.id))
                )
            )


@dataclass(frozen=True)
class BothGroupsOfTheProject(Then[Laid, Searched]):
    """그 프로젝트의 사용자가 만든 세션 그룹과 배포의 replica group이 가진 세션 그룹이 모두 온다."""

    @override
    def says(self) -> str:
        return Says(
            "그 프로젝트의 사용자가 생성한 세션 그룹과 배포의 replica group 이 가진 세션 그룹이 "
            "모두 옵니다",
            english=(
                "the session group the user created in that project and the session group held by "
                "the deployment's replica group both come back"
            ),
        )

    @override
    def look(self, laid: Laid, answered: Answered[Searched]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            Held(
                "items",
                [one.entity_id for one in payload.items],
                TheseGroups(
                    frozenset({laid.users_group.id, laid.deployment_group.id}),
                    Says(
                        "사용자가 생성한 세션 그룹과 배포의 replica group 이 가진 세션 그룹",
                        english=(
                            "the session group the user created and the session group held by the "
                            "deployment's replica group"
                        ),
                    ),
                ),
            ),
            Same("total_count", payload.total_count, 2),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class ListingTheProjectFirstPage(When[Laid, SessionGroupAdapter, Searched]):
    """그 프로젝트의 세션 그룹을 방향 오름차순으로 한 건씩 검색한다."""

    @override
    def operation(self) -> str:
        return "global_search"

    @override
    def describe(self, laid: Laid) -> str:
        return Says(
            f"{laid.caller.username} 이 {laid.project.name} 프로젝트의 세션 그룹을 방향 "
            "오름차순으로 한 건씩 조회합니다",
            english=(
                f"{laid.caller.username} searches the session groups of {laid.project.name}, "
                "ordered by the placement direction and one per page"
            ),
        )

    @override
    async def call(self, adapter: SessionGroupAdapter, laid: Laid) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.global_search(
                AdminSearchSessionGroupsInput(
                    filter=SessionGroupFilter(project_id=UUIDFilter(equals=laid.project.id)),
                    order=[
                        SessionGroupOrder(
                            field=SessionGroupOrderField.PLACEMENT_DIRECTION,
                            direction=OrderDirection.ASC,
                        )
                    ],
                    limit=1,
                )
            )


@dataclass(frozen=True)
class TheFirstPackedPage(Then[Laid, Searched]):
    """방향이 pack 인 세션 그룹 하나가 첫 페이지에 오고, 다음 페이지가 있다고 답한다.

    다른 프로젝트의 세션 그룹은 프로젝트 필터에 걸려 오지 않는다.
    """

    @override
    def says(self) -> str:
        return Says(
            "방향이 pack 인 사용자의 세션 그룹 하나가 첫 페이지에 오고 다음 페이지가 있다고 "
            "답합니다. 다른 프로젝트의 세션 그룹은 빠집니다",
            english=(
                "the user's packed session group comes back alone on the first page and the "
                "answer says a next page exists; the session groups of the other project are "
                "left out"
            ),
        )

    @override
    def look(self, laid: Laid, answered: Answered[Searched]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            Held(
                "items",
                [one.entity_id for one in payload.items],
                SameAs(
                    [UUID(str(laid.users_group.id))],
                    Says(
                        "사용자가 만든 세션 그룹",
                        english="the session group the user made",
                    ),
                ),
            ),
            Same("total_count", payload.total_count, 2),
            Same("has_next_page", payload.has_next_page, True),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheSuperadminFindsBothGroups(
    Scenario[TestSeedingSession, SessionGroupsAndACaller, SessionGroupAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-finds-a-users-group-and-a-deployments-group"

    @override
    def describe(self) -> str:
        return Says(
            "아무 권한도 받지 않은 superadmin 이 한 프로젝트를 필터로 전체 검색하면, 그 "
            "프로젝트의 사용자가 생성한 세션 그룹과 배포의 replica group 이 가진 세션 그룹이 모두 "
            "옵니다. 이 동작은 역할이라 요청한 사용자가 superadmin 입니다",
            english=(
                "when a superadmin with no grant searches everything filtered by one project, the "
                "session group the user created in that project and the session group held by the "
                "deployment's replica group both come back; a role checks this operation, so the "
                "requesting user is a superadmin"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return SessionGroupsInTwoProjects(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, Searched]:
        return SearchingTheProject()

    @override
    def then(self) -> Then[Laid, Searched]:
        return BothGroupsOfTheProject()


@dataclass(frozen=True)
class AGrantedUserMayNotSearchEverything(
    Scenario[TestSeedingSession, SessionGroupsAndACaller, SessionGroupAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-who-is-not-a-superadmin-may-not-search-every-session-group"

    @override
    def describe(self) -> str:
        return Says(
            "그 프로젝트에서 세션 그룹 읽기 권한을 받았어도 superadmin 이 아닌 사용자가 전체 "
            "검색하면, 역할로 거부됩니다",
            english=(
                "when a user granted session group read in that project but not a superadmin "
                "searches everything, the role rejects it"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return SessionGroupsInTwoProjects(granted_in=GrantedIn.THE_PROJECT)

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, Searched]:
        return SearchingTheProject()

    @override
    def then(self) -> Then[Laid, Searched]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class OrderedByThePlacementDirection(
    Scenario[TestSeedingSession, SessionGroupsAndACaller, SessionGroupAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "ordering-by-the-placement-direction-puts-pack-on-the-first-page"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 그 프로젝트의 세션 그룹을 방향 오름차순으로 한 건씩 조회하면, 방향이 "
            "pack 인 사용자의 세션 그룹이 첫 페이지에 오고 다음 페이지가 있다고 답합니다. 다른 "
            "프로젝트의 세션 그룹은 빠집니다. 이 동작은 역할이라 요청한 사용자가 superadmin 입니다",
            english=(
                "when a superadmin searches the session groups of the project filtered by that "
                "project and ordered by the placement direction in ascending order, one per page, "
                "the user's packed group comes back alone on the first page and the answer says a "
                "next page exists; the session groups of the other project are left out; a role "
                "checks this operation, so the requesting user is a superadmin"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return SessionGroupsInTwoProjects(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, Searched]:
        return ListingTheProjectFirstPage()

    @override
    def then(self) -> Then[Laid, Searched]:
        return TheFirstPackedPage()


@dataclass(frozen=True)
class SearchingTheProjectOfTheRetiredOne(When[RetiredLaid, SessionGroupAdapter, Searched]):
    """그 프로젝트로 걸러 전체 검색한다. 삭제된 세션 그룹을 이름 짓지 않는다."""

    @override
    def operation(self) -> str:
        return "global_search"

    @override
    def describe(self, laid: RetiredLaid) -> str:
        return Says(
            f"{laid.caller.username} 이 {laid.project.name} 프로젝트를 필터로 전체 검색합니다",
            english=(
                f"{laid.caller.username} searches everything filtered by the project "
                f"{laid.project.name}"
            ),
        )

    @override
    async def call(self, adapter: SessionGroupAdapter, laid: RetiredLaid) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.global_search(
                AdminSearchSessionGroupsInput(
                    filter=SessionGroupFilter(project_id=UUIDFilter(equals=laid.project.id))
                )
            )


@dataclass(frozen=True)
class SearchingTheDeletedGroupsOfTheProject(When[RetiredLaid, SessionGroupAdapter, Searched]):
    """그 프로젝트에서 삭제 시각이 찍힌 세션 그룹만 걸러 전체 검색한다."""

    @override
    def operation(self) -> str:
        return "global_search"

    @override
    def describe(self, laid: RetiredLaid) -> str:
        return Says(
            f"{laid.caller.username} 이 {laid.project.name} 프로젝트를 필터로 두고 삭제된 세션 "
            "그룹만 전체 검색합니다",
            english=(
                f"{laid.caller.username} searches everything filtered by the project "
                f"{laid.project.name} and by the groups that carry a deletion time"
            ),
        )

    @override
    async def call(self, adapter: SessionGroupAdapter, laid: RetiredLaid) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.global_search(
                AdminSearchSessionGroupsInput(
                    filter=SessionGroupFilter(
                        project_id=UUIDFilter(equals=laid.project.id),
                        deleted_at=NullableDateTimeFilter(is_null=False),
                    )
                )
            )


@dataclass(frozen=True)
class OnlyTheLiveGroup(Then[RetiredLaid, Searched]):
    """삭제 시각이 찍힌 세션 그룹은 빠지고 사용자가 만든 세션 그룹 하나만 온다."""

    @override
    def says(self) -> str:
        return Says(
            "삭제 시각이 찍힌 세션 그룹은 빠지고 사용자가 만든 세션 그룹 하나만 옵니다",
            english=(
                "the session group that carries a deletion time is left out and only the one "
                "the user made comes back"
            ),
        )

    @override
    def look(self, laid: RetiredLaid, answered: Answered[Searched]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            Held(
                "items",
                [one.entity_id for one in payload.items],
                SameAs(
                    [UUID(str(laid.live_group.id))],
                    Says(
                        "사용자가 만든 세션 그룹",
                        english="the session group the user made",
                    ),
                ),
            ),
            Same("total_count", payload.total_count, 1),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class OnlyTheRetiredGroup(Then[RetiredLaid, Searched]):
    """삭제 시각이 찍힌 세션 그룹 하나만 온다."""

    @override
    def says(self) -> str:
        return Says(
            "삭제 시각이 찍힌 세션 그룹 하나만 옵니다",
            english="only the session group that carries a deletion time comes back",
        )

    @override
    def look(self, laid: RetiredLaid, answered: Answered[Searched]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            Held(
                "items",
                [one.entity_id for one in payload.items],
                SameAs(
                    [UUID(str(laid.retired_group.id))],
                    Says(
                        "서비스를 마친 복제본 그룹이 가진 세션 그룹",
                        english="the session group of the replica group that stopped serving",
                    ),
                ),
            ),
            Same("total_count", payload.total_count, 1),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class ASoftDeletedGroupIsLeftOut(
    Scenario[TestSeedingSession, RetiredLaid, SessionGroupAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-soft-deleted-group-is-left-out-of-the-search"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 그 프로젝트로 걸러 전체 검색하면, 삭제 시각이 찍힌 세션 그룹은 빠지고 "
            "사용자가 만든 세션 그룹만 옵니다. 이 동작은 역할이라 요청한 사용자가 superadmin 입니다",
            english=(
                "when a superadmin searches everything filtered by the project, the session "
                "group that carries a deletion time is left out and only the session group the "
                "user made comes back; a role checks this operation, so the requesting user is "
                "a superadmin"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RetiredLaid]:
        return SessionGroupsWithARetiredOne()

    @override
    def when(self) -> When[RetiredLaid, SessionGroupAdapter, Searched]:
        return SearchingTheProjectOfTheRetiredOne()

    @override
    def then(self) -> Then[RetiredLaid, Searched]:
        return OnlyTheLiveGroup()


@dataclass(frozen=True)
class ASoftDeletedGroupIsFoundWhenNamed(
    Scenario[TestSeedingSession, RetiredLaid, SessionGroupAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-soft-deleted-group-comes-back-when-the-filter-names-it"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 그 프로젝트로 걸러 삭제된 세션 그룹만 요청하면, 삭제 시각이 찍힌 세션 "
            "그룹 하나만 옵니다. 이 동작은 역할이라 요청한 사용자가 superadmin 입니다",
            english=(
                "when a superadmin searches everything filtered by the project and by the groups "
                "that carry a deletion time, only the session group that carries one comes "
                "back; a role checks this operation, so the requesting user is a superadmin"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, RetiredLaid]:
        return SessionGroupsWithARetiredOne()

    @override
    def when(self) -> When[RetiredLaid, SessionGroupAdapter, Searched]:
        return SearchingTheDeletedGroupsOfTheProject()

    @override
    def then(self) -> Then[RetiredLaid, Searched]:
        return OnlyTheRetiredGroup()


SCENARIOS: list[SearchingStep | RetiredSearchingStep] = [
    TheSuperadminFindsBothGroups(),
    AGrantedUserMayNotSearchEverything(),
    OrderedByThePlacementDirection(),
    ASoftDeletedGroupIsLeftOut(),
    ASoftDeletedGroupIsFoundWhenNamed(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep | RetiredSearchingStep,
    adapter: SessionGroupAdapter,
    engine: ExtendedAsyncSAEngine,
) -> None:
    await run_scenario(scenario, adapter, engine)
