import logging
from typing import (
    Any,
    List,
    Mapping,
    Optional,
    Self,
    cast,
)

from glide import Batch, ConditionalChange, ExpirySet, ExpiryType, ScoreBoundary

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_valkey_client,
    valkey_decorator,
)
from ai.backend.common.types import RedisTarget
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_EXPIRATION = 3600  # 1 hour default expiration


class ValkeyLiveClient:
    """
    Client for interacting with Valkey for live status tracking and service discovery.
    This client provides high-level operations for scheduler and manager components.
    """

    _client: AbstractValkeyClient
    _closed: bool

    def __init__(self, client: AbstractValkeyClient) -> None:
        self._client = client
        self._closed = False

    @classmethod
    async def create(
        cls,
        redis_target: RedisTarget,
        *,
        db_id: int,
        human_readable_name: str,
        pubsub_channels: Optional[set[str]] = None,
    ) -> Self:
        """
        Create a ValkeyLiveClient instance.

        :param redis_target: The target Redis server to connect to.
        :param db_id: The database index to use.
        :param human_readable_name: The name of the client.
        :param pubsub_channels: Set of channels to subscribe to for pub/sub functionality.
        :return: An instance of ValkeyLiveClient.
        """
        client = create_valkey_client(
            target=redis_target,
            db_id=db_id,
            human_readable_name=human_readable_name,
            pubsub_channels=pubsub_channels,
        )
        await client.connect()
        return cls(client=client)

    async def close(self) -> None:
        """
        Close the ValkeyLiveClient connection.
        """
        if self._closed:
            log.warning("ValkeyLiveClient is already closed.")
            return
        self._closed = True
        await self._client.disconnect()

    # Internal methods (no decorator)
    async def _get(self, key: str) -> Optional[bytes]:
        """Internal method to get value by key."""
        return await self._client.client.get(key)

    async def _set(
        self,
        key: str,
        value: str | bytes,
        *,
        ex: Optional[int] = None,
        xx: Optional[bool] = None,
    ) -> None:
        """Internal method to set value for key with optional expiration."""
        expiry = None
        if ex is not None:
            expiry = ExpirySet(ExpiryType.SEC, ex)
        elif ex is None:
            # Set default expiration when no expire is specified
            expiry = ExpirySet(ExpiryType.SEC, _DEFAULT_EXPIRATION)

        conditional_set = ConditionalChange.ONLY_IF_EXISTS if xx else None
        await self._client.client.set(key, value, conditional_set=conditional_set, expiry=expiry)

    async def _delete(self, keys: str | List[str]) -> int:
        """Internal method to delete one or more keys."""
        if isinstance(keys, str):
            keys = [keys]
        return await self._client.client.delete(cast(List[str | bytes], keys))

    async def _time(self) -> tuple[int, int]:
        """Internal method to get server time."""
        result = await self._client.client.time()
        if isinstance(result, list) and len(result) == 2:
            return (int(result[0]), int(result[1]))
        return cast(tuple[int, int], result)

    async def _count_sorted_set_members(
        self,
        name: str,
        min_score: int | float | str,
        max_score: int | float | str,
    ) -> int:
        """Internal method to count members in sorted set within score range."""
        return await self._client.client.zcount(
            name, ScoreBoundary(float(min_score)), ScoreBoundary(float(max_score))
        )

    async def _hset(
        self,
        name: str,
        key: Optional[str] = None,
        value: Optional[str | bytes] = None,
        *,
        mapping: Optional[Mapping[str, str | bytes]] = None,
    ) -> int:
        """Internal method to set hash field(s)."""
        if mapping is not None:
            return await self._client.client.hset(
                name, cast(Mapping[str | bytes, str | bytes], mapping)
            )
        elif key is not None and value is not None:
            return await self._client.client.hset(name, {key: value})
        else:
            raise ValueError("Either provide key/value or mapping")

    # Public methods for specific use cases (with decorator)
    @valkey_decorator()
    async def get_live_data(self, key: str) -> Optional[bytes]:
        """Get live data value by key."""
        return await self._get(key)

    @valkey_decorator()
    async def get(self, key: str) -> Optional[bytes]:
        """Get value by key (deprecated: use get_live_data)."""
        return await self._get(key)

    @valkey_decorator()
    async def store_live_data(
        self,
        key: str,
        value: str | bytes,
        *,
        ex: Optional[int] = None,
        xx: Optional[bool] = None,
    ) -> None:
        """Store live data value for key with optional expiration."""
        await self._set(key, value, ex=ex, xx=xx)

    @valkey_decorator()
    async def set(
        self,
        key: str,
        value: str | bytes,
        *,
        ex: Optional[int] = None,
        xx: Optional[bool] = None,
    ) -> None:
        """Set value for key with optional expiration (deprecated: use store_live_data)."""
        await self._set(key, value, ex=ex, xx=xx)

    @valkey_decorator()
    async def delete(self, keys: str | List[str]) -> int:
        """Delete one or more keys."""
        return await self._delete(keys)

    @valkey_decorator()
    async def time(self) -> tuple[int, int]:
        """Get server time."""
        return await self._time()

    @valkey_decorator()
    async def count_active_connections(self, session_id: str) -> int:
        """Count active connections for a session."""
        return await self._count_sorted_set_members(
            f"session.{session_id}.active_app_connections",
            float("-inf"),
            float("+inf"),
        )

    @valkey_decorator()
    async def store_scheduler_metadata(
        self,
        name: str,
        key: Optional[str] = None,
        value: Optional[str | bytes] = None,
        *,
        mapping: Optional[Mapping[str, str | bytes]] = None,
    ) -> int:
        """Store scheduler metadata in hash fields."""
        return await self._hset(name, key, value, mapping=mapping)

    @valkey_decorator()
    async def hset(
        self,
        name: str,
        key: Optional[str] = None,
        value: Optional[str | bytes] = None,
        *,
        mapping: Optional[Mapping[str, str | bytes]] = None,
    ) -> int:
        """Set hash field(s) for scheduler operations (deprecated: use store_scheduler_metadata)."""
        return await self._hset(name, key, value, mapping=mapping)

    def create_batch(self, is_atomic: bool = False) -> "ValkeyLiveBatch":
        """
        Create a batch for pipeline operations.

        :param is_atomic: Whether the batch should be atomic (transaction).
        :return: A ValkeyLiveBatch instance.
        """
        return ValkeyLiveBatch(Batch(is_atomic=is_atomic))

    @valkey_decorator()
    async def execute_batch(self, batch: "ValkeyLiveBatch") -> Any:
        """
        Execute a batch of commands.

        :param batch: The batch to execute.
        :return: List of command results.
        """
        return await self._client.client.exec(batch._batch, raise_on_error=True)

    @valkey_decorator()
    async def get_multiple_keys(self, keys: List[str]) -> List[bytes | None]:
        """
        Get multiple keys in a single batch operation.

        :param keys: List of keys to get.
        :return: List of values corresponding to the keys.
        """
        if not keys:
            return []

        batch = self.create_batch()
        for key in keys:
            batch.get(key)

        results = await self.execute_batch(batch)
        return results

    @valkey_decorator()
    async def update_connection_tracker(
        self,
        tracker_key: str,
        tracker_value: str,
    ) -> None:
        """
        Update connection tracker with current timestamp.

        :param tracker_key: The key for the connection tracker sorted set.
        :param tracker_value: The value to add to the tracker.
        """
        # Get current server time
        time_result = await self._time()
        current_time = time_result[0] + (time_result[1] / 1000000)

        # Add to sorted set with timestamp as score
        await self._client.client.zadd(tracker_key, {tracker_value: current_time})


