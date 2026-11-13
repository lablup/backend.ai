from __future__ import annotations

import asyncio
import uuid
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.agent import resources as resources_mod
from ai.backend.agent.docker.agent import DockerAgent, DockerKernelCreationContext
from ai.backend.agent.errors.agent import ContainerCreationError
from ai.backend.agent.port_pool import PortPool
from ai.backend.agent.resources import AbstractComputePlugin, KernelResourceSpec
from ai.backend.common.types import (
    AgentId,
    BinarySize,
    ContainerId,
    DeviceId,
    DeviceName,
    KernelId,
    ResourceSlot,
    SessionId,
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


class _StopAfterStart(Exception):
    """Ends `start_container` right after `docker start`, past the code under test."""


class TestOnContainerCreated:
    @pytest.fixture
    def container(self) -> MagicMock:
        container = MagicMock(_id=str(CID), id=str(CID))
        container.start = AsyncMock(side_effect=_StopAfterStart())
        return container

    @pytest.fixture
    def docker(self, container: MagicMock) -> Iterator[MagicMock]:
        docker = MagicMock()
        docker.close = AsyncMock()
        docker.containers.create = AsyncMock(return_value=container)
        with (
            patch("ai.backend.agent.docker.agent.Docker", return_value=docker),
            patch("ai.backend.agent.docker.agent._build_log_config"),
        ):
            yield docker

    def _context(self, tmp_path: Path, hooks: dict[str, AsyncMock]) -> Any:
        ctx: Any = object.__new__(DockerKernelCreationContext)
        ctx.kernel_config = cast(Any, {"image": {"labels": {}}, "cluster_hostname": "main1"})
        ctx.local_config = MagicMock()
        ctx.local_config.debug.log_kernel_config = False
        ctx.port_pool = PortPool((30000, 30009), cooldown_sec=0)
        ctx.cluster_ssh_port_mapping = None
        ctx.network_plugin_ctx = MagicMock()
        ctx.image_ref = MagicMock()
        ctx.ownership_data = MagicMock()
        ctx.internal_data = {}
        ctx.container_configs = []
        ctx.computer_docker_args = {"HostConfig": {}}
        ctx.computers = {
            DeviceName(name): SimpleNamespace(instance=SimpleNamespace(on_container_created=hook))
            for name, hook in hooks.items()
        }
        ctx.resource_lock = asyncio.Lock()
        ctx.domain_socket_proxies = []
        ctx.config_dir = tmp_path
        ctx.agent_id = AgentId("a1")
        ctx.kernel_id = KernelId(uuid.uuid4())
        ctx.session_id = SessionId(uuid.uuid4())
        ctx._apply_seccomp_profile = AsyncMock()
        return ctx

    def _kernel(self, allocations: dict[DeviceName, Any]) -> Any:
        kernel = MagicMock()
        kernel.resource_spec = SimpleNamespace(allocations=allocations)
        kernel.service_ports = []
        kernel.environ = {}
        return kernel

    async def _start(self, ctx: Any, kernel: Any) -> None:
        await DockerKernelCreationContext.start_container(
            ctx, kernel, [], None, [], cast(Any, {"network_config": {"mode": "bridge"}})
        )

    @pytest.mark.usefixtures("docker")
    async def test_passes_each_plugin_its_own_allocation_before_the_start(
        self, tmp_path: Path, container: MagicMock
    ) -> None:
        order: list[str] = []
        cuda_hook = AsyncMock(side_effect=lambda *_: order.append("cuda"))
        cpu_hook = AsyncMock(side_effect=lambda *_: order.append("cpu"))

        def start() -> None:
            order.append("start")
            raise _StopAfterStart()

        container.start.side_effect = start
        cuda_alloc = {CUDA_MEM: {DeviceId("0"): Decimal(1 << 30)}}
        cpu_alloc = {SlotName("cpu"): {DeviceId("root"): Decimal(2)}}
        ctx = self._context(tmp_path, {"cuda": cuda_hook, "cpu": cpu_hook})

        with pytest.raises(ContainerCreationError):
            await self._start(ctx, self._kernel({CUDA: cuda_alloc, DeviceName("cpu"): cpu_alloc}))

        cuda_hook.assert_awaited_once_with(CID, cuda_alloc)
        cpu_hook.assert_awaited_once_with(CID, cpu_alloc)
        assert order == ["cuda", "cpu", "start"]

    @pytest.mark.usefixtures("docker")
    async def test_a_failing_hook_aborts_the_start(
        self, tmp_path: Path, container: MagicMock
    ) -> None:
        hook = AsyncMock(side_effect=RuntimeError("no dmem"))
        ctx = self._context(tmp_path, {"cuda": hook})
        kernel = self._kernel({CUDA: {CUDA_MEM: {DeviceId("0"): Decimal(1)}}})

        with pytest.raises(ContainerCreationError) as caught:
            await self._start(ctx, kernel)

        assert caught.value.container_id == CID
        kernel.set_container_id.assert_called_once_with(CID)
        container.start.assert_not_awaited()


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
