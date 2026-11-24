"""에이전트의 GPU 장치 읽기 — 다른 사용자의 커널이 담기므로 superadmin 만 지나간다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

import pytest

from ai.backend.common.data.user.types import UserRole
from ai.backend.common.dto.manager.v2.agent.response import (
    AgentGPUDeviceInfo,
    AgentGPUDevicesPayload,
)
from ai.backend.common.types import AgentId
from ai.backend.manager.api.adapters.agent.adapter import AgentAdapter
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.testutils.scenario_steps import Given, Says, Scenario, Then, When
from bai_scenario.components.agent import (
    AgentsAndACaller,
    AgentsAndSomeone,
    NoGPUDevicesComeBack,
    NoGPUDevicesComeBackPerAgent,
)
from bai_scenario.components.answers import TheCallIsRefused
from bai_scenario.runner.acting import ActingAs
from bai_scenario.runner.planting import TestSeedingSession
from bai_scenario.runner.steps import run_scenario

type LoadedGPUDevices = list[list[AgentGPUDeviceInfo] | None]
type LoadStep = Scenario[TestSeedingSession, AgentsAndACaller, AgentAdapter, LoadedGPUDevices]
type GetStep = Scenario[TestSeedingSession, AgentsAndACaller, AgentAdapter, AgentGPUDevicesPayload]


@dataclass(frozen=True)
class LoadingGPUDevices(When[AgentsAndACaller, AgentAdapter, LoadedGPUDevices]):
    @override
    def operation(self) -> str:
        return "batch_load_gpu_devices"

    @override
    def describe(self, laid: AgentsAndACaller) -> str:
        return Says(
            f"{laid.caller.username}이 에이전트 {len(laid.agents)}개의 GPU 를 한 번에 조회합니다",
            english=f"{laid.caller.username} loads the GPUs of {len(laid.agents)} agents at once",
        )

    @override
    async def call(self, adapter: AgentAdapter, laid: AgentsAndACaller) -> LoadedGPUDevices:
        with ActingAs(laid.caller):
            return await adapter.batch_load_gpu_devices([
                AgentId(agent.agent_id) for agent in laid.agents
            ])


@dataclass(frozen=True)
class GettingGPUDevices(When[AgentsAndACaller, AgentAdapter, AgentGPUDevicesPayload]):
    @override
    def operation(self) -> str:
        return "get_gpu_devices"

    @override
    def describe(self, laid: AgentsAndACaller) -> str:
        agent_id = laid.agents[0].agent_id
        return Says(
            f"{laid.caller.username}이 에이전트 {agent_id}의 GPU 를 조회합니다",
            english=f"{laid.caller.username} reads the GPUs of agent {agent_id}",
        )

    @override
    async def call(self, adapter: AgentAdapter, laid: AgentsAndACaller) -> AgentGPUDevicesPayload:
        with ActingAs(laid.caller):
            return await adapter.get_gpu_devices(AgentId(laid.agents[0].agent_id))


@dataclass(frozen=True)
class TheSuperadminLoadsGPUDevices(
    Scenario[TestSeedingSession, AgentsAndACaller, AgentAdapter, LoadedGPUDevices]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-loads-an-empty-value-for-the-agents-never-scanned"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 여러 에이전트의 GPU 를 한 번에 조회하면, 스캔한 적이 없는 에이전트 "
            "자리는 빈 값으로 옵니다",
            english=(
                "when the superadmin loads the GPUs of several agents at once, the entries of "
                "the agents never scanned come back as empty values"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AgentsAndACaller]:
        return AgentsAndSomeone(readable=2, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AgentsAndACaller, AgentAdapter, LoadedGPUDevices]:
        return LoadingGPUDevices()

    @override
    def then(self) -> Then[AgentsAndACaller, LoadedGPUDevices]:
        return NoGPUDevicesComeBackPerAgent()


@dataclass(frozen=True)
class AUserReadingTheGroupMayNotLoadGPUDevices(
    Scenario[TestSeedingSession, AgentsAndACaller, AgentAdapter, LoadedGPUDevices]
):
    @override
    def summary(self) -> str:
        return "a-user-reading-the-group-may-not-load-gpu-devices"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 만 부를 수 있는 조회라, 그 그룹의 에이전트를 읽을 수 있는 일반 사용자라도 "
            "권한 부족으로 거부됩니다",
            english=(
                "the read is open to the superadmin alone, so even a regular user who can read "
                "the agents of the group is rejected for lack of privilege"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AgentsAndACaller]:
        return AgentsAndSomeone(readable=1, granted=True)

    @override
    def when(self) -> When[AgentsAndACaller, AgentAdapter, LoadedGPUDevices]:
        return LoadingGPUDevices()

    @override
    def then(self) -> Then[AgentsAndACaller, LoadedGPUDevices]:
        return TheCallIsRefused(InsufficientPrivilege)


@dataclass(frozen=True)
class TheSuperadminGetsGPUDevices(
    Scenario[TestSeedingSession, AgentsAndACaller, AgentAdapter, AgentGPUDevicesPayload]
):
    @override
    def summary(self) -> str:
        return "the-superadmin-gets-an-empty-value-for-an-agent-never-scanned"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 이 스캔한 적이 없는 에이전트의 GPU 를 조회하면 빈 값이 옵니다",
            english=(
                "when the superadmin reads the GPUs of an agent never scanned, an empty value "
                "comes back"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AgentsAndACaller]:
        return AgentsAndSomeone(readable=1, role=UserRole.SUPERADMIN)

    @override
    def when(self) -> When[AgentsAndACaller, AgentAdapter, AgentGPUDevicesPayload]:
        return GettingGPUDevices()

    @override
    def then(self) -> Then[AgentsAndACaller, AgentGPUDevicesPayload]:
        return NoGPUDevicesComeBack()


@dataclass(frozen=True)
class AUserReadingTheGroupMayNotGetGPUDevices(
    Scenario[TestSeedingSession, AgentsAndACaller, AgentAdapter, AgentGPUDevicesPayload]
):
    @override
    def summary(self) -> str:
        return "a-user-reading-the-group-may-not-get-gpu-devices"

    @override
    def describe(self) -> str:
        return Says(
            "superadmin 만 부를 수 있는 조회라, 그 그룹의 에이전트를 읽을 수 있는 일반 사용자라도 "
            "권한 부족으로 거부됩니다",
            english=(
                "the read is open to the superadmin alone, so even a regular user who can read "
                "the agents of the group is rejected for lack of privilege"
            ),
        )

    @override
    def given(self) -> Given[TestSeedingSession, AgentsAndACaller]:
        return AgentsAndSomeone(readable=1, granted=True)

    @override
    def when(self) -> When[AgentsAndACaller, AgentAdapter, AgentGPUDevicesPayload]:
        return GettingGPUDevices()

    @override
    def then(self) -> Then[AgentsAndACaller, AgentGPUDevicesPayload]:
        return TheCallIsRefused(InsufficientPrivilege)


LOAD_SCENARIOS: list[LoadStep] = [
    TheSuperadminLoadsGPUDevices(),
    AUserReadingTheGroupMayNotLoadGPUDevices(),
]

GET_SCENARIOS: list[GetStep] = [
    TheSuperadminGetsGPUDevices(),
    AUserReadingTheGroupMayNotGetGPUDevices(),
]


@pytest.mark.parametrize("scenario", LOAD_SCENARIOS, ids=lambda s: s.summary())
async def test_loading_gpu_devices(
    scenario: LoadStep, adapter: AgentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)


@pytest.mark.parametrize("scenario", GET_SCENARIOS, ids=lambda s: s.summary())
async def test_getting_gpu_devices(
    scenario: GetStep, adapter: AgentAdapter, engine: ExtendedAsyncSAEngine
) -> None:
    await run_scenario(scenario, adapter, engine)
