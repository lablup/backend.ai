"""스코프로 세션 그룹 검색 — 스코프들이 닿는 사용자 그룹을 합쳐서, 그 스코프를 모두 읽을 수 있는 사람에게."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.common.dto.manager.v2.session_group.request import (
    ScopedSearchSessionGroupsInput,
)
from ai.backend.common.dto.manager.v2.session_group.response import (
    AdminSearchSessionGroupsPayload,
)
from ai.backend.common.dto.manager.v2.session_group.types import SessionGroupScope
from ai.backend.manager.api.adapters.session_group.adapter import SessionGroupAdapter
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Held,
    Same,
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
type ScopedStep = Scenario[TestSeedingSession, Laid, SessionGroupAdapter, Searched]


@dataclass(frozen=True)
class SearchingInTheProject(When[Laid, SessionGroupAdapter, Searched]):
    """그룹들이 있는 프로젝트 범위에서 필터 없이 검색한다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: Laid) -> str:
        return f"{laid.caller.username}이 {laid.project.name} 프로젝트 범위에서 조회"

    @override
    async def call(self, adapter: SessionGroupAdapter, laid: Laid) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchSessionGroupsInput(
                    scope=SessionGroupScope(project=[UUIDScope(value=laid.project.id)])
                )
            )


@dataclass(frozen=True)
class SearchingTheirOwn(When[Laid, SessionGroupAdapter, Searched]):
    """부르는 사람 자신의 사용자 스코프에서 필터 없이 검색한다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: Laid) -> str:
        return f"{laid.caller.username}이 자기 스코프에서 조회"

    @override
    async def call(self, adapter: SessionGroupAdapter, laid: Laid) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchSessionGroupsInput(
                    scope=SessionGroupScope(user=[UUIDScope(value=laid.caller.id)])
                )
            )


@dataclass(frozen=True)
class SearchingTheOwners(When[Laid, SessionGroupAdapter, Searched]):
    """그룹들을 만든 사람의 사용자 스코프에서 필터 없이 검색한다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: Laid) -> str:
        return f"{laid.caller.username}이 {laid.owner.username}의 스코프에서 조회"

    @override
    async def call(self, adapter: SessionGroupAdapter, laid: Laid) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchSessionGroupsInput(
                    scope=SessionGroupScope(user=[UUIDScope(value=laid.owner.id)])
                )
            )


@dataclass(frozen=True)
class SearchingTheirOwnAndTheOtherProject(When[Laid, SessionGroupAdapter, Searched]):
    """자기 사용자 스코프와 다른 프로젝트 스코프를 함께 넘겨 검색한다."""

    @override
    def operation(self) -> str:
        return "scoped_search"

    @override
    def describe(self, laid: Laid) -> str:
        return (
            f"{laid.caller.username}이 자기 스코프와 {laid.other_project.name} 프로젝트 "
            "범위를 함께 조회"
        )

    @override
    async def call(self, adapter: SessionGroupAdapter, laid: Laid) -> Searched:
        with ActingAs(laid.caller):
            return await adapter.scoped_search(
                ScopedSearchSessionGroupsInput(
                    scope=SessionGroupScope(
                        project=[UUIDScope(value=laid.other_project.id)],
                        user=[UUIDScope(value=laid.caller.id)],
                    )
                )
            )


@dataclass(frozen=True)
class OnlyTheUsersGroupOfTheProject(Then[Laid, Searched]):
    """그 프로젝트의 사용자가 만든 그룹만 남는다."""

    @override
    def says(self) -> str:
        return "그 프로젝트의 사용자가 만든 그룹만 남는다"

    @override
    def look(self, laid: Laid, answered: Answered[Searched]) -> list[Verdict]:
        payload = answered.response
        if payload is None:
            return [MissingResponse(answered.raised)]
        return [
            Held(
                "items",
                [one.entity_id for one in payload.items],
                TheseGroups(frozenset({laid.users_group.id}), "그 프로젝트의 사용자가 만든 그룹"),
            ),
            Same("total_count", payload.total_count, 1),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheOwnersGroups(Then[Laid, Searched]):
    """그 사용자가 두 프로젝트에 만든 그룹만 남는다."""

    @override
    def says(self) -> str:
        return "그 사용자가 두 프로젝트에 만든 그룹만 남는다"

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
                    frozenset({laid.users_group.id, laid.elsewhere_group.id}),
                    "그 사용자가 두 프로젝트에 만든 그룹",
                ),
            ),
            Same("total_count", payload.total_count, 2),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class TheOwnersGroupsAndTheOtherProjects(Then[Laid, Searched]):
    """그 사용자가 만든 그룹과 다른 프로젝트의 그룹이 합쳐져 남는다."""

    @override
    def says(self) -> str:
        return "그 사용자가 만든 그룹과 다른 프로젝트의 그룹이 합쳐져 남는다"

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
                    frozenset({
                        laid.users_group.id,
                        laid.elsewhere_group.id,
                        laid.strangers_group.id,
                    }),
                    "그 사용자가 만든 그룹과 다른 프로젝트의 그룹",
                ),
            ),
            Same("total_count", payload.total_count, 3),
            Same("has_next_page", payload.has_next_page, False),
            Same("has_previous_page", payload.has_previous_page, False),
        ]


