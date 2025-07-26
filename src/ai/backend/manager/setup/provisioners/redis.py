from dataclasses import dataclass
from typing import override

from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.clients.valkey_client.valkey_stream.client import ValkeyStreamClient
from ai.backend.common.defs import (
    REDIS_IMAGE_DB,
    REDIS_LIVE_DB,
    REDIS_STATISTICS_DB,
    REDIS_STREAM_DB,
    RedisRole,
)
from ai.backend.common.stage.types import Provisioner
from ai.backend.common.types import RedisProfileTarget
from ai.backend.manager.config.unified import RedisConfig


@dataclass
class RedisSpec:
    redis_config: RedisConfig


@dataclass
class RedisClients:
    redis_profile_target: RedisProfileTarget
    valkey_live: ValkeyLiveClient
    valkey_stat: ValkeyStatClient
    valkey_image: ValkeyImageClient
    valkey_stream: ValkeyStreamClient


class RedisProvisioner(Provisioner):
    @property
    @override
    def name(self) -> str:
        return "redis-provisioner"

    @override
    async def setup(self, spec: RedisSpec) -> RedisClients:
        redis_profile_target = RedisProfileTarget.from_dict(spec.redis_config.model_dump())
        valkey_live = await ValkeyLiveClient.create(
            redis_profile_target.profile_target(RedisRole.LIVE),
            db_id=REDIS_LIVE_DB,
            human_readable_name="live",
        )
        valkey_stat = await ValkeyStatClient.create(
            redis_profile_target.profile_target(RedisRole.STATISTICS),
            db_id=REDIS_STATISTICS_DB,
            human_readable_name="stat",
        )
        valkey_image = await ValkeyImageClient.create(
            redis_profile_target.profile_target(RedisRole.IMAGE),
            db_id=REDIS_IMAGE_DB,
            human_readable_name="image",
        )
        valkey_stream = await ValkeyStreamClient.create(
            redis_profile_target.profile_target(RedisRole.STREAM),
            human_readable_name="stream",
            db_id=REDIS_STREAM_DB,
        )
        return RedisClients(
            redis_profile_target=redis_profile_target,
            valkey_live=valkey_live,
            valkey_stat=valkey_stat,
            valkey_image=valkey_image,
            valkey_stream=valkey_stream,
        )

    @override
    async def teardown(self, resource: RedisClients) -> None:
        await resource.valkey_image.close()
        await resource.valkey_stat.close()
        await resource.valkey_live.close()
        await resource.valkey_stream.close()
