from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.agent.kernel_registry.exception import KernelRecoveryDataParseError
from ai.backend.agent.kernel_registry.writer.container import ContainerBasedKernelRegistryWriter
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.docker import ImageRef
from ai.backend.common.types import AgentId, KernelId, SessionId, SessionTypes


@pytest.fixture
def writer() -> ContainerBasedKernelRegistryWriter:
    """Writer instance with scratch root."""
    return ContainerBasedKernelRegistryWriter(Path("/tmp/scratch"))


@pytest.fixture
def mock_kernel() -> MagicMock:
    """Mock kernel with required attributes."""
    kernel_id = KernelId(uuid.uuid4())
    session_id = SessionId(uuid.uuid4())
    agent_id = AgentId("test-agent")

    kernel = MagicMock()
    kernel.kernel_id = kernel_id
    kernel.agent_id = agent_id
    kernel.image = ImageRef(
        name="python",
        project="stable",
        tag="3.10-ubuntu22.04",
        registry="cr.backend.ai",
        architecture="x86_64",
        is_local=False,
    )
    kernel.session_type = SessionTypes.INTERACTIVE
    kernel.ownership_data = KernelOwnershipData(
        kernel_id=kernel_id,
        session_id=session_id,
        agent_id=agent_id,
    )
    kernel.network_id = str(uuid.uuid4())
    kernel.version = 1
    kernel.network_driver = "bridge"
    kernel.resource_spec = MagicMock()
    kernel.service_ports = []
    kernel.environ = {}
    kernel.data = {
        "block_service_ports": False,
        "domain_socket_proxies": [],
        "repl_in_port": 2000,
        "repl_out_port": 2001,
    }
    return kernel


@pytest.fixture
def mock_config_mgr() -> MagicMock:
    """Mock ScratchConfig manager."""
    mgr = MagicMock()
    mgr.save_json_recovery_data = AsyncMock()
    return mgr


class TestSaveKernel:
    async def test_saves_recovery_data_of_the_given_kernel_only(
        self,
        writer: ContainerBasedKernelRegistryWriter,
        mock_kernel: MagicMock,
        mock_config_mgr: MagicMock,
    ) -> None:
        recovery_data = MagicMock()
        with (
            patch.object(writer, "_parse_recovery_data_from_kernel", return_value=recovery_data),
            patch(
                "ai.backend.agent.kernel_registry.writer.container.ScratchUtils"
            ) as scratch_utils,
            patch(
                "ai.backend.agent.kernel_registry.writer.container.ScratchConfig",
                return_value=mock_config_mgr,
            ),
            patch(
                "ai.backend.agent.kernel_registry.writer.container.KernelRecoveryScratchData"
            ) as scratch_data,
        ):
            await writer.save_kernel(mock_kernel)

        scratch_utils.get_scratch_kernel_config_dir.assert_called_once_with(
            Path("/tmp/scratch"), mock_kernel.kernel_id
        )
        scratch_data.from_kernel_recovery_data.assert_called_once_with(recovery_data)
        mock_config_mgr.save_json_recovery_data.assert_awaited_once_with(
            scratch_data.from_kernel_recovery_data.return_value
        )

    async def test_raises_on_parse_error(
        self,
        writer: ContainerBasedKernelRegistryWriter,
        mock_kernel: MagicMock,
        mock_config_mgr: MagicMock,
    ) -> None:
        with (
            patch.object(
                writer,
                "_parse_recovery_data_from_kernel",
                side_effect=KernelRecoveryDataParseError(),
            ),
            patch("ai.backend.agent.kernel_registry.writer.container.ScratchUtils"),
            patch(
                "ai.backend.agent.kernel_registry.writer.container.ScratchConfig",
                return_value=mock_config_mgr,
            ),
            pytest.raises(KernelRecoveryDataParseError),
        ):
            await writer.save_kernel(mock_kernel)

        mock_config_mgr.save_json_recovery_data.assert_not_called()

    async def test_skips_kernel_without_recovery_data(
        self,
        writer: ContainerBasedKernelRegistryWriter,
        mock_kernel: MagicMock,
        mock_config_mgr: MagicMock,
    ) -> None:
        with (
            patch.object(writer, "_parse_recovery_data_from_kernel", return_value=None),
            patch("ai.backend.agent.kernel_registry.writer.container.ScratchUtils"),
            patch(
                "ai.backend.agent.kernel_registry.writer.container.ScratchConfig",
                return_value=mock_config_mgr,
            ),
        ):
            await writer.save_kernel(mock_kernel)

        mock_config_mgr.save_json_recovery_data.assert_not_called()
