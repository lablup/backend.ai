"""V2 SDK client for the resource group domain."""

from __future__ import annotations

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.resource_group.request import (
    AdminSearchResourceGroupsInput,
    CreateResourceGroupInput,
    UpdateResourceGroupConfigInput,
    UpdateResourceGroupFairShareSpecInput,
    UpdateResourceGroupInput,
)
from ai.backend.common.dto.manager.v2.resource_group.response import (
    AdminSearchResourceGroupsPayload,
    CreateResourceGroupPayload,
    DeleteResourceGroupPayload,
    ResourceGroupNode,
    ResourceInfoNode,
    UpdateResourceGroupConfigPayloadNode,
    UpdateResourceGroupFairShareSpecPayloadNode,
    UpdateResourceGroupPayload,
)

_PATH = "/v2/resource-groups"


class V2ResourceGroupClient(BaseDomainClient):
    """SDK client for resource group management."""

    async def search(
        self, request: AdminSearchResourceGroupsInput
    ) -> AdminSearchResourceGroupsPayload:
        """Search resource groups with filters, orders, and pagination."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=AdminSearchResourceGroupsPayload,
        )

    async def create(self, request: CreateResourceGroupInput) -> CreateResourceGroupPayload:
        """Create a new resource group."""
        return await self._client.typed_request(
            "POST",
            _PATH,
            request=request,
            response_model=CreateResourceGroupPayload,
        )

    async def get(self, name: str) -> ResourceGroupNode:
        """Retrieve a single resource group by name."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{name}",
            response_model=ResourceGroupNode,
        )

    async def update(
        self, name: str, request: UpdateResourceGroupInput
    ) -> UpdateResourceGroupPayload:
        """Update an existing resource group."""
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{name}",
            request=request,
            response_model=UpdateResourceGroupPayload,
        )

    async def delete(self, name: str) -> DeleteResourceGroupPayload:
        """Purge a resource group by name."""
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{name}",
            response_model=DeleteResourceGroupPayload,
        )

    async def get_resource_info(self, name: str) -> ResourceInfoNode:
        """Get resource information for a resource group."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{name}/resource-info",
            response_model=ResourceInfoNode,
        )

    async def update_fair_share_spec(
        self, name: str, request: UpdateResourceGroupFairShareSpecInput
    ) -> UpdateResourceGroupFairShareSpecPayloadNode:
        """Update fair share spec for a resource group."""
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{name}/fair-share-spec",
            request=request,
            response_model=UpdateResourceGroupFairShareSpecPayloadNode,
        )

    async def update_config(
        self, name: str, request: UpdateResourceGroupConfigInput
    ) -> UpdateResourceGroupConfigPayloadNode:
        """Update resource group configuration."""
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{name}/config",
            request=request,
            response_model=UpdateResourceGroupConfigPayloadNode,
        )
