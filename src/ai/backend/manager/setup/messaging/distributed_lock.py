from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai.backend.common import redis_helper
from ai.backend.common.defs import REDIS_STREAM_LOCK
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.lock import AbstractDistributedLock, EtcdLock, FileLock, RedisLock
from ai.backend.common.stage.types import Provisioner
from ai.backend.common.types import RedisProfileTarget, RedisRole
from ai.backend.manager.config.unified import ManagerUnifiedConfig
from ai.backend.manager.defs import LockID
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.pglock import PgAdvisoryLock
from ai.backend.manager.types import DistributedLockFactory

if TYPE_CHECKING:
    from ai.backend.manager.pglock import PgAdvisoryLock


@dataclass
class DistributedLockSpec:
    config: ManagerUnifiedConfig
    etcd: AsyncEtcd
    database: ExtendedAsyncSAEngine


class DistributedLockProvisioner(Provisioner[DistributedLockSpec, DistributedLockFactory]):
    @property
    def name(self) -> str:
        return "distributed_lock"

    async def setup(self, spec: DistributedLockSpec) -> DistributedLockFactory:
        ipc_base_path = spec.config.manager.ipc_base_path
        manager_id = spec.config.manager.id
        lock_backend = spec.config.manager.distributed_lock

        match lock_backend:
            case "filelock":
                return lambda lock_id, lifetime_hint: FileLock(
                    ipc_base_path / f"{manager_id}.{lock_id}.lock",
                    timeout=0,
                )
            case "pg_advisory":
                return lambda lock_id, lifetime_hint: PgAdvisoryLock(spec.database, lock_id)
            case "redlock":
                redlock_config = spec.config.manager.redlock_config
                redis_profile_target: RedisProfileTarget = RedisProfileTarget.from_dict(
                    spec.config.redis.model_dump()
                )
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
                return lambda lock_id, lifetime_hint: EtcdLock(
                    str(lock_id),
                    spec.etcd,
                    lifetime=min(lifetime_hint * 2, lifetime_hint + 30),
                )
            case other:
                raise ValueError(f"Invalid lock backend: {other}")

    async def teardown(self, resource: DistributedLockFactory) -> None:
        # The factory itself doesn't need cleanup
        # Individual locks are cleaned up separately
        pass