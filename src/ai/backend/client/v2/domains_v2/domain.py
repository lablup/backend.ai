"""V2 REST SDK client for the domain resource."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.domain.request import (
    AdminSearchDomainsInput,
    CreateDomainContainerRegistryRelationsInput,
    CreateDomainInput,
    DeleteDomainInput,
    PartialBulkDeleteDomainsInput,
    PartialBulkRestoreDomainsInput,
    PartialBulkUpdateDomainsInput,
    PurgeDomainContainerRegistryRelationsInput,
    PurgeDomainInput,
    UpdateDomainInput,
)
from ai.backend.common.dto.manager.v2.domain.response import (
    AdminSearchDomainsPayload,
    CreateDomainContainerRegistryRelationsPayload,
    DeleteDomainPayload,
    DomainNode,
    DomainPayload,
    PurgeDomainContainerRegistryRelationsPayload,
    PurgeDomainPayload,
    RestoreDomainPayload,
)

_PATH = "/v2/domains"


class V2DomainClient(BaseDomainClient):
    """SDK client for ``/v2/domains`` endpoints."""

    async def admin_search(
        self,
        request: AdminSearchDomainsInput,
    ) -> AdminSearchDomainsPayload:
        """Search domains with filters, orders, and pagination (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=AdminSearchDomainsPayload,
        )

    async def get(self, domain_name: str) -> DomainNode:
        """Retrieve a single domain by name."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{domain_name}",
            response_model=DomainNode,
        )

    async def admin_create(self, request: CreateDomainInput) -> DomainPayload:
        """Create a new domain (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            _PATH,
            request=request,
            response_model=DomainPayload,
        )

    async def update(self, domain_id: UUID, request: UpdateDomainInput) -> DomainPayload:
        """Update a domain."""
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{domain_id}",
            request=request,
            response_model=DomainPayload,
        )

    async def delete(self, domain_id: UUID) -> DeleteDomainPayload:
        """Soft-delete a domain."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{domain_id}/delete",
            response_model=DeleteDomainPayload,
        )

    async def restore(self, domain_id: UUID) -> RestoreDomainPayload:
        """Restore a soft-deleted domain."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/{domain_id}/restore",
            response_model=RestoreDomainPayload,
        )

    async def partial_bulk_update(
        self, request: PartialBulkUpdateDomainsInput
    ) -> PartialBulkPayload[DomainNode]:
        """Update several domains, answering for each one."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/partial-bulk-update",
            request=request,
            response_model=PartialBulkPayload[DomainNode],
        )

    async def partial_bulk_delete(
        self, request: PartialBulkDeleteDomainsInput
    ) -> PartialBulkPayload[DomainNode]:
        """Soft-delete several domains, answering for each one."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/partial-bulk-delete",
            request=request,
            response_model=PartialBulkPayload[DomainNode],
        )

    async def partial_bulk_restore(
        self, request: PartialBulkRestoreDomainsInput
    ) -> PartialBulkPayload[DomainNode]:
        """Restore several soft-deleted domains, answering for each one."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/partial-bulk-restore",
            request=request,
            response_model=PartialBulkPayload[DomainNode],
        )

    async def create_container_registry_relations(
        self, request: CreateDomainContainerRegistryRelationsInput
    ) -> CreateDomainContainerRegistryRelationsPayload:
        """Relate a domain to container registries."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/container-registry-relations",
            request=request,
            response_model=CreateDomainContainerRegistryRelationsPayload,
        )

    async def purge_container_registry_relations(
        self, request: PurgeDomainContainerRegistryRelationsInput
    ) -> PurgeDomainContainerRegistryRelationsPayload:
        """Remove the relations between a domain and container registries."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/container-registry-relations/purge",
            request=request,
            response_model=PurgeDomainContainerRegistryRelationsPayload,
        )

    async def admin_update(self, domain_name: str, request: UpdateDomainInput) -> DomainPayload:
        """Deprecated. Use :meth:`update`."""
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{domain_name}",
            request=request,
            response_model=DomainPayload,
        )

    async def admin_delete(self, request: DeleteDomainInput) -> DeleteDomainPayload:
        """Deprecated. Use :meth:`delete`."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/delete",
            request=request,
            response_model=DeleteDomainPayload,
        )

    async def admin_purge(self, request: PurgeDomainInput) -> PurgeDomainPayload:
        """Permanently purge a domain (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/purge",
            request=request,
            response_model=PurgeDomainPayload,
        )
