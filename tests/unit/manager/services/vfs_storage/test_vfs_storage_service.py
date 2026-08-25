"""
Tests for VFSStorageService quota scope operations.
Tests the service layer with mocked repository and storage-proxy clients.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.repositories.vfs_storage.repository import VFSStorageRepository
from ai.backend.manager.services.vfs_storage.actions.get_quota_scope import (
    GetQuotaScopeAction,
    GetQuotaScopeActionResult,
)
from ai.backend.manager.services.vfs_storage.actions.search_quota_scopes import (
    SearchQuotaScopesAction,
    SearchQuotaScopesActionResult,
)
from ai.backend.manager.services.vfs_storage.actions.set_quota_scope import (
    SetQuotaScopeAction,
    SetQuotaScopeActionResult,
)
from ai.backend.manager.services.vfs_storage.actions.unset_quota_scope import (
    UnsetQuotaScopeAction,
    UnsetQuotaScopeActionResult,
)
from ai.backend.manager.services.vfs_storage.service import VFSStorageService


class TestVFSStorageServiceQuotaScope:
    """Test cases for VFSStorageService quota scope operations."""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        return MagicMock(spec=VFSStorageRepository)

    @pytest.fixture
    def mock_storage_manager(self) -> MagicMock:
        return MagicMock(spec=StorageSessionManager)

    @pytest.fixture
    def mock_manager_client(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service_with_storage_manager(
        self,
        mock_repository: MagicMock,
        mock_storage_manager: MagicMock,
    ) -> VFSStorageService:
        return VFSStorageService(
            vfs_storage_repository=mock_repository,
            storage_manager=mock_storage_manager,
        )

    @pytest.fixture
    def service_without_storage_manager(
        self,
        mock_repository: MagicMock,
    ) -> VFSStorageService:
        return VFSStorageService(
            vfs_storage_repository=mock_repository,
            storage_manager=None,
        )

    @staticmethod
    def _setup_proxy_and_client(
        monkeypatch: pytest.MonkeyPatch,
        mock_storage_manager: MagicMock,
        mock_manager_client: AsyncMock,
    ) -> None:
        """Helper to mock get_proxy_and_volume and get_manager_facing_client."""
        monkeypatch.setattr(
            StorageSessionManager,
            "get_proxy_and_volume",
            MagicMock(return_value=("proxy1", "volume1")),
        )
        mock_storage_manager.get_manager_facing_client.return_value = mock_manager_client

    # =========================================================================
    # GetQuotaScope
    # =========================================================================

    async def test_get_quota_scope(
        self,
        monkeypatch: pytest.MonkeyPatch,
        service_with_storage_manager: VFSStorageService,
        mock_storage_manager: MagicMock,
        mock_manager_client: AsyncMock,
    ) -> None:
        """Test valid storage_host_name/quota_scope_id returns usage/limit."""
        self._setup_proxy_and_client(monkeypatch, mock_storage_manager, mock_manager_client)
        mock_manager_client.get_quota_scope.return_value = {
            "used_bytes": 1024,
            "limit_bytes": 4096,
        }

        action = GetQuotaScopeAction(
            storage_host_name="proxy1:volume1",
            quota_scope_id="scope-1",
        )
        result = await service_with_storage_manager.get_quota_scope(action)

        assert isinstance(result, GetQuotaScopeActionResult)
        assert result.quota_scope_id == "scope-1"
        assert result.storage_host_name == "proxy1:volume1"
        assert result.usage_bytes == 1024
        assert result.hard_limit_bytes == 4096

    async def test_get_quota_scope_negative_usage_bytes_converted_to_none(
        self,
        monkeypatch: pytest.MonkeyPatch,
        service_with_storage_manager: VFSStorageService,
        mock_storage_manager: MagicMock,
        mock_manager_client: AsyncMock,
    ) -> None:
        """Test negative usage_bytes converted to None."""
        self._setup_proxy_and_client(monkeypatch, mock_storage_manager, mock_manager_client)
        mock_manager_client.get_quota_scope.return_value = {
            "used_bytes": -1,
            "limit_bytes": 4096,
        }

        action = GetQuotaScopeAction(
            storage_host_name="proxy1:volume1",
            quota_scope_id="scope-1",
        )
        result = await service_with_storage_manager.get_quota_scope(action)

        assert result.usage_bytes is None
        assert result.hard_limit_bytes == 4096

    async def test_get_quota_scope_no_storage_manager_raises_runtime_error(
        self,
        service_without_storage_manager: VFSStorageService,
    ) -> None:
        """Test no storage_manager raises RuntimeError."""
        action = GetQuotaScopeAction(
            storage_host_name="proxy1:volume1",
            quota_scope_id="scope-1",
        )

        with pytest.raises(RuntimeError, match="Storage manager is not configured"):
            await service_without_storage_manager.get_quota_scope(action)

    # =========================================================================
    # SetQuotaScope
    # =========================================================================

    async def test_set_quota_scope(
        self,
        monkeypatch: pytest.MonkeyPatch,
        service_with_storage_manager: VFSStorageService,
        mock_storage_manager: MagicMock,
        mock_manager_client: AsyncMock,
    ) -> None:
        """Test hard_limit_bytes updates storage proxy + returns updated state."""
        self._setup_proxy_and_client(monkeypatch, mock_storage_manager, mock_manager_client)
        mock_manager_client.update_quota_scope = AsyncMock()
        mock_manager_client.get_quota_scope.return_value = {
            "used_bytes": 512,
            "limit_bytes": 8192,
        }

        action = SetQuotaScopeAction(
            storage_host_name="proxy1:volume1",
            quota_scope_id="scope-1",
            hard_limit_bytes=8192,
        )
        result = await service_with_storage_manager.set_quota_scope(action)

        assert isinstance(result, SetQuotaScopeActionResult)
        assert result.usage_bytes == 512
        assert result.hard_limit_bytes == 8192
        mock_manager_client.update_quota_scope.assert_called_once_with("volume1", "scope-1", 8192)

    async def test_set_quota_scope_negative_usage_bytes_converted_to_none(
        self,
        monkeypatch: pytest.MonkeyPatch,
        service_with_storage_manager: VFSStorageService,
        mock_storage_manager: MagicMock,
        mock_manager_client: AsyncMock,
    ) -> None:
        """Test negative usage_bytes converted to None after set."""
        self._setup_proxy_and_client(monkeypatch, mock_storage_manager, mock_manager_client)
        mock_manager_client.update_quota_scope = AsyncMock()
        mock_manager_client.get_quota_scope.return_value = {
            "used_bytes": -1,
            "limit_bytes": 8192,
        }

        action = SetQuotaScopeAction(
            storage_host_name="proxy1:volume1",
            quota_scope_id="scope-1",
            hard_limit_bytes=8192,
        )
        result = await service_with_storage_manager.set_quota_scope(action)

        assert result.usage_bytes is None
        assert result.hard_limit_bytes == 8192

    # =========================================================================
    # UnsetQuotaScope
    # =========================================================================

    async def test_unset_quota_scope(
        self,
        monkeypatch: pytest.MonkeyPatch,
        service_with_storage_manager: VFSStorageService,
        mock_storage_manager: MagicMock,
        mock_manager_client: AsyncMock,
    ) -> None:
        """Test quota deletion returns quota_scope_id."""
        self._setup_proxy_and_client(monkeypatch, mock_storage_manager, mock_manager_client)
        mock_manager_client.delete_quota_scope_quota = AsyncMock()

        action = UnsetQuotaScopeAction(
            storage_host_name="proxy1:volume1",
            quota_scope_id="scope-1",
        )
        result = await service_with_storage_manager.unset_quota_scope(action)

        assert isinstance(result, UnsetQuotaScopeActionResult)
        assert result.quota_scope_id == "scope-1"
        assert result.storage_host_name == "proxy1:volume1"
        mock_manager_client.delete_quota_scope_quota.assert_called_once_with("volume1", "scope-1")

    async def test_unset_quota_scope_no_storage_manager_raises_runtime_error(
        self,
        service_without_storage_manager: VFSStorageService,
    ) -> None:
        """Test no storage_manager raises RuntimeError."""
        action = UnsetQuotaScopeAction(
            storage_host_name="proxy1:volume1",
            quota_scope_id="scope-1",
        )

        with pytest.raises(RuntimeError, match="Storage manager is not configured"):
            await service_without_storage_manager.unset_quota_scope(action)

    # =========================================================================
    # SearchQuotaScopes
    # =========================================================================

    async def test_search_quota_scopes(
        self,
        monkeypatch: pytest.MonkeyPatch,
        service_with_storage_manager: VFSStorageService,
        mock_storage_manager: MagicMock,
        mock_manager_client: AsyncMock,
    ) -> None:
        """Test aggregates volumes across all storage hosts."""
        self._setup_proxy_and_client(monkeypatch, mock_storage_manager, mock_manager_client)
        mock_storage_manager.get_all_volumes = AsyncMock(
            return_value=[
                ("proxy1:volume1", {"some": "info"}),
                ("proxy1:volume2", {"other": "info"}),
            ]
        )
        mock_manager_client.get_quota_scope.side_effect = [
            {"used_bytes": 100, "limit_bytes": 1000},
            {"used_bytes": 200, "limit_bytes": 2000},
        ]

        action = SearchQuotaScopesAction()
        result = await service_with_storage_manager.search_quota_scopes(action)

        assert isinstance(result, SearchQuotaScopesActionResult)
        assert len(result.quota_scopes) == 2
        assert result.quota_scopes[0].storage_host_name == "proxy1:volume1"
        assert result.quota_scopes[0].usage_bytes == 100
        assert result.quota_scopes[0].hard_limit_bytes == 1000
        assert result.quota_scopes[1].storage_host_name == "proxy1:volume2"
        assert result.quota_scopes[1].usage_bytes == 200
        assert result.quota_scopes[1].hard_limit_bytes == 2000

    async def test_search_quota_scopes_error_handled(
        self,
        monkeypatch: pytest.MonkeyPatch,
        service_with_storage_manager: VFSStorageService,
        mock_storage_manager: MagicMock,
        mock_manager_client: AsyncMock,
    ) -> None:
        """Test storage proxy error handled via try/except — errored volumes skipped."""
        self._setup_proxy_and_client(monkeypatch, mock_storage_manager, mock_manager_client)
        mock_storage_manager.get_all_volumes = AsyncMock(
            return_value=[
                ("proxy1:volume1", {}),
                ("proxy1:volume2", {}),
            ]
        )
        mock_manager_client.get_quota_scope.side_effect = [
            Exception("Connection refused"),
            {"used_bytes": 200, "limit_bytes": 2000},
        ]

        action = SearchQuotaScopesAction()
        result = await service_with_storage_manager.search_quota_scopes(action)

        assert len(result.quota_scopes) == 1
        assert result.quota_scopes[0].storage_host_name == "proxy1:volume2"

    async def test_search_quota_scopes_negative_usage_bytes_converted_to_none(
        self,
        monkeypatch: pytest.MonkeyPatch,
        service_with_storage_manager: VFSStorageService,
        mock_storage_manager: MagicMock,
        mock_manager_client: AsyncMock,
    ) -> None:
        """Test negative usage_bytes converted to None in search results."""
        self._setup_proxy_and_client(monkeypatch, mock_storage_manager, mock_manager_client)
        mock_storage_manager.get_all_volumes = AsyncMock(return_value=[("proxy1:volume1", {})])
        mock_manager_client.get_quota_scope.return_value = {
            "used_bytes": -1,
            "limit_bytes": 5000,
        }

        action = SearchQuotaScopesAction()
        result = await service_with_storage_manager.search_quota_scopes(action)

        assert len(result.quota_scopes) == 1
        assert result.quota_scopes[0].usage_bytes is None
        assert result.quota_scopes[0].hard_limit_bytes == 5000

    async def test_search_quota_scopes_no_storage_manager_raises_runtime_error(
        self,
        service_without_storage_manager: VFSStorageService,
    ) -> None:
        """Test no storage_manager raises RuntimeError."""
        action = SearchQuotaScopesAction()

        with pytest.raises(RuntimeError, match="Storage manager is not configured"):
            await service_without_storage_manager.search_quota_scopes(action)
