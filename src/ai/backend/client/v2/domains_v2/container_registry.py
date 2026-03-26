"""V2 REST SDK client for the container registry domain."""

from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.container_registry.request import (
    AdminSearchContainerRegistriesInput,
    CreateContainerRegistryInput,
    DeleteContainerRegistryInput,
    UpdateContainerRegistryInput,
)
from ai.backend.common.dto.manager.v2.container_registry.response import (
    AdminSearchContainerRegistriesPayload,
    CreateContainerRegistryPayload,
    DeleteContainerRegistryPayload,
    UpdateContainerRegistryPayload,
)

_PATH = "/v2/container-registries"


class V2ContainerRegistryClient(BaseDomainClient):
    """SDK client for the ``/v2/container-registries`` REST endpoints."""

    async def admin_search(
        self,
        request: AdminSearchContainerRegistriesInput,
    ) -> AdminSearchContainerRegistriesPayload:
        """Search container registries with admin scope."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=AdminSearchContainerRegistriesPayload,
        )

    async def admin_create(
        self,
        request: CreateContainerRegistryInput,
    ) -> CreateContainerRegistryPayload:
        """Create a new container registry (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            _PATH,
            request=request,
            response_model=CreateContainerRegistryPayload,
        )

    async def admin_update(
        self,
        request: UpdateContainerRegistryInput,
    ) -> UpdateContainerRegistryPayload:
        """Update an existing container registry (superadmin only)."""
        return await self._client.typed_request(
            "PATCH",
            _PATH,
            request=request,
            response_model=UpdateContainerRegistryPayload,
        )

    async def admin_delete(
        self,
        request: DeleteContainerRegistryInput,
    ) -> DeleteContainerRegistryPayload:
        """Delete a container registry (superadmin only). Hard delete."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/delete",
            request=request,
            response_model=DeleteContainerRegistryPayload,
        )
