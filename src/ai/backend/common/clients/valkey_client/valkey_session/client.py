import logging
from typing import Optional, Self

from glide import ExpirySet, ExpiryType

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_layer_aware_valkey_decorator,
    create_valkey_client,
)
from ai.backend.common.metrics.metric import LayerType
from ai.backend.common.types import ValkeyTarget
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Layer-specific decorator for valkey_session client
valkey_decorator = create_layer_aware_valkey_decorator(LayerType.VALKEY_SESSION)


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

    @valkey_decorator()
    async def close(self) -> None:
        """
        Close the ValkeySessionClient connection.
        """
        if self._closed:
            log.debug("ValkeySessionClient is already closed.")
            return
        self._closed = True
        await self._client.disconnect()

    @valkey_decorator()
    async def get_session_data(self, session_key: str) -> Optional[bytes]:
        """
        Get session data by session key.

        :param session_key: The session key to retrieve.
        :return: The session data as bytes, or None if not found.
        """
        return await self._client.client.get(session_key)

    @valkey_decorator()
    async def set_session_data(
        self, session_key: str, session_data: str | bytes, ttl_seconds: int
    ) -> None:
        """
        Set session data with expiration.

        :param session_key: The session key to set.
        :param session_data: The session data to store.
        :param ttl_seconds: Time to live in seconds.
        """
        await self._client.client.set(
            session_key,
            session_data,
            expiry=ExpirySet(ExpiryType.SEC, ttl_seconds),
        )

    @valkey_decorator()
    async def get_login_history(self, username: str) -> Optional[bytes]:
        """
        Get login failure history for a user.

        :param username: The username to check.
        :return: The login history data as bytes, or None if not found.
        """
        key = f"login_history_{username}"
        return await self._client.client.get(key)

    @valkey_decorator()
    async def set_login_block(
        self, username: str, block_data: str | bytes, block_duration_seconds: int
    ) -> None:
        """
        Set login block for a user with expiration.

        :param username: The username to block.
        :param block_data: The block data to store.
        :param block_duration_seconds: How long to block in seconds.
        """
        key = f"login_history_{username}"
        await self._client.client.set(
            key,
            block_data,
            expiry=ExpirySet(ExpiryType.SEC, block_duration_seconds),
        )

    @valkey_decorator()
    async def flush_all_sessions(self) -> None:
        """
        Flush all data in the current database (typically used for session cleanup).
        """
        await self._client.client.flushdb()

    @valkey_decorator()
    async def get_server_time_second(self) -> int:
        """
        Get the current server time.

        :return: Server time as (seconds, microseconds).
        """
        result = await self._client.client.time()
        seconds_bytes, _ = result
        return int(seconds_bytes)
