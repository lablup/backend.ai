from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.defs import REDIS_LIVE_DB, REDIS_STATISTICS_DB, RedisRole
from ai.backend.common.dependencies import DependencyProvider
from ai.backend.common.health_checker import CID_REDIS_LIVE, CID_REDIS_STAT, ServiceHealthChecker
from ai.backend.common.health_checker.checkers.valkey import ValkeyHealthChecker
from ai.backend.common.types import RedisProfileTarget

from ...config import ServerConfig


@dataclass
class WorkerValkeyClients:
    """Valkey clients for app proxy worker."""

    valkey_live: ValkeyLiveClient
    valkey_stat: ValkeyStatClient


class RedisProvider(DependencyProvider[ServerConfig, WorkerValkeyClients]):
    """Provider for Redis configuration and Valkey clients."""

    @property
    def stage_name(self) -> str:
        return "redis"

    @asynccontextmanager
    async def provide(self, setup_input: ServerConfig) -> AsyncIterator[WorkerValkeyClients]:
        """Create and provide Valkey clients."""
        redis_profile_target = RedisProfileTarget.from_dict(setup_input.redis.to_dict())

        valkey_live = await ValkeyLiveClient.create(
            valkey_target=redis_profile_target.profile_target(RedisRole.LIVE).to_valkey_target(),
            db_id=REDIS_LIVE_DB,
            human_readable_name="appproxy-worker",
        )
        valkey_stat = await ValkeyStatClient.create(
            valkey_target=redis_profile_target.profile_target(
                RedisRole.STATISTICS
            ).to_valkey_target(),
            db_id=REDIS_STATISTICS_DB,
            human_readable_name="appproxy-worker",
        )

        try:
            yield WorkerValkeyClients(
                valkey_live=valkey_live,
                valkey_stat=valkey_stat,
            )
        finally:
            await valkey_live.close()
            await valkey_stat.close()

    def gen_health_checkers(self, resource: WorkerValkeyClients) -> ServiceHealthChecker:
        """
        Return health checkers for worker Valkey clients.

        Args:
            resource: The initialized Valkey clients

        Returns:
            Health checker for Valkey clients
        """
        return ValkeyHealthChecker(
            clients={
                CID_REDIS_LIVE: resource.valkey_live,
                CID_REDIS_STAT: resource.valkey_stat,
            }
        )
