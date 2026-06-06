"""Valkey-backed offset + write-lease coordinator for TUS uploads (BA-3974)."""

from __future__ import annotations

import logging
from typing import Final, Self

from glide import ConditionalChange, ExpirySet, ExpiryType, Script

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
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

valkey_tus_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.VALKEY, layer=LayerType.VALKEY_TUS)),
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

_OFFSET_KEY_PREFIX: Final = "tus.upload.offset"
_LEASE_KEY_PREFIX: Final = "tus.upload.lease"
_DEFAULT_TTL_SECONDS: Final = 24 * 60 * 60
_DEFAULT_LEASE_TTL_SECONDS: Final = 60

# Compare-and-delete: only release if the caller still owns the lease.
RELEASE_LEASE_SCRIPT: Final[str] = """
local current = redis.call('GET', KEYS[1])
if current == ARGV[1] then
    redis.call('DEL', KEYS[1])
    return 1
else
    return 0
end
"""


class ValkeyTusClient:
    """Per-session committed offset and write lease, shared across replicas."""

    _client: AbstractValkeyClient
    _release_lease_script: Script

    def __init__(self, client: AbstractValkeyClient) -> None:
        self._client = client
        self._release_lease_script = Script(RELEASE_LEASE_SCRIPT)

    @classmethod
    async def create(
        cls,
        valkey_target: ValkeyTarget,
        *,
        db_id: int,
        human_readable_name: str,
    ) -> Self:
        client = create_valkey_client(
            valkey_target=valkey_target,
            db_id=db_id,
            human_readable_name=human_readable_name,
        )
        await client.connect()
        return cls(client=client)

    @valkey_tus_resilience.apply()
    async def close(self) -> None:
        await self._client.disconnect()

    @staticmethod
    def _key(session_id: str) -> str:
        return f"{_OFFSET_KEY_PREFIX}:{session_id}"

    @staticmethod
    def _lease_key(session_id: str) -> str:
        return f"{_LEASE_KEY_PREFIX}:{session_id}"

    @valkey_tus_resilience.apply()
    async def acquire_session_lease(
        self,
        session_id: str,
        holder_token: str,
        *,
        ttl_seconds: int = _DEFAULT_LEASE_TTL_SECONDS,
    ) -> bool:
        """``SET NX EX``: ``True`` on admission, ``False`` if another replica holds it."""
        async with self._client.client() as conn:
            result = await conn.set(
                self._lease_key(session_id),
                holder_token,
                conditional_set=ConditionalChange.ONLY_IF_DOES_NOT_EXIST,
                expiry=ExpirySet(ExpiryType.SEC, ttl_seconds),
            )
        return result is not None

    @valkey_tus_resilience.apply()
    async def release_session_lease(self, session_id: str, holder_token: str) -> bool:
        """Compare-and-delete: only release if ``holder_token`` still owns the lease."""
        async with self._client.client() as conn:
            result = await conn.invoke_script(
                script=self._release_lease_script,
                keys=[self._lease_key(session_id)],
                args=[holder_token],
            )
        return int(result) == 1

    @valkey_tus_resilience.apply()
    async def initialize_offset(
        self,
        session_id: str,
        *,
        ttl_seconds: int = _DEFAULT_TTL_SECONDS,
    ) -> None:
        """Initialize the per-session committed offset to 0."""
        async with self._client.client() as conn:
            await conn.set(
                self._key(session_id),
                "0",
                expiry=ExpirySet(ExpiryType.SEC, ttl_seconds),
            )

    @valkey_tus_resilience.apply()
    async def get_offset(self, session_id: str) -> int | None:
        async with self._client.client() as conn:
            raw = await conn.get(self._key(session_id))
        if raw is None:
            return None
        decoded = raw.decode() if isinstance(raw, bytes) else raw
        return int(decoded)

    @valkey_tus_resilience.apply()
    async def advance_offset(
        self,
        session_id: str,
        length: int,
        *,
        ttl_seconds: int = _DEFAULT_TTL_SECONDS,
    ) -> int:
        """``INCRBY`` the offset by ``length`` and return the new value. Call after fsync."""
        key = self._key(session_id)
        async with self._client.client() as conn:
            new_value = await conn.incrby(key, length)
            await conn.expire(key, ttl_seconds)
            return int(new_value)
