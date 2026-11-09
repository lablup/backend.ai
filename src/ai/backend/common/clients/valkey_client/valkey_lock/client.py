"""Valkey-based distributed lock client."""

from __future__ import annotations

from typing import Final, Self

from glide import ConditionalChange, ExpirySet, ExpiryType, Script

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_valkey_client,
)
from ai.backend.common.clients.valkey_client.sentinel_monitor.base import AbstractSentinelMonitor
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience import MetricArgs, MetricPolicy, Resilience
from ai.backend.common.types import ValkeyTarget

# No retry policy: a retried SET NX whose reply was lost would find our own token and fail.
valkey_lock_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.VALKEY, layer=LayerType.VALKEY_LOCK)),
    ]
)

RELEASE_SCRIPT: Final[str] = """
local current = redis.call('GET', KEYS[1])
if current == ARGV[1] then
    redis.call('DEL', KEYS[1])
    return 1
else
    return 0
end
"""


class ValkeyLockClient:
    """
    Client for distributed locks keyed by the lock name with a per-holder token.

    The key and value layout matches redis-py ``Lock``.
    """

    _client: AbstractValkeyClient
    _release_script: Script

    def __init__(self, client: AbstractValkeyClient) -> None:
        self._client = client
        self._release_script = Script(RELEASE_SCRIPT)

    @classmethod
    async def create(
        cls,
        valkey_target: ValkeyTarget,
        *,
        db_id: int,
        human_readable_name: str,
        sentinel_monitor: AbstractSentinelMonitor | None = None,
    ) -> Self:
        client = create_valkey_client(
            valkey_target=valkey_target,
            db_id=db_id,
            human_readable_name=human_readable_name,
            sentinel_monitor=sentinel_monitor,
        )
        await client.connect()
        return cls(client=client)

    @valkey_lock_resilience.apply()
    async def close(self) -> None:
        await self._client.disconnect()

    @valkey_lock_resilience.apply()
    async def acquire(self, name: str, token: str, lifetime_ms: int | None) -> bool:
        """Set ``name`` to ``token`` if absent. ``lifetime_ms=None`` sets no expiry."""
        expiry = ExpirySet(ExpiryType.MILLSEC, lifetime_ms) if lifetime_ms is not None else None
        async with self._client.client() as conn:
            result = await conn.set(
                name,
                token,
                conditional_set=ConditionalChange.ONLY_IF_DOES_NOT_EXIST,
                expiry=expiry,
            )
        return result is not None

    @valkey_lock_resilience.apply()
    async def release(self, name: str, token: str) -> bool:
        """Delete ``name`` only if it still holds ``token``."""
        async with self._client.client() as conn:
            result = await conn.invoke_script(
                script=self._release_script,
                keys=[name],
                args=[token],
            )
        return bool(result == 1)
