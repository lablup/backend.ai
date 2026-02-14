from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.manager.dependencies.messaging.composer import (
    MessagingComposer,
    MessagingInput,
    MessagingResources,
)
from ai.backend.manager.dependencies.messaging.event_producer import EventProducerInput
from ai.backend.manager.dependencies.messaging.message_queue import MessageQueueInput


def _make_mock_config() -> Any:
    config = MagicMock()
    config.debug.log_events = False
    return config


class TestMessagingComposer:
    """Test MessagingComposer lifecycle."""

    @pytest.mark.asyncio
    async def test_compose_creates_all_resources(self) -> None:
        """Composer should create all messaging resources in correct order."""
        mock_event_hub = MagicMock()
        mock_message_queue = MagicMock()
        mock_event_fetcher = MagicMock()
        mock_event_producer = MagicMock()

        call_order: list[str] = []

        async def mock_enter_dependency(provider: Any, setup_input: Any) -> MagicMock:
            stage_name = provider.stage_name
            call_order.append(stage_name)
            if stage_name == "event-hub":
                assert setup_input is None
                return mock_event_hub
            if stage_name == "message-queue":
                assert isinstance(setup_input, MessageQueueInput)
                return mock_message_queue
            if stage_name == "event-fetcher":
                assert setup_input is mock_message_queue
                return mock_event_fetcher
            if stage_name == "event-producer":
                assert isinstance(setup_input, EventProducerInput)
                assert setup_input.message_queue is mock_message_queue
                return mock_event_producer
            raise ValueError(f"Unexpected provider: {stage_name}")

        mock_stack = MagicMock()
        mock_stack.enter_dependency = AsyncMock(side_effect=mock_enter_dependency)

        config = _make_mock_config()
        messaging_input = MessagingInput(config=config)

        composer = MessagingComposer()
        assert composer.stage_name == "messaging"

        async with composer.compose(mock_stack, messaging_input) as resources:
            assert isinstance(resources, MessagingResources)
            assert resources.event_hub is mock_event_hub
            assert resources.message_queue is mock_message_queue
            assert resources.event_fetcher is mock_event_fetcher
            assert resources.event_producer is mock_event_producer

        # Verify composition order
        assert call_order == [
            "event-hub",
            "message-queue",
            "event-fetcher",
            "event-producer",
        ]

    @pytest.mark.asyncio
    async def test_compose_passes_config_correctly(self) -> None:
        """Composer should pass config to message queue and event producer."""
        config = _make_mock_config()
        messaging_input = MessagingInput(config=config)

        captured_inputs: dict[str, Any] = {}

        async def mock_enter_dependency(provider: Any, setup_input: Any) -> MagicMock:
            stage_name = provider.stage_name
            captured_inputs[stage_name] = setup_input
            return MagicMock()

        mock_stack = MagicMock()
        mock_stack.enter_dependency = AsyncMock(side_effect=mock_enter_dependency)

        composer = MessagingComposer()

        async with composer.compose(mock_stack, messaging_input):
            # Verify config is passed to message queue
            mq_input = captured_inputs["message-queue"]
            assert isinstance(mq_input, MessageQueueInput)
            assert mq_input.config is config

            # Verify config is passed to event producer
            ep_input = captured_inputs["event-producer"]
            assert isinstance(ep_input, EventProducerInput)
            assert ep_input.config is config