class ValkeyLiveBatch:
    """
    Batch operations wrapper for ValkeyLiveClient.
    This provides high-level batch operations for scheduler operations.
    """

    def __init__(self, batch: Batch) -> None:
        self._batch = batch

    def get(self, key: str) -> None:
        """
        Add get operation to batch.

        :param key: The key to get.
        """
        self._batch.get(key)

    def delete(self, keys: str | List[str]) -> None:
        """
        Add delete operation to batch.

        :param keys: The key(s) to delete.
        """
        if isinstance(keys, str):
            keys = [keys]
        self._batch.delete(cast(List[str | bytes], keys))

    def store_scheduler_metadata(
        self,
        name: str,
        mapping: Mapping[str, str | bytes],
    ) -> None:
        """
        Add scheduler metadata storage operation to batch.

        :param name: The name of the hash.
        :param mapping: Dictionary of field-value pairs.
        """
        self._batch.hset(name, cast(Mapping[str | bytes, str | bytes], mapping))

    def hset(
        self,
        name: str,
        mapping: Mapping[str, str | bytes],
    ) -> None:
        """
        Add hash set operation to batch (deprecated: use store_scheduler_metadata).

        :param name: The name of the hash.
        :param mapping: Dictionary of field-value pairs.
        """
        self._batch.hset(name, cast(Mapping[str | bytes, str | bytes], mapping))
