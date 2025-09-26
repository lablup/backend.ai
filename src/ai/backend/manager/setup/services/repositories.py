from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.stage.types import Provisioner
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.image.repositories import RepositoryArgs
from ai.backend.manager.repositories.repositories import Repositories
from ai.backend.manager.setup.infrastructure.redis import ValkeyClients


@dataclass
class RepositoriesSpec:
    database: ExtendedAsyncSAEngine
    storage_manager: StorageSessionManager
    config_provider: ManagerConfigProvider
    valkey_clients: ValkeyClients


class RepositoriesProvisioner(Provisioner[RepositoriesSpec, Repositories]):
    @property
    def name(self) -> str:
        return "repositories"

    async def setup(self, spec: RepositoriesSpec) -> Repositories:
        repositories = Repositories.create(
            args=RepositoryArgs(
                db=spec.database,
                storage_manager=spec.storage_manager,
                config_provider=spec.config_provider,
                valkey_stat_client=spec.valkey_clients.valkey_stat,
            )
        )
        return repositories

    async def teardown(self, resource: Repositories) -> None:
        # Repositories don't have an explicit cleanup method
        pass