from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.stage.types import Provisioner
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.service.base import ServicesContext
from ai.backend.manager.service.container_registry.base import PerProjectRegistryQuotaRepository
from ai.backend.manager.service.container_registry.harbor import (
    PerProjectContainerRegistryQuotaClientPool,
    PerProjectContainerRegistryQuotaService,
)


@dataclass
class ServicesSpec:
    database: ExtendedAsyncSAEngine


class ServicesProvisioner(Provisioner[ServicesSpec, ServicesContext]):
    @property
    def name(self) -> str:
        return "services"

    async def setup(self, spec: ServicesSpec) -> ServicesContext:
        per_project_container_registries_quota = PerProjectContainerRegistryQuotaService(
            repository=PerProjectRegistryQuotaRepository(spec.database),
            client_pool=PerProjectContainerRegistryQuotaClientPool(),
        )

        services_ctx = ServicesContext(
            per_project_container_registries_quota,
        )
        return services_ctx

    async def teardown(self, resource: ServicesContext) -> None:
        # ServicesContext doesn't have an explicit cleanup method
        pass