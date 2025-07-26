from contextlib import asynccontextmanager as actxmgr
from dataclasses import dataclass
from typing import AsyncIterator, override

from ai.backend.common.stage.types import Provisioner, ProvisionStage, SpecGenerator
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.service.base import ServicesContext
from ai.backend.manager.service.container_registry.base import PerProjectRegistryQuotaRepository
from ai.backend.manager.service.container_registry.harbor import (
    PerProjectContainerRegistryQuotaClientPool,
    PerProjectContainerRegistryQuotaService,
)


@actxmgr
async def services_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    db = root_ctx.db

    per_project_container_registries_quota = PerProjectContainerRegistryQuotaService(
        repository=PerProjectRegistryQuotaRepository(db),
        client_pool=PerProjectContainerRegistryQuotaClientPool(),
    )

    root_ctx.services_ctx = ServicesContext(
        per_project_container_registries_quota,
    )
    yield None


@dataclass
class ServicesSpec:
    db: ExtendedAsyncSAEngine


class ServicesProvisioner(Provisioner):
    @property
    @override
    def name(self) -> str:
        return "services-provisioner"

    @override
    async def setup(self, spec: ServicesSpec) -> ServicesContext:
        per_project_container_registries_quota = PerProjectContainerRegistryQuotaService(
            repository=PerProjectRegistryQuotaRepository(spec.db),
            client_pool=PerProjectContainerRegistryQuotaClientPool(),
        )

        services_ctx = ServicesContext(
            per_project_container_registries_quota,
        )
        return services_ctx

    @override
    async def teardown(self, resource: ServicesContext) -> None:
        # Nothing to clean up
        pass


class ServicesSpecGenerator(SpecGenerator[ServicesSpec]):
    def __init__(self, db: ExtendedAsyncSAEngine):
        self.db = db

    @override
    async def wait_for_spec(self) -> ServicesSpec:
        return ServicesSpec(db=self.db)


# Type alias for Services stage
ServicesStage = ProvisionStage[ServicesSpec, ServicesContext]
