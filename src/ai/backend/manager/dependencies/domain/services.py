from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai.backend.manager.repositories.container_registry_quota.repository import (
    PerProjectRegistryQuotaRepository,
)
from ai.backend.manager.service.base import ServicesContext
from ai.backend.manager.service.container_registry.harbor import (
    PerProjectContainerRegistryQuotaClientPool,
    PerProjectContainerRegistryQuotaService,
)

from .base import DomainDependency

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


@dataclass
class ServicesInput:
    """Input required for services context setup."""

    db: ExtendedAsyncSAEngine


class ServicesContextDependency(DomainDependency[ServicesInput, ServicesContext]):
    """Provides ServicesContext lifecycle management.

    ServicesContext aggregates service-layer objects that are used by the API layer.
    """

    @property
    def stage_name(self) -> str:
        return "services-context"

    @asynccontextmanager
    async def provide(self, setup_input: ServicesInput) -> AsyncIterator[ServicesContext]:
        """Initialize and provide a ServicesContext.

        Args:
            setup_input: Input containing the database engine.

        Yields:
            Initialized ServicesContext instance.
        """
        per_project_container_registries_quota = PerProjectContainerRegistryQuotaService(
            repository=PerProjectRegistryQuotaRepository(setup_input.db),
            client_pool=PerProjectContainerRegistryQuotaClientPool(),
        )
        yield ServicesContext(per_project_container_registries_quota)
