from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.manager.dependencies.domain.notification import NotificationCenterDependency


class TestNotificationCenterDependency:
    """Test NotificationCenterDependency lifecycle."""

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.domain.notification.NotificationCenter")
    async def test_provide_notification_center(self, mock_nc_class: MagicMock) -> None:
        """Dependency should create and close NotificationCenter."""
        mock_nc = MagicMock()
        mock_nc.close = AsyncMock()
        mock_nc_class.return_value = mock_nc

        dependency = NotificationCenterDependency()

        async with dependency.provide(None) as nc:
            assert nc is mock_nc
            mock_nc_class.assert_called_once()

        mock_nc.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.domain.notification.NotificationCenter")
    async def test_cleanup_on_exception(self, mock_nc_class: MagicMock) -> None:
        """Dependency should cleanup NotificationCenter even on exception."""
        mock_nc = MagicMock()
        mock_nc.close = AsyncMock()
        mock_nc_class.return_value = mock_nc

        dependency = NotificationCenterDependency()

        with pytest.raises(RuntimeError):
            async with dependency.provide(None) as nc:
                assert nc is mock_nc
                raise RuntimeError("Test error")

        mock_nc.close.assert_called_once()

    def test_stage_name(self) -> None:
        """Dependency should have correct stage name."""
        dependency = NotificationCenterDependency()
        assert dependency.stage_name == "notification-center"

    def test_gen_health_checkers_returns_none(self) -> None:
        """NonMonitorable dependency should return None for health checkers."""
        dependency = NotificationCenterDependency()
        assert dependency.gen_health_checkers(MagicMock()) is None
