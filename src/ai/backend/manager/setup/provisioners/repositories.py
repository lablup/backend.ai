from dataclasses import dataclass
from typing import override

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.stage.types import Provisioner
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.image.repositories import RepositoryArgs
from ai.backend.manager.repositories.repositories import Repositories


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
