from __future__ import annotations

import asyncio
import hashlib
import logging
import random
import socket
import time
from collections.abc import AsyncGenerator, Iterable
from dataclasses import dataclass
from typing import Optional, Self, override

import glide
from aiotools.server import process_index

from ai.backend.common.clients.valkey_client.valkey_stream.client import ValkeyStreamClient
from ai.backend.common.defs import REDIS_STREAM_DB
from ai.backend.common.message_queue.abc import AbstractConsumer
from ai.backend.common.message_queue.types import MessageId, MQMessage
from ai.backend.common.types import RedisTarget
from ai.backend.logging.utils import BraceStyleAdapter

from .exceptions import MessageQueueClosedError

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_AUTOCLAIM_IDLE_TIMEOUT = 300_000  # 5 minutes
_DEFAULT_AUTOCLAIM_INTERVAL = 60_000
_DEFAULT_READ_BLOCK_MS = 10_000  # 10 second
_DEFAULT_READ_COUNT = 64


@dataclass
class _BackoffState:
    """Tracks exponential backoff state for a stream."""

    attempt: int = 0
    last_error_time: float = 0.0

    def increment(self) -> None:
        """Increment attempt counter and record error time."""
        self.attempt += 1
        self.last_error_time = time.monotonic()

    def reset(self) -> None:
        """Reset backoff state after successful operation."""
        self.attempt = 0
        self.last_error_time = 0.0


@dataclass
class RedisConsumerArgs:
    stream_keys: Iterable[str]
    group_name: str
    node_id: str
    db: int = 0
    autoclaim_idle_timeout: int = _DEFAULT_AUTOCLAIM_IDLE_TIMEOUT
    autoclaim_start_id: Optional[str] = None
    backoff_initial_delay: float = 0.1  # 100ms first retry
    backoff_max_delay: float = 30.0  # cap at 30 seconds
    backoff_max_attempts: Optional[int] = None  # None = infinite retry


