import logging
from typing import Final, Self

from glide import ExpirySet, ExpiryType, Script

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_valkey_client,
)
from ai.backend.common.clients.valkey_client.sentinel_monitor.base import AbstractSentinelMonitor
from ai.backend.common.exception import BackendAIError
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
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

# Resilience instance for valkey_session layer
valkey_session_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.VALKEY, layer=LayerType.VALKEY_SESSION)),
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

# No retry policy: a retried script whose reply was lost would change the count twice.
valkey_login_attempt_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.VALKEY, layer=LayerType.VALKEY_SESSION)),
    ]
)


SESSION_KEY_PREFIX = "AIOHTTP_SESSION_"
LOGIN_HISTORY_KEY_PREFIX = "login_history_"
LOGIN_FAIL_COUNT_KEY_PREFIX = "login_fail_count_"

# KEYS[1]: fail count key, ARGV[1]: allowed fail count, ARGV[2]: TTL in seconds.
RESERVE_LOGIN_ATTEMPT_SCRIPT: Final[str] = """
local count = tonumber(redis.call('GET', KEYS[1]) or '0')
if count >= tonumber(ARGV[1]) then
    redis.call('EXPIRE', KEYS[1], ARGV[2])
    return 0
end
redis.call('INCR', KEYS[1])
redis.call('EXPIRE', KEYS[1], ARGV[2])
return 1
"""

RELEASE_LOGIN_ATTEMPT_SCRIPT: Final[str] = """
local count = tonumber(redis.call('GET', KEYS[1]) or '0')
if count <= 1 then
    redis.call('DEL', KEYS[1])
    return 0
end
return redis.call('DECR', KEYS[1])
"""


