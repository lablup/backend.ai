from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import TYPE_CHECKING

from ai.backend.common.clients.valkey_client.valkey_bgtask.client import ValkeyBgtaskClient
from ai.backend.common.clients.valkey_client.valkey_container_log.client import (
    ValkeyContainerLogClient,
)
from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.clients.valkey_client.valkey_stream.client import ValkeyStreamClient
from ai.backend.common.defs import (
    REDIS_BGTASK_DB,
    REDIS_CONTAINER_LOG,
    REDIS_IMAGE_DB,
    REDIS_LIVE_DB,
    REDIS_STATISTICS_DB,
    REDIS_STREAM_DB,
    RedisRole,
)

if TYPE_CHECKING:
    from ..api.context import RootContext


@actxmgr
async def redis_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    valkey_profile_target = root_ctx.config_provider.config.redis.to_valkey_profile_target()
    root_ctx.valkey_profile_target = valkey_profile_target

    root_ctx.valkey_container_log = await ValkeyContainerLogClient.create(
        valkey_profile_target.profile_target(RedisRole.CONTAINER_LOG),
        db_id=REDIS_CONTAINER_LOG,
        human_readable_name="container_log",  # saving container_log queue
    )
    root_ctx.valkey_live = await ValkeyLiveClient.create(
        valkey_profile_target.profile_target(RedisRole.LIVE),
        db_id=REDIS_LIVE_DB,
        human_readable_name="live",  # tracking live status of various entities
    )
    root_ctx.valkey_stat = await ValkeyStatClient.create(
        valkey_profile_target.profile_target(RedisRole.STATISTICS),
        db_id=REDIS_STATISTICS_DB,
        human_readable_name="stat",  # temporary storage for stat snapshots
    )
    root_ctx.valkey_image = await ValkeyImageClient.create(
        valkey_profile_target.profile_target(RedisRole.IMAGE),
        db_id=REDIS_IMAGE_DB,
        human_readable_name="image",  # per-agent image availability
    )
    root_ctx.valkey_stream = await ValkeyStreamClient.create(
        valkey_profile_target.profile_target(RedisRole.STREAM),
        human_readable_name="stream",
        db_id=REDIS_STREAM_DB,
    )
    root_ctx.valkey_schedule = await ValkeyScheduleClient.create(
        valkey_profile_target.profile_target(RedisRole.STREAM),
        db_id=REDIS_LIVE_DB,
        human_readable_name="schedule",  # scheduling marks and coordination
    )
    root_ctx.valkey_bgtask = await ValkeyBgtaskClient.create(
        valkey_profile_target.profile_target(RedisRole.BGTASK),
        human_readable_name="bgtask",
        db_id=REDIS_BGTASK_DB,
    )
    # Ping ValkeyLiveClient directly
    await root_ctx.valkey_live.get_server_time()
    # ValkeyImageClient has its own connection handling
    # No need to ping it separately as it's already connected
    yield
    await root_ctx.valkey_container_log.close()
    await root_ctx.valkey_image.close()
    await root_ctx.valkey_stat.close()
    await root_ctx.valkey_live.close()
    await root_ctx.valkey_stream.close()
    await root_ctx.valkey_schedule.close()
    await root_ctx.valkey_bgtask.close()
