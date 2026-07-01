import logging
from typing import Self

from glide import ExpirySet, ExpiryType

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_valkey_client,
)
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
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

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


SESSION_KEY_PREFIX = "AIOHTTP_SESSION_"
LOGIN_HISTORY_KEY_PREFIX = "login_history_"


class ValkeySessionClient:
    """
    Client for session management operations using Valkey/Glide.
    Provides session-specific methods instead of generic Redis operations.
    """

    _client: AbstractValkeyClient
    _closed: bool

    def __init__(
        self,
        client: AbstractValkeyClient,
    ) -> None:
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
        )
        await client.connect()
        return cls(client=client)

    @valkey_session_resilience.apply()
    async def close(self) -> None:
        """
        Close the ValkeySessionClient connection.
        """
        if self._closed:
            log.debug("ValkeySessionClient is already closed.")
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
    async def get_login_history(self, username: str) -> bytes | None:
        """
        Get login failure history for a user.

        :param username: The username to check.
        :return: The login history data as bytes, or None if not found.
        """
        key = f"{LOGIN_HISTORY_KEY_PREFIX}{username}"
        async with self._client.client() as conn:
            return await conn.get(key)

    @valkey_session_resilience.apply()
    async def set_login_block(
        self, username: str, block_data: str | bytes, block_duration_seconds: int
    ) -> None:
        """
        Set login block for a user with expiration.

        :param username: The username to block.
        :param block_data: The block data to store.
        :param block_duration_seconds: How long to block in seconds.
        """
        key = f"{LOGIN_HISTORY_KEY_PREFIX}{username}"
        async with self._client.client() as conn:
            await conn.set(
                key,
                block_data,
                expiry=ExpirySet(ExpiryType.SEC, block_duration_seconds),
            )

    @valkey_session_resilience.apply()
    async def clear_login_block(self, username: str) -> None:
        """
        Clear the login failure/block history for a user.

        :param username: The username whose block to clear.
        """
        key = f"{LOGIN_HISTORY_KEY_PREFIX}{username}"
        async with self._client.client() as conn:
            await conn.delete([key])

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
