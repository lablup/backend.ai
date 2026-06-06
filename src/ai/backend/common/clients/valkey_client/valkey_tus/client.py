"""
Minimal Valkey-backed TUS upload offset coordinator (main-branch patch).

Stores a single integer per upload session — the committed byte offset — so
that all storage-proxy replicas behind a load balancer share one consistent
view of the upload's progress. This replaces the BA-3974-racy
``Path(upload_temp_path).stat().st_size`` lookup with a Valkey-backed value
that is immune to per-replica NFS attribute cache staleness.

Only three operations are exposed:

- :meth:`initialize_offset` — set the offset to 0 at session creation.
- :meth:`get_offset` — read the current committed offset (used by the
  PATCH handler to validate the caller-supplied ``Upload-Offset`` before
  writing the chunk to disk).
- :meth:`advance_offset` — atomically ``INCRBY`` the offset by the actual
  number of bytes durably written. Called *after* ``fsync`` so a crash
  between the disk commit and this call leaves the offset at its old
  value, and a retry from the client appends the same chunk again (idem-
  potent at the TUS protocol level).

A 24-hour sliding TTL reclaims abandoned session counters.
"""

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
_LOCK_KEY_PREFIX: Final = "tus.upload.lock"
_DEFAULT_TTL_SECONDS: Final = 24 * 60 * 60
_DEFAULT_LOCK_TTL_SECONDS: Final = 60

# Compare-and-delete release. ``DEL`` only if the value still equals the
# caller-supplied holder token — this prevents a process whose lease has
# already expired from accidentally deleting the next holder's lease.
RELEASE_LOCK_SCRIPT: Final[str] = """
local current = redis.call('GET', KEYS[1])
if current == ARGV[1] then
    redis.call('DEL', KEYS[1])
    return 1
else
    return 0
end
"""


class ValkeyTusOffsetClient:
    """Tiny Valkey-backed offset coordinator for TUS uploads."""

    _client: AbstractValkeyClient
    _release_lock_script: Script

    def __init__(self, client: AbstractValkeyClient) -> None:
        self._client = client
        self._release_lock_script = Script(RELEASE_LOCK_SCRIPT)

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
    def _lock_key(session_id: str) -> str:
        return f"{_LOCK_KEY_PREFIX}:{session_id}"

    @valkey_tus_resilience.apply()
    async def acquire_lock(
        self,
        session_id: str,
        holder_token: str,
        *,
        ttl_seconds: int = _DEFAULT_LOCK_TTL_SECONDS,
    ) -> bool:
        """Sokovan-style TTL lease.

        Acquires the per-session lock by atomically setting the lock key with
        ``SET NX EX``. Returns ``True`` if acquired, ``False`` if another
        replica already holds the lease. The lease auto-expires after
        ``ttl_seconds`` so a crashed holder cannot deadlock the session.
        """
        async with self._client.client() as conn:
            result = await conn.set(
                self._lock_key(session_id),
                holder_token,
                conditional_set=ConditionalChange.ONLY_IF_DOES_NOT_EXIST,
                expiry=ExpirySet(ExpiryType.SEC, ttl_seconds),
            )
        return result is not None

    @valkey_tus_resilience.apply()
    async def release_lock(self, session_id: str, holder_token: str) -> bool:
        """Compare-and-delete release.

        Only deletes the lock key if the stored value still equals the
        caller-supplied ``holder_token``. This prevents a process whose lease
        has already expired (and was acquired by another replica in the
        meantime) from accidentally releasing the new holder's lease.
        """
        async with self._client.client() as conn:
            result = await conn.invoke_script(
                script=self._release_lock_script,
                keys=[self._lock_key(session_id)],
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
        """Set the offset for ``session_id`` to 0. Called once per upload session."""
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
        """Atomically advance the offset by ``length`` and return the new value.

        Called *after* the chunk has been durably appended to the file. Because
        the TUS spec mandates strictly sequential PATCH per resource
        (``core.patch.offset-match`` MUST), the caller is the sole writer for
        this session at this moment — no separate CAS check is needed here.
        The precondition (client_offset == server_offset) is validated upfront
        via :meth:`get_offset` before the file write, and ``INCRBY`` itself is
        atomic at the Redis server.
        """
        key = self._key(session_id)
        async with self._client.client() as conn:
            new_value = await conn.incrby(key, length)
            await conn.expire(key, ttl_seconds)
            return int(new_value)
