"""에이전트 자원 조회 — 에이전트 이름을 풀어낸 뒤, 그 에이전트에 대한 권한을 검사하고 조회한다.

이름을 풀어내는 단계는 인증만 확인한다. 에이전트가 보고한 슬롯을 미리 만들어 두는 seed가 아직
없어, 조회가 성공해 슬롯이 반환되는 시나리오는 여기 없다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.resource_slot.response import AgentResourceNode
from ai.backend.manager.api.adapters.resource_slot.adapter import ResourceSlotAdapter
from ai.backend.manager.errors.base.entity import EntityNotFoundError
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.errors.resource_slot import AgentResourceNotFound
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Configured, Given, Scenario, Then, When
from bai_scenario.components.agent_resource import AnAgentAndACaller, AnAgentAndSomeone
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.components.system import ENFORCEMENT
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import SeedingSession
from bai_scenario.runner.steps import run_scenario

UNKNOWN_AGENT = "no-such-agent"
UNREPORTED_SLOT = "cpu"

type ReadingStep = Scenario[
    SeedingSession, AnAgentAndACaller, ResourceSlotAdapter, AgentResourceNode
]


@dataclass(frozen=True)
class ReadingAnAgentSlot(When[AnAgentAndACaller, ResourceSlotAdapter, AgentResourceNode]):
    """에이전트 이름과 슬롯 이름으로 조회한다. 지정하지 않으면 미리 만들어 둔 에이전트의 이름을 쓴다."""

    agent: str | None = None

    @override
    def operation(self) -> str:
        return "get_agent_resource"

    @override
    def describe(self, laid: AnAgentAndACaller) -> str:
        return (
            f"{laid.caller.username}이 {self.agent or laid.agent.agent_id} 에이전트의 "
            f"{UNREPORTED_SLOT} 슬롯 조회"
        )

    @override
    async def call(
        self, adapter: ResourceSlotAdapter, laid: AnAgentAndACaller
    ) -> AgentResourceNode:
        with ActingAs(laid.caller):
            return await adapter.get_agent_resource(
                self.agent or laid.agent.agent_id, UNREPORTED_SLOT
            )


@dataclass(frozen=True)
class ASlotTheAgentDoesNotReportIsNotFound(
    Scenario[SeedingSession, AnAgentAndACaller, ResourceSlotAdapter, AgentResourceNode]
):
    @override
    def summary(self) -> str:
        return "reading-a-slot-the-agent-does-not-report-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 에이전트가 보고하지 않는 슬롯을 조회하면 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AnAgentAndACaller]:
        return AnAgentAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnAgentAndACaller, ResourceSlotAdapter, AgentResourceNode]:
        return ReadingAnAgentSlot()

    @override
    def then(self) -> Then[AnAgentAndACaller, AgentResourceNode]:
        return TheCallIsRefused(AgentResourceNotFound)


@dataclass(frozen=True)
class AUserReadingAgentsInTheGroupPassesTheGate(
    Scenario[SeedingSession, AnAgentAndACaller, ResourceSlotAdapter, AgentResourceNode]
):
    @override
    def summary(self) -> str:
        return "a-user-reading-agents-in-the-group-reaches-the-slot-the-agent-does-not-report"

    @override
    def describe(self) -> str:
        return (
            "리소스 그룹의 에이전트를 읽을 수 있는 사용자가 에이전트가 보고하지 않는 슬롯을 조회하면 "
            "권한 검사를 통과한 뒤 대상을 찾을 수 없다는 이유로 거부된다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnAgentAndACaller]:
        return AnAgentAndSomeone(granted=True)

    @override
    def when(self) -> When[AnAgentAndACaller, ResourceSlotAdapter, AgentResourceNode]:
        return ReadingAnAgentSlot()

    @override
    def then(self) -> Then[AnAgentAndACaller, AgentResourceNode]:
        return TheCallIsRefused(AgentResourceNotFound)


@dataclass(frozen=True)
class AUserGrantedNothingMayNotReadAnAgentSlot(
    Scenario[SeedingSession, AnAgentAndACaller, ResourceSlotAdapter, AgentResourceNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-may-not-read-an-agent-slot"

    @override
    def describe(self) -> str:
        return "아무 권한도 없는 사용자가 조회하면 권한 부족으로 거부된다. 에이전트에 대한 권한을 슬롯을 찾기 전에 검사한다"

    @override
    def given(self) -> Given[SeedingSession, AnAgentAndACaller]:
        return AnAgentAndSomeone()

    @override
    def when(self) -> When[AnAgentAndACaller, ResourceSlotAdapter, AgentResourceNode]:
        return ReadingAnAgentSlot()

    @override
    def then(self) -> Then[AnAgentAndACaller, AgentResourceNode]:
        return TheCallIsRefused(NotEnoughPermission)


@dataclass(frozen=True)
class AnAgentNameNothingAnswersToIsNotFound(
    Scenario[SeedingSession, AnAgentAndACaller, ResourceSlotAdapter, AgentResourceNode]
):
    @override
    def summary(self) -> str:
        return "reading-an-agent-name-nothing-answers-to-is-not-found"

    @override
    def describe(self) -> str:
        return "슈퍼관리자가 존재하지 않는 에이전트 이름으로 조회하면 대상을 찾을 수 없다는 이유로 거부된다"

    @override
    def given(self) -> Given[SeedingSession, AnAgentAndACaller]:
        return AnAgentAndSomeone(role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AnAgentAndACaller, ResourceSlotAdapter, AgentResourceNode]:
        return ReadingAnAgentSlot(agent=UNKNOWN_AGENT)

    @override
    def then(self) -> Then[AnAgentAndACaller, AgentResourceNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class AUserGrantedNothingReadingAnUnknownAgentIsNotFound(
    Scenario[SeedingSession, AnAgentAndACaller, ResourceSlotAdapter, AgentResourceNode]
):
    @override
    def summary(self) -> str:
        return "a-user-granted-nothing-reading-an-unknown-agent-name-is-not-found"

    @override
    def describe(self) -> str:
        return (
            "아무 권한도 없는 사용자가 존재하지 않는 에이전트 이름으로 조회하면 대상을 찾을 수 없다는 이유로 거부된다. "
            "이름을 풀어내는 단계는 인증만 확인하고, 권한은 풀어낸 에이전트에 대해 검사한다"
        )

    @override
    def given(self) -> Given[SeedingSession, AnAgentAndACaller]:
        return AnAgentAndSomeone()

    @override
    def when(self) -> When[AnAgentAndACaller, ResourceSlotAdapter, AgentResourceNode]:
        return ReadingAnAgentSlot(agent=UNKNOWN_AGENT)

    @override
    def then(self) -> Then[AnAgentAndACaller, AgentResourceNode]:
        return TheCallIsRefused(EntityNotFoundError)


@dataclass(frozen=True)
class EnforcementOffLetsAnyonePassTheGateToAnAgentSlot(
    Scenario[SeedingSession, AnAgentAndACaller, ResourceSlotAdapter, AgentResourceNode],
    Configured,
):
    @override
    def summary(self) -> str:
        return "turning-enforcement-off-lets-a-user-pass-the-gate-to-the-slot-the-agent-does-not-report"

    @override
    def describe(self) -> str:
        return (
            "권한 검사를 끄면 아무 권한도 없는 사용자도 권한 검사를 통과하고, "
            "에이전트가 보고하지 않는 슬롯이므로 대상을 찾을 수 없다는 이유로 거부된다"
        )

    @override
    def config(self) -> Mapping[str, Any]:
        return {ENFORCEMENT: False}

    @override
    def given(self) -> Given[SeedingSession, AnAgentAndACaller]:
        return AnAgentAndSomeone()

    @override
    def when(self) -> When[AnAgentAndACaller, ResourceSlotAdapter, AgentResourceNode]:
        return ReadingAnAgentSlot()

    @override
    def then(self) -> Then[AnAgentAndACaller, AgentResourceNode]:
        return TheCallIsRefused(AgentResourceNotFound)


SCENARIOS: list[ReadingStep] = [
    ASlotTheAgentDoesNotReportIsNotFound(),
    AUserReadingAgentsInTheGroupPassesTheGate(),
    AUserGrantedNothingMayNotReadAnAgentSlot(),
    AnAgentNameNothingAnswersToIsNotFound(),
    AUserGrantedNothingReadingAnUnknownAgentIsNotFound(),
    EnforcementOffLetsAnyonePassTheGateToAnAgentSlot(),
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.summary())
async def test_reading_agent_resources(
    scenario: ReadingStep, adapter: ResourceSlotAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
