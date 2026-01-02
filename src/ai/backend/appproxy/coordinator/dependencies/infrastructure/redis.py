from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from redis.asyncio import Redis

from ai.backend.common import redis_helper
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_schedule import ValkeyScheduleClient
from ai.backend.common.defs import REDIS_LIVE_DB, REDIS_STREAM_LOCK, RedisRole
from ai.backend.common.dependencies import DependencyProvider
from ai.backend.common.health_checker import (
    CID_REDIS_CORE_LIVE,
    CID_REDIS_LIVE,
    CID_REDIS_SCHEDULE,
    ServiceHealthChecker,
)
from ai.backend.common.health_checker.checkers.valkey import ValkeyHealthChecker
from ai.backend.common.types import RedisProfileTarget

from ...config import ServerConfig


@dataclass
class CoordinatorValkeyClients:
    """Valkey and Redis clients for app proxy coordinator."""

    valkey_live: ValkeyLiveClient
    core_valkey_live: ValkeyLiveClient
    redis_lock: Redis
    valkey_schedule: ValkeyScheduleClient


class RedisProvider(DependencyProvider[ServerConfig, CoordinatorValkeyClients]):
    """Provider for Redis configuration and Valkey clients."""

    @property
    def stage_name(self) -> str:
        return "redis"

    @asynccontextmanager
    async def provide(self, setup_input: ServerConfig) -> AsyncIterator[CoordinatorValkeyClients]:
        """Create and provide Redis/Valkey clients."""
        redis_profile_target = RedisProfileTarget.from_dict(setup_input.redis.to_dict())
        core_redis_profile_target = RedisProfileTarget.from_dict(
            (setup_input.core_redis or setup_input.redis).to_dict()
        )

        # Create valkey clients for live data access
        valkey_live = await ValkeyLiveClient.create(
            valkey_target=redis_profile_target.profile_target(RedisRole.LIVE).to_valkey_target(),
            db_id=REDIS_LIVE_DB,
            human_readable_name="appproxy-coordinator-live",
        )
        core_valkey_live = await ValkeyLiveClient.create(
            valkey_target=core_redis_profile_target.profile_target(
                RedisRole.LIVE
            ).to_valkey_target(),
            db_id=REDIS_LIVE_DB,
            human_readable_name="appproxy-coordinator-core-live",
        )

        # Keep redis_lock for distributed locking (not yet migrated)
        redis_lock = redis_helper.get_redis_object_for_lock(
            redis_profile_target.profile_target(RedisRole.STREAM),
            name="lock",  # distributed locks
            db=REDIS_STREAM_LOCK,
        )

        # Initialize ValkeyScheduleClient for health status updates
        valkey_schedule = await ValkeyScheduleClient.create(
            valkey_target=core_redis_profile_target.profile_target(
                RedisRole.STREAM
            ).to_valkey_target(),
            db_id=REDIS_LIVE_DB,
            human_readable_name="appproxy-schedule",
        )

        try:
            yield CoordinatorValkeyClients(
                valkey_live=valkey_live,
                core_valkey_live=core_valkey_live,
                redis_lock=redis_lock.client,
                valkey_schedule=valkey_schedule,
            )
        finally:
            await valkey_live.close()
            await core_valkey_live.close()
            await valkey_schedule.close()
            await redis_lock.close()

    def gen_health_checkers(self, resource: CoordinatorValkeyClients) -> ServiceHealthChecker:
        """
        Return health checkers for coordinator Valkey clients.

        Args:
            resource: The initialized Valkey clients

        Returns:
            Health checker for Valkey clients
        """
        return ValkeyHealthChecker(
            clients={
                CID_REDIS_LIVE: resource.valkey_live,
                CID_REDIS_CORE_LIVE: resource.core_valkey_live,
                CID_REDIS_SCHEDULE: resource.valkey_schedule,
            }
        )
