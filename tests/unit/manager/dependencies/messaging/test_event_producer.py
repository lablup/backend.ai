from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.types import AGENTID_MANAGER
from ai.backend.manager.dependencies.messaging.event_producer import (
    EventProducerDependency,
    EventProducerInput,
)


@dataclass
class MockDebugConfig:
    """Simple mock for debug config."""

    log_events: bool


@dataclass
class MockConfig:
    """Simple mock for unified config."""

    debug: MockDebugConfig


class TestEventProducerDependency:
    """Test EventProducerDependency lifecycle."""

    @pytest.mark.asyncio
    @patch(
        "ai.backend.manager.dependencies.messaging.event_producer.asyncio.sleep",
        new_callable=AsyncMock,
    )
    @patch("ai.backend.manager.dependencies.messaging.event_producer.EventProducer")
    async def test_provide_event_producer(
        self,
        mock_producer_class: MagicMock,
        mock_sleep: AsyncMock,
    ) -> None:
        """Dependency should create event producer with correct parameters."""
        mock_producer = MagicMock()
        mock_producer.close = AsyncMock()
        mock_producer_class.return_value = mock_producer

        mock_queue = MagicMock()
        config = MockConfig(debug=MockDebugConfig(log_events=True))
        producer_input = EventProducerInput(
            message_queue=mock_queue,
            config=config,  # type: ignore[arg-type]
        )

        dependency = EventProducerDependency()

        async with dependency.provide(producer_input) as producer:
            assert producer is mock_producer
            mock_producer_class.assert_called_once_with(
                mock_queue,
                source=AGENTID_MANAGER,
                log_events=True,
            )

        # Producer should be closed after context exit
        mock_producer.close.assert_called_once()
        mock_sleep.assert_called_once_with(0.2)

    @pytest.mark.asyncio
    @patch(
        "ai.backend.manager.dependencies.messaging.event_producer.asyncio.sleep",
        new_callable=AsyncMock,
    )
    @patch("ai.backend.manager.dependencies.messaging.event_producer.EventProducer")
    async def test_cleanup_on_exception(
        self,
        mock_producer_class: MagicMock,
        mock_sleep: AsyncMock,
    ) -> None:
        """Dependency should close event producer even on exception."""
        mock_producer = MagicMock()
        mock_producer.close = AsyncMock()
        mock_producer_class.return_value = mock_producer

        mock_queue = MagicMock()
        config = MockConfig(debug=MockDebugConfig(log_events=False))
        producer_input = EventProducerInput(
            message_queue=mock_queue,
            config=config,  # type: ignore[arg-type]
        )

        dependency = EventProducerDependency()

        with pytest.raises(RuntimeError):
            async with dependency.provide(producer_input) as producer:
                assert producer is mock_producer
                raise RuntimeError("Test error")

        # Producer should still be closed
        mock_producer.close.assert_called_once()
        mock_sleep.assert_called_once_with(0.2)