class ValkeySessionClient:
    """
    Client for session management operations using Valkey/Glide.
    Provides session-specific methods instead of generic Redis operations.
    """

    _client: AbstractValkeyClient
    _closed: bool
    _reserve_login_attempt_script: Script
    _release_login_attempt_script: Script

    def __init__(
        self,
        client: AbstractValkeyClient,
    ) -> None:
        self._client = client
        self._closed = False
        self._reserve_login_attempt_script = Script(RESERVE_LOGIN_ATTEMPT_SCRIPT)
        self._release_login_attempt_script = Script(RELEASE_LOGIN_ATTEMPT_SCRIPT)

    @classmethod
    async def create(
        cls,
        valkey_target: ValkeyTarget,
        *,
        db_id: int,
        human_readable_name: str,
        sentinel_monitor: AbstractSentinelMonitor | None = None,
    ) -> Self:
        """
        Create a ValkeySessionClient instance.

        :param redis_target: The target Redis server to connect to.
        :param db_id: The database index to use.
        :param human_readable_name: The human-readable name for the client.
        :return: An instance of ValkeySessionClient.
        """
        client = create_valkey_client(
            valkey_target=valkey_target,
            db_id=db_id,
            human_readable_name=human_readable_name,
            sentinel_monitor=sentinel_monitor,
        )
        await client.connect()
        return cls(client=client)

    @valkey_session_resilience.apply()
    async def close(self) -> None:
        """
        Close the ValkeySessionClient connection.
        """
        if self._closed:
            log.debug("valkey session client already closed")
            return
        self._closed = True
        await self._client.disconnect()

    @valkey_session_resilience.apply()
    async def get_session_data(self, session_key: str) -> bytes | None:
        """
        Get session data by session key.

        :param session_key: The session key to retrieve.
        :return: The session data as bytes, or None if not found.
        """
        async with self._client.client() as conn:
            return await conn.get(session_key)

    @valkey_session_resilience.apply()
    async def set_session_data(
        self, session_key: str, session_data: str | bytes, ttl_seconds: int
    ) -> None:
        """
        Set session data with expiration.

        :param session_key: The session key to set.
        :param session_data: The session data to store.
        :param ttl_seconds: Time to live in seconds.
        """
        async with self._client.client() as conn:
            await conn.set(
                session_key,
                session_data,
                expiry=ExpirySet(ExpiryType.SEC, ttl_seconds),
            )

    @valkey_session_resilience.apply()
    async def delete_session_data(self, session_key: str) -> None:
        """
        Delete session data by session key.

        :param session_key: The session key to delete.
        """
        async with self._client.client() as conn:
            await conn.delete([session_key])

    @valkey_session_resilience.apply()
    async def get_login_session(self, session_token: str) -> bytes | None:
        """
        Get login session data by session token.

        :param session_token: The session token (prefix is added internally).
        :return: The session data as bytes, or None if not found.
        """
        async with self._client.client() as conn:
            return await conn.get(f"{SESSION_KEY_PREFIX}{session_token}")

    @valkey_session_resilience.apply()
    async def get_login_sessions(self, session_tokens: list[str]) -> list[bytes | None]:
        """
        Get login session data for several session tokens in a single batch operation.

        :param session_tokens: The session tokens (prefix is added internally).
        :return: The session data in the order of ``session_tokens``, None where not found.
        """
        if not session_tokens:
            return []
        keys: list[str | bytes] = [f"{SESSION_KEY_PREFIX}{token}" for token in session_tokens]
        async with self._client.client() as conn:
            return await conn.mget(keys)

    @valkey_session_resilience.apply()
    async def set_login_session(
        self, session_token: str, session_data: str | bytes, ttl_seconds: int
    ) -> None:
        """
        Set login session data with expiration.

        :param session_token: The session token (prefix is added internally).
        :param session_data: The session data to store.
        :param ttl_seconds: Time to live in seconds.
        """
        async with self._client.client() as conn:
            await conn.set(
                f"{SESSION_KEY_PREFIX}{session_token}",
                session_data,
                expiry=ExpirySet(ExpiryType.SEC, ttl_seconds),
            )

    @valkey_session_resilience.apply()
    async def delete_login_session(self, session_token: str) -> None:
        """
        Delete login session data by session token.

        :param session_token: The session token (prefix is added internally).
        """
        async with self._client.client() as conn:
            await conn.delete([f"{SESSION_KEY_PREFIX}{session_token}"])

    @valkey_session_resilience.apply()
    async def delete_login_sessions(self, session_tokens: list[str]) -> None:
        """
        Delete login session data for several session tokens in a single batch operation.

        :param session_tokens: The session tokens (prefix is added internally).
        """
        if not session_tokens:
            return
        keys: list[str | bytes] = [f"{SESSION_KEY_PREFIX}{token}" for token in session_tokens]
        async with self._client.client() as conn:
            await conn.delete(keys)

    @valkey_login_attempt_resilience.apply()
    async def reserve_login_attempt(
        self, username: str, allowed_fail_count: int, block_duration_seconds: int
    ) -> bool:
        """
        Count a login attempt against the user unless the count reached the limit.
        Both outcomes restart the expiration.

        :return: True if the attempt may proceed, False if the user is blocked.
        """
        async with self._client.client() as conn:
            result = await conn.invoke_script(
                script=self._reserve_login_attempt_script,
                keys=[f"{LOGIN_FAIL_COUNT_KEY_PREFIX}{username}"],
                args=[str(allowed_fail_count), str(block_duration_seconds)],
            )
        return bool(result == 1)

    @valkey_login_attempt_resilience.apply()
    async def release_login_attempt(self, username: str) -> None:
        """
        Take back an attempt reserved by `reserve_login_attempt`.
        """
        async with self._client.client() as conn:
            await conn.invoke_script(
                script=self._release_login_attempt_script,
                keys=[f"{LOGIN_FAIL_COUNT_KEY_PREFIX}{username}"],
            )

    @valkey_session_resilience.apply()
    async def clear_login_block(self, username: str) -> None:
        """
        Clear the login failure/block history for a user.

        :param username: The username whose block to clear.
        """
        keys: list[str | bytes] = [
            f"{LOGIN_FAIL_COUNT_KEY_PREFIX}{username}",
            f"{LOGIN_HISTORY_KEY_PREFIX}{username}",
        ]
        async with self._client.client() as conn:
            await conn.delete(keys)

    @valkey_session_resilience.apply()
    async def flush_all_sessions(self) -> None:
        """
        Flush all data in the current database (typically used for session cleanup).
        """
        async with self._client.client() as conn:
            await conn.flushdb()

    @valkey_session_resilience.apply()
    async def get_server_time_second(self) -> int:
        """
        Get the current server time.

        :return: Server time as (seconds, microseconds).
        """
        async with self._client.client() as conn:
            result = await conn.time()
        seconds_bytes, _ = result
        return int(seconds_bytes)

    async def ping(self) -> None:
        """
        Ping the Valkey server to check connection.

        :raises: Exception if ping fails
        """
        async with self._client.client() as conn:
            await conn.ping()
