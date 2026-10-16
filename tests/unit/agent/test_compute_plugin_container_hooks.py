from __future__ import annotations

from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.agent import resources as resources_mod
from ai.backend.agent.docker.agent import DockerAgent
from ai.backend.agent.resources import AbstractComputePlugin, KernelResourceSpec
from ai.backend.common.types import (
    BinarySize,
    ContainerId,
    DeviceId,
    DeviceName,
    ResourceSlot,
    SlotName,
    SlotTypes,
)

CUDA = DeviceName("cuda")
CUDA_MEM = SlotName("cuda.mem")
CID = ContainerId("c0ffee")


def _spec(allocations: dict[DeviceName, Any]) -> KernelResourceSpec:
    return KernelResourceSpec(
        slots=ResourceSlot({}),
        allocations=allocations,
        scratch_disk_size=0,
        mounts=[],
    )


class TestDefaultHooks:
    async def test_are_no_ops(self) -> None:
        plugin = MagicMock(spec=AbstractComputePlugin)
        alloc = {CUDA_MEM: {DeviceId("0"): Decimal(1)}}
        await AbstractComputePlugin.on_container_created(plugin, CID, alloc)
        await AbstractComputePlugin.on_container_destroyed(plugin, CID, alloc)
        assert not plugin.mock_calls


class TestNotifyContainerDestroyed:
    @pytest.fixture
    def agent(self) -> DockerAgent:
        agent = DockerAgent.__new__(DockerAgent)
        agent.computers = {}
        return agent

    def _attach(self, agent: DockerAgent, name: str, hook: AsyncMock) -> None:
        instance = MagicMock()
        instance.on_container_destroyed = hook
        computer = MagicMock()
        computer.instance = instance
        agent.computers = {**agent.computers, DeviceName(name): computer}

    async def test_passes_each_plugin_its_own_allocation(self, agent: DockerAgent) -> None:
        cuda_hook, cpu_hook = AsyncMock(), AsyncMock()
        self._attach(agent, "cuda", cuda_hook)
        self._attach(agent, "cpu", cpu_hook)
        cuda_alloc = {CUDA_MEM: {DeviceId("0"): Decimal(1 << 30)}}
        cpu_alloc = {SlotName("cpu"): {DeviceId("root"): Decimal(2)}}

        await agent._notify_container_destroyed(
            CID, _spec({CUDA: cuda_alloc, DeviceName("cpu"): cpu_alloc})
        )

        cuda_hook.assert_awaited_once_with(CID, cuda_alloc)
        cpu_hook.assert_awaited_once_with(CID, cpu_alloc)

    async def test_continues_after_a_failing_plugin(self, agent: DockerAgent) -> None:
        failing, other = AsyncMock(side_effect=RuntimeError("boom")), AsyncMock()
        self._attach(agent, "cuda", failing)
        self._attach(agent, "cpu", other)

        await agent._notify_container_destroyed(CID, _spec({CUDA: {}, DeviceName("cpu"): {}}))

        other.assert_awaited_once()

    async def test_skips_a_plugin_that_is_no_longer_loaded(self, agent: DockerAgent) -> None:
        await agent._notify_container_destroyed(CID, _spec({CUDA: {}}))


class TestBytesSlotSerialization:
    @pytest.fixture(autouse=True)
    def bytes_slot(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            resources_mod,
            "known_slot_types",
            {**resources_mod.known_slot_types, CUDA_MEM: SlotTypes.BYTES},
        )

    @pytest.mark.parametrize("amount", [1795162112, 6 * (1 << 30), 5000 * (1 << 20) + 1])
    def test_round_trips_exactly(self, amount: int) -> None:
        spec = _spec({CUDA: {CUDA_MEM: {DeviceId("0"): Decimal(amount)}}})
        restored = KernelResourceSpec.read_from_string(spec.write_to_string())
        assert restored.allocations[CUDA][CUDA_MEM] == {DeviceId("0"): Decimal(amount)}

    def test_reads_a_binary_size_string_written_by_older_agents(self) -> None:
        text = _spec({}).write_to_string() + "CUDA.MEM_SHARES=0:6g\n"
        restored = KernelResourceSpec.read_from_string(text)
        assert restored.allocations[CUDA][CUDA_MEM] == {
            DeviceId("0"): Decimal(BinarySize.from_str("6g"))
        }
