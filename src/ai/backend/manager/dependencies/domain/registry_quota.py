from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from ai.backend.manager.repositories.container_registry_quota.repository import (
    PerProjectRegistryQuotaRepository,
)
from ai.backend.manager.services.container_registry.quota import (
    AbstractPerProjectContainerRegistryQuotaService,
    PerProjectContainerRegistryQuotaClientPool,
    PerProjectContainerRegistryQuotaService,
)

from .base import DomainDependency

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


@dataclass
class RegistryQuotaServiceInput:
    """Input required for the registry quota service setup."""

    db: ExtendedAsyncSAEngine


class RegistryQuotaServiceDependency(
    DomainDependency[RegistryQuotaServiceInput, AbstractPerProjectContainerRegistryQuotaService]
):
    """Provides the per-project container registry quota service."""

    @property
    @override
    def stage_name(self) -> str:
        return "registry-quota-service"

    @asynccontextmanager
    @override
    async def provide(
        self, setup_input: RegistryQuotaServiceInput
    ) -> AsyncIterator[AbstractPerProjectContainerRegistryQuotaService]:
        yield PerProjectContainerRegistryQuotaService(
            repository=PerProjectRegistryQuotaRepository(setup_input.db),
            client_pool=PerProjectContainerRegistryQuotaClientPool(),
        )
