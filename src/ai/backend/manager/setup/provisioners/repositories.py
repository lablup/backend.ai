import asyncio
from dataclasses import dataclass
from typing import override

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.stage.types import Provisioner, ProvisionStage, SpecGenerator
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.image.repositories import RepositoryArgs
from ai.backend.manager.repositories.repositories import Repositories
from ai.backend.manager.setup.provisioners.redis import RedisClients, RedisStage
from ai.backend.manager.setup.provisioners.storage_manager import StorageManagerStage


@dataclass
class RepositoriesSpec:
    db: ExtendedAsyncSAEngine
    storage_manager: StorageSessionManager
    config_provider: ManagerConfigProvider
    valkey_stat_client: ValkeyStatClient


class RepositoriesProvisioner(Provisioner):
    @property
    @override
    def name(self) -> str:
        return "repositories-provisioner"

    @override
    async def setup(self, spec: RepositoriesSpec) -> Repositories:
        return Repositories.create(
            args=RepositoryArgs(
                db=spec.db,
                storage_manager=spec.storage_manager,
                config_provider=spec.config_provider,
                valkey_stat_client=spec.valkey_stat_client,
            )
        )

    @override
    async def teardown(self, resource: Repositories) -> None:
        # Nothing to clean up
        pass


class RepositoriesSpecGenerator(SpecGenerator[RepositoriesSpec]):
    def __init__(
        self,
        redis_stage: RedisStage,
        storage_manager_stage: StorageManagerStage,
        db: ExtendedAsyncSAEngine,
        config_provider: ManagerConfigProvider,
    ):
        self.redis_stage = redis_stage
        self.storage_manager_stage = storage_manager_stage
        self.db = db
        self.config_provider = config_provider

    @override
    async def wait_for_spec(self) -> RepositoriesSpec:
        redis_clients_result, storage_manager_result = await asyncio.gather(
            self.redis_stage.wait_for_resource(), self.storage_manager_stage.wait_for_resource()
        )
        redis_clients: RedisClients = redis_clients_result
        storage_manager: StorageSessionManager = storage_manager_result
        return RepositoriesSpec(
            db=self.db,
            storage_manager=storage_manager,
            config_provider=self.config_provider,
            valkey_stat_client=redis_clients.valkey_stat,
        )


# Type alias for Repositories stage
RepositoriesStage = ProvisionStage[RepositoriesSpec, Repositories]
