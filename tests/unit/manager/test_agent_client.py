from typing import cast
from unittest.mock import AsyncMock, MagicMock, Mock
from uuid import uuid4

import pytest

from ai.backend.common.types import (
    AgentId,
    ClusterInfo,
    ImageConfig,
    KernelCreationConfig,
    KernelId,
    SessionId,
)
from ai.backend.manager.clients.agent.client import AgentClient


@pytest.fixture
def mock_peer() -> MagicMock:
    """Create a mock PeerInvoker with async call methods."""
    peer = MagicMock()
    peer.call = MagicMock()
    return peer


class TestAgentClientPassesAgentId:
    @pytest.mark.asyncio
    async def test_gather_hwinfo_passes_agent_id(self, mock_peer: MagicMock) -> None:
        client = AgentClient(mock_peer, AgentId("test-agent"))

        mock_peer.call.gather_hwinfo = AsyncMock(return_value={})

        await client.gather_hwinfo()

        mock_peer.call.gather_hwinfo.assert_called_once_with(agent_id=AgentId("test-agent"))

    @pytest.mark.asyncio
    async def test_scan_gpu_alloc_map_passes_agent_id(self, mock_peer: MagicMock) -> None:
        client = AgentClient(mock_peer, AgentId("gpu-agent"))

        mock_peer.call.scan_gpu_alloc_map = AsyncMock(return_value={})

        await client.scan_gpu_alloc_map()

        mock_peer.call.scan_gpu_alloc_map.assert_called_once_with(agent_id=AgentId("gpu-agent"))

    @pytest.mark.asyncio
    async def test_create_kernels_passes_agent_id(self, mock_peer: MagicMock) -> None:
        client = AgentClient(mock_peer, AgentId("agent-2"))

        mock_peer.call.create_kernels = AsyncMock(return_value={})
        kernel_configs = cast(list[KernelCreationConfig], [Mock(spec=KernelCreationConfig)])
        cluster_info = cast(ClusterInfo, Mock(spec=ClusterInfo))

        await client.create_kernels(
            SessionId(uuid4()), [KernelId(uuid4())], kernel_configs, cluster_info, {}
        )

        args, kwargs = mock_peer.call.create_kernels.call_args
        assert kwargs["agent_id"] == AgentId("agent-2")

    @pytest.mark.asyncio
    async def test_destroy_kernel_passes_agent_id(self, mock_peer: MagicMock) -> None:
        client = AgentClient(mock_peer, AgentId("agent-1"))

        mock_peer.call.destroy_kernel = AsyncMock()

        await client.destroy_kernel(KernelId(uuid4()), SessionId(uuid4()), "test-reason")

        args, kwargs = mock_peer.call.destroy_kernel.call_args
        assert kwargs["agent_id"] == AgentId("agent-1")

    @pytest.mark.asyncio
    async def test_execute_passes_agent_id(self, mock_peer: MagicMock) -> None:
        client = AgentClient(mock_peer, AgentId("exec-agent"))

        mock_peer.call.execute = AsyncMock(return_value={})

        await client.execute(
            SessionId(uuid4()), KernelId(uuid4()), 1, "run-1", "query", "print('hello')", {}, None
        )

        args, kwargs = mock_peer.call.execute.call_args
        assert kwargs["agent_id"] == AgentId("exec-agent")

    @pytest.mark.asyncio
    async def test_check_and_pull_passes_agent_id(self, mock_peer: MagicMock) -> None:
        client = AgentClient(mock_peer, AgentId("image-agent"))

        mock_peer.call.check_and_pull = AsyncMock(return_value={})
        image_configs = {"python": Mock(spec=ImageConfig)}

        await client.check_and_pull(image_configs)

        mock_peer.call.check_and_pull.assert_called_once_with(
            image_configs, agent_id=AgentId("image-agent")
        )

    @pytest.mark.asyncio
    async def test_create_local_network_passes_agent_id(self, mock_peer: MagicMock) -> None:
        client = AgentClient(mock_peer, AgentId("network-agent"))

        mock_peer.call.create_local_network = AsyncMock()

        await client.create_local_network("test-network")

        mock_peer.call.create_local_network.assert_called_once_with(
            "test-network", agent_id=AgentId("network-agent")
        )

    @pytest.mark.asyncio
    async def test_assign_port_passes_agent_id(self, mock_peer: MagicMock) -> None:
        client = AgentClient(mock_peer, AgentId("port-agent"))

        mock_peer.call.assign_port = AsyncMock(return_value=30000)

        result = await client.assign_port()

        assert result == 30000
        mock_peer.call.assign_port.assert_called_once_with(agent_id=AgentId("port-agent"))

    @pytest.mark.asyncio
    async def test_upload_file_passes_agent_id(self, mock_peer: MagicMock) -> None:
        client = AgentClient(mock_peer, AgentId("file-agent"))

        mock_peer.call.upload_file = AsyncMock(return_value={})

        kernel_id = KernelId(uuid4())
        await client.upload_file(kernel_id, "test.py", b"data")

        mock_peer.call.upload_file.assert_called_once_with(
            str(kernel_id), "test.py", b"data", agent_id=AgentId("file-agent")
        )

    @pytest.mark.asyncio
    async def test_start_service_passes_agent_id(self, mock_peer: MagicMock) -> None:
        client = AgentClient(mock_peer, AgentId("service-agent"))

        mock_peer.call.start_service = AsyncMock(return_value={})

        kernel_id = KernelId(uuid4())
        await client.start_service(kernel_id, "jupyter", {})

        mock_peer.call.start_service.assert_called_once_with(
            str(kernel_id), "jupyter", {}, agent_id=AgentId("service-agent")
        )

    @pytest.mark.asyncio
    async def test_different_agents_use_different_ids(self, mock_peer: MagicMock) -> None:
        client1 = AgentClient(mock_peer, AgentId("agent-1"))
        client2 = AgentClient(mock_peer, AgentId("agent-2"))

        mock_peer.call.gather_hwinfo = AsyncMock(return_value={})

        await client1.gather_hwinfo()
        await client2.gather_hwinfo()

        calls = mock_peer.call.gather_hwinfo.call_args_list
        assert len(calls) == 2
        assert calls[0].kwargs["agent_id"] == AgentId("agent-1")
        assert calls[1].kwargs["agent_id"] == AgentId("agent-2")
