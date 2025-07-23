from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.clients.valkey_client.valkey_stream.client import ValkeyStreamClient
from ai.backend.common.defs import (
    REDIS_IMAGE_DB,
    REDIS_LIVE_DB,
    REDIS_STATISTICS_DB,
    REDIS_STREAM_DB,
)
from ai.backend.common.stage.types import Provisioner
from ai.backend.common.types import RedisProfileTarget, RedisRole
from ai.backend.manager.config.unified import ManagerUnifiedConfig


@dataclass
class ValkeyClients:
    """Container for all Valkey/Redis client instances"""

    valkey_live: ValkeyLiveClient
    valkey_stat: ValkeyStatClient
    valkey_image: ValkeyImageClient
    valkey_stream: ValkeyStreamClient


@dataclass
class ValkeyClientsSpec:
    config: ManagerUnifiedConfig


class ValkeyClientsProvisioner(Provisioner[ValkeyClientsSpec, ValkeyClients]):
    @property
    def name(self) -> str:
        return "valkey_clients"

    async def setup(self, spec: ValkeyClientsSpec) -> ValkeyClients:
        # Create Redis profile target from configuration
        redis_profile_target = RedisProfileTarget.from_dict(spec.config.redis.model_dump())

        # Initialize all Valkey clients
        valkey_live = await ValkeyLiveClient.create(
            redis_profile_target.profile_target(RedisRole.LIVE),
            db_id=REDIS_LIVE_DB,
            human_readable_name="live",  # tracking live status of various entities
        )

        valkey_stat = await ValkeyStatClient.create(
            redis_profile_target.profile_target(RedisRole.STATISTICS),
            db_id=REDIS_STATISTICS_DB,
            human_readable_name="stat",  # temporary storage for stat snapshots
        )

        valkey_image = await ValkeyImageClient.create(
            redis_profile_target.profile_target(RedisRole.IMAGE),
            db_id=REDIS_IMAGE_DB,
            human_readable_name="image",  # per-agent image availability
        )

        valkey_stream = await ValkeyStreamClient.create(
            redis_profile_target.profile_target(RedisRole.STREAM),
            human_readable_name="stream",
            db_id=REDIS_STREAM_DB,
        )

        # Health check - verify connectivity
        await valkey_live.get_server_time()

        return ValkeyClients(
            valkey_live=valkey_live,
            valkey_stat=valkey_stat,
            valkey_image=valkey_image,
            valkey_stream=valkey_stream,
        )

    async def teardown(self, resource: ValkeyClients) -> None:
        # Close all clients in reverse order
        await resource.valkey_stream.close()
        await resource.valkey_image.close()
        await resource.valkey_stat.close()
        await resource.valkey_live.close()
