from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.defs import REDIS_STREAM_DB
from ai.backend.manager.dependencies.messaging.message_queue import (
    EVENT_DISPATCHER_CONSUMER_GROUP,
    MessageQueueDependency,
    MessageQueueInput,
)


@dataclass
class MockManagerConfig:
    """Simple mock for manager config."""

    id: str
    use_experimental_redis_event_dispatcher: bool


@dataclass
class MockDebugConfig:
    """Simple mock for debug config."""

    log_events: bool


@dataclass
class MockConfig:
    """Simple mock for unified config."""

    manager: MockManagerConfig
    redis: MagicMock
    debug: MockDebugConfig


def _make_mock_config(*, use_experimental: bool = False) -> MockConfig:
    mock_redis = MagicMock()
    mock_profile_target = MagicMock()
    mock_stream_target = MagicMock()
    mock_profile_target.profile_target.return_value = mock_stream_target
    mock_redis.to_redis_profile_target.return_value = mock_profile_target

    return MockConfig(
        manager=MockManagerConfig(
            id="test-manager-id",
            use_experimental_redis_event_dispatcher=use_experimental,
        ),
        redis=mock_redis,
        debug=MockDebugConfig(log_events=False),
    )


class TestMessageQueueDependency:
    """Test MessageQueueDependency lifecycle."""

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.messaging.message_queue.RedisQueue")
    async def test_provide_redis_queue(self, mock_redis_queue_class: MagicMock) -> None:
        """Dependency should create RedisQueue when experimental flag is off."""
        mock_queue = MagicMock()
        mock_queue.close = AsyncMock()
        mock_redis_queue_class.create = AsyncMock(return_value=mock_queue)

        config = _make_mock_config(use_experimental=False)
        dependency = MessageQueueDependency()
        queue_input = MessageQueueInput(config=config)  # type: ignore[arg-type]

        async with dependency.provide(queue_input) as queue:
            assert queue is mock_queue
            mock_redis_queue_class.create.assert_called_once()
            # Verify RedisMQArgs construction
            call_args = mock_redis_queue_class.create.call_args
            args = call_args[0][1]
            assert args.anycast_stream_key == "events"
            assert args.broadcast_channel == "events_all"
            assert args.group_name == EVENT_DISPATCHER_CONSUMER_GROUP
            assert args.node_id == "test-manager-id"
            assert args.db == REDIS_STREAM_DB

        # Queue should be closed after context exit
        mock_queue.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.messaging.message_queue.HiRedisQueue")
    async def test_provide_hiredis_queue(self, mock_hiredis_class: MagicMock) -> None:
        """Dependency should create HiRedisQueue when experimental flag is on."""
        mock_queue = MagicMock()
        mock_queue.close = AsyncMock()
        mock_hiredis_class.return_value = mock_queue

        config = _make_mock_config(use_experimental=True)
        dependency = MessageQueueDependency()
        queue_input = MessageQueueInput(config=config)  # type: ignore[arg-type]

        async with dependency.provide(queue_input) as queue:
            assert queue is mock_queue
            mock_hiredis_class.assert_called_once()

        # Queue should be closed after context exit
        mock_queue.close.assert_called_once()

    @pytest.mark.asyncio
    @patch("ai.backend.manager.dependencies.messaging.message_queue.RedisQueue")
    async def test_cleanup_on_exception(self, mock_redis_queue_class: MagicMock) -> None:
        """Dependency should close queue even on exception."""
        mock_queue = MagicMock()
        mock_queue.close = AsyncMock()
        mock_redis_queue_class.create = AsyncMock(return_value=mock_queue)

        config = _make_mock_config(use_experimental=False)
        dependency = MessageQueueDependency()
        queue_input = MessageQueueInput(config=config)  # type: ignore[arg-type]

        with pytest.raises(RuntimeError):
            async with dependency.provide(queue_input) as queue:
                assert queue is mock_queue
                raise RuntimeError("Test error")

        # Queue should still be closed
        mock_queue.close.assert_called_once()
