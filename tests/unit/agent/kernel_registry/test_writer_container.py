from __future__ import annotations

import logging
import uuid
from collections.abc import MutableMapping
from pathlib import Path
from typing import cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.agent.kernel import AbstractKernel
from ai.backend.agent.kernel_registry.exception import (
    KernelRecoveryDataParseError,
    UnsupportedKernelType,
)
from ai.backend.agent.kernel_registry.writer.container import ContainerBasedKernelRegistryWriter
from ai.backend.agent.kernel_registry.writer.types import KernelRegistrySaveMetadata
from ai.backend.agent.types import KernelOwnershipData
from ai.backend.common.docker import ImageRef
from ai.backend.common.types import AgentId, KernelId, SessionId, SessionTypes


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
        MutableMapping[KernelId, AbstractKernel],
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

    async def test_a_kernel_not_yet_fully_built_is_skipped_without_a_traceback(
        self,
        writer: ContainerBasedKernelRegistryWriter,
        kernel_registry_data: MutableMapping[KernelId, AbstractKernel],
        metadata: KernelRegistrySaveMetadata,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Registered before its REPL ports exist: ordinary under concurrent creates, and its
        own start writes it a moment later. One warning line, not an exception traceback."""
        with (
            patch.object(
                writer,
                "_parse_recovery_data_from_kernel",
                side_effect=KernelRecoveryDataParseError(),
            ),
            patch("ai.backend.agent.kernel_registry.writer.container.ScratchUtils"),
            patch("ai.backend.agent.kernel_registry.writer.container.ScratchConfig"),
            caplog.at_level(logging.WARNING, logger="ai.backend.agent.kernel_registry"),
        ):
            await writer.save_kernel_registry(kernel_registry_data, metadata)
        records = [r for r in caplog.records if "not complete yet" in r.getMessage()]
        assert len(records) == 1
        assert records[0].levelno == logging.WARNING
        assert records[0].exc_info is None

    async def test_a_kernel_destroyed_while_saving_is_not_re_made_on_disk(
        self,
        writer: ContainerBasedKernelRegistryWriter,
        kernel_registry_data: MutableMapping[KernelId, AbstractKernel],
        metadata: KernelRegistrySaveMetadata,
        mock_config_mgr: MagicMock,
    ) -> None:
        """The other side of the same race: the snapshot still names a kernel whose scratch
        directory a destroy has just removed. The save must not put the directory back, and
        must not fail the save either -- the kernel is simply gone."""
        mock_config_mgr.save_json_recovery_data = AsyncMock(side_effect=FileNotFoundError())
        with (
            patch.object(writer, "_parse_recovery_data_from_kernel", return_value=MagicMock()),
            patch("ai.backend.agent.kernel_registry.writer.container.KernelRecoveryScratchData"),
            patch("ai.backend.agent.kernel_registry.writer.container.ScratchUtils"),
            patch(
                "ai.backend.agent.kernel_registry.writer.container.ScratchConfig",
                return_value=mock_config_mgr,
            ),
        ):
            await writer.save_kernel_registry(kernel_registry_data, metadata)
        _, kwargs = mock_config_mgr.save_json_recovery_data.await_args
        assert kwargs.get("create_config_dir") is False

    async def test_a_kernel_created_while_saving_does_not_break_the_save(
        self,
        writer: ContainerBasedKernelRegistryWriter,
        kernel_registry_data: MutableMapping[KernelId, AbstractKernel],
        metadata: KernelRegistrySaveMetadata,
        mock_kernel: MagicMock,
        mock_config_mgr: MagicMock,
    ) -> None:
        """The save awaits once per kernel over the LIVE registry, and a create on this node
        registers its kernel in between. Measured with 27 sessions started at once: one create
        failed on `dictionary changed size during iteration`, in its own save."""
        registered_meanwhile = KernelId(uuid.uuid4())

        async def _register_while_saving(_data: object, **_kwargs: object) -> None:
            kernel_registry_data[registered_meanwhile] = mock_kernel

        mock_config_mgr.save_json_recovery_data = AsyncMock(side_effect=_register_while_saving)
        with (
            patch.object(writer, "_parse_recovery_data_from_kernel", return_value=MagicMock()),
            patch("ai.backend.agent.kernel_registry.writer.container.KernelRecoveryScratchData"),
            patch("ai.backend.agent.kernel_registry.writer.container.ScratchUtils"),
            patch(
                "ai.backend.agent.kernel_registry.writer.container.ScratchConfig",
                return_value=mock_config_mgr,
            ),
        ):
            await writer.save_kernel_registry(kernel_registry_data, metadata)
        assert registered_meanwhile in kernel_registry_data

    async def test_a_kernel_it_cannot_write_down_is_raised_not_skipped(
        self,
        writer: ContainerBasedKernelRegistryWriter,
        kernel_registry_data: MutableMapping[KernelId, AbstractKernel],
        metadata: KernelRegistrySaveMetadata,
        mock_config_mgr: MagicMock,
    ) -> None:
        """A backend whose kernels this registry cannot record must not be skipped in silence.

        Skipped, the agent starts, runs sessions, loses every one of them at the next restart, and
        reports the same "saved" it does when it saved them -- and the first time anybody finds
        out is a production upgrade with live sessions.
        """
        with (
            patch.object(
                writer,
                "_parse_recovery_data_from_kernel",
                side_effect=UnsupportedKernelType(
                    "a kernel from a backend this build cannot record"
                ),
            ),
            patch("ai.backend.agent.kernel_registry.writer.container.ScratchUtils"),
            patch(
                "ai.backend.agent.kernel_registry.writer.container.ScratchConfig",
                return_value=mock_config_mgr,
            ),
            pytest.raises(UnsupportedKernelType),
        ):
            await writer.save_kernel_registry(kernel_registry_data, metadata)

        mock_config_mgr.save_json_recovery_data.assert_not_called()
