"""세션 그룹 전체 검색 — 슈퍼관리자에게만, 배포의 replica group이 가진 세션 그룹까지."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.query import UUIDFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.session_group.request import (
    AdminSearchSessionGroupsInput,
    SessionGroupFilter,
    SessionGroupOrder,
    SessionGroupPlacementDirectionFilter,
)
from ai.backend.common.dto.manager.v2.session_group.response import (
    AdminSearchSessionGroupsPayload,
)
from ai.backend.common.dto.manager.v2.session_group.types import (
    SessionGroupOrderField,
    SessionGroupPlacementDirectionEnum,
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
    SessionGroupsInTwoProjects,
    TheseGroups,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Laid = SessionGroupsAndACaller
type Searched = AdminSearchSessionGroupsPayload
type SearchingStep = Scenario[TestSeedingSession, Laid, SessionGroupAdapter, Searched]


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
class SearchingTheProjectByDirection(When[Laid, SessionGroupAdapter, Searched]):
    """그 프로젝트의 세션 그룹을 방향으로 걸러 전체 검색한다."""

    direction: SessionGroupPlacementDirectionEnum

    @override
    def operation(self) -> str:
        return "global_search"

    @override
    def describe(self, laid: Laid) -> str:
        return Says(
            f"{laid.caller.username} 이 {laid.project.name} 프로젝트와 방향 {self.direction.value} "
            "를 필터로 전체 검색합니다",
            english=(
                f"{laid.caller.username} searches everything filtered by the project "
                f"{laid.project.name} and the direction {self.direction.value}"
            ),
        )

    @override
    async def call(self, adapter: SessionGroupAdapter, laid: Laid) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.global_search(
                AdminSearchSessionGroupsInput(
                    filter=SessionGroupFilter(
                        project_id=UUIDFilter(equals=laid.project.id),
                        placement_direction=SessionGroupPlacementDirectionFilter(
                            equals=self.direction
                        ),
                    )
                )
            )


@dataclass(frozen=True)
class ListingTheProjectByDirection(When[Laid, SessionGroupAdapter, Searched]):
    """그 프로젝트의 세션 그룹을 정해진 방향 순서로 전체 검색한다."""

    direction: OrderDirection

    @override
    def operation(self) -> str:
        return "global_search"

    @override
    def describe(self, laid: Laid) -> str:
        return Says(
            f"{laid.caller.username} 이 {laid.project.name} 프로젝트를 필터로 두고 방향 순서로 전체 "
            "검색합니다",
            english=(
                f"{laid.caller.username} searches everything filtered by the project "
                f"{laid.project.name}, ordered by the placement direction"
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
                            direction=self.direction,
                        )
                    ],
                )
            )


@dataclass(frozen=True)
class OnlyThePackedGroup(Then[Laid, Searched]):
    """그 방향을 쓰는 세션 그룹만 온다."""

    @override
    def says(self) -> str:
        return Says(
            "그 방향으로 배치하는 세션 그룹 하나만 옵니다",
            english="only the one session group that places its members that way comes back",
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
            Same("total_count", payload.total_count, 1),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class ThePacksComeFirst(Then[Laid, Searched]):
    """방향이 pack 인 세션 그룹이 먼저 온다."""

    @override
    def says(self) -> str:
        return Says(
            "방향이 pack 인 세션 그룹이 먼저, spread 인 세션 그룹이 그다음에 옵니다",
            english=(
                "the session group that packs its members comes first and the one that spreads "
                "them comes next"
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
                    [UUID(str(laid.users_group.id)), UUID(str(laid.deployment_group.id))],
                    Says(
                        "사용자가 만든 세션 그룹, 그리고 배포의 replica group 이 가진 세션 그룹",
                        english=(
                            "the session group the user made, then the one the deployment's "
                            "replica group holds"
                        ),
                    ),
                ),
            ),
            Same("total_count", payload.total_count, 2),
            Same("has_next_page", payload.has_next_page, False),
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
class FilteredByThePlacementDirection(
    Scenario[TestSeedingSession, SessionGroupsAndACaller, SessionGroupAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-filter-on-the-placement-direction-leaves-the-packed-group"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 그 프로젝트를 방향 pack 으로 걸러 전체 검색하면, 사용자가 만든 세션 "
            "그룹만 오고 방향이 spread 인 배포의 세션 그룹은 빠집니다. 이 동작은 역할이라 요청한 "
            "사용자가 superadmin 입니다",
            english=(
                "when a superadmin searches everything filtered by the project and the direction "
                "pack, only the session group the user created comes back and the deployment's "
                "group, which spreads, is left out; a role checks this operation, so the "
                "requesting user is a superadmin"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return SessionGroupsInTwoProjects(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, Searched]:
        return SearchingTheProjectByDirection(SessionGroupPlacementDirectionEnum.PACK)

    @override
    def then(self) -> Then[Laid, Searched]:
        return OnlyThePackedGroup()


@dataclass(frozen=True)
class OrderedByThePlacementDirection(
    Scenario[TestSeedingSession, SessionGroupsAndACaller, SessionGroupAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "ordering-by-the-placement-direction-puts-pack-before-spread"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 그 프로젝트의 세션 그룹을 방향 오름차순으로 검색하면, 방향이 pack 인 "
            "사용자의 세션 그룹이 먼저 오고 방향이 spread 인 배포의 세션 그룹이 그다음에 옵니다. "
            "이 동작은 역할이라 요청한 사용자가 superadmin 입니다",
            english=(
                "when a superadmin searches the session groups of the project ordered by the "
                "placement direction in ascending order, the user's packed group comes first and "
                "the deployment's spreading group comes next; a role checks this operation, so "
                "the requesting user is a superadmin"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return SessionGroupsInTwoProjects(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, Searched]:
        return ListingTheProjectByDirection(OrderDirection.ASC)

    @override
    def then(self) -> Then[Laid, Searched]:
        return ThePacksComeFirst()


SCENARIOS: list[SearchingStep] = [
    TheSuperadminFindsBothGroups(),
    AGrantedUserMayNotSearchEverything(),
    FilteredByThePlacementDirection(),
    OrderedByThePlacementDirection(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_searching(
    scenario: SearchingStep, adapter: SessionGroupAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
