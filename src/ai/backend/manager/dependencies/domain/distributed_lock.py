from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai.backend.common import redis_helper
from ai.backend.common.defs import REDIS_STREAM_LOCK, RedisRole
from ai.backend.common.lock import EtcdLock, FileLock, RedisLock
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.pglock import PgAdvisoryLock
from ai.backend.manager.types import DistributedLockFactory

from .base import DomainDependency

if TYPE_CHECKING:
    from ai.backend.common.etcd import AsyncEtcd
    from ai.backend.manager.config.provider import ManagerConfigProvider
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class DistributedLockInput:
    """Input required for distributed lock factory setup."""

    config_provider: ManagerConfigProvider
    db: ExtendedAsyncSAEngine
    etcd: AsyncEtcd


def create_lock_factory(
    config_provider: ManagerConfigProvider,
    db: ExtendedAsyncSAEngine,
    etcd: AsyncEtcd,
) -> DistributedLockFactory:
    """Create a distributed lock factory based on configuration.

    This is a pure function that replaces the legacy ``init_lock_factory``
    in ``server.py`` by accepting explicit dependencies instead of ``RootContext``.
    """
    config = config_provider.config
    ipc_base_path = config.manager.ipc_base_path
    manager_id = config.manager.id
    lock_backend = config.manager.distributed_lock
    log.debug("using {} as the distributed lock backend", lock_backend)
    match lock_backend:
        case "filelock":
            return lambda lock_id, lifetime_hint: FileLock(  # noqa: ARG005
                ipc_base_path / f"{manager_id}.{lock_id}.lock",
                timeout=0,
            )
        case "pg_advisory":
            return lambda lock_id, lifetime_hint: PgAdvisoryLock(  # noqa: ARG005
                db, lock_id
            )
        case "redlock":
            redlock_config = config.manager.redlock_config
            redis_profile_target = config.redis.to_redis_profile_target()
            redis_lock = redis_helper.get_redis_object_for_lock(
                redis_profile_target.profile_target(RedisRole.STREAM_LOCK),
                name="lock",
                db=REDIS_STREAM_LOCK,
            )
            return lambda lock_id, lifetime_hint: RedisLock(
                str(lock_id),
                redis_lock,
                lifetime=min(lifetime_hint * 2, lifetime_hint + 30),
                lock_retry_interval=redlock_config["lock_retry_interval"],
            )
        case "etcd":
            return lambda lock_id, lifetime_hint: EtcdLock(
                str(lock_id),
                etcd,
                lifetime=min(lifetime_hint * 2, lifetime_hint + 30),
            )
        case other:
            raise ValueError(f"Invalid lock backend: {other}")


class DistributedLockFactoryDependency(
    DomainDependency[DistributedLockInput, DistributedLockFactory],
):
    """Provides DistributedLockFactory lifecycle management.

    Creates a lock factory based on the configured backend
    (filelock, pg_advisory, redlock, or etcd).
    """

    @property
    def stage_name(self) -> str:
        return "distributed-lock-factory"

    @asynccontextmanager
    async def provide(
        self, setup_input: DistributedLockInput
    ) -> AsyncIterator[DistributedLockFactory]:
        """Initialize and provide a DistributedLockFactory.

        Args:
            setup_input: Input containing config_provider, db, and etcd references.

        Yields:
            A callable factory that creates distributed locks.
        """
        factory = create_lock_factory(
            config_provider=setup_input.config_provider,
            db=setup_input.db,
            etcd=setup_input.etcd,
        )
        yield factory
