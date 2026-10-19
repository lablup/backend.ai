from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.appproxy.worker.config import ServerConfig
from ai.backend.common.clients.valkey_client.sentinel_monitor.monitor_set import SentinelMonitorSet
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.defs import REDIS_LIVE_DB, REDIS_STATISTICS_DB, RedisRole
from ai.backend.common.dependencies import DependencyProvider
from ai.backend.common.health_checker import CID_REDIS_LIVE, CID_REDIS_STAT, ServiceHealthChecker
from ai.backend.common.health_checker.checkers.valkey import ValkeyHealthChecker
from ai.backend.common.types import RedisProfileTarget


@dataclass
class WorkerValkeyClients:
    """Valkey clients for app proxy worker."""

    valkey_live: ValkeyLiveClient
    valkey_stat: ValkeyStatClient


@dataclass
class RedisProviderInput:
    config: ServerConfig
    sentinel_monitors: SentinelMonitorSet


class RedisProvider(DependencyProvider[RedisProviderInput, WorkerValkeyClients]):
    """Provider for Redis configuration and Valkey clients."""

    @property
    @override
    def stage_name(self) -> str:
        return "redis"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: RedisProviderInput) -> AsyncIterator[WorkerValkeyClients]:
        """Create and provide Valkey clients."""
        sentinel_monitors = setup_input.sentinel_monitors
        redis_profile_target = RedisProfileTarget.from_dict(setup_input.config.redis.to_dict())
        live_target = redis_profile_target.profile_target(RedisRole.LIVE).to_valkey_target()
        stat_target = redis_profile_target.profile_target(RedisRole.STATISTICS).to_valkey_target()

        valkey_live = await ValkeyLiveClient.create(
            valkey_target=live_target,
            db_id=REDIS_LIVE_DB,
            human_readable_name="appproxy-worker",
            sentinel_monitor=sentinel_monitors.monitor_for(live_target),
        )
        valkey_stat = await ValkeyStatClient.create(
            valkey_target=stat_target,
            db_id=REDIS_STATISTICS_DB,
            human_readable_name="appproxy-worker",
            sentinel_monitor=sentinel_monitors.monitor_for(stat_target),
        )

        try:
            yield WorkerValkeyClients(
                valkey_live=valkey_live,
                valkey_stat=valkey_stat,
            )
        finally:
            await valkey_live.close()
            await valkey_stat.close()

    @override
    def gen_liveness_checker(self, resource: WorkerValkeyClients) -> ServiceHealthChecker:
        """Liveness — Valkey connection-stuck observed; restart recovers."""
        return ValkeyHealthChecker(
            clients={
                CID_REDIS_LIVE: resource.valkey_live,
                CID_REDIS_STAT: resource.valkey_stat,
            }
        )
