from __future__ import annotations

import logging
import uuid
from collections.abc import MutableMapping
from pathlib import Path
from typing import cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.agent.kernel import AbstractKernel
from ai.backend.agent.kernel_registry.exception import KernelRecoveryDataParseError
from ai.backend.agent.kernel_registry.writer.container import ContainerBasedKernelRegistryWriter
from ai.backend.agent.kernel_registry.writer.types import KernelRegistrySaveMetadata
from ai.backend.agent.scratch.types import KernelRecoveryScratchData
from ai.backend.agent.scratch.utils import ScratchConfig, ScratchUtils, StagedRecoveryData
from ai.backend.agent.types import KernelLifecycleStatus, KernelOwnershipData
from ai.backend.common.docker import ImageRef
from ai.backend.common.types import AgentId, KernelId, SessionId, SessionTypes


@pytest.fixture
def writer(tmp_path: Path) -> ContainerBasedKernelRegistryWriter:
    """Writer instance with scratch root."""
    return ContainerBasedKernelRegistryWriter(tmp_path)


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
    kernel.state = KernelLifecycleStatus.RUNNING
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
    mgr.stage_json_recovery_data = AsyncMock(return_value=MagicMock())
    return mgr


@pytest.fixture
def serialized_recovery_data() -> KernelRecoveryScratchData:
    data = MagicMock()
    data.model_dump_json.return_value = "{}"
    return cast(KernelRecoveryScratchData, data)


@pytest.fixture
def registry_with_destroyable_kernel(
    kernel_registry_data: MutableMapping[KernelId, AbstractKernel],
    mock_kernel: MagicMock,
    tmp_path: Path,
) -> tuple[KernelId, Path]:
    destroyed_kernel_id = KernelId(uuid.uuid4())
    kernel_registry_data[destroyed_kernel_id] = mock_kernel
    for kernel_id in kernel_registry_data:
        config_path = ScratchUtils.get_scratch_kernel_config_dir(tmp_path, kernel_id)
        config_path.mkdir(parents=True)
    return (
        destroyed_kernel_id,
        ScratchUtils.get_scratch_kernel_config_dir(tmp_path, destroyed_kernel_id),
    )


