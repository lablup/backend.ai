from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..api.context import RootContext


@actxmgr
async def services_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from ..service.base import ServicesContext
    from ..service.container_registry.base import PerProjectRegistryQuotaRepository
    from ..service.container_registry.harbor import (
        PerProjectContainerRegistryQuotaClientPool,
        PerProjectContainerRegistryQuotaService,
    )

    db = root_ctx.db

    per_project_container_registries_quota = PerProjectContainerRegistryQuotaService(
        repository=PerProjectRegistryQuotaRepository(db),
        client_pool=PerProjectContainerRegistryQuotaClientPool(),
    )

    root_ctx.services_ctx = ServicesContext(
        per_project_container_registries_quota,
    )
    yield None
