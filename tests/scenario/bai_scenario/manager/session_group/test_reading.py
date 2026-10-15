"""세션 그룹 하나 읽기 — 누가 무엇을 읽을 수 있는가."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import override

import pytest

from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.dto.manager.v2.session_group.response import SessionGroupNode
from ai.backend.manager.api.adapters.session_group.adapter import SessionGroupAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import (
    Answered,
    Given,
    Refused,
    Scenario,
    Then,
    Verdict,
    When,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.session_group import (
    GrantedIn,
    SessionGroupsAndACaller,
    SessionGroupsInTwoProjects,
    UsersGroupLook,
)
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Laid = SessionGroupsAndACaller
type ReadingStep = Scenario[TestSeedingSession, Laid, SessionGroupAdapter, SessionGroupNode]


@dataclass(frozen=True)
class ReadingTheUsersGroup(When[Laid, SessionGroupAdapter, SessionGroupNode]):
    """사용자가 만든 그룹을 id로 읽는다."""

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: Laid) -> str:
        return f"{laid.caller.username}이 사용자가 만든 그룹을 id로 조회"

    @override
    async def call(self, adapter: SessionGroupAdapter, laid: Laid) -> SessionGroupNode:
        with ActingAs(laid.caller):
            return await adapter.get(SessionGroupID(laid.users_group.id))


@dataclass(frozen=True)
class ReadingTheDeploymentGroup(When[Laid, SessionGroupAdapter, SessionGroupNode]):
    """배포의 그룹을 id로 읽는다."""

    @override
    def operation(self) -> str:
        return "get"

    @override
    def describe(self, laid: Laid) -> str:
        return f"{laid.caller.username}이 배포의 그룹을 id로 조회"

    @override
    async def call(self, adapter: SessionGroupAdapter, laid: Laid) -> SessionGroupNode:
        with ActingAs(laid.caller):
            return await adapter.get(SessionGroupID(laid.deployment_group.id))


@dataclass(frozen=True)
class TheUsersGroupNode(Then[Laid, SessionGroupNode]):
    """사용자가 만든 그룹의 노드가 통째로 온다."""

    started: datetime

    @override
    def says(self) -> str:
        return "사용자가 만든 그룹 전체가 온다"

    @override
    def look(self, laid: Laid, answered: Answered[SessionGroupNode]) -> list[Verdict]:
        node = answered.response
        if node is None:
            return [Refused(EntityNotFoundError, answered.raised)]
        return UsersGroupLook(self.started).verdicts("", node, laid)


@dataclass(frozen=True)
class AGrantedUserReadsTheUsersGroup(
    Scenario[TestSeedingSession, SessionGroupsAndACaller, SessionGroupAdapter, SessionGroupNode]
):
    started: datetime

    @override
    def summary(self) -> str:
        return "a-granted-user-reads-a-users-session-group"

    @override
    def describe(self) -> str:
        return (
            "그 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자가 사용자가 만든 그룹을 "
            "id로 조회하면, 그 그룹이 온다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return SessionGroupsInTwoProjects(granted_in=GrantedIn.THE_PROJECT)

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, SessionGroupNode]:
        return ReadingTheUsersGroup()

    @override
    def then(self) -> Then[Laid, SessionGroupNode]:
        return TheUsersGroupNode(started=self.started)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotRead(
    Scenario[TestSeedingSession, SessionGroupsAndACaller, SessionGroupAdapter, SessionGroupNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-a-session-group"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 받지 않은 사용자가 사용자가 만든 그룹을 id로 조회하면, "
            "권한 부족으로 거부된다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return SessionGroupsInTwoProjects()

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, SessionGroupNode]:
        return ReadingTheUsersGroup()

    @override
    def then(self) -> Then[Laid, SessionGroupNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class ADeploymentsGroupIsNotFound(
    Scenario[TestSeedingSession, SessionGroupsAndACaller, SessionGroupAdapter, SessionGroupNode]
):
    @override
    def summary(self) -> str:
        return "a-deployments-session-group-is-not-found-even-when-granted"

    @override
    def describe(self) -> str:
        return (
            "그 프로젝트에서 세션 그룹 읽기 권한을 받은 사용자가 배포의 그룹을 id로 조회하면, "
            "권한이 아니라 대상이 없다는 것으로 거부된다"
        )

    @override
    def given(self) -> Given[TestSeedingSession, Laid]:
        return SessionGroupsInTwoProjects(granted_in=GrantedIn.THE_PROJECT)

    @override
    def when(self) -> When[Laid, SessionGroupAdapter, SessionGroupNode]:
        return ReadingTheDeploymentGroup()

    @override
    def then(self) -> Then[Laid, SessionGroupNode]:
        return TheCallIsRefused(EntityNotFoundError)


SCENARIOS: list[ReadingStep] = [
    AGrantedUserReadsTheUsersGroup(started=datetime.now(UTC)),
    AUserGrantedNothingMayNotRead(),
    ADeploymentsGroupIsNotFound(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading(
    scenario: ReadingStep, adapter: SessionGroupAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
