import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional, Self, cast

from glide import (
    Batch,
    ExpirySet,
    ExpiryType,
    StreamAddOptions,
    StreamGroupOptions,
    StreamReadGroupOptions,
    TrimByMaxLen,
)
from glide.exceptions import TimeoutError as GlideTimeoutError

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_layer_aware_valkey_decorator,
    create_valkey_client,
)
from ai.backend.common.json import dump_json, load_json
from ai.backend.common.message_queue.types import BroadcastPayload
from ai.backend.common.metrics.metric import LayerType
from ai.backend.common.types import ValkeyTarget
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Layer-specific decorator for valkey_stream client
valkey_decorator = create_layer_aware_valkey_decorator(LayerType.VALKEY_STREAM)

_MAX_STREAM_LENGTH = 128
_DEFAULT_CACHE_EXPIRATION = 300  # 5 minutes
_DEFAULT_AUTOCLAIM_COUNT = 10


@dataclass
class StreamMessage:
    msg_id: bytes
    payload: Mapping[bytes, bytes]

    @classmethod
    def from_list(cls, msg_id: bytes, list_payload: list[list[bytes]]) -> Self:
        payload = {k: v for k, v in list_payload}
        return cls(msg_id=msg_id, payload=payload)


@dataclass
class AutoClaimMessage:
    next_start_id: bytes
    messages: list[StreamMessage]


class ValkeyStreamClient:
    """
    Client for interacting with Valkey Streams using GlideClient.
    """

    _client: AbstractValkeyClient
    _closed: bool

    def __init__(self, client: AbstractValkeyClient) -> None:
        self._client = client
        self._closed = False

    @classmethod
    async def create(
        cls,
        valkey_target: ValkeyTarget,
        *,
        db_id: int,
        human_readable_name: str,
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
        client = create_valkey_client(
            valkey_target=valkey_target,
            db_id=db_id,
            human_readable_name=human_readable_name,
            pubsub_channels=pubsub_channels,
        )
        await client.connect()
        return cls(client=client)

    @valkey_decorator()
    async def close(self) -> None:
        """
        Close the ValkeyStreamClient connection.
        """
        if self._closed:
            log.debug("ValkeyStreamClient is already closed.")
            return
        self._closed = True
        await self._client.disconnect()

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
        await self._client.client.xgroup_create(
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
        try:
            result = await self._client.client.xreadgroup(
                {stream_key: ">"},
                group_name,
                consumer_name,
                StreamReadGroupOptions(block_ms=block_ms, count=count),
            )
        except GlideTimeoutError:
            return None
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
        await self._client.client.xack(stream_key, group_name, [message_id])

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
        await self._client.client.xadd(
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
        tx = self._create_batch()
        tx.xack(stream_key, group_name, [message_id])
        values = [(k, v) for k, v in payload.items()]
        tx.xadd(
            stream_key,
            cast(list[tuple[str | bytes, str | bytes]], values),
            StreamAddOptions(
                make_stream=True, trim=TrimByMaxLen(exact=False, threshold=_MAX_STREAM_LENGTH)
            ),
        )
        await self._client.client.exec(tx, raise_on_error=True)

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
        res = await self._client.client.xautoclaim(
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
        msgs = cast(Mapping[bytes, list[list[bytes]]], res[1])
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
        await self._client.client.publish(message=message, channel=channel)

    @valkey_decorator()
    async def broadcast_with_cache(
        self,
        channel: str,
        cache_id: str,
        payload: Mapping[str, str],
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
        await self._client.client.exec(tx, raise_on_error=True)

    @valkey_decorator()
    async def fetch_cached_broadcast_message(
        self,
        cache_id: str,
    ) -> Optional[Mapping[str, str]]:
        """
        Fetch a cached broadcast message by its ID.

        :param cache_id: The ID of the cached message.
        :return: The cached message payload or None if not found.
        """
        result = await self._client.client.get(cache_id)
        if not result:
            return None
        payload = load_json(result)
        return cast(Mapping[str, str], payload)

    @valkey_decorator()
    async def broadcast_batch(
        self,
        channel: str,
        events: list[BroadcastPayload],
        timeout: int = _DEFAULT_CACHE_EXPIRATION,
    ) -> None:
        """
        Broadcast multiple messages to a channel in a batch with optional caching.

        :param channel: The channel to broadcast the messages to.
        :param events: List of BroadcastPayload objects containing payload and optional cache_id.
        :param timeout: The expiration time for the cached messages in seconds.
        :raises: GlideClientError if the messages cannot be broadcasted or cached.
        """
        if not events:
            return

        tx = self._create_batch()
        for event in events:
            message = dump_json(event.payload)
            # Only set cache if cache_id is provided
            if event.cache_id:
                tx.set(key=event.cache_id, value=message, expiry=ExpirySet(ExpiryType.SEC, timeout))
            tx.publish(
                message=message,
                channel=channel,
            )
        await self._client.client.exec(tx, raise_on_error=True)

    @valkey_decorator()
    async def receive_broadcast_message(
        self,
    ) -> Mapping[str, str]:
        """
        Receive a broadcast message from a channel.
        This method blocks until a message is received.

        :return: The payload of the received message.
        """
        message = await self._client.client.get_pubsub_message()
        return load_json(message.message)

    def _create_batch(self, is_atomic: bool = False) -> Batch:
        """
        Create a batch object for batch operations.

        :param is_atomic: Whether the batch should be atomic (transaction-like).
        :return: A Batch object.
        """
        return Batch(is_atomic=is_atomic)
