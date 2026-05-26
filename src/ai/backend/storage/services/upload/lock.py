"""TUS upload session locking — distributed lock factory and constants."""

from __future__ import annotations

from ai.backend.common.lock import DistributedLockFactory, RedisLock
from ai.backend.common.types import RedisConnectionInfo

# Public — used by the engine to build session lock keys and pass lifetime to
# the factory.
LOCK_KEY_PREFIX = "tus.upload.lock"  # tus.upload.lock:{session_id}
LOCK_LIFETIME_SECONDS = 30.0  # lock auto-expires after this (crash safety)

_ACQUIRE_TIMEOUT_SECONDS = 10.0  # max wait to acquire the per-session lock
# Poll interval while waiting for the lock; the RedisLock default (1s) is far
# too coarse for the short, highly-contended per-chunk critical section.
_RETRY_INTERVAL_SECONDS = 0.05


def create_tus_lock_factory(redis: RedisConnectionInfo) -> DistributedLockFactory:
    """
    Build the per-session lock factory backed by :class:`RedisLock` over ``redis``.

    Mirrors the manager's ``create_lock_factory``: the caller owns ``redis``
    (lifecycle/close) and the returned factory closes over it, producing a fresh
    lock per ``lock_id`` so the factory can live as a standalone resource.
    """

    def _factory(lock_id: str, lifetime_hint: float) -> RedisLock:
        return RedisLock(
            lock_id,
            redis,
            timeout=_ACQUIRE_TIMEOUT_SECONDS,
            lifetime=lifetime_hint,
            lock_retry_interval=_RETRY_INTERVAL_SECONDS,
        )

    return _factory
