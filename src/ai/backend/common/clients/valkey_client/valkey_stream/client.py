import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, List, Mapping, Optional, ParamSpec, Self, TypeVar, cast

from glide import (
    ExpirySet,
    ExpiryType,
    GlideClient,
    StreamAddOptions,
    StreamGroupOptions,
    StreamReadGroupOptions,
    TrimByMaxLen,
)

from ai.backend.common import redis_helper
from ai.backend.common.clients.valkey_client.client import ValkeyClient
from ai.backend.common.exception import UnreachableError
from ai.backend.common.json import dump_json, load_json
from ai.backend.common.metrics.metric import ClientMetricObserver, ClientType
from ai.backend.common.types import RedisTarget
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_MAX_STREAM_LENGTH = 128
_DEFAULT_CACHE_EXPIRATION = 60  # 1 minutes
_DEFAULT_AUTOCLAIM_COUNT = 10


@dataclass
class StreamMessage:
    msg_id: bytes
    payload: Mapping[bytes, bytes]

    @classmethod
    def from_list(cls, msg_id: bytes, list_payload: List[List[bytes]]) -> Self:
        payload = {k: v for k, v in list_payload}
        return cls(msg_id=msg_id, payload=payload)


@dataclass
class AutoClaimMessage:
    next_start_id: bytes
    messages: list[StreamMessage]


P = ParamSpec("P")
R = TypeVar("R")


def valkey_decorator(
    retry_count: int = 3,
    retry_delay: float = 0.1,
) -> Callable[
    [Callable[P, Awaitable[R]]],
    Callable[P, Awaitable[R]],
]:
    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        observer = ClientMetricObserver.instance()

        async def wrapper(*args, **kwargs) -> R:
            log.debug("Calling {} with args: {}, kwargs: {}", func.__name__, args, kwargs)
            start = time.perf_counter()
            for attempt in range(retry_count):
                try:
                    observer.observe_client_operation_triggered(
                        client_type=ClientType.VALKEY,
                        operation=func.__name__,
                    )
                    res = await func(*args, **kwargs)
                    observer.observe_client_operation(
                        client_type=ClientType.VALKEY,
                        operation=func.__name__,
                        success=True,
                        duration=time.perf_counter() - start,
                    )
                    return res
                except Exception as e:
                    log.warning(
                        "Error in {} (attempt {}/{}) with args: {}, kwargs: {}: {}",
                        func.__name__,
                        attempt + 1,
                        retry_count,
                        args,
                        kwargs,
                        e,
                    )
                    if attempt < retry_count - 1:
                        await asyncio.sleep(retry_delay)
                        continue
                    observer.observe_client_operation(
                        client_type=ClientType.VALKEY,
                        operation=func.__name__,
                        success=False,
                        duration=time.perf_counter() - start,
                    )
                    raise e
            raise UnreachableError(
                f"Reached unreachable code in {func.__name__} after {retry_count} attempts"
            )

        return wrapper

    return decorator


