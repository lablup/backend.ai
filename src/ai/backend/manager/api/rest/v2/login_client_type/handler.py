"""REST v2 handler for the login client type domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.login_client_type.request import (
    CreateLoginClientTypeInput,
    SearchLoginClientTypesInput,
    UpdateLoginClientTypeInput,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import LoginClientTypeIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.login_client_type import LoginClientTypeAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


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

    async def admin_update(
        self,
        path: PathParam[LoginClientTypeIdPathParam],
        body: BodyParam[UpdateLoginClientTypeInput],
    ) -> APIResponse:
        """Update a login client type (superadmin only)."""
        result = await self._adapter.admin_update(path.parsed.login_client_type_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_delete(
        self,
        path: PathParam[LoginClientTypeIdPathParam],
    ) -> APIResponse:
        """Delete a login client type (superadmin only)."""
        result = await self._adapter.admin_delete(path.parsed.login_client_type_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
