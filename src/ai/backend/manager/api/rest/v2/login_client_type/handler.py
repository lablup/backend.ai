"""REST v2 handler for the login client type domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.login_client_type.request import (
    CreateLoginClientTypeInput,
    PartialBulkPurgeLoginClientTypesInput,
    PartialBulkUpdateLoginClientTypesInput,
    SearchLoginClientTypesInput,
    UpdateLoginClientTypeInput,
)
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.api.rest.v2.path_params import LoginClientTypeIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.login_client_type.adapter import LoginClientTypeAdapter

log: Final = StructuredLogger(logging.getLogger(__spec__.name))


class V2LoginClientTypeHandler:
    """REST v2 handler for login client type operations."""

    def __init__(self, *, adapter: LoginClientTypeAdapter) -> None:
        self._adapter = adapter

    # --- Non-admin methods ---

    async def get(
        self,
        path: PathParam[LoginClientTypeIdPathParam],
    ) -> APIResponse:
        """Get a login client type by id (authenticated users)."""
        result = await self._adapter.get(path.parsed.login_client_type_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def search(
        self,
        body: BodyParam[SearchLoginClientTypesInput],
    ) -> APIResponse:
        """Search login client types with filter/order/pagination."""
        result = await self._adapter.search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    # --- Admin methods ---

    async def admin_create(
        self,
        body: BodyParam[CreateLoginClientTypeInput],
    ) -> APIResponse:
        """Create a new login client type (superadmin only)."""
        result = await self._adapter.admin_create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def update(
        self,
        path: PathParam[LoginClientTypeIdPathParam],
        body: BodyParam[UpdateLoginClientTypeInput],
    ) -> APIResponse:
        """Update a login client type."""
        result = await self._adapter.update(path.parsed.login_client_type_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def purge(
        self,
        path: PathParam[LoginClientTypeIdPathParam],
    ) -> APIResponse:
        """Permanently remove a login client type."""
        result = await self._adapter.purge(path.parsed.login_client_type_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def partial_bulk_update(
        self,
        body: BodyParam[PartialBulkUpdateLoginClientTypesInput],
    ) -> APIResponse:
        """Update several login client types, answering for each one."""
        result = await self._adapter.partial_bulk_update(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def partial_bulk_purge(
        self,
        body: BodyParam[PartialBulkPurgeLoginClientTypesInput],
    ) -> APIResponse:
        """Permanently remove several login client types, answering for each one."""
        result = await self._adapter.partial_bulk_purge(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