@pytest.fixture
def existing_config_path(mock_kernel: MagicMock, tmp_path: Path) -> Path:
    config_path = ScratchUtils.get_scratch_kernel_config_dir(tmp_path, mock_kernel.kernel_id)
    config_path.mkdir(parents=True)
    return config_path


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

    async def test_a_kernel_not_yet_started_is_skipped_without_a_traceback(
        self,
        writer: ContainerBasedKernelRegistryWriter,
        kernel_registry_data: MutableMapping[KernelId, AbstractKernel],
        metadata: KernelRegistrySaveMetadata,
        mock_kernel: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Registered before its REPL ports exist: ordinary under concurrent creates, and its
        own start writes it a moment later. One warning line, not an exception traceback."""
        mock_kernel.state = KernelLifecycleStatus.PREPARING
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
        records = [r for r in caplog.records if "not started yet" in r.getMessage()]
        assert len(records) == 1
        assert records[0].levelno == logging.WARNING
        assert records[0].exc_info is None

    async def test_a_running_kernel_it_cannot_parse_is_reported_as_a_fault(
        self,
        writer: ContainerBasedKernelRegistryWriter,
        kernel_registry_data: MutableMapping[KernelId, AbstractKernel],
        metadata: KernelRegistrySaveMetadata,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A RUNNING kernel has its ports by contract; missing ones are a broken invariant, not
        the start-up race, and keep the traceback that says so."""
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
        records = [r for r in caplog.records if "Failed to parse" in r.getMessage()]
        assert len(records) == 1
        assert records[0].levelno == logging.ERROR
        assert records[0].exc_info is not None

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
        staged = MagicMock()

        async def _register_while_saving(_data: object) -> MagicMock:
            kernel_registry_data[registered_meanwhile] = mock_kernel
            return staged

        mock_config_mgr.stage_json_recovery_data = AsyncMock(side_effect=_register_while_saving)
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
        staged.commit.assert_called_once()

    async def test_a_kernel_replaced_under_the_same_id_while_saving_is_not_written(
        self,
        writer: ContainerBasedKernelRegistryWriter,
        kernel_registry_data: MutableMapping[KernelId, AbstractKernel],
        metadata: KernelRegistrySaveMetadata,
        mock_kernel: MagicMock,
        existing_config_path: Path,
        serialized_recovery_data: KernelRecoveryScratchData,
    ) -> None:
        """A restart destroys and re-creates a kernel under the same id and keeps its scratch
        directory. The snapshot still holds the old object; its record must not land in the
        new incarnation's directory, and nothing staged may be left behind."""
        original_stage = ScratchConfig.stage_json_recovery_data

        async def _replace_while_staging(
            config: ScratchConfig, data: KernelRecoveryScratchData
        ) -> StagedRecoveryData:
            staged = await original_stage(config, data)
            kernel_registry_data[mock_kernel.kernel_id] = MagicMock()
            return staged

        with (
            patch.object(writer, "_parse_recovery_data_from_kernel", return_value=MagicMock()),
            patch.object(
                KernelRecoveryScratchData,
                "from_kernel_recovery_data",
                return_value=serialized_recovery_data,
            ),
            patch.object(ScratchConfig, "stage_json_recovery_data", new=_replace_while_staging),
        ):
            await writer.save_kernel_registry(kernel_registry_data, metadata)

        assert list(existing_config_path.iterdir()) == []

    async def test_destroyed_kernel_is_not_saved_from_snapshot(
        self,
        writer: ContainerBasedKernelRegistryWriter,
        kernel_registry_data: MutableMapping[KernelId, AbstractKernel],
        metadata: KernelRegistrySaveMetadata,
        registry_with_destroyable_kernel: tuple[KernelId, Path],
        serialized_recovery_data: KernelRecoveryScratchData,
    ) -> None:
        destroyed_kernel_id, destroyed_config_path = registry_with_destroyable_kernel
        original_stage = ScratchConfig.stage_json_recovery_data

        async def _destroy_before_its_stage(
            config: ScratchConfig, data: KernelRecoveryScratchData
        ) -> StagedRecoveryData:
            if config._config_path == destroyed_config_path:
                del kernel_registry_data[destroyed_kernel_id]
                destroyed_config_path.rmdir()
            return await original_stage(config, data)

        with (
            patch.object(
                writer,
                "_parse_recovery_data_from_kernel",
                return_value=MagicMock(),
            ),
            patch.object(
                KernelRecoveryScratchData,
                "from_kernel_recovery_data",
                return_value=serialized_recovery_data,
            ),
            patch.object(ScratchConfig, "stage_json_recovery_data", new=_destroy_before_its_stage),
        ):
            await writer.save_kernel_registry(kernel_registry_data, metadata)

        assert not destroyed_config_path.exists()

    async def test_saves_recovery_data_to_existing_config_dir(
        self,
        writer: ContainerBasedKernelRegistryWriter,
        kernel_registry_data: MutableMapping[KernelId, AbstractKernel],
        metadata: KernelRegistrySaveMetadata,
        existing_config_path: Path,
        serialized_recovery_data: KernelRecoveryScratchData,
    ) -> None:
        with (
            patch.object(
                writer,
                "_parse_recovery_data_from_kernel",
                return_value=MagicMock(),
            ),
            patch.object(
                KernelRecoveryScratchData,
                "from_kernel_recovery_data",
                return_value=serialized_recovery_data,
            ),
        ):
            await writer.save_kernel_registry(kernel_registry_data, metadata)

        assert [p.name for p in existing_config_path.iterdir()] == ["recovery.json"]

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
        mock_config_mgr.stage_json_recovery_data.assert_not_called()