class RedisConsumer(AbstractConsumer):
    """
    Redis-based consumer implementation for consuming messages from streams.

    This component handles consuming messages from Redis streams using consumer groups.
    Supports automatic claiming of idle messages, retry logic, and message acknowledgment.
    """

    _client: ValkeyStreamClient
    _consume_queue: asyncio.Queue[MQMessage]
    _stream_keys: set[str]
    _group_name: str
    _consumer_id: str
    _redis_target: RedisTarget
    _autoclaim_idle_timeout: int
    _closed: bool
    _loop_tasks: list[asyncio.Task]
    _backoff_initial_delay: float
    _backoff_max_delay: float
    _backoff_max_attempts: Optional[int]
    _backoff_state: dict[str, _BackoffState]

    def __init__(
        self,
        client: ValkeyStreamClient,
        redis_target: RedisTarget,
        args: RedisConsumerArgs,
    ) -> None:
        """
        Initialize the Redis consumer.

        Args:
            client: ValkeyStreamClient for Redis operations
            redis_target: Redis connection configuration (for additional connections)
            stream_keys: Set of Redis stream keys to consume from
            group_name: Consumer group name
            node_id: Node identifier for generating unique consumer ID
            autoclaim_idle_timeout: Timeout for auto-claiming idle messages (ms)
            autoclaim_start_id: Starting ID for auto-claim (default: "0-0")
        """
        self._client = client
        self._consume_queue = asyncio.Queue()
        self._stream_keys = set(args.stream_keys)
        self._group_name = args.group_name
        self._consumer_id = _generate_consumer_id(args.node_id)
        self._redis_target = redis_target
        self._autoclaim_idle_timeout = args.autoclaim_idle_timeout
        self._closed = False

        # Backoff configuration
        self._backoff_initial_delay = args.backoff_initial_delay
        self._backoff_max_delay = args.backoff_max_delay
        self._backoff_max_attempts = args.backoff_max_attempts
        self._backoff_state = {}

        start_id = args.autoclaim_start_id or "0-0"
        self._loop_tasks = []

        # Create background tasks for each stream
        for stream_key in args.stream_keys:
            self._loop_tasks.append(asyncio.create_task(self._read_messages_loop(stream_key)))
            self._loop_tasks.append(
                asyncio.create_task(
                    self._auto_claim_loop(stream_key, start_id, args.autoclaim_idle_timeout)
                )
            )

    @classmethod
    async def create(
        cls,
        redis_target: RedisTarget,
        args: RedisConsumerArgs,
    ) -> Self:
        """
        Create a new RedisConsumer instance.

        Args:
            redis_target: Redis connection configuration
            stream_keys: Set of Redis stream keys to consume from
            group_name: Consumer group name
            node_id: Node identifier for generating unique consumer ID
            db: Redis database number (default: 0)
            autoclaim_idle_timeout: Timeout for auto-claiming idle messages (ms)
            autoclaim_start_id: Starting ID for auto-claim (default: "0-0")

        Returns:
            Configured RedisConsumer instance
        """
        client = await ValkeyStreamClient.create(
            redis_target.to_valkey_target(),
            human_readable_name="redis_consumer",
            db_id=args.db,
        )

        # Create consumer groups if they don't exist
        for stream_key in set(args.stream_keys):
            try:
                await client.make_consumer_group(stream_key, args.group_name)
            except Exception:
                # Group may already exist
                pass

        return cls(
            client,
            redis_target,
            args,
        )

    @override
    async def consume_queue(self) -> AsyncGenerator[MQMessage, None]:  # type: ignore[override]
        """
        Consume messages from the queue.

        This method blocks until messages are available and yields them as they arrive.
        Each message should be acknowledged using the done() method after processing.

        Yields:
            MQMessage: Messages from the streams
        """
        while not self._closed:
            try:
                yield await self._consume_queue.get()
            except asyncio.CancelledError:
                break

    @override
    async def done(self, msg_id: MessageId) -> None:
        """
        Acknowledge that a message has been processed successfully.

        Args:
            msg_id: The message identifier to acknowledge

        Raises:
            MessageQueueClosedError: If the consumer is closed
        """
        if self._closed:
            raise MessageQueueClosedError("Consumer is closed")

        # Note: We acknowledge on the first stream key as the message could be from any stream
        # In practice, msg_id should be unique across streams so this should work
        for stream_key in self._stream_keys:
            try:
                await self._client.done_stream_message(stream_key, self._group_name, msg_id)
                break
            except Exception:
                continue  # Try next stream if this one fails

    @override
    async def close(self) -> None:
        """
        Close the consumer and cleanup resources.

        This cancels all background tasks and closes the Redis client connection.
        """
        if self._closed:
            return

        self._closed = True

        # Cancel all background tasks
        for task in self._loop_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                log.debug("Task {} cancelled", task.get_name())

        await self._client.close()
        log.debug("RedisConsumer closed")

    async def _read_messages_loop(self, stream_key: str) -> None:
        """
        Background task to read messages from a specific stream.

        Args:
            stream_key: The Redis stream key to read from
        """
        log.info("Starting read messages loop for stream {}", stream_key)
        target = self._redis_target.to_valkey_target()
        # Set the request timeout to be longer than the read block time
        target.request_timeout = (_DEFAULT_READ_BLOCK_MS // 1000) + 1  # add 1 second buffer

        client = await ValkeyStreamClient.create(
            target,
            human_readable_name="redis_consumer_reader",
            db_id=REDIS_STREAM_DB,
        )

        try:
            while not self._closed:
                try:
                    await self._read_messages(client, stream_key)
                    self._reset_backoff(stream_key)
                except glide.ClosingError:
                    log.info(
                        "Client connection closed, stopping read messages loop for stream {}",
                        stream_key,
                    )
                    break
                except glide.GlideError as e:
                    await self._failover_consumer(stream_key, e)
                    await self._handle_backoff(stream_key)
                except Exception as e:
                    log.error("Error while reading messages from stream {}: {}", stream_key, e)
                    await self._handle_backoff(stream_key)
        finally:
            await client.close()

    async def _read_messages(self, client: ValkeyStreamClient, stream_key: str) -> None:
        """
        Read messages from a stream and put them in the consume queue.

        Args:
            client: ValkeyStreamClient for reading messages
            stream_key: The Redis stream key to read from
        """
        payload = await client.read_consumer_group(
            stream_key,
            self._group_name,
            self._consumer_id,
            count=_DEFAULT_READ_COUNT,
            block_ms=_DEFAULT_READ_BLOCK_MS,
        )

        if not payload:
            return

        for msg in payload:
            mq_msg = MQMessage(msg_id=msg.msg_id, payload={**msg.payload})
            await self._consume_queue.put(mq_msg)

    async def _auto_claim_loop(
        self, stream_key: str, autoclaim_start_id: str, autoclaim_idle_timeout: int
    ) -> None:
        """
        Background task to automatically claim idle messages.

        Args:
            stream_key: The Redis stream key to auto-claim from
            autoclaim_start_id: Starting ID for auto-claim
            autoclaim_idle_timeout: Timeout for considering messages idle (ms)
        """
        log.debug("Starting auto claim loop for stream {}", stream_key)

        while not self._closed:
            try:
                next_start_id, claimed = await self._auto_claim(
                    stream_key, autoclaim_start_id, autoclaim_idle_timeout
                )
                if claimed:
                    autoclaim_start_id = next_start_id
                    self._reset_backoff(stream_key)
                    continue
            except glide.TimeoutError:
                # If the auto claim times out, we just continue to the next iteration
                pass
            except glide.ClosingError:
                log.info(
                    "Client connection closed, stopping auto claim loop for stream {}", stream_key
                )
                break
            except glide.GlideError as e:
                await self._failover_consumer(stream_key, e)
                await self._handle_backoff(stream_key)
                continue
            except Exception as e:
                log.exception(
                    "Error while auto claiming messages from stream {}: {}", stream_key, e
                )
                await self._handle_backoff(stream_key)
                continue

            await asyncio.sleep(_DEFAULT_AUTOCLAIM_INTERVAL / 1000)

    async def _auto_claim(
        self, stream_key: str, autoclaim_start_id: str, autoclaim_idle_timeout: int
    ) -> tuple[str, bool]:
        """
        Auto-claim idle messages from the stream.

        Args:
            stream_key: The Redis stream key to auto-claim from
            autoclaim_start_id: Starting ID for auto-claim
            autoclaim_idle_timeout: Timeout for considering messages idle (ms)

        Returns:
            Tuple of (next_start_id, claimed_any_messages)
        """
        message = await self._client.auto_claim_stream_message(
            stream_key,
            self._group_name,
            self._consumer_id,
            autoclaim_start_id,
            autoclaim_idle_timeout,
        )

        if message is None:
            return autoclaim_start_id, False

        for msg in message.messages:
            mq_msg = MQMessage(msg.msg_id, {**msg.payload})
            if mq_msg.retry():
                await self._retry_message(stream_key, mq_msg)
                continue
            # Discard the message if retry limit exceeded
            await self._client.done_stream_message(stream_key, self._group_name, mq_msg.msg_id)

        return autoclaim_start_id, len(message.messages) > 0

    async def _retry_message(self, stream_key: str, message: MQMessage) -> None:
        """
        Retry a failed message by re-queuing it.

        Args:
            stream_key: The Redis stream key to retry the message on
            message: The message to retry
        """
        await self._client.reque_stream_message(
            stream_key, self._group_name, message.msg_id, message.payload
        )

    async def _handle_backoff(self, stream_key: str) -> None:
        """
        Handle exponential backoff for a stream.

        Increments attempt counter, calculates delay with jitter, and sleeps.

        Args:
            stream_key: The Redis stream key experiencing connection issues
        """
        if stream_key not in self._backoff_state:
            self._backoff_state[stream_key] = _BackoffState()

        state = self._backoff_state[stream_key]
        state.increment()

        # Calculate delay with exponential backoff
        delay = min(
            self._backoff_initial_delay * (2 ** (state.attempt - 1)),
            self._backoff_max_delay,
        )

        # Add jitter (50-100% of calculated delay)
        actual_delay = delay * (0.5 + random.random() * 0.5)

        await asyncio.sleep(actual_delay)

    def _reset_backoff(self, stream_key: str) -> None:
        """
        Reset backoff state for a stream after successful operation.

        Args:
            stream_key: The Redis stream key that successfully completed operation
        """
        if stream_key in self._backoff_state:
            self._backoff_state[stream_key].reset()

    async def _failover_consumer(self, stream_key: str, e: Exception) -> None:
        """
        Handle consumer failover scenarios.

        Args:
            stream_key: The Redis stream key that caused the error
            e: The exception that occurred
        """
        # If the group does not exist, create it
        if "NOGROUP" in str(e):
            log.warning(
                "Consumer group does not exist. Creating group {} for stream {}",
                self._group_name,
                stream_key,
            )
            try:
                await self._client.make_consumer_group(stream_key, self._group_name)
            except Exception as internal_exception:
                log.exception(
                    "Error while creating consumer group {} for stream {}: {}",
                    self._group_name,
                    stream_key,
                    internal_exception,
                )
        else:
            log.exception("Error while reading messages from stream {}: {}", stream_key, e)


def _generate_consumer_id(node_id: Optional[str]) -> str:
    """
    Generate a unique consumer ID based on node ID, installation path, and process index.

    Args:
        node_id: Optional node identifier

    Returns:
        Unique consumer ID string
    """
    h = hashlib.sha256()
    h.update(str(node_id or socket.getfqdn()).encode("utf8"))
    hostname_hash = h.hexdigest()

    h = hashlib.sha256()
    h.update(__file__.encode("utf8"))
    installation_path_hash = h.hexdigest()

    pidx = process_index.get(0)
    return f"{hostname_hash}:{installation_path_hash}:{pidx}"
