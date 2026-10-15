"""REST v2 handler for the container registry domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.data.entity.container_registry import ContainerRegistryID
from ai.backend.common.dto.manager.v2.container_registry.request import (
    AdminSearchContainerRegistriesInput,
    CreateContainerRegistryInput,
    DeleteContainerRegistryInput,
    PartialBulkPurgeContainerRegistriesInput,
    UpdateContainerRegistryInput,
)
from ai.backend.common.dto.manager.v2.container_registry.response import (
    DeleteContainerRegistryPayload,
)
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.api.rest.v2.path_params import RegistryIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.container_registry.adapter import ContainerRegistryAdapter

log: Final = StructuredLogger(logging.getLogger(__spec__.name))


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

    async def admin_purge(
        self,
        path: PathParam[RegistryIdPathParam],
    ) -> APIResponse:
        """Purge a container registry (superadmin only)."""
        result = await self._adapter.admin_purge(ContainerRegistryID(path.parsed.registry_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_partial_bulk_purge(
        self,
        body: BodyParam[PartialBulkPurgeContainerRegistriesInput],
    ) -> APIResponse:
        """Purge several container registries (superadmin only), answering for each one."""
        result = await self._adapter.admin_partial_bulk_purge(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_delete(
        self,
        body: BodyParam[DeleteContainerRegistryInput],
    ) -> APIResponse:
        """Deprecated. Use `DELETE /v2/container-registries/{registry_id}`."""
        result = await self._adapter.admin_purge(ContainerRegistryID(body.parsed.id))
        return APIResponse.build(
            status_code=HTTPStatus.OK, response_model=DeleteContainerRegistryPayload(id=result.id)
        )
