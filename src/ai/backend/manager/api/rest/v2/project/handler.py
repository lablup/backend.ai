"""REST v2 handler for the project resource."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.group.request import AdminSearchGroupsInput
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import ProjectIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.project import ProjectAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2ProjectHandler:
    """REST v2 handler for project operations."""

    def __init__(self, *, adapter: ProjectAdapter) -> None:
        self._adapter = adapter

    async def get(
        self,
        path: PathParam[ProjectIdPathParam],
    ) -> APIResponse:
        """Retrieve a single project by UUID."""
        result = await self._adapter.get(path.parsed.project_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_search(
        self,
        body: BodyParam[AdminSearchGroupsInput],
    ) -> APIResponse:
        """Search projects with filters, orders, and pagination (superadmin only)."""
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
