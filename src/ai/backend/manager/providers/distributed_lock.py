from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import TYPE_CHECKING

from ai.backend.common import redis_helper
from ai.backend.common.defs import REDIS_STREAM_LOCK, RedisRole
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.types import DistributedLockFactory

if TYPE_CHECKING:
    from ..api.context import RootContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


def init_lock_factory(root_ctx: RootContext) -> DistributedLockFactory:
    ipc_base_path = root_ctx.config_provider.config.manager.ipc_base_path
    manager_id = root_ctx.config_provider.config.manager.id
    lock_backend = root_ctx.config_provider.config.manager.distributed_lock
    log.debug("using {} as the distributed lock backend", lock_backend)
    match lock_backend:
        case "filelock":
            from ai.backend.common.lock import FileLock

            return lambda lock_id, lifetime_hint: FileLock(
                ipc_base_path / f"{manager_id}.{lock_id}.lock",
                timeout=0,
            )
        case "pg_advisory":
            from ..pglock import PgAdvisoryLock

            return lambda lock_id, lifetime_hint: PgAdvisoryLock(root_ctx.db, lock_id)
        case "redlock":
            from ai.backend.common.lock import RedisLock

            redlock_config = root_ctx.config_provider.config.manager.redlock_config
            redis_profile_target = root_ctx.config_provider.config.redis.to_redis_profile_target()
            redis_lock = redis_helper.get_redis_object(
                redis_profile_target.profile_target(RedisRole.STREAM_LOCK),
                name="lock",  # distributed locks
                db=REDIS_STREAM_LOCK,
            )
            return lambda lock_id, lifetime_hint: RedisLock(
                str(lock_id),
                redis_lock,
                lifetime=min(lifetime_hint * 2, lifetime_hint + 30),
                lock_retry_interval=redlock_config["lock_retry_interval"],
            )
        case "etcd":
            from ai.backend.common.lock import EtcdLock

            return lambda lock_id, lifetime_hint: EtcdLock(
                str(lock_id),
                root_ctx.etcd,
                lifetime=min(lifetime_hint * 2, lifetime_hint + 30),
            )
        case other:
            raise ValueError(f"Invalid lock backend: {other}")


@actxmgr
async def distributed_lock_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    root_ctx.distributed_lock_factory = init_lock_factory(root_ctx)
    yield
