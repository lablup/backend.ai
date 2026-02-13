from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.agent.kernel_registry.exception import (
    KernelRegistryLoadError,
    KernelRegistryNotFound,
)
from ai.backend.agent.kernel_registry.loader.container import ContainerBasedKernelRegistryLoader
from ai.backend.common.types import KernelId


@pytest.fixture
def scratch_root(tmp_path: Path) -> Path:
    return tmp_path / "scratches"


@pytest.fixture
def mock_agent() -> MagicMock:
    agent = MagicMock()
    agent.enumerate_containers = AsyncMock(return_value=[])
    return agent


@pytest.fixture
def loader(scratch_root: Path, mock_agent: MagicMock) -> ContainerBasedKernelRegistryLoader:
    return ContainerBasedKernelRegistryLoader(scratch_root, mock_agent)


@pytest.fixture
def kernel_id() -> KernelId:
    return KernelId(uuid.uuid4())


def _make_scratch_config_dir(scratch_root: Path, kernel_id: KernelId) -> Path:
    config_dir = scratch_root / str(kernel_id) / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


class TestLoadKernelRecoveryFromScratch:
    """Tests for _load_kernel_recovery_from_scratch."""

    async def test_missing_recovery_json(
        self,
        loader: ContainerBasedKernelRegistryLoader,
        scratch_root: Path,
        kernel_id: KernelId,
    ) -> None:
        """Raise KernelRegistryNotFound when recovery.json is missing."""
        config_dir = _make_scratch_config_dir(scratch_root, kernel_id)
        # No files created — recovery.json is missing

        with pytest.raises(KernelRegistryNotFound):
            await loader._load_kernel_recovery_from_scratch(config_dir)

    async def test_missing_environ_txt(
        self,
        loader: ContainerBasedKernelRegistryLoader,
        scratch_root: Path,
        kernel_id: KernelId,
    ) -> None:
        """Raise KernelRegistryNotFound when environ.txt is missing."""
        config_dir = _make_scratch_config_dir(scratch_root, kernel_id)
        # Create recovery.json but not environ.txt
        mock_json_data = MagicMock()
        with patch("ai.backend.agent.kernel_registry.loader.container.ScratchConfig") as MockConfig:
            instance = MockConfig.return_value
            instance.get_json_recovery_data = AsyncMock(return_value=mock_json_data)
            instance.get_kernel_environ = AsyncMock(side_effect=FileNotFoundError("environ.txt"))
            instance.get_kernel_resource_spec = AsyncMock(return_value=MagicMock())

            with pytest.raises(KernelRegistryNotFound):
                await loader._load_kernel_recovery_from_scratch(config_dir)

    async def test_missing_resource_txt(
        self,
        loader: ContainerBasedKernelRegistryLoader,
        scratch_root: Path,
        kernel_id: KernelId,
    ) -> None:
        """Raise KernelRegistryNotFound when resource.txt is missing."""
        config_dir = _make_scratch_config_dir(scratch_root, kernel_id)
        with patch("ai.backend.agent.kernel_registry.loader.container.ScratchConfig") as MockConfig:
            instance = MockConfig.return_value
            instance.get_json_recovery_data = AsyncMock(return_value=MagicMock())
            instance.get_kernel_environ = AsyncMock(return_value={"KEY": "val"})
            instance.get_kernel_resource_spec = AsyncMock(
                side_effect=FileNotFoundError("resource.txt")
            )

            with pytest.raises(KernelRegistryNotFound):
                await loader._load_kernel_recovery_from_scratch(config_dir)

    async def test_os_error_raises_load_error(
        self,
        loader: ContainerBasedKernelRegistryLoader,
        scratch_root: Path,
        kernel_id: KernelId,
    ) -> None:
        """Raise KernelRegistryLoadError on OSError (e.g. too many open files)."""
        config_dir = _make_scratch_config_dir(scratch_root, kernel_id)
        with patch("ai.backend.agent.kernel_registry.loader.container.ScratchConfig") as MockConfig:
            instance = MockConfig.return_value
            instance.get_json_recovery_data = AsyncMock(return_value=MagicMock())
            instance.get_kernel_environ = AsyncMock(side_effect=OSError(24, "Too many open files"))
            instance.get_kernel_resource_spec = AsyncMock(return_value=MagicMock())

            with pytest.raises(KernelRegistryLoadError):
                await loader._load_kernel_recovery_from_scratch(config_dir)

    async def test_corrupt_data_raises_load_error(
        self,
        loader: ContainerBasedKernelRegistryLoader,
        scratch_root: Path,
        kernel_id: KernelId,
    ) -> None:
        """Raise KernelRegistryLoadError on corrupt data (e.g. parse failure)."""
        config_dir = _make_scratch_config_dir(scratch_root, kernel_id)
        with patch("ai.backend.agent.kernel_registry.loader.container.ScratchConfig") as MockConfig:
            instance = MockConfig.return_value
            instance.get_json_recovery_data = AsyncMock(return_value=MagicMock())
            instance.get_kernel_environ = AsyncMock(return_value={"KEY": "val"})
            instance.get_kernel_resource_spec = AsyncMock(side_effect=ValueError("invalid data"))

            with pytest.raises(KernelRegistryLoadError):
                await loader._load_kernel_recovery_from_scratch(config_dir)


