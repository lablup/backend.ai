import logging
import time
from decimal import Decimal
from typing import Optional, Self

from glide import Batch, ExpirySet, ExpiryType, ScoreBoundary

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_valkey_client,
    valkey_decorator,
)
from ai.backend.common.types import RedisTarget
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_RATE_LIMIT_EXPIRATION = 60 * 15  # 15 minutes
_TIME_PRECISION = Decimal("1e-3")  # milliseconds


class ValkeyRateLimitClient:
    """
    Client for rate limiting operations using Valkey.
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
        Create a ValkeyRateLimitClient instance.

        :param redis_target: The target Redis server to connect to.
        :param db_id: The database index to use.
        :param human_readable_name: The human-readable name of the client.
        :return: An instance of ValkeyRateLimitClient.
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
        Close the ValkeyRateLimitClient connection.
        """
        if self._closed:
            log.warning("ValkeyRateLimitClient is already closed.")
            return
        self._closed = True
        await self._client.disconnect()

    @valkey_decorator()
    async def execute_rate_limit_logic(
        self,
        access_key: str,
        window: int = _DEFAULT_RATE_LIMIT_EXPIRATION,
    ) -> int:
        """
        Execute the rate limiting logic for rolling counter.
        This replicates the Lua script logic using individual commands.

        :param access_key: The access key to rate limit.
        :param window: The time window for rate limiting in seconds.
        :return: The current count.
        """
        now = Decimal(time.time()).quantize(_TIME_PRECISION)
        now_float = float(now)

        # Increment request ID counter
        request_id = await self._client.client.incr("__request_id")
        if request_id >= 1e12:
            await self._client.client.set("__request_id", "1")
            request_id = 1

        # Use batch for atomicity
        tx = self._create_batch(is_atomic=True)

        # Remove expired entries
        tx.zremrangebyscore(
            access_key,
            ScoreBoundary(0),
            ScoreBoundary(now_float - window),
        )

        # Add current request
        tx.zadd(access_key, {str(request_id): now_float})

        # Set expiration
        tx.expire(access_key, window)

        # Get current count
        tx.zcard(access_key)

        results = await self._client.client.exec(tx, raise_on_error=True)

        # The last result is the count
        count = results[-1] if results else 0
        if isinstance(count, (int, str)):
            return int(count)
        return 0

    @valkey_decorator()
    async def get_rolling_count(self, access_key: str) -> int:
        """
        Get the current rolling count for an access key.

        :param access_key: The access key to get the count for.
        :return: The current count.
        """
        result = await self._client.client.zcard(access_key)
        if isinstance(result, (int, str)):
            return int(result)
        return 0

    @valkey_decorator()
    async def set_rate_limit_config(
        self,
        key: str,
        value: str,
        expiration: int = _DEFAULT_RATE_LIMIT_EXPIRATION,
    ) -> None:
        """
        Set rate limit configuration with expiration time.

        :param key: The key to set.
        :param value: The configuration value to set.
        :param expiration: The expiration time in seconds.
        """
        await self._client.client.set(
            key=key,
            value=value,
            expiry=ExpirySet(ExpiryType.SEC, expiration),
        )

    @valkey_decorator()
    async def set_with_expiration(
        self,
        key: str,
        value: str,
        expiration: int = _DEFAULT_RATE_LIMIT_EXPIRATION,
    ) -> None:
        """
        Set a key with expiration time (deprecated: use set_rate_limit_config).

        :param key: The key to set.
        :param value: The value to set.
        :param expiration: The expiration time in seconds.
        """
        await self._client.client.set(
            key=key,
            value=value,
            expiry=ExpirySet(ExpiryType.SEC, expiration),
        )

    @valkey_decorator()
    async def increment_with_expiration(
        self,
        key: str,
        expiration: int = _DEFAULT_RATE_LIMIT_EXPIRATION,
    ) -> int:
        """
        Increment a key and set expiration if it doesn't exist.

        :param key: The key to increment.
        :param expiration: The expiration time in seconds.
        :return: The new value after increment.
        """
        tx = self._create_batch(is_atomic=True)
        tx.incr(key)
        tx.expire(key, expiration)
        results = await self._client.client.exec(tx, raise_on_error=True)
        # Handle the result properly by extracting the first result
        if results and len(results) > 0:
            result = results[0]
            if isinstance(result, (int, str)):
                return int(result)
        return 0

    @valkey_decorator()
    async def get_rate_limit_data(self, key: str) -> Optional[str]:
        """
        Get rate limit data by key.

        :param key: The key to get.
        :return: The rate limit data or None if not found.
        """
        result = await self._client.client.get(key)
        return result.decode("utf-8") if result else None

    @valkey_decorator()
    async def get_key(self, key: str) -> Optional[str]:
        """
        Get the value of a key (deprecated: use get_rate_limit_data).

        :param key: The key to get.
        :return: The value or None if not found.
        """
        result = await self._client.client.get(key)
        return result.decode("utf-8") if result else None

    @valkey_decorator()
    async def delete_key(self, key: str) -> bool:
        """
        Delete a key.

        :param key: The key to delete.
        :return: True if the key was deleted, False otherwise.
        """
        result = await self._client.client.delete([key])
        return result > 0

    @valkey_decorator()
    async def flush_database(self) -> None:
        """
        Flush all keys in the current database.
        """
        await self._client.client.flushdb()

    @valkey_decorator()
    async def remove_expired_entries(
        self,
        key: str,
        now: float,
        window: int = _DEFAULT_RATE_LIMIT_EXPIRATION,
    ) -> None:
        """
        Remove expired entries from a sorted set.

        :param key: The sorted set key.
        :param now: The current timestamp.
        :param window: The time window in seconds.
        """
        cutoff_time = now - window
        await self._client.client.zremrangebyscore(
            key, ScoreBoundary(0), ScoreBoundary(cutoff_time)
        )

    @valkey_decorator()
    async def add_to_sorted_set_with_expiration(
        self,
        key: str,
        score: float,
        member: str,
        expiration: int = _DEFAULT_RATE_LIMIT_EXPIRATION,
    ) -> None:
        """
        Add a member to a sorted set with expiration.

        :param key: The sorted set key.
        :param score: The score for the member.
        :param member: The member to add.
        :param expiration: The expiration time in seconds.
        """
        tx = self._create_batch(is_atomic=True)
        tx.zadd(key, {member: score})
        tx.expire(key, expiration)
        await self._client.client.exec(tx, raise_on_error=True)

    def _create_batch(self, is_atomic: bool = False) -> Batch:
        """
        Create a batch for transaction operations.

        :param is_atomic: Whether the batch should be atomic.
        :return: A Batch instance.
        """
        return Batch(is_atomic=is_atomic)
