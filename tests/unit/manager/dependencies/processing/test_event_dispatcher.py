from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.manager.dependencies.processing.event_dispatcher import (
    EventDispatcherDependency,
    EventDispatcherInput,
)


class TestEventDispatcherDependency:
    """Test EventDispatcherDependency lifecycle."""

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.processing.event_dispatcher.EventDispatcher")
    async def test_provide_event_dispatcher(
        self,
        mock_dispatcher_class: MagicMock,
    ) -> None:
        """Dependency should create EventDispatcher and close on exit."""
        mock_dispatcher = MagicMock()
        mock_dispatcher.close = AsyncMock()
        mock_dispatcher_class.return_value = mock_dispatcher

        mock_message_queue = MagicMock()
        mock_event_observer = MagicMock()

        dependency = EventDispatcherDependency()
        dispatcher_input = EventDispatcherInput(
            message_queue=mock_message_queue,
            log_events=True,
            event_observer=mock_event_observer,
        )

        async with dependency.provide(dispatcher_input) as dispatcher:
            assert dispatcher is mock_dispatcher
            mock_dispatcher_class.assert_called_once_with(
                mock_message_queue,
                log_events=True,
                event_observer=mock_event_observer,
            )

        mock_dispatcher.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.processing.event_dispatcher.EventDispatcher")
    async def test_provide_event_dispatcher_none_observer(
        self,
        mock_dispatcher_class: MagicMock,
    ) -> None:
        """Dependency should accept None event_observer."""
        mock_dispatcher = MagicMock()
        mock_dispatcher.close = AsyncMock()
        mock_dispatcher_class.return_value = mock_dispatcher

        dependency = EventDispatcherDependency()
        dispatcher_input = EventDispatcherInput(
            message_queue=MagicMock(),
            log_events=False,
            event_observer=None,
        )

        async with dependency.provide(dispatcher_input) as dispatcher:
            assert dispatcher is mock_dispatcher
            mock_dispatcher_class.assert_called_once_with(
                dispatcher_input.message_queue,
                log_events=False,
                event_observer=None,
            )

        mock_dispatcher.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.processing.event_dispatcher.EventDispatcher")
    async def test_cleanup_on_exception(
        self,
        mock_dispatcher_class: MagicMock,
    ) -> None:
        """Dependency should cleanup EventDispatcher even on exception."""
        mock_dispatcher = MagicMock()
        mock_dispatcher.close = AsyncMock()
        mock_dispatcher_class.return_value = mock_dispatcher

        dependency = EventDispatcherDependency()
        dispatcher_input = EventDispatcherInput(
            message_queue=MagicMock(),
            log_events=False,
            event_observer=None,
        )

        with pytest.raises(RuntimeError):
            async with dependency.provide(dispatcher_input) as dispatcher:
                assert dispatcher is mock_dispatcher
                raise RuntimeError("Test error")

        mock_dispatcher.close.assert_called_once()
