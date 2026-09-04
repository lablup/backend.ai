import logging
from dataclasses import dataclass
from typing import Final, Self, cast

from glide import Batch, ExpireOptions

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_valkey_client,
)
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.exception import BackendAIError, UnreachableError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience import (
    BackoffStrategy,
    MetricArgs,
    MetricPolicy,
    Resilience,
    RetryArgs,
    RetryPolicy,
)
from ai.backend.common.types import ValkeyTarget
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Resilience instance for valkey_rate_limit layer
valkey_rate_limit_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.VALKEY, layer=LayerType.VALKEY_RATE_LIMIT)),
        RetryPolicy(
            RetryArgs(
                max_retries=3,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.FIXED,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)

_DEFAULT_RATE_LIMIT_WINDOW: Final = 60 * 15


@dataclass(frozen=True)
class RateLimitState:
    count: int
    reset: int


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

    @valkey_rate_limit_resilience.apply()
    async def close(self) -> None:
        """
        Close the ValkeyRateLimitClient connection.
        """
        if self._closed:
            log.debug("ValkeyRateLimitClient is already closed.")
            return
        self._closed = True
        await self._client.disconnect()

    @valkey_rate_limit_resilience.apply()
    async def count_request(
        self,
        user_id: UserID,
        window: int = _DEFAULT_RATE_LIMIT_WINDOW,
    ) -> RateLimitState:
        """
        Count a request against the user's current window and return its state.

        :param user_id: The user the counter is keyed by.
        :param window: The window length in seconds, applied when the request opens a window.
        :return: The count and the seconds until the window ends.
        """
        key = f"user.{user_id}"
        batch = Batch(is_atomic=True)
        batch.hincrby(key, "count", 1)
        batch.expire(key, window, ExpireOptions.HasNoExpiry)
        batch.ttl(key)
        async with self._client.client() as conn:
            results = await conn.exec(batch, raise_on_error=True)
        if results is None:
            raise UnreachableError("an atomic batch without WATCH cannot be aborted")
        count, _, reset = results
        return RateLimitState(count=cast(int, count), reset=cast(int, reset))

    @valkey_rate_limit_resilience.apply()
    async def get_state(self, user_id: UserID) -> RateLimitState | None:
        """
        Read the user's current window without counting a request.

        :param user_id: The user the counter is keyed by.
        :return: The window state, or None when no window is open for the user.
        """
        key = f"user.{user_id}"
        batch = Batch(is_atomic=True)
        batch.hget(key, "count")
        batch.ttl(key)
        async with self._client.client() as conn:
            results = await conn.exec(batch, raise_on_error=True)
        if results is None:
            return None
        count, reset = results
        if count is None:
            return None
        return RateLimitState(count=int(cast(bytes, count)), reset=cast(int, reset))

    @valkey_rate_limit_resilience.apply()
    async def delete_key(self, key: str) -> bool:
        """
        Delete a key.

        :param key: The key to delete.
        :return: True if the key was deleted, False otherwise.
        """
        async with self._client.client() as conn:
            result = await conn.delete([key])
        return result > 0

    @valkey_rate_limit_resilience.apply()
    async def flush_database(self) -> None:
        """
        Flush all keys in the current database.
        """
        async with self._client.client() as conn:
            await conn.flushdb()
