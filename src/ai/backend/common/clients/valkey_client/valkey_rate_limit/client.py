import logging
import time
from decimal import Decimal
from typing import Final, Optional, Self, cast

from glide import Batch, ExpirySet, ExpiryType, ScoreBoundary, Script

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_layer_aware_valkey_decorator,
    create_valkey_client,
)
from ai.backend.common.metrics.metric import LayerType
from ai.backend.common.types import ValkeyTarget
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Layer-specific decorator for valkey_rate_limit client
valkey_decorator = create_layer_aware_valkey_decorator(LayerType.VALKEY_RATE_LIMIT)

_DEFAULT_RATE_LIMIT_EXPIRATION = 60 * 15  # 15 minutes
_TIME_PRECISION = Decimal("1e-3")  # milliseconds


_RATE_LIMIT_SCRIPT: Final[str] = """
local access_key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local request_id = tonumber(redis.call('INCR', '__request_id'))
if request_id >= 1e12 then
    redis.call('SET', '__request_id', 1)
end
if redis.call('EXISTS', access_key) == 1 then
    redis.call('ZREMRANGEBYSCORE', access_key, 0, now - window)
end
redis.call('ZADD', access_key, now, tostring(request_id))
redis.call('EXPIRE', access_key, window)
return redis.call('ZCARD', access_key)
"""


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
        valkey_target: ValkeyTarget,
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
            valkey_target=valkey_target,
            db_id=db_id,
            human_readable_name=human_readable_name,
        )
        await client.connect()
        return cls(client=client)

    @valkey_decorator()
    async def close(self) -> None:
        """
        Close the ValkeyRateLimitClient connection.
        """
        if self._closed:
            log.debug("ValkeyRateLimitClient is already closed.")
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
        result = await self._client.client.invoke_script(
            Script(_RATE_LIMIT_SCRIPT),
            keys=[access_key],
            args=[str(now_float), str(window)],
        )

        # The last result is the count
        count = cast(int, result)
        return count

    @valkey_decorator()
    async def get_rolling_count(self, access_key: str) -> int:
        """
        Get the current rolling count for an access key.

        :param access_key: The access key to get the count for.
        :return: The current count.
        """
        return await self._client.client.zcard(access_key)

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
        tx = self._create_batch()
        tx.incr(key)
        tx.expire(key, expiration)
        results = await self._client.client.exec(tx, raise_on_error=True)
        # Handle the result properly by extracting the first result
        if results and len(results) > 0:
            return cast(int, results[0])
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
        tx = self._create_batch()
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
