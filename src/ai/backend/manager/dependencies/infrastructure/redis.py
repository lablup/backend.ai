from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import override

from ai.backend.common.clients.valkey_client.sentinel_monitor.monitor_set import (
    SentinelMonitorSet,
)
from ai.backend.common.clients.valkey_client.valkey_artifact.client import (
    ValkeyArtifactDownloadTrackingClient,
)
from ai.backend.common.clients.valkey_client.valkey_bgtask.client import ValkeyBgtaskClient
from ai.backend.common.clients.valkey_client.valkey_container_log.client import (
    ValkeyContainerLogClient,
)
from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_rate_limit.client import ValkeyRateLimitClient
from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.clients.valkey_client.valkey_session.client import ValkeySessionClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.clients.valkey_client.valkey_stream.client import ValkeyStreamClient
from ai.backend.common.defs import (
    REDIS_BGTASK_DB,
    REDIS_CONTAINER_LOG,
    REDIS_IMAGE_DB,
    REDIS_LIVE_DB,
    REDIS_RATE_LIMIT_DB,
    REDIS_STATISTICS_DB,
    REDIS_STREAM_DB,
    RedisRole,
)
from ai.backend.common.dependencies import DependencyProvider
from ai.backend.common.health_checker import (
    CID_REDIS_ARTIFACT,
    CID_REDIS_BGTASK,
    CID_REDIS_CONTAINER_LOG,
    CID_REDIS_IMAGE,
    CID_REDIS_LIVE,
    CID_REDIS_SCHEDULE,
    CID_REDIS_STAT,
    CID_REDIS_STREAM,
    ServiceHealthChecker,
)
from ai.backend.common.health_checker.checkers.valkey import ValkeyHealthChecker
from ai.backend.manager.config.unified import ManagerUnifiedConfig


@dataclass
class ValkeyInput:
    config: ManagerUnifiedConfig
    sentinel_monitors: SentinelMonitorSet


@dataclass
class ValkeyClients:
    """Container for all specialized Valkey client instances."""

    artifact: ValkeyArtifactDownloadTrackingClient
    container_log: ValkeyContainerLogClient
    live: ValkeyLiveClient
    stat: ValkeyStatClient
    image: ValkeyImageClient
    stream: ValkeyStreamClient
    schedule: ValkeyScheduleClient
    bgtask: ValkeyBgtaskClient
    rate_limit: ValkeyRateLimitClient
    session: ValkeySessionClient

    async def close(self) -> None:
        """Close all Valkey client connections."""
        await self.rate_limit.flush_database()
        await self.rate_limit.close()
        await self.artifact.close()
        await self.container_log.close()
        await self.image.close()
        await self.stat.close()
        await self.live.close()
        await self.stream.close()
        await self.schedule.close()
        await self.bgtask.close()
        await self.session.close()


