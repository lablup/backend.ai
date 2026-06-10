"""Valkey-backed offset + write-lease coordinator for TUS uploads."""

from __future__ import annotations

import asyncio
import logging
from typing import Final, NewType, Self, cast

from glide import Batch, ConditionalChange, ExpirySet, ExpiryType, Script

from ai.backend.common.clients.valkey_client.client import (
    AbstractValkeyClient,
    create_valkey_client,
)
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
from ai.backend.logging import BraceStyleAdapter

from .exceptions import TusLeaseHeldError, TusLeaseLostError, TusSessionNotFoundError

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

TusSessionId = NewType("TusSessionId", str)


_OFFSET_KEY_PREFIX: Final = "tus.upload.offset"
_LEASE_KEY_PREFIX: Final = "tus.upload.lease"
_DEFAULT_TTL_SECONDS: Final = 24 * 60 * 60
_DEFAULT_LEASE_TTL_SECONDS: Final = 30
_DEFAULT_LEASE_HEARTBEAT_SECONDS: Final = 10


# Compare-and-expire: refresh the lease TTL only if we still own it. Returns
# 1 on success, 0 if the lease no longer belongs to ``holder_token`` (in
# which case the background heartbeat should stop and the PATCH be aborted).
EXTEND_LEASE_SCRIPT: Final[str] = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    redis.call('EXPIRE', KEYS[1], ARGV[2])
    return 1
end
return 0
"""


# Compare-and-delete release: drop the lease only if we still own it. Used by
# cleanup paths (drain failed, precondition mismatch) where we want to free the
# lease for the next PATCH without advancing the offset.
RELEASE_LEASE_SCRIPT: Final[str] = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    redis.call('DEL', KEYS[1])
    return 1
end
return 0
"""


# Advance-and-release in one atomic Lua step. Refuses to advance if the
# caller no longer owns the lease (lease expired and was claimed by another
# storage-proxy while we held it), preventing offset double-counting. On
# success: ``INCRBY`` offset + refresh its TTL + ``DEL`` the lease.
#
# KEYS = [offset_key, lease_key]
# ARGV = [length, holder_token, offset_ttl]
# Returns the new offset, or -1 if the lease is no longer ours.
ADVANCE_OFFSET_SCRIPT: Final[str] = """
if redis.call('GET', KEYS[2]) ~= ARGV[2] then
    return -1
end
local new_off = redis.call('INCRBY', KEYS[1], ARGV[1])
redis.call('EXPIRE', KEYS[1], ARGV[3])
redis.call('DEL', KEYS[2])
return new_off
"""


