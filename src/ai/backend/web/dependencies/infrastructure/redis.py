from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai.backend.common.clients.valkey_client.valkey_session.client import ValkeySessionClient
from ai.backend.common.defs import REDIS_STATISTICS_DB, RedisRole
from ai.backend.common.dependencies import DependencyProvider
from ai.backend.common.health_checker import CID_REDIS_SESSION, ServiceHealthChecker
from ai.backend.common.health_checker.checkers.valkey import ValkeyHealthChecker
from ai.backend.web.config.unified import WebServerUnifiedConfig


class RedisProvider(DependencyProvider[WebServerUnifiedConfig, ValkeySessionClient]):
    """
    Provider for Redis/Valkey session storage.
    """

    @property
    def stage_name(self) -> str:
        return "redis"

    @asynccontextmanager
    async def provide(
        self, setup_input: WebServerUnifiedConfig
    ) -> AsyncIterator[ValkeySessionClient]:
        """
        Provide ValkeySessionClient for session storage.
        """
        valkey_profile_target = setup_input.session.redis.to_valkey_profile_target()
        valkey_target = valkey_profile_target.profile_target(RedisRole.STATISTICS)

        # Create ValkeySessionClient for session management
        valkey_session_client = await ValkeySessionClient.create(
            valkey_target=valkey_target,
            db_id=REDIS_STATISTICS_DB,
            human_readable_name="web.session",
        )

        try:
            yield valkey_session_client
        finally:
            await valkey_session_client.close()

    def gen_health_checkers(self, resource: ValkeySessionClient) -> ServiceHealthChecker:
        """
        Return health checker for session Valkey client.

        Args:
            resource: The initialized Valkey session client

        Returns:
            Health checker for session storage
        """
        return ValkeyHealthChecker(clients={CID_REDIS_SESSION: resource})