class TestLoadKernelRegistry:
    """Tests for load_kernel_registry."""

    async def test_skips_kernel_without_config_dir(
        self,
        loader: ContainerBasedKernelRegistryLoader,
        mock_agent: MagicMock,
        kernel_id: KernelId,
    ) -> None:
        """Skip kernels whose scratch config directory does not exist."""
        mock_agent.enumerate_containers = AsyncMock(return_value=[(kernel_id, MagicMock())])
        # scratch_root doesn't exist, so config_path.is_dir() is False
        result = await loader.load_kernel_registry()
        assert len(result) == 0

    async def test_skips_kernel_on_registry_not_found(
        self,
        loader: ContainerBasedKernelRegistryLoader,
        mock_agent: MagicMock,
        scratch_root: Path,
        kernel_id: KernelId,
    ) -> None:
        """Skip kernels that raise KernelRegistryNotFound."""
        _make_scratch_config_dir(scratch_root, kernel_id)
        mock_agent.enumerate_containers = AsyncMock(return_value=[(kernel_id, MagicMock())])

        with patch.object(
            loader,
            "_load_kernel_recovery_from_scratch",
            side_effect=KernelRegistryNotFound(),
        ):
            result = await loader.load_kernel_registry()
            assert len(result) == 0

    async def test_skips_kernel_on_load_error(
        self,
        loader: ContainerBasedKernelRegistryLoader,
        mock_agent: MagicMock,
        scratch_root: Path,
        kernel_id: KernelId,
    ) -> None:
        """Skip kernels that raise KernelRegistryLoadError."""
        _make_scratch_config_dir(scratch_root, kernel_id)
        mock_agent.enumerate_containers = AsyncMock(return_value=[(kernel_id, MagicMock())])

        with patch.object(
            loader,
            "_load_kernel_recovery_from_scratch",
            side_effect=KernelRegistryLoadError(),
        ):
            result = await loader.load_kernel_registry()
            assert len(result) == 0

    async def test_loads_valid_kernel(
        self,
        loader: ContainerBasedKernelRegistryLoader,
        mock_agent: MagicMock,
        scratch_root: Path,
        kernel_id: KernelId,
    ) -> None:
        """Successfully load a kernel from valid scratch data."""
        _make_scratch_config_dir(scratch_root, kernel_id)
        mock_agent.enumerate_containers = AsyncMock(return_value=[(kernel_id, MagicMock())])
        mock_recovery_data = MagicMock()
        mock_kernel = MagicMock()
        mock_recovery_data.to_docker_kernel.return_value = mock_kernel

        with patch.object(
            loader,
            "_load_kernel_recovery_from_scratch",
            return_value=mock_recovery_data,
        ):
            result = await loader.load_kernel_registry()
            assert len(result) == 1
            assert result[kernel_id] is mock_kernel
