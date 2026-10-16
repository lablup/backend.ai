"""V2 SDK client for the login client type domain."""

from __future__ import annotations

from typing import Final
from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.v2.common import PartialBulkPayload
from ai.backend.common.dto.manager.v2.login_client_type.request import (
    CreateLoginClientTypeInput,
    PartialBulkPurgeLoginClientTypesInput,
    PartialBulkUpdateLoginClientTypesInput,
    SearchLoginClientTypesInput,
    UpdateLoginClientTypeInput,
)
from ai.backend.common.dto.manager.v2.login_client_type.response import (
    CreateLoginClientTypePayload,
    DeleteLoginClientTypePayload,
    LoginClientTypeNode,
    PurgeLoginClientTypePayload,
    SearchLoginClientTypesPayload,
    UpdateLoginClientTypePayload,
)

_PATH: Final = "/v2/login-client-types"


class V2LoginClientTypeClient(BaseDomainClient):
    """SDK client for login client type CRUD operations.

    Mirrors the REST v2 surface introduced in BA-5630.
    """

    async def admin_create(
        self,
        request: CreateLoginClientTypeInput,
    ) -> CreateLoginClientTypePayload:
        """Create a new login client type (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/",
            request=request,
            response_model=CreateLoginClientTypePayload,
        )

    async def search(
        self,
        request: SearchLoginClientTypesInput,
    ) -> SearchLoginClientTypesPayload:
        """Search login client types with filter/order/pagination (superadmin only)."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/search",
            request=request,
            response_model=SearchLoginClientTypesPayload,
        )

    async def get(self, login_client_type_id: UUID) -> LoginClientTypeNode:
        """Get a single login client type by ID (authenticated users)."""
        return await self._client.typed_request(
            "GET",
            f"{_PATH}/{login_client_type_id}",
            response_model=LoginClientTypeNode,
        )

    async def update(
        self,
        login_client_type_id: UUID,
        request: UpdateLoginClientTypeInput,
    ) -> UpdateLoginClientTypePayload:
        """Update a login client type."""
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{login_client_type_id}",
            request=request,
            response_model=UpdateLoginClientTypePayload,
        )

    async def purge(self, login_client_type_id: UUID) -> PurgeLoginClientTypePayload:
        """Permanently remove a login client type."""
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{login_client_type_id}",
            response_model=PurgeLoginClientTypePayload,
        )

    async def partial_bulk_update(
        self, request: PartialBulkUpdateLoginClientTypesInput
    ) -> PartialBulkPayload[LoginClientTypeNode]:
        """Update several login client types, answering for each one."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/partial-bulk-update",
            request=request,
            response_model=PartialBulkPayload[LoginClientTypeNode],
        )

    async def partial_bulk_purge(
        self, request: PartialBulkPurgeLoginClientTypesInput
    ) -> PartialBulkPayload[LoginClientTypeNode]:
        """Permanently remove several login client types, answering for each one."""
        return await self._client.typed_request(
            "POST",
            f"{_PATH}/partial-bulk-purge",
            request=request,
            response_model=PartialBulkPayload[LoginClientTypeNode],
        )

    async def admin_update(
        self,
        login_client_type_id: UUID,
        request: UpdateLoginClientTypeInput,
    ) -> UpdateLoginClientTypePayload:
        """Deprecated. Use :meth:`update`."""
        return await self._client.typed_request(
            "PATCH",
            f"{_PATH}/{login_client_type_id}",
            request=request,
            response_model=UpdateLoginClientTypePayload,
        )

    async def admin_delete(
        self,
        login_client_type_id: UUID,
    ) -> DeleteLoginClientTypePayload:
        """Deprecated. Use :meth:`purge`."""
        return await self._client.typed_request(
            "DELETE",
            f"{_PATH}/{login_client_type_id}",
            response_model=DeleteLoginClientTypePayload,
        )