class ValkeyTusClient:
    """Per-session committed offset and write lease, shared across storage-proxy instances."""

    _client: AbstractValkeyClient
    _advance_offset_script: Script
    _extend_lease_script: Script
    _release_lease_script: Script

    def __init__(self, client: AbstractValkeyClient) -> None:
        self._client = client
        self._advance_offset_script = Script(ADVANCE_OFFSET_SCRIPT)
        self._extend_lease_script = Script(EXTEND_LEASE_SCRIPT)
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

    def _create_batch(self, is_atomic: bool = False) -> Batch:
        return Batch(is_atomic=is_atomic)

    @staticmethod
    def _offset_key(session_id: TusSessionId) -> str:
        return f"{_OFFSET_KEY_PREFIX}:{session_id}"

    @staticmethod
    def _lease_key(session_id: TusSessionId) -> str:
        return f"{_LEASE_KEY_PREFIX}:{session_id}"

    @valkey_tus_resilience.apply()
    async def initialize_offset(
        self,
        session_id: TusSessionId,
        *,
        ttl_seconds: int = _DEFAULT_TTL_SECONDS,
    ) -> None:
        """Initialize the per-session committed offset to 0."""
        async with self._client.client() as conn:
            await conn.set(
                self._offset_key(session_id),
                "0",
                expiry=ExpirySet(ExpiryType.SEC, ttl_seconds),
            )

    @valkey_tus_resilience.apply()
    async def get_offset(self, session_id: TusSessionId) -> int | None:
        async with self._client.client() as conn:
            raw = await conn.get(self._offset_key(session_id))
        if raw is None:
            return None
        decoded = raw.decode() if isinstance(raw, bytes) else raw
        return int(decoded)

    @valkey_tus_resilience.apply()
    async def try_load_offset(
        self,
        session_id: TusSessionId,
        holder_token: str,
        *,
        lease_ttl_seconds: int = _DEFAULT_LEASE_TTL_SECONDS,
    ) -> int:
        """Atomically claim the per-session lease and read the committed offset.

        Single MULTI/EXEC round-trip: ``SET lease NX EX`` + ``GET offset``.
        Returns the canonical committed offset on success. Raises
        :class:`TusLeaseHeldError` if another storage-proxy currently holds
        the lease, or :class:`TusSessionNotFoundError` if no offset is
        registered (in which case the lease we just acquired is released).
        """
        lease_key = self._lease_key(session_id)
        offset_key = self._offset_key(session_id)
        tx = self._create_batch(is_atomic=True)
        tx.set(
            lease_key,
            holder_token,
            conditional_set=ConditionalChange.ONLY_IF_DOES_NOT_EXIST,
            expiry=ExpirySet(ExpiryType.SEC, lease_ttl_seconds),
        )
        tx.get(offset_key)
        async with self._client.client() as conn:
            results = await conn.exec(tx, raise_on_error=True)
            if results is None:
                raise UnreachableError(
                    "try_load_offset: MULTI/EXEC returned no results — no WATCH in use "
                    "and SET+GET were queued, so this path should be unreachable."
                )
            set_ok = results[0] is not None
            offset_raw = results[1]
            if not set_ok:
                raise TusLeaseHeldError(
                    f"TUS session {session_id} lease is held by another storage-proxy"
                )
            if offset_raw is None:
                # We hold the lease but the session has no offset; drop it so
                # the next PATCH does not have to wait for the TTL.
                await conn.delete([lease_key])
                raise TusSessionNotFoundError(
                    f"TUS session {session_id} is not registered or has expired"
                )
            decoded = (
                offset_raw.decode() if isinstance(offset_raw, bytes) else cast(str, offset_raw)
            )
            return int(decoded)

    async def watch_lease(
        self,
        session_id: TusSessionId,
        holder_token: str,
        *,
        interval: float = _DEFAULT_LEASE_HEARTBEAT_SECONDS,
        ttl_seconds: int = _DEFAULT_LEASE_TTL_SECONDS,
    ) -> None:
        """Background loop: refresh the lease every ``interval`` seconds.

        Stops on its own when ``extend_lease`` returns ``False`` (the lease
        was reclaimed by another holder). The PATCH handler keeps draining;
        its final ``advance_offset`` then raises ``TusLeaseLostError`` which
        surfaces the conflict to the client as 409.
        """
        while True:
            await asyncio.sleep(interval)
            if not await self.extend_lease(session_id, holder_token, ttl_seconds=ttl_seconds):
                log.warning(
                    "lease heartbeat: session {} lost lease (holder={})",
                    session_id,
                    holder_token,
                )
                return

    @valkey_tus_resilience.apply()
    async def extend_lease(
        self,
        session_id: TusSessionId,
        holder_token: str,
        *,
        ttl_seconds: int = _DEFAULT_LEASE_TTL_SECONDS,
    ) -> bool:
        """Refresh the lease TTL iff still owned by ``holder_token``.

        Returns ``True`` on a successful renewal, ``False`` if the lease was
        reclaimed by another holder (heartbeat task should stop in that
        case). Called periodically from a background heartbeat coroutine so
        long-running PATCH bodies do not lose the lease mid-drain.
        """
        async with self._client.client() as conn:
            result = await conn.invoke_script(
                script=self._extend_lease_script,
                keys=[self._lease_key(session_id)],
                args=[holder_token, str(ttl_seconds)],
            )
        return int(cast(int, result)) == 1

    @valkey_tus_resilience.apply()
    async def release_lease(self, session_id: TusSessionId, holder_token: str) -> None:
        """Drop the lease iff still owned by ``holder_token``. Idempotent; no-op otherwise.

        Used by cleanup paths (drain failed, precondition mismatch) to free
        the lease immediately instead of waiting for its TTL. Never raises
        on ownership loss — the caller's primary concern is its own error.
        """
        async with self._client.client() as conn:
            await conn.invoke_script(
                script=self._release_lease_script,
                keys=[self._lease_key(session_id)],
                args=[holder_token],
            )

    @valkey_tus_resilience.apply()
    async def advance_offset(
        self,
        session_id: TusSessionId,
        holder_token: str,
        length: int,
        *,
        offset_ttl_seconds: int = _DEFAULT_TTL_SECONDS,
    ) -> int:
        """Advance the committed offset and release the lease atomically.

        Runs ``ADVANCE_OFFSET_SCRIPT`` so the ownership check, ``INCRBY``,
        TTL refresh, and lease ``DEL`` all happen in a single Redis step.
        Returns the new committed offset. Raises :class:`TusLeaseLostError`
        if the lease is no longer owned by ``holder_token`` (expired and
        reclaimed by another storage-proxy while we were writing).
        """
        lease_key = self._lease_key(session_id)
        offset_key = self._offset_key(session_id)
        async with self._client.client() as conn:
            result = await conn.invoke_script(
                script=self._advance_offset_script,
                keys=[offset_key, lease_key],
                args=[str(length), holder_token, str(offset_ttl_seconds)],
            )
        new_offset = int(cast(int, result))
        if new_offset < 0:
            raise TusLeaseLostError(
                f"TUS session {session_id} lease was reclaimed by another storage-proxy"
            )
        return new_offset