@dataclass(frozen=True)
class AGrantedUserFindsOnlyTheUsersGroup(
    Scenario[TestSeedingSession, SessionGroupsAndACaller, SessionGroupAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-granted-user-finds-only-the-users-group-of-the-project"

    @override
    def describe(self) -> str:
        return (
            "그 프로젝트에서만 세션 그룹 읽기 권한을 받은 사용자가 그 프로젝트 범위로 검색하면, "
            "배포의 그룹과 다른 프로젝트의 그룹은 빠지고 그 프로젝트의 사용자가 만든 그룹만 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return SessionGroupsInTwoProjects(granted_in=GrantedIn.THE_PROJECT)

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, Searched]:
        return SearchingInTheProject()

    @override
    def then(self) -> Then[Laid, Searched]:
        return OnlyTheUsersGroupOfTheProject()


@dataclass(frozen=True)
class AProjectNotGrantedIsRefused(
    Scenario[TestSeedingSession, SessionGroupsAndACaller, SessionGroupAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "searching-a-project-not-granted-is-refused"

    @override
    def describe(self) -> str:
        return (
            "다른 프로젝트에서만 세션 그룹 읽기 권한을 받은 사용자가 그룹들이 있는 프로젝트 "
            "범위로 검색하면, 권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return SessionGroupsInTwoProjects(granted_in=GrantedIn.THE_OTHER_PROJECT)

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, Searched]:
        return SearchingInTheProject()

    @override
    def then(self) -> Then[Laid, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnOwnerFindsTheirOwnGroups(
    Scenario[TestSeedingSession, SessionGroupsAndACaller, SessionGroupAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "an-owner-finds-the-groups-they-made-in-their-own-scope"

    @override
    def describe(self) -> str:
        return (
            "자기 스코프에서 세션 그룹 읽기 권한을 받은 사용자가 자기 스코프로 검색하면, "
            "두 프로젝트에 자기가 만든 그룹이 오고 배포의 그룹과 다른 사용자의 그룹은 빠진다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return SessionGroupsInTwoProjects(granted_in=GrantedIn.THEIR_OWN)

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, Searched]:
        return SearchingTheirOwn()

    @override
    def then(self) -> Then[Laid, Searched]:
        return TheOwnersGroups()


@dataclass(frozen=True)
class AnotherUsersScopeIsRefused(
    Scenario[TestSeedingSession, SessionGroupsAndACaller, SessionGroupAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "searching-another-users-scope-is-refused"

    @override
    def describe(self) -> str:
        return (
            "그룹들이 있는 프로젝트에서만 세션 그룹 읽기 권한을 받은 사용자가 그룹들을 만든 "
            "사용자의 스코프로 검색하면, 권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return SessionGroupsInTwoProjects(granted_in=GrantedIn.THE_PROJECT)

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, Searched]:
        return SearchingTheOwners()

    @override
    def then(self) -> Then[Laid, Searched]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ScopesOfDifferentKindsAreJoined(
    Scenario[TestSeedingSession, SessionGroupsAndACaller, SessionGroupAdapter, Searched]
):
    @override
    def summary(self) -> str:
        return "a-user-scope-and-a-project-scope-are-joined"

    @override
    def describe(self) -> str:
        return (
            "자기 스코프와 다른 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자가 두 스코프를 "
            "함께 넘겨 검색하면, 자기가 만든 그룹과 그 프로젝트에서 다른 사용자가 만든 그룹이 "
            "합쳐져 오고 배포의 그룹은 빠진다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return SessionGroupsInTwoProjects(granted_in=GrantedIn.THEIR_OWN_AND_THE_OTHER_PROJECT)

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, Searched]:
        return SearchingTheirOwnAndTheOtherProject()

    @override
    def then(self) -> Then[Laid, Searched]:
        return TheOwnersGroupsAndTheOtherProjects()


SCENARIOS: list[ScopedStep] = [
    AGrantedUserFindsOnlyTheUsersGroup(),
    AProjectNotGrantedIsRefused(),
    AnOwnerFindsTheirOwnGroups(),
    AnotherUsersScopeIsRefused(),
    ScopesOfDifferentKindsAreJoined(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_scoped_searching(
    scenario: ScopedStep, adapter: SessionGroupAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
