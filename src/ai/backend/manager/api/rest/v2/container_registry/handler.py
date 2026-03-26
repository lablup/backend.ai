"""REST v2 handler for the container registry domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam
from ai.backend.common.dto.manager.v2.container_registry.request import (
    AdminSearchContainerRegistriesInput,
    CreateContainerRegistryInput,
    DeleteContainerRegistryInput,
    UpdateContainerRegistryInput,
)
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.container_registry import ContainerRegistryAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2ContainerRegistryHandler:
    """REST v2 handler for container registry operations."""

    def __init__(self, *, adapter: ContainerRegistryAdapter) -> None:
        self._adapter = adapter

    async def admin_search_container_registries(
        self,
        body: BodyParam[AdminSearchContainerRegistriesInput],
    ) -> APIResponse:
        """Search container registries with admin scope."""
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_create(
        self,
        body: BodyParam[CreateContainerRegistryInput],
    ) -> APIResponse:
        """Create a new container registry (superadmin only)."""
        result = await self._adapter.admin_create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def admin_update(
        self,
        body: BodyParam[UpdateContainerRegistryInput],
    ) -> APIResponse:
        """Update an existing container registry (superadmin only)."""
        result = await self._adapter.admin_update(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_delete(
        self,
        body: BodyParam[DeleteContainerRegistryInput],
    ) -> APIResponse:
        """Delete a container registry (superadmin only). Hard delete via Purger."""
        result = await self._adapter.admin_delete(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
