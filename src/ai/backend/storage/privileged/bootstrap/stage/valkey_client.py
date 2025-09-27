from dataclasses import dataclass
from typing import override

from ai.backend.common.clients.valkey_client.valkey_bgtask.client import ValkeyBgtaskClient
from ai.backend.common.defs import REDIS_BGTASK_DB, RedisRole
from ai.backend.common.stage.types import (
    ArgsSpecGenerator,
    Provisioner,
    ProvisionStage,
)
from ai.backend.common.types import RedisProfileTarget


@dataclass
class ValkeyClientSpec:
    redis_profile_target: RedisProfileTarget


class ValkeyClientSpecGenerator(ArgsSpecGenerator[ValkeyClientSpec]):
    pass


@dataclass
class ValkeyClientResult:
    bgtask_client: ValkeyBgtaskClient


class ValkeyClientProvisioner(Provisioner[ValkeyClientSpec, ValkeyClientResult]):
    @property
    @override
    def name(self) -> str:
        return "storage-worker-valkey-client"

    @override
    async def setup(self, spec: ValkeyClientSpec) -> ValkeyClientResult:
        valkey_client = await ValkeyBgtaskClient.create(
            spec.redis_profile_target.profile_target(RedisRole.BGTASK).to_valkey_target(),
            human_readable_name="storage_privileged_bgtask",
            db_id=REDIS_BGTASK_DB,
        )
        return ValkeyClientResult(valkey_client)

    @override
    async def teardown(self, resource: ValkeyClientResult) -> None:
        await resource.bgtask_client.close()


class ValkeyClientStage(ProvisionStage[ValkeyClientSpec, ValkeyClientResult]):
    pass
