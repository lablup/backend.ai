import logging
from typing import Optional, Self

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_valkey_client,
    valkey_decorator,
)
from ai.backend.common.types import RedisTarget
from ai.backend.logging.utils import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

_DEFAULT_LOCK_TTL = 300


class ValkeyStreamLockClient:
    """
    Client for distributed locking operations using Valkey.
    """

    _client: AbstractValkeyClient
    _closed: bool
    _default_ttl: int
    name: str

    def __init__(self, client: AbstractValkeyClient, default_ttl: int = _DEFAULT_LOCK_TTL) -> None:
        self._client = client
        self._closed = False
        self._default_ttl = default_ttl
        self.name = "valkey_stream_lock"

    @classmethod
    async def create(
        cls,
        redis_target: RedisTarget,
        *,
        db_id: int,
        human_readable_name: str,
        default_ttl: int = _DEFAULT_LOCK_TTL,
    ) -> Self:
        """
        Create a ValkeyStreamLockClient instance.

        :param redis_target: The target Redis server to connect to.
        :param db_id: The database index to use.
        :param human_readable_name: The human-readable name of the client.
        :param default_ttl: The default TTL for locks (in seconds).
        :return: An instance of ValkeyStreamLockClient.
        """
        client = create_valkey_client(
            target=redis_target,
            db_id=db_id,
            human_readable_name=human_readable_name,
            pubsub_channels=None,
        )
        await client.connect()
        return cls(client=client, default_ttl=default_ttl)

    async def close(self) -> None:
        """
        Close the ValkeyStreamLockClient connection.
        """
        if self._closed:
            log.warning("ValkeyStreamLockClient is already closed.")
            return
        self._closed = True
        await self._client.disconnect()

    @property
    def client(self):
        """
        Return the underlying Glide client for compatibility with AsyncRedisLock.
        """
        return self._client.client

    @valkey_decorator()
    async def ping(self) -> str:
        """
        Ping the Redis server.
        """
        result = await self._client.client.ping()
        return result.decode() if isinstance(result, bytes) else result

    @valkey_decorator()
    async def set_with_expiry(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """
        Set a key with an expiry time.
        """
        from glide import ExpirySet, ExpiryType

        expiry_time = ttl if ttl is not None else self._default_ttl
        expiry = ExpirySet(ExpiryType.SEC, expiry_time)
        result = await self._client.client.set(key, value, expiry=expiry)
        return result is not None

    @valkey_decorator()
    async def get(self, key: str) -> Optional[str]:
        """
        Get a value by key.
        """
        result = await self._client.client.get(key)
        return result.decode() if isinstance(result, bytes) else result

    @valkey_decorator()
    async def delete(self, key: str) -> int:
        """
        Delete a key.
        """
        return await self._client.client.delete([key])

    @valkey_decorator()
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists.
        """
        result = await self._client.client.exists([key])
        return result > 0

    @valkey_decorator()
    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiry time for a key.
        """
        return await self._client.client.expire(key, seconds)

    @valkey_decorator()
    async def ttl(self, key: str) -> int:
        """
        Get TTL of a key.
        """
        return await self._client.client.ttl(key)