class ValkeyDependency(DependencyProvider[ValkeyInput, ValkeyClients]):
    """Provides lifecycle management for 9 specialized Valkey clients."""

    @property
    @override
    def stage_name(self) -> str:
        return "valkey"

    @asynccontextmanager
    @override
    async def provide(self, setup_input: ValkeyInput) -> AsyncIterator[ValkeyClients]:
        """Initialize and provide all Valkey clients.

        Args:
            setup_input: Configuration containing redis settings and the Sentinel monitors

        Yields:
            ValkeyClients instance containing all 9 specialized clients
        """
        valkey_profile_target = setup_input.config.redis.to_valkey_profile_target()
        sentinel_monitors = setup_input.sentinel_monitors

        # Create all 9 specialized clients
        clients = ValkeyClients(
            artifact=await ValkeyArtifactDownloadTrackingClient.create(
                valkey_profile_target.profile_target(RedisRole.STATISTICS),
                db_id=REDIS_STATISTICS_DB,
                human_readable_name="artifact",
                sentinel_monitor=sentinel_monitors.monitor_for(
                    valkey_profile_target.profile_target(RedisRole.STATISTICS)
                ),
            ),
            container_log=await ValkeyContainerLogClient.create(
                valkey_profile_target.profile_target(RedisRole.CONTAINER_LOG),
                db_id=REDIS_CONTAINER_LOG,
                human_readable_name="container_log",
                sentinel_monitor=sentinel_monitors.monitor_for(
                    valkey_profile_target.profile_target(RedisRole.CONTAINER_LOG)
                ),
            ),
            live=await ValkeyLiveClient.create(
                valkey_profile_target.profile_target(RedisRole.LIVE),
                db_id=REDIS_LIVE_DB,
                human_readable_name="live",
                sentinel_monitor=sentinel_monitors.monitor_for(
                    valkey_profile_target.profile_target(RedisRole.LIVE)
                ),
            ),
            stat=await ValkeyStatClient.create(
                valkey_profile_target.profile_target(RedisRole.STATISTICS),
                db_id=REDIS_STATISTICS_DB,
                human_readable_name="stat",
                sentinel_monitor=sentinel_monitors.monitor_for(
                    valkey_profile_target.profile_target(RedisRole.STATISTICS)
                ),
            ),
            image=await ValkeyImageClient.create(
                valkey_profile_target.profile_target(RedisRole.IMAGE),
                db_id=REDIS_IMAGE_DB,
                human_readable_name="image",
                sentinel_monitor=sentinel_monitors.monitor_for(
                    valkey_profile_target.profile_target(RedisRole.IMAGE)
                ),
            ),
            stream=await ValkeyStreamClient.create(
                valkey_profile_target.profile_target(RedisRole.STREAM),
                human_readable_name="stream",
                db_id=REDIS_STREAM_DB,
                sentinel_monitor=sentinel_monitors.monitor_for(
                    valkey_profile_target.profile_target(RedisRole.STREAM)
                ),
            ),
            schedule=await ValkeyScheduleClient.create(
                valkey_profile_target.profile_target(RedisRole.STREAM),
                db_id=REDIS_LIVE_DB,
                human_readable_name="schedule",
                sentinel_monitor=sentinel_monitors.monitor_for(
                    valkey_profile_target.profile_target(RedisRole.STREAM)
                ),
            ),
            bgtask=await ValkeyBgtaskClient.create(
                valkey_profile_target.profile_target(RedisRole.BGTASK),
                human_readable_name="bgtask",
                db_id=REDIS_BGTASK_DB,
                sentinel_monitor=sentinel_monitors.monitor_for(
                    valkey_profile_target.profile_target(RedisRole.BGTASK)
                ),
            ),
            rate_limit=await ValkeyRateLimitClient.create(
                valkey_profile_target.profile_target(RedisRole.RATE_LIMIT),
                db_id=REDIS_RATE_LIMIT_DB,
                human_readable_name="ratelimit",
                sentinel_monitor=sentinel_monitors.monitor_for(
                    valkey_profile_target.profile_target(RedisRole.RATE_LIMIT)
                ),
            ),
            session=await ValkeySessionClient.create(
                valkey_profile_target.profile_target(RedisRole.STATISTICS),
                db_id=REDIS_STATISTICS_DB,
                human_readable_name="session",
                sentinel_monitor=sentinel_monitors.monitor_for(
                    valkey_profile_target.profile_target(RedisRole.STATISTICS)
                ),
            ),
        )

        # Health check
        await clients.live.get_server_time()

        try:
            yield clients
        finally:
            await clients.close()

    @override
    def gen_liveness_checker(
        self,
        resource: ValkeyClients,
    ) -> ServiceHealthChecker:
        """Liveness — Valkey connection-stuck observed; restart recovers."""
        return ValkeyHealthChecker(
            clients={
                CID_REDIS_ARTIFACT: resource.artifact,
                CID_REDIS_CONTAINER_LOG: resource.container_log,
                CID_REDIS_LIVE: resource.live,
                CID_REDIS_STAT: resource.stat,
                CID_REDIS_IMAGE: resource.image,
                CID_REDIS_STREAM: resource.stream,
                CID_REDIS_SCHEDULE: resource.schedule,
                CID_REDIS_BGTASK: resource.bgtask,
            }
        )
