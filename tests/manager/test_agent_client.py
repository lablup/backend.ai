from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from ai.backend.common.types import AgentId, ClusterInfo, ImageConfig, KernelCreationConfig
from ai.backend.manager.clients.agent.client import AgentClient


@pytest.fixture
def mock_agent_cache() -> tuple[MagicMock, MagicMock]:
    cache = MagicMock()
    mock_rpc = MagicMock()
    mock_rpc.call = MagicMock()

    cache.rpc_context.return_value.__aenter__ = AsyncMock(return_value=mock_rpc)
    cache.rpc_context.return_value.__aexit__ = AsyncMock()

    return cache, mock_rpc


class TestAgentClientPassesAgentId:
    @pytest.mark.asyncio
    async def test_gather_hwinfo_passes_agent_id(
        self, mock_agent_cache: tuple[MagicMock, MagicMock]
    ) -> None:
        cache, mock_rpc = mock_agent_cache
        client = AgentClient(cache, AgentId("test-agent"))

        mock_rpc.call.gather_hwinfo = AsyncMock(return_value={})

        await client.gather_hwinfo()

        mock_rpc.call.gather_hwinfo.assert_called_once_with(agent_id=AgentId("test-agent"))

    @pytest.mark.asyncio
    async def test_scan_gpu_alloc_map_passes_agent_id(
        self, mock_agent_cache: tuple[MagicMock, MagicMock]
    ) -> None:
        cache, mock_rpc = mock_agent_cache
        client = AgentClient(cache, AgentId("gpu-agent"))

        mock_rpc.call.scan_gpu_alloc_map = AsyncMock(return_value={})

        await client.scan_gpu_alloc_map()

        mock_rpc.call.scan_gpu_alloc_map.assert_called_once_with(agent_id=AgentId("gpu-agent"))

    @pytest.mark.asyncio
    async def test_create_kernels_passes_agent_id(
        self, mock_agent_cache: tuple[MagicMock, MagicMock]
    ) -> None:
        cache, mock_rpc = mock_agent_cache
        client = AgentClient(cache, AgentId("agent-2"))

        mock_rpc.call.create_kernels = AsyncMock(return_value={})
        kernel_configs = [Mock(spec=KernelCreationConfig)]
        cluster_info = Mock(spec=ClusterInfo)

        await client.create_kernels("session-1", ["kernel-1"], kernel_configs, cluster_info, {})  # type: ignore[arg-type]

        args, kwargs = mock_rpc.call.create_kernels.call_args
        assert kwargs["agent_id"] == AgentId("agent-2")

    @pytest.mark.asyncio
    async def test_destroy_kernel_passes_agent_id(
        self, mock_agent_cache: tuple[MagicMock, MagicMock]
    ) -> None:
        cache, mock_rpc = mock_agent_cache
        client = AgentClient(cache, AgentId("agent-1"))

        mock_rpc.call.destroy_kernel = AsyncMock()

        await client.destroy_kernel("kernel-id", "session-id", "test-reason")

        args, kwargs = mock_rpc.call.destroy_kernel.call_args
        assert kwargs["agent_id"] == AgentId("agent-1")

    @pytest.mark.asyncio
    async def test_execute_passes_agent_id(
        self, mock_agent_cache: tuple[MagicMock, MagicMock]
    ) -> None:
        cache, mock_rpc = mock_agent_cache
        client = AgentClient(cache, AgentId("exec-agent"))

        mock_rpc.call.execute = AsyncMock(return_value={})

        await client.execute(
            "session-1", "kernel-1", 1, "run-1", "query", "print('hello')", {}, None
        )

        args, kwargs = mock_rpc.call.execute.call_args
        assert kwargs["agent_id"] == AgentId("exec-agent")

    @pytest.mark.asyncio
    async def test_check_and_pull_passes_agent_id(
        self, mock_agent_cache: tuple[MagicMock, MagicMock]
    ) -> None:
        cache, mock_rpc = mock_agent_cache
        client = AgentClient(cache, AgentId("image-agent"))

        mock_rpc.call.check_and_pull = AsyncMock(return_value={})
        image_configs = {"python": Mock(spec=ImageConfig)}

        await client.check_and_pull(image_configs)

        mock_rpc.call.check_and_pull.assert_called_once_with(
            image_configs, agent_id=AgentId("image-agent")
        )

    @pytest.mark.asyncio
    async def test_create_local_network_passes_agent_id(
        self, mock_agent_cache: tuple[MagicMock, MagicMock]
    ) -> None:
        cache, mock_rpc = mock_agent_cache
        client = AgentClient(cache, AgentId("network-agent"))

        mock_rpc.call.create_local_network = AsyncMock()

        await client.create_local_network("test-network")

        mock_rpc.call.create_local_network.assert_called_once_with(
            "test-network", agent_id=AgentId("network-agent")
        )

    @pytest.mark.asyncio
    async def test_assign_port_passes_agent_id(
        self, mock_agent_cache: tuple[MagicMock, MagicMock]
    ) -> None:
        cache, mock_rpc = mock_agent_cache
        client = AgentClient(cache, AgentId("port-agent"))

        mock_rpc.call.assign_port = AsyncMock(return_value=30000)

        result = await client.assign_port()

        assert result == 30000
        mock_rpc.call.assign_port.assert_called_once_with(agent_id=AgentId("port-agent"))

    @pytest.mark.asyncio
    async def test_upload_file_passes_agent_id(
        self, mock_agent_cache: tuple[MagicMock, MagicMock]
    ) -> None:
        cache, mock_rpc = mock_agent_cache
        client = AgentClient(cache, AgentId("file-agent"))

        mock_rpc.call.upload_file = AsyncMock(return_value={})

        await client.upload_file("kernel-1", "test.py", b"data")

        mock_rpc.call.upload_file.assert_called_once_with(
            "kernel-1", "test.py", b"data", agent_id=AgentId("file-agent")
        )

    @pytest.mark.asyncio
    async def test_start_service_passes_agent_id(
        self, mock_agent_cache: tuple[MagicMock, MagicMock]
    ) -> None:
        cache, mock_rpc = mock_agent_cache
        client = AgentClient(cache, AgentId("service-agent"))

        mock_rpc.call.start_service = AsyncMock(return_value={})

        await client.start_service("kernel-1", "jupyter", {})

        mock_rpc.call.start_service.assert_called_once_with(
            "kernel-1", "jupyter", {}, agent_id=AgentId("service-agent")
        )

    @pytest.mark.asyncio
    async def test_different_agents_use_different_ids(
        self, mock_agent_cache: tuple[MagicMock, MagicMock]
    ) -> None:
        cache, mock_rpc = mock_agent_cache

        client1 = AgentClient(cache, AgentId("agent-1"))
        client2 = AgentClient(cache, AgentId("agent-2"))

        mock_rpc.call.gather_hwinfo = AsyncMock(return_value={})

        await client1.gather_hwinfo()
        await client2.gather_hwinfo()

        calls = mock_rpc.call.gather_hwinfo.call_args_list
        assert len(calls) == 2
        assert calls[0].kwargs["agent_id"] == AgentId("agent-1")
        assert calls[1].kwargs["agent_id"] == AgentId("agent-2")
