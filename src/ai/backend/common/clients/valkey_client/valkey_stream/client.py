from dataclasses import dataclass
from typing import List, Mapping, Optional, Self

from glide import (
    GlideClient,
    StreamAddOptions,
    StreamGroupOptions,
    StreamReadGroupOptions,
    TrimByMaxLen,
)

from ai.backend.common import redis_helper
from ai.backend.common.clients.valkey_client.client import ValkeyClient
from ai.backend.common.json import dump_json, load_json
from ai.backend.common.types import RedisTarget

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


class ValkeyStreamClient(ValkeyClient):
    """
    Client for interacting with Valkey Streams using GlideClient.
    """

    _client: GlideClient
    _is_cluster_mode: bool

    def __init__(self, client: GlideClient, is_cluster_mode: bool) -> None:
        self._client = client
        self._is_cluster_mode = is_cluster_mode

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
        await self._client.close()

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
            values,
            StreamAddOptions(
                make_stream=True, trim=TrimByMaxLen(exact=False, threshold=_MAX_STREAM_LENGTH)
            ),
        )

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
            values,
            StreamAddOptions(
                make_stream=True, trim=TrimByMaxLen(exact=False, threshold=_MAX_STREAM_LENGTH)
            ),
        )
        await self._client.exec(tx, raise_on_error=True)

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
        next_start_id: bytes = res[0]
        messages = [
            StreamMessage.from_list(msg_id=key, list_payload=msg) for key, msg in res[1].items()
        ]
        return AutoClaimMessage(
            next_start_id=next_start_id,
            messages=messages,
        )

    async def broadcast(
        self,
        channel: str,
        payload: Mapping[bytes, bytes],
    ) -> None:
        """
        Broadcast a message to a channel.

        :param channel: The channel to broadcast the message to.
        :param payload: The payload of the message.
        :raises: GlideClientError if the message cannot be broadcasted.
        """
        message = dump_json(payload)
        await self._client.publish(message=message, channel=channel)

    async def broadcast_with_cache(
        self,
        channel: str,
        cache_id: str,
        payload: Mapping[bytes, bytes],
        timeout: int = _DEFAULT_CACHE_EXPIRATION,
    ) -> None:
        """
        Broadcast a message to a channel with caching.

        :param channel: The channel to broadcast the message to.
        :param cache_id: The ID for caching the message.
        :param payload: The payload of the message.
        :raises: GlideClientError if the message cannot be broadcasted or cached.
        """
        message = dump_json(payload)
        tx = self._create_batch()
        tx.hset(
            cache_id,
            field_value_map=payload,
        )
        tx.expire(
            cache_id,
            timeout,
        )
        tx.publish(
            message=message,
            channel=channel,
        )
        await self._client.exec(tx, raise_on_error=True)

    async def get_cached_broadcast_message(
        self,
        cache_id: str,
    ) -> Optional[Mapping[bytes, bytes]]:
        """
        Get a cached broadcast message by its ID.

        :param cache_id: The ID of the cached message.
        :return: The cached message payload or None if not found.
        """
        result = await self._client.hgetall(cache_id)
        if not result:
            return None
        return result

    async def receive_broadcast_message(
        self,
    ) -> Mapping[bytes, bytes]:
        """
        Receive a broadcast message from a channel.
        This method blocks until a message is received.

        :return: The payload of the received message.
        """
        message = await self._client.get_pubsub_message()
        return load_json(message.message)

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
        await self._client.delete(key)

    def _container_log_key(self, container_id: str) -> str:
        return f"containerlog.{container_id}"
