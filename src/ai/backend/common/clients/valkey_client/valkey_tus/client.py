"""
Valkey client for TUS resumable-upload sessions.

Stores per-session upload metadata (the source of truth) on the Glide-based
valkey connection so that multiple Storage Proxy replicas share one view of an
upload's progress without relying on shared-filesystem semantics. This client is
metadata-only; the per-session distributed lock that serializes the
read-modify-write window is a separate :class:`DistributedLockFactory` resource
(see :mod:`ai.backend.storage.services.upload.tus_session`). The payload bytes
stay on the shared filesystem; only this small metadata lives in Valkey.
"""

from __future__ import annotations

import logging
from typing import Final, Self

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
from ai.backend.common.types import TusSessionId, ValkeyTarget
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

_STATE_KEY_PREFIX: Final = "tus.upload.session"  # tus.upload.session:{session_id}

# Stale (never-completed / abandoned) sessions are reclaimed by this TTL, so no
# separate GC sweep is needed.
_DEFAULT_STATE_TTL_SECONDS: Final = 24 * 60 * 60


class ValkeyTusClient:
    """Valkey-backed metadata store for TUS uploads."""

    _client: AbstractValkeyClient

    def __init__(self, client: AbstractValkeyClient) -> None:
        self._client = client

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
    def _state_key(session_id: TusSessionId) -> str:
        return f"{_STATE_KEY_PREFIX}:{session_id}"

    @valkey_tus_resilience.apply()
    async def get_session_state(self, session_id: TusSessionId) -> bytes | None:
        """Return the raw serialized session state, or ``None`` if absent."""
        async with self._client.client() as conn:
            return await conn.get(self._state_key(session_id))

    @valkey_tus_resilience.apply()
    async def set_session_state(
        self,
        session_id: TusSessionId,
        payload: str | bytes,
        *,
        ttl_seconds: int = _DEFAULT_STATE_TTL_SECONDS,
    ) -> None:
        async with self._client.client() as conn:
            await conn.set(
                self._state_key(session_id),
                payload,
                expiry=ExpirySet(ExpiryType.SEC, ttl_seconds),
            )

    @valkey_tus_resilience.apply()
    async def delete_session_state(self, session_id: TusSessionId) -> None:
        async with self._client.client() as conn:
            await conn.delete([self._state_key(session_id)])
