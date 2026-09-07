import logging
from dataclasses import dataclass
from typing import Self, cast

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


@dataclass(frozen=True)
class RateLimitState:
    count: int
    limit: int
    reset_after_seconds: int


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

    def _user_window_key(self, user_id: UserID) -> str:
        return f"user.{user_id}.rate_limit_window"

    def _ip_window_key(self, client_ip: str) -> str:
        return f"ip.{client_ip}.rate_limit_window"

    @valkey_rate_limit_resilience.apply()
    async def consume_user_rate_limit(
        self, user_id: UserID, window_seconds: int, limit: int
    ) -> RateLimitState:
        """
        Consume one request of the user's current window and return its state.

        :param user_id: The user the counter is keyed by.
        :param window_seconds: The window length, applied when the request opens a window.
        :param limit: The limit to fix for the window, taken only when the request opens one.
        :return: The count, the limit fixed for the window, and the seconds until it ends.
        """
        return await self._consume_window(self._user_window_key(user_id), window_seconds, limit)

    @valkey_rate_limit_resilience.apply()
    async def consume_ip_rate_limit(
        self, client_ip: str, window_seconds: int, limit: int
    ) -> RateLimitState:
        """
        Consume one request of the address's current window and return its state.

        Unauthenticated requests are counted here: they name no keypair, so the address
        the server sees is the only caller identity there is.

        :param client_ip: The address the counter is keyed by.
        :param window_seconds: The window length, applied when the request opens a window.
        :param limit: The limit to fix for the window, taken only when the request opens one.
        :return: The count, the limit fixed for the window, and the seconds until it ends.
        """
        return await self._consume_window(self._ip_window_key(client_ip), window_seconds, limit)

    async def _consume_window(self, key: str, window_seconds: int, limit: int) -> RateLimitState:
        batch = Batch(is_atomic=True)
        batch.hincrby(key, "count", 1)
        batch.hsetnx(key, "limit", str(limit))
        batch.expire(key, window_seconds, ExpireOptions.HasNoExpiry)
        batch.hget(key, "limit")
        batch.ttl(key)
        async with self._client.client() as conn:
            results = await conn.exec(batch, raise_on_error=True)
        if results is None:
            raise UnreachableError("an atomic batch without WATCH cannot be aborted")
        count, _, _, fixed_limit, ttl = results
        return RateLimitState(
            count=cast(int, count),
            limit=int(cast(bytes, fixed_limit)),
            reset_after_seconds=cast(int, ttl),
        )

    @valkey_rate_limit_resilience.apply()
    async def get_state(self, user_id: UserID) -> RateLimitState | None:
        """
        Read the user's current window without counting a request.

        :param user_id: The user the counter is keyed by.
        :return: The window state, or None when no window is open for the user.

        ``consume_user_rate_limit()`` fixes the limit in the same atomic batch that opens a window,
        so an open window always carries one.
        """
        key = self._user_window_key(user_id)
        batch = Batch(is_atomic=True)
        batch.hmget(key, ["count", "limit"])
        batch.ttl(key)
        async with self._client.client() as conn:
            results = await conn.exec(batch, raise_on_error=True)
        if results is None:
            return None
        fields, ttl = cast(list[object], results)
        count, limit = cast(list[object], fields)
        if count is None:
            return None
        return RateLimitState(
            count=int(cast(bytes, count)),
            limit=int(cast(bytes, limit)),
            reset_after_seconds=cast(int, ttl),
        )

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
