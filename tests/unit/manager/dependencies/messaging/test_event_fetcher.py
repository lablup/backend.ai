from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ai.backend.manager.dependencies.messaging.event_fetcher import EventFetcherDependency


class TestEventFetcherDependency:
    """Test EventFetcherDependency lifecycle."""

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.messaging.event_fetcher.EventFetcher")
    async def test_provide_event_fetcher(self, mock_fetcher_class: MagicMock) -> None:
        """Dependency should create event fetcher with the given message queue."""
        mock_fetcher = MagicMock()
        mock_fetcher_class.return_value = mock_fetcher
        mock_queue = MagicMock()

        dependency = EventFetcherDependency()

        async with dependency.provide(mock_queue) as fetcher:
            assert fetcher is mock_fetcher
            mock_fetcher_class.assert_called_once_with(mock_queue)

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.messaging.event_fetcher.EventFetcher")
    async def test_message_queue_reference(self, mock_fetcher_class: MagicMock) -> None:
        """Dependency should pass the correct message queue reference."""
        mock_queue = MagicMock()
        mock_fetcher_class.return_value = MagicMock()

        dependency = EventFetcherDependency()

        async with dependency.provide(mock_queue):
            call_args = mock_fetcher_class.call_args[0]
            assert call_args[0] is mock_queue
