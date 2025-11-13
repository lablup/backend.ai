from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.dependencies.components.storage import StorageManagerDependency


class TestStorageManagerDependency:
    """

    Test StorageManagerDependency lifecycle.
    """

    @pytest.mark.asyncio
    async def test_stage_name(self) -> None:
        """

        Dependency should have correct stage name.
        """
        dependency = StorageManagerDependency()
        assert dependency.stage_name == "storage-manager"

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.components.storage.StorageSessionManager")
    async def test_provide_storage_manager(
        self, mock_storage_class: MagicMock, mock_config: ManagerUnifiedConfig
    ) -> None:
        """

        Dependency should create and close storage manager.
        """
        mock_storage = MagicMock()
        mock_storage.aclose = AsyncMock()
        mock_storage_class.return_value = mock_storage

        mock_volumes = MagicMock()
        mock_config.volumes = mock_volumes

        dependency = StorageManagerDependency()

        async with dependency.provide(mock_config) as storage:
            assert storage is mock_storage
            mock_storage_class.assert_called_once_with(mock_volumes)

        # Storage manager should be closed after context exit
        mock_storage.aclose.assert_called_once()

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.components.storage.StorageSessionManager")
    async def test_cleanup_on_exception(
        self, mock_storage_class: MagicMock, mock_config: ManagerUnifiedConfig
    ) -> None:
        """

        Dependency should cleanup storage manager even on exception.
        """
        mock_storage = MagicMock()
        mock_storage.aclose = AsyncMock()
        mock_storage_class.return_value = mock_storage

        mock_volumes = MagicMock()
        mock_config.volumes = mock_volumes

        dependency = StorageManagerDependency()

        with pytest.raises(RuntimeError):
            async with dependency.provide(mock_config) as storage:
                assert storage is mock_storage
                raise RuntimeError("Test error")

        # Storage manager should still be closed
        mock_storage.aclose.assert_called_once()
