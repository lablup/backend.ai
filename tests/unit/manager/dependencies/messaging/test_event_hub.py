from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.manager.dependencies.messaging.event_hub import EventHubDependency


class TestEventHubDependency:
    """Test EventHubDependency lifecycle."""

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.messaging.event_hub.EventHub")
    async def test_provide_event_hub(self, mock_hub_class: MagicMock) -> None:
        """Dependency should create and shut down event hub."""
        mock_hub = MagicMock()
        mock_hub.shutdown = AsyncMock()
        mock_hub_class.return_value = mock_hub

        dependency = EventHubDependency()

        async with dependency.provide(None) as event_hub:
            assert event_hub is mock_hub
            mock_hub_class.assert_called_once()

        # Event hub should be shut down after context exit
        mock_hub.shutdown.assert_called_once()

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.messaging.event_hub.EventHub")
    async def test_cleanup_on_exception(self, mock_hub_class: MagicMock) -> None:
        """Dependency should shut down event hub even on exception."""
        mock_hub = MagicMock()
        mock_hub.shutdown = AsyncMock()
        mock_hub_class.return_value = mock_hub

        dependency = EventHubDependency()

        with pytest.raises(RuntimeError):
            async with dependency.provide(None) as event_hub:
                assert event_hub is mock_hub
                raise RuntimeError("Test error")

        # Event hub should still be shut down
        mock_hub.shutdown.assert_called_once()
