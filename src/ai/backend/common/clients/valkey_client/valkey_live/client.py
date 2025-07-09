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
    This client provides domain-specific operations for scheduler and manager components.
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

    @valkey_decorator()
    async def get_live_data(self, key: str) -> Optional[bytes]:
        """Get live data value by key."""
        return await self._client.client.get(key)

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
        expiry = None
        if ex is not None:
            expiry = ExpirySet(ExpiryType.SEC, ex)
        elif ex is None:
            expiry = ExpirySet(ExpiryType.SEC, _DEFAULT_EXPIRATION)

        conditional_set = ConditionalChange.ONLY_IF_EXISTS if xx else None
        await self._client.client.set(key, value, conditional_set=conditional_set, expiry=expiry)

    @valkey_decorator()
    async def delete_live_data(self, keys: str | List[str]) -> int:
        """Delete live data keys."""
        if isinstance(keys, str):
            keys = [keys]
        return await self._client.client.delete(cast(List[str | bytes], keys))

    @valkey_decorator()
    async def get_server_time(self) -> float:
        """Get server time as float timestamp."""
        result = await self._client.client.time()
        if len(result) != 2:
            raise ValueError(
                f"Unexpected result from time command: {result}. Expected a tuple of (seconds, microseconds)."
            )
        seconds_bytes, microseconds_bytes = result
        seconds = cast(int, seconds_bytes)
        microseconds = cast(int, microseconds_bytes)
        return seconds + (microseconds / 10**6)

    @valkey_decorator()
    async def count_active_connections(self, session_id: str) -> int:
        """Count active connections for a session."""
        return await self._client.client.zcount(
            f"session.{session_id}.active_app_connections",
            ScoreBoundary(float("-inf")),
            ScoreBoundary(float("+inf")),
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
        if mapping is not None:
            return await self._client.client.hset(
                name, cast(Mapping[str | bytes, str | bytes], mapping)
            )
        elif key is not None and value is not None:
            return await self._client.client.hset(name, {key: value})
        else:
            raise ValueError("Either provide key/value or mapping")

    def _create_batch(self, is_atomic: bool = False) -> Batch:
        """
        Create a batch for pipeline operations (internal use only).

        :param is_atomic: Whether the batch should be atomic (transaction).
        :return: A Batch instance.
        """
        return Batch(is_atomic=is_atomic)

    async def _execute_batch(self, batch: Batch) -> Any:
        """
        Execute a batch of commands (internal use only).

        :param batch: The batch to execute.
        :return: List of command results.
        """
        return await self._client.client.exec(batch, raise_on_error=True)

    @valkey_decorator()
    async def get_multiple_live_data(self, keys: List[str]) -> List[bytes | None]:
        """
        Get multiple live data keys in a single batch operation.

        :param keys: List of keys to get.
        :return: List of values corresponding to the keys.
        """
        if not keys:
            return []

        batch = self._create_batch()
        for key in keys:
            batch.get(key)

        results = await self._execute_batch(batch)
        return results

    @valkey_decorator()
    async def update_connection_tracker(
        self,
        session_id: str,
        connection_id: str,
    ) -> None:
        """
        Update connection tracker with current timestamp.

        :param session_id: The session ID to track connections for.
        :param connection_id: The connection ID to add/update.
        """
        current_time = await self.get_server_time()
        tracker_key = f"session.{session_id}.active_app_connections"
        await self._client.client.zadd(tracker_key, {connection_id: current_time})
