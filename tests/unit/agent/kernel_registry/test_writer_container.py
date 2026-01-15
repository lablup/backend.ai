from __future__ import annotations

import uuid
from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.agent.kernel_registry.exception import KernelRecoveryDataParseError
from ai.backend.agent.kernel_registry.writer.container import ContainerBasedKernelRegistryWriter
from ai.backend.agent.kernel_registry.writer.types import KernelRegistrySaveMetadata
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.docker import ImageRef
from ai.backend.common.types import AgentId, KernelId, SessionId, SessionTypes

if TYPE_CHECKING:
    from ai.backend.agent.kernel import AbstractKernel


@pytest.fixture
def writer() -> ContainerBasedKernelRegistryWriter:
    """Writer instance with scratch root."""
    return ContainerBasedKernelRegistryWriter(Path("/tmp/scratch"))


@pytest.fixture
def metadata() -> KernelRegistrySaveMetadata:
    """Default save metadata."""
    return KernelRegistrySaveMetadata(force=False)


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
def kernel_registry_data(
    mock_kernel: MagicMock,
) -> MutableMapping[KernelId, AbstractKernel]:
    """Registry data with single kernel."""
    return cast(
        MutableMapping[KernelId, "AbstractKernel"],
        {mock_kernel.kernel_id: mock_kernel},
    )


@pytest.fixture
def mock_config_mgr() -> MagicMock:
    """Mock ScratchConfig manager."""
    mgr = MagicMock()
    mgr.save_json_recovery_data = AsyncMock()
    return mgr


class TestSaveKernelRegistry:
    """Tests for save_kernel_registry method."""

    async def test_save_kernel_registry_skips_kernel_on_parse_error(
        self,
        writer: ContainerBasedKernelRegistryWriter,
        kernel_registry_data: MutableMapping[KernelId, AbstractKernel],
        metadata: KernelRegistrySaveMetadata,
    ) -> None:
        """Skip kernel with parse error and continue processing others."""
        with (
            patch.object(
                writer,
                "_parse_recovery_data_from_kernel",
                side_effect=KernelRecoveryDataParseError(),
            ),
            patch("ai.backend.agent.kernel_registry.writer.container.ScratchUtils"),
            patch("ai.backend.agent.kernel_registry.writer.container.ScratchConfig"),
        ):
            # Should not raise, just skip the kernel
            await writer.save_kernel_registry(kernel_registry_data, metadata)

    async def test_save_kernel_registry_skips_none_recovery_data(
        self,
        writer: ContainerBasedKernelRegistryWriter,
        kernel_registry_data: MutableMapping[KernelId, AbstractKernel],
        metadata: KernelRegistrySaveMetadata,
        mock_config_mgr: MagicMock,
    ) -> None:
        """Skip kernels that return None from parse method."""
        with (
            patch.object(
                writer,
                "_parse_recovery_data_from_kernel",
                return_value=None,
            ),
            patch("ai.backend.agent.kernel_registry.writer.container.ScratchUtils"),
            patch(
                "ai.backend.agent.kernel_registry.writer.container.ScratchConfig",
                return_value=mock_config_mgr,
            ),
        ):
            await writer.save_kernel_registry(kernel_registry_data, metadata)

        # Verify save was not called since recovery data was None
        mock_config_mgr.save_json_recovery_data.assert_not_called()
