from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.manager.dependencies.components.storage import StorageManagerDependency


@dataclass
class MockVolumesConfig:
    """Simple mock for volumes config."""

    pass


@dataclass
class MockConfig:
    """Simple mock for manager config."""

    volumes: MockVolumesConfig


class TestStorageManagerDependency:
    """

    Test StorageManagerDependency lifecycle.
    """

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.components.storage.StorageSessionManager")
    async def test_provide_storage_manager(self, mock_storage_class: MagicMock) -> None:
        """

        Dependency should create and close storage manager.
        """
        config = MockConfig(volumes=MockVolumesConfig())
        mock_storage = MagicMock()
        mock_storage.aclose = AsyncMock()
        mock_storage_class.return_value = mock_storage

        dependency = StorageManagerDependency()

        async with dependency.provide(config) as storage:  # type: ignore[arg-type]
            assert storage is mock_storage
            mock_storage_class.assert_called_once_with(config.volumes)

        # Storage manager should be closed after context exit
        mock_storage.aclose.assert_called_once()

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.components.storage.StorageSessionManager")
    async def test_cleanup_on_exception(self, mock_storage_class: MagicMock) -> None:
        """

        Dependency should cleanup storage manager even on exception.
        """
        config = MockConfig(volumes=MockVolumesConfig())
        mock_storage = MagicMock()
        mock_storage.aclose = AsyncMock()
        mock_storage_class.return_value = mock_storage

        dependency = StorageManagerDependency()

        with pytest.raises(RuntimeError):
            async with dependency.provide(config) as storage:  # type: ignore[arg-type]
                assert storage is mock_storage
                raise RuntimeError("Test error")

        # Storage manager should still be closed
        mock_storage.aclose.assert_called_once()
