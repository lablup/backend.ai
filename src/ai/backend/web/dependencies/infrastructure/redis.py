from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.common.clients.valkey_client.sentinel_monitor.monitor_set import SentinelMonitorSet
from ai.backend.common.clients.valkey_client.valkey_session.client import ValkeySessionClient
from ai.backend.common.defs import REDIS_STATISTICS_DB, RedisRole
from ai.backend.common.dependencies import DependencyProvider
from ai.backend.common.health_checker import CID_REDIS_SESSION, ServiceHealthChecker
from ai.backend.common.health_checker.checkers.valkey import ValkeyHealthChecker
from ai.backend.web.config.unified import WebServerUnifiedConfig


@dataclass
class RedisProviderInput:
    config: WebServerUnifiedConfig
    sentinel_monitors: SentinelMonitorSet


class RedisProvider(DependencyProvider[RedisProviderInput, ValkeySessionClient]):
    """
    Provider for Redis/Valkey session storage.
    """

    @property
    @override
    def stage_name(self) -> str:
        return "redis"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: RedisProviderInput) -> AsyncIterator[ValkeySessionClient]:
        """
        Provide ValkeySessionClient for session storage.
        """
        valkey_profile_target = setup_input.config.session.redis.to_valkey_profile_target()
        valkey_target = valkey_profile_target.profile_target(RedisRole.STATISTICS)

        # Create ValkeySessionClient for session management
        valkey_session_client = await ValkeySessionClient.create(
            valkey_target=valkey_target,
            db_id=REDIS_STATISTICS_DB,
            human_readable_name="web.session",
            sentinel_monitor=setup_input.sentinel_monitors.monitor_for(valkey_target),
        )

        try:
            yield valkey_session_client
        finally:
            await valkey_session_client.close()

    @override
    def gen_liveness_checker(self, resource: ValkeySessionClient) -> ServiceHealthChecker:
        """Liveness — Valkey connection-stuck observed; restart recovers."""
        return ValkeyHealthChecker(clients={CID_REDIS_SESSION: resource})
