"""에이전트의 자원 그룹 바꾸기 — 충돌 세션을 어떻게 다룰지가 분기다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest
import sqlalchemy as sa

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.agent.request import (
    UpdateAgentResourceGroupBody,
    UpdateAgentResourceGroupInput,
)
from ai.backend.common.dto.manager.v2.agent.response import UpdateAgentResourceGroupPayload
from ai.backend.common.types import AgentId
from ai.backend.manager.api.adapters.agent.adapter import AgentAdapter
from ai.backend.manager.errors.agent import AgentHasConflictingSessions
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.session_designated_agent.row import SessionDesignatedAgentRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.agent import (
    AnAgentToMoveAndACaller,
    AnAgentToMoveAndSomeone,
    TheAgentMoved,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type Moved = UpdateAgentResourceGroupPayload
type MoveStep = Scenario[TestSeedingSession, AnAgentToMoveAndACaller, AgentAdapter, Moved]


@dataclass(frozen=True)
class MovingTheAgent(When[AnAgentToMoveAndACaller, AgentAdapter, Moved]):
    """에이전트를 옮긴다. ``from_body`` 면 REST 가 지나는 경로로 부른다."""

    force: bool = False
    from_body: bool = False

    @override
    def operation(self) -> str:
        if self.from_body:
            return "update_resource_group_from_body"
        return "update_resource_group"

    @override
    def describe(self, laid: AnAgentToMoveAndACaller) -> str:
        ko = f"{laid.caller.username}이 "
        en = f"{laid.caller.username} "
        if self.from_body:
            ko += "REST 본문으로 "
            en += "through the REST body "
        if self.force:
            ko += "강제로 "
            en += "with force "
        ko += f"에이전트 {laid.agent.agent_id}를 {laid.target.name} 그룹으로 옮깁니다"
        en += f"moves agent {laid.agent.agent_id} to group {laid.target.name}"
        return Says(ko, english=en)

    @override
    async def call(self, adapter: AgentAdapter, laid: AnAgentToMoveAndACaller) -> Moved:
        agent_id = AgentId(laid.agent.agent_id)
        with ActingAs(laid.caller):
            if self.from_body:
                return await adapter.update_resource_group_from_body(
                    agent_id,
                    UpdateAgentResourceGroupBody(
                        resource_group_id=laid.target.id,
                        force=self.force,
                    ),
                )
            return await adapter.update_resource_group(
                UpdateAgentResourceGroupInput(
                    agent_id=agent_id,
                    resource_group_id=laid.target.id,
                    force=self.force,
                )
            )


@dataclass(frozen=True)
class MovingRow(Scenario[TestSeedingSession, AnAgentToMoveAndACaller, AgentAdapter, Moved]):
    named: str
    guarantees: str
    situation: AnAgentToMoveAndSomeone
    force: bool = False
    from_body: bool = False

    @override
    def summary(self) -> str:
        return self.named

    @override
    def describe(self) -> str:
        return self.guarantees

    @override
    def given(self) -> Given[TestSeedingSession, AnAgentToMoveAndACaller]:
        return self.situation

    @override
    def when(self) -> When[AnAgentToMoveAndACaller, AgentAdapter, Moved]:
        return MovingTheAgent(force=self.force, from_body=self.from_body)

    @override
    def then(self) -> Then[AnAgentToMoveAndACaller, Moved]:
        return TheAgentMoved(policy="terminate")


@dataclass(frozen=True)
class RefusedRow(Scenario[TestSeedingSession, AnAgentToMoveAndACaller, AgentAdapter, Moved]):
    named: str
    guarantees: str
    expected: type[BaseException]
    situation: AnAgentToMoveAndSomeone
    from_body: bool = False

    @override
    def summary(self) -> str:
        return self.named

    @override
    def describe(self) -> str:
        return self.guarantees

    @override
    def given(self) -> Given[TestSeedingSession, AnAgentToMoveAndACaller]:
        return self.situation

    @override
    def when(self) -> When[AnAgentToMoveAndACaller, AgentAdapter, Moved]:
        return MovingTheAgent(from_body=self.from_body)

    @override
    def then(self) -> Then[AnAgentToMoveAndACaller, Moved]:
        return TheCallIsRefused(self.expected)


SUPERADMIN = AnAgentToMoveAndSomeone()
NOBODY = AnAgentToMoveAndSomeone(role=UserRole.USER)
WITH_CONFLICT = AnAgentToMoveAndSomeone(conflicting=True)

SCENARIOS: list[MoveStep] = [
    MovingRow(
        named="the-superadmin-moves-an-agent-through-the-rest-body",
        guarantees=Says(
            "superadmin 이 REST 본문으로 에이전트를 옮겨도 바뀐 그룹을 담은 응답이 옵니다",
            english=(
                "when the superadmin moves an agent through the REST body, the answer carrying "
                "the new group comes back"
            ),
        ),
        situation=SUPERADMIN,
        from_body=True,
    ),
    RefusedRow(
        named="a-user-granted-nothing-may-not-move-an-agent",
        guarantees=Says(
            "superadmin 만 부를 수 있는 변경이라, 아무 권한도 없는 일반 사용자가 에이전트를 "
            "옮기면 권한 부족으로 거부됩니다",
            english=(
                "the move is open to the superadmin alone, so a regular user holding no "
                "permission is rejected for lack of privilege"
            ),
        ),
        expected=InsufficientPrivilege,
        situation=NOBODY,
    ),
    RefusedRow(
        named="a-user-granted-nothing-may-not-move-an-agent-through-the-rest-body",
        guarantees=Says(
            "superadmin 만 부를 수 있는 변경이라, 아무 권한도 없는 일반 사용자가 REST 본문으로 "
            "에이전트를 옮겨도 권한 부족으로 거부됩니다",
            english=(
                "the move is open to the superadmin alone, so a regular user holding no "
                "permission is rejected for lack of privilege even through the REST body"
            ),
        ),
        expected=InsufficientPrivilege,
        situation=NOBODY,
        from_body=True,
    ),
    RefusedRow(
        named="an-agent-designated-by-another-groups-session-needs-force",
        guarantees=Says(
            "다른 그룹의 세션이 지정한 에이전트를 강제하지 않고 옮기면 충돌한다는 이유로 "
            "거부됩니다",
            english=(
                "when an agent designated by a session of another group is moved without force, "
                "the call is rejected as conflicting"
            ),
        ),
        expected=AgentHasConflictingSessions,
        situation=WITH_CONFLICT,
    ),
    MovingRow(
        named="force-moves-an-agent-designated-by-another-groups-session",
        guarantees=Says(
            "다른 그룹의 세션이 지정한 에이전트를 강제로 옮기면 지정을 지우고 바뀐 그룹을 담은 "
            "응답이 옵니다",
            english=(
                "when an agent designated by a session of another group is moved with force, "
                "the designation is dropped and the answer carrying the new group comes back"
            ),
        ),
        situation=WITH_CONFLICT,
        force=True,
    ),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_changing_resource_group(
    scenario: MoveStep, adapter: AgentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
    assert await designated_agent_count(engine) == expected_designations(scenario)


async def designated_agent_count(engine: ExtendedAsyncSAEngine) -> int:
    """세션 지정 에이전트 행의 수. 이 표의 상황은 많아야 하나를 심는다."""
    async with engine.begin_readonly_session() as session:
        query = sa.select(sa.func.count()).select_from(SessionDesignatedAgentRow)
        return int(await session.scalar(query) or 0)


def expected_designations(scenario: MoveStep) -> int:
    """강제로 옮긴 행만 지정을 지운다. 충돌로 거부된 행은 지정을 그대로 둔다."""
    if isinstance(scenario, RefusedRow):
        return 1 if scenario.expected is AgentHasConflictingSessions else 0
    return 0
