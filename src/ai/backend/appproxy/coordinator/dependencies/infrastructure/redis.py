from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.appproxy.coordinator.config import ServerConfig
from ai.backend.common.clients.valkey_client.sentinel_monitor.monitor_set import SentinelMonitorSet
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_lock.client import ValkeyLockClient
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


@dataclass
class CoordinatorValkeyClients:
    """Valkey clients for app proxy coordinator."""

    valkey_live: ValkeyLiveClient
    core_valkey_live: ValkeyLiveClient
    valkey_lock: ValkeyLockClient
    valkey_schedule: ValkeyScheduleClient


@dataclass
class RedisProviderInput:
    config: ServerConfig
    sentinel_monitors: SentinelMonitorSet


class RedisProvider(DependencyProvider[RedisProviderInput, CoordinatorValkeyClients]):
    """Provider for Redis configuration and Valkey clients."""

    @property
    @override
    def stage_name(self) -> str:
        return "redis"

    @asynccontextmanager
    @override
    async def provide(
        self, setup_input: RedisProviderInput
    ) -> AsyncIterator[CoordinatorValkeyClients]:
        """Create and provide Redis/Valkey clients."""
        config = setup_input.config
        sentinel_monitors = setup_input.sentinel_monitors
        redis_profile_target = RedisProfileTarget.from_dict(config.redis.to_dict())
        core_redis_profile_target = RedisProfileTarget.from_dict(
            (config.core_redis or config.redis).to_dict()
        )
        live_target = redis_profile_target.profile_target(RedisRole.LIVE).to_valkey_target()
        core_live_target = core_redis_profile_target.profile_target(
            RedisRole.LIVE
        ).to_valkey_target()
        core_stream_target = core_redis_profile_target.profile_target(
            RedisRole.STREAM
        ).to_valkey_target()

        # Create valkey clients for live data access
        valkey_live = await ValkeyLiveClient.create(
            valkey_target=live_target,
            db_id=REDIS_LIVE_DB,
            human_readable_name="appproxy-coordinator-live",
            sentinel_monitor=sentinel_monitors.monitor_for(live_target),
        )
        core_valkey_live = await ValkeyLiveClient.create(
            valkey_target=core_live_target,
            db_id=REDIS_LIVE_DB,
            human_readable_name="appproxy-coordinator-core-live",
            sentinel_monitor=sentinel_monitors.monitor_for(core_live_target),
        )

        lock_target = redis_profile_target.profile_target(RedisRole.STREAM).to_valkey_target()
        valkey_lock = await ValkeyLockClient.create(
            valkey_target=lock_target,
            db_id=REDIS_STREAM_LOCK,
            human_readable_name="appproxy-coordinator-lock",
            sentinel_monitor=sentinel_monitors.monitor_for(lock_target),
        )

        # Initialize ValkeyScheduleClient for health status updates
        valkey_schedule = await ValkeyScheduleClient.create(
            valkey_target=core_stream_target,
            db_id=REDIS_LIVE_DB,
            human_readable_name="appproxy-schedule",
            sentinel_monitor=sentinel_monitors.monitor_for(core_stream_target),
        )

        try:
            yield CoordinatorValkeyClients(
                valkey_live=valkey_live,
                core_valkey_live=core_valkey_live,
                valkey_lock=valkey_lock,
                valkey_schedule=valkey_schedule,
            )
        finally:
            await valkey_live.close()
            await core_valkey_live.close()
            await valkey_schedule.close()
            await valkey_lock.close()

    @override
    def gen_liveness_checker(self, resource: CoordinatorValkeyClients) -> ServiceHealthChecker:
        """Liveness — Valkey connection-stuck observed; restart recovers."""
        return ValkeyHealthChecker(
            clients={
                CID_REDIS_LIVE: resource.valkey_live,
                CID_REDIS_CORE_LIVE: resource.core_valkey_live,
                CID_REDIS_SCHEDULE: resource.valkey_schedule,
            }
        )
