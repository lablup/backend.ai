"""New-style group module using RouteRegistry and constructor DI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.middleware.auth import superadmin_required
from ai.backend.manager.api.rest.routing import RouteRegistry

from .handler import GroupHandler

if TYPE_CHECKING:
    from ai.backend.manager.service.container_registry.harbor import (
        AbstractPerProjectContainerRegistryQuotaService,
    )
    from ai.backend.manager.services.processors import Processors


def register_routes(
    registry: RouteRegistry,
    processors: Processors,
    *,
    quota_service: AbstractPerProjectContainerRegistryQuotaService,
) -> None:
    """Register group routes on the given RouteRegistry.

    ``processors`` is forwarded to ``GroupHandler`` for constructor DI
    consistency.  The per-project container registry quota service has
    not yet been migrated to the Action/Processor pattern, so it is
    passed explicitly via *quota_service*.
    """
    handler = GroupHandler(processors=processors, quota_service=quota_service)

    registry.add(
        "POST",
        "/group/registry-quota",
        handler.create_registry_quota,
        middlewares=[superadmin_required],
    )
    registry.add(
        "GET",
        "/group/registry-quota",
        handler.read_registry_quota,
        middlewares=[superadmin_required],
    )
    registry.add(
        "PATCH",
        "/group/registry-quota",
        handler.update_registry_quota,
        middlewares=[superadmin_required],
    )
    registry.add(
        "DELETE",
        "/group/registry-quota",
        handler.delete_registry_quota,
        middlewares=[superadmin_required],
    )
