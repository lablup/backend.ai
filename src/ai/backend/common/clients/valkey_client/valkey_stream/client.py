from typing import Mapping, Optional

from glide import (
    GlideClient,
    StreamAddOptions,
    StreamGroupOptions,
    StreamReadGroupOptions,
    TrimByMaxLen,
)

from ai.backend.common.clients.valkey_client.client import ValkeyClient
from ai.backend.common.json import dump_json, load_json

_MAX_STREAM_LENGTH = 128
_DEFAULT_CACHE_EXPIRATION = 60  # 1 minutes


class ValkeyStreamClient(ValkeyClient):
    """
    Client for interacting with Valkey Streams using GlideClient.
    """

    _client: GlideClient
    _is_cluster_mode: bool

    def __init__(self, client: GlideClient, is_cluster_mode: bool) -> None:
        self._client = client
        self._is_cluster_mode = is_cluster_mode

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
    ) -> Optional[Mapping[bytes, bytes]]:
        """
        Read messages from a consumer group.

        :param stream_key: The key of the Valkey stream.
        :param group_name: The name of the consumer group.
        :param consumer_name: The name of the consumer.
        :param count: Number of messages to read.
        :param block_ms: Time to block waiting for messages in milliseconds.
        :return: Mapping of message data or None if no messages are available.
        :raises: GlideClientError if the group does not exist or other errors occur.
        """
        return await self._client.xreadgroup(
            {stream_key: ">"},
            group_name,
            consumer_name,
            StreamReadGroupOptions(block_ms=block_ms, count=count),
        )

    async def done_stream_message(
        self,
        stream_key: str,
        group_name: str,
        message_id: str,
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
        message_id: str,
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