class ValkeyStreamClient(ValkeyClient):
    """
    Client for interacting with Valkey Streams using GlideClient.
    """

    _client: GlideClient
    _is_cluster_mode: bool
    _closed: bool

    def __init__(self, client: GlideClient, is_cluster_mode: bool) -> None:
        self._client = client
        self._is_cluster_mode = is_cluster_mode
        self._closed = False

    @classmethod
    async def create(
        cls,
        redis_target: RedisTarget,
        *,
        name: str,
        db: int = 0,
        pubsub_channels: Optional[set[str]] = None,
    ) -> Self:
        """
        Create a ValkeyStreamClient instance.

        :param redis_target: The target Redis server to connect to.
        :param name: The name of the client.
        :param db: The database index to use.
        :param pubsub_channels: Set of channels to subscribe to for pub/sub functionality.
        :return: An instance of ValkeyStreamClient.
        """
        client = await redis_helper.create_valkey_client(
            redis_target=redis_target, name=name, db=db, pubsub_channels=pubsub_channels
        )
        return cls(client=client, is_cluster_mode=redis_target.is_cluster)

    async def close(self) -> None:
        """
        Close the ValkeyStreamClient connection.
        """
        if self._closed:
            log.warning("ValkeyStreamClient is already closed.")
            return
        self._closed = True
        await self._client.close(err_message="ValkeyStreamClient is closed.")

    @valkey_decorator()
    async def make_consumer_group(
        self,
        stream_key: str,
        group_name: str,
    ) -> None:
        """
        Create a consumer group for the specified stream.
        If the stream does not exist, it will be created.

        :param stream_key: The key of the Valkey stream.
        :param group_name: The name of the consumer group to create.
        :raises: GlideClientError if the group already exists.
        """
        await self._client.xgroup_create(
            stream_key, group_name, "$", StreamGroupOptions(make_stream=True)
        )

    @valkey_decorator()
    async def read_consumer_group(
        self,
        stream_key: str,
        group_name: str,
        consumer_name: str,
        count: int = 1,
        block_ms: int = 0,
    ) -> Optional[list[StreamMessage]]:
        """
        Read messages from a consumer group.

        :param stream_key: The key of the Valkey stream.
        :param group_name: The name of the consumer group.
        :param consumer_name: The name of the consumer.
        :param count: Number of messages to read.
        :param block_ms: Time to block waiting for messages in milliseconds.
        :return: A list of messages, each represented as a mapping of bytes to bytes.
        :raises: GlideClientError if the group does not exist or other errors occur.
        """
        result = await self._client.xreadgroup(
            {stream_key: ">"},
            group_name,
            consumer_name,
            StreamReadGroupOptions(block_ms=block_ms, count=count),
        )
        if not result:
            return None
        messages: list[StreamMessage] = []
        for _, payload in result.items():
            if payload is None:
                continue
            for msg_id, msg_data in payload.items():
                if msg_data is None:
                    continue
                messages.append(StreamMessage.from_list(msg_id, msg_data))
        return messages

    @valkey_decorator(retry_count=3, retry_delay=0.1)
    async def done_stream_message(
        self,
        stream_key: str,
        group_name: str,
        message_id: bytes,
    ) -> None:
        """
        Acknowledge a message in the consumer group.

        :param stream_key: The key of the Valkey stream.
        :param group_name: The name of the consumer group.
        :param message_id: The ID of the message to acknowledge.
        :raises: GlideClientError if the message cannot be acknowledged.
        """
        await self._client.xack(stream_key, group_name, [message_id])

    @valkey_decorator()
    async def enqueue_stream_message(
        self,
        stream_key: str,
        payload: Mapping[bytes, bytes],
    ) -> None:
        """
        Enqueue a message to the Valkey stream.

        :param stream_key: The key of the Valkey stream.
        :param payload: The message payload to add to the stream.
        :raises: GlideClientError if the message cannot be added.
        """
        values = [(k, v) for k, v in payload.items()]
        await self._client.xadd(
            stream_key,
            cast(list[tuple[str | bytes, str | bytes]], values),
            StreamAddOptions(
                make_stream=True, trim=TrimByMaxLen(exact=False, threshold=_MAX_STREAM_LENGTH)
            ),
        )

    @valkey_decorator()
    async def reque_stream_message(
        self,
        stream_key: str,
        group_name: str,
        message_id: bytes,
        payload: Mapping[bytes, bytes],
    ) -> None:
        """
        Requeue a message in the consumer group.

        :param stream_key: The key of the Valkey stream.
        :param group_name: The name of the consumer group.
        :param message_id: The ID of the message to requeue.
        :param payload: The payload to re-add to the stream.
        :raises: GlideClientError if the message cannot be requeued.
        """
        tx = self._create_batch(is_atomic=True)
        tx.xack(stream_key, group_name, [message_id])
        values = [(k, v) for k, v in payload.items()]
        tx.xadd(
            stream_key,
            cast(list[tuple[str | bytes, str | bytes]], values),
            StreamAddOptions(
                make_stream=True, trim=TrimByMaxLen(exact=False, threshold=_MAX_STREAM_LENGTH)
            ),
        )
        await self._client.exec(tx, raise_on_error=True)

    @valkey_decorator()
    async def auto_claim_stream_message(
        self,
        stream_key: str,
        group_name: str,
        consumer_name: str,
        start_id: str,
        min_idle_timeout: int,
        count: int = _DEFAULT_AUTOCLAIM_COUNT,
    ) -> Optional[AutoClaimMessage]:
        """
        Auto claim messages from a stream for a consumer group.

        :param stream_key: The key of the Valkey stream.
        :param group_name: The name of the consumer group.
        :param consumer_name: The name of the consumer.
        :param start_id: The ID to start claiming from.
        :param min_idle_timeout: Minimum idle time in milliseconds to consider a message for claiming.
        :param count: Maximum number of messages to claim.
        :return: An AutoClaimMessage containing the next start ID and claimed messages, or None if no messages are available.
        :raises: GlideClientError if the group does not exist or other errors occur.
        """
        res = await self._client.xautoclaim(
            key=stream_key,
            group_name=group_name,
            consumer_name=consumer_name,
            start=start_id,
            min_idle_time_ms=min_idle_timeout,
            count=count,
        )
        if len(res) < 2:
            return None
        next_start_id = cast(bytes, res[0])
        msgs = cast(Mapping[bytes, List[List[bytes]]], res[1])
        messages = [
            StreamMessage.from_list(msg_id=key, list_payload=msg) for key, msg in msgs.items()
        ]
        return AutoClaimMessage(
            next_start_id=next_start_id,
            messages=messages,
        )

    @valkey_decorator()
    async def broadcast(
        self,
        channel: str,
        payload: Mapping[str, Any],
    ) -> None:
        """
        Broadcast a message to a channel.

        :param channel: The channel to broadcast the message to.
        :param payload: The payload of the message.
        :raises: GlideClientError if the message cannot be broadcasted.
        """
        message = dump_json(payload)
        await self._client.publish(message=message, channel=channel)

    @valkey_decorator()
    async def broadcast_with_cache(
        self,
        channel: str,
        cache_id: str,
        payload: Mapping[str, Any],
        timeout: int = _DEFAULT_CACHE_EXPIRATION,
    ) -> None:
        """
        Broadcast a message to a channel with caching.

        :param channel: The channel to broadcast the message to.
        :param cache_id: The ID for caching the message.
        :param payload: The payload of the message.
        :param timeout: The expiration time for the cached message in seconds.
        :raises: GlideClientError if the message cannot be broadcasted or cached.
        """
        message = dump_json(payload)
        tx = self._create_batch()
        tx.set(key=cache_id, value=message, expiry=ExpirySet(ExpiryType.SEC, timeout))
        tx.publish(
            message=message,
            channel=channel,
        )
        await self._client.exec(tx, raise_on_error=True)

    @valkey_decorator()
    async def fetch_cached_broadcast_message(
        self,
        cache_id: str,
    ) -> Optional[Mapping[bytes, bytes]]:
        """
        Fetch a cached broadcast message by its ID.

        :param cache_id: The ID of the cached message.
        :return: The cached message payload or None if not found.
        """
        result = await self._client.hgetall(cache_id)
        if not result:
            return None
        return result

    @valkey_decorator()
    async def receive_broadcast_message(
        self,
    ) -> Mapping[str, str]:
        """
        Receive a broadcast message from a channel.
        This method blocks until a message is received.

        :return: The payload of the received message.
        """
        message = await self._client.get_pubsub_message()
        return load_json(message.message)

    @valkey_decorator()
    async def enqueue_container_logs(
        self,
        container_id: str,
        logs: bytes,
    ) -> None:
        """
        Enqueue logs for a specific container.
        TODO: Replace with a more efficient log storage solution.

        :param container_id: The ID of the container.
        :param logs: The logs to enqueue.
        :raises: GlideClientError if the logs cannot be enqueued.
        """
        key = self._container_log_key(container_id)
        tx = self._create_batch(is_atomic=True)
        tx.rpush(
            key,
            [logs],
        )
        tx.expire(
            key,
            3600,  # 1 hour expiration
        )
        await self._client.exec(tx, raise_on_error=True)

    @valkey_decorator()
    async def container_log_len(
        self,
        container_id: str,
    ) -> int:
        """
        Get the length of logs for a specific container.

        :param container_id: The ID of the container.
        :return: The number of logs for the container.
        :raises: GlideClientError if the length cannot be retrieved.
        """
        key = self._container_log_key(container_id)
        return await self._client.llen(key)

    @valkey_decorator()
    async def pop_container_logs(
        self,
        container_id: str,
        count: int = 1,
    ) -> Optional[list[bytes]]:
        """
        Pop logs for a specific container.

        :param container_id: The ID of the container.
        :return: List of logs for the container.
        :raises: GlideClientError if the logs cannot be popped.
        """
        key = self._container_log_key(container_id)
        return await self._client.lpop_count(key, count)

    @valkey_decorator()
    async def clear_container_logs(
        self,
        container_id: str,
    ) -> None:
        """
        Clear logs for a specific container.

        :param container_id: The ID of the container.
        :raises: GlideClientError if the logs cannot be cleared.
        """
        key = self._container_log_key(container_id)
        await self._client.delete([key])

    def _container_log_key(self, container_id: str) -> str:
        return f"containerlog.{container_id}"
