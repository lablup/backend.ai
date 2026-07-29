"""REST v2 handler for the idle checker assignment domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.idle_checker_assignment.request import (
    CreateIdleCheckerAssignmentInput,
    PurgeIdleCheckerAssignmentInput,
    ScopedSearchIdleCheckerAssignmentsInput,
    SearchIdleCheckerAssignmentsInput,
    UpdateIdleCheckerAssignmentInput,
)
from ai.backend.common.identifier.idle_checker import IdleCheckerAssignmentID
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import IdleCheckerAssignmentIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.idle_checker_assignment.adapter import (
        IdleCheckerAssignmentAdapter,
    )

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2IdleCheckerAssignmentHandler:
    """REST v2 handler for idle checker assignment operations."""

    def __init__(self, *, adapter: IdleCheckerAssignmentAdapter) -> None:
        self._adapter = adapter

    async def admin_create(
        self,
        body: BodyParam[CreateIdleCheckerAssignmentInput],
    ) -> APIResponse:
        """Bind a global idle checker to a scope (superadmin only)."""
        result = await self._adapter.admin_create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def admin_search(
        self,
        body: BodyParam[SearchIdleCheckerAssignmentsInput],
    ) -> APIResponse:
        """Search idle checker assignments across all scopes (superadmin only)."""
        result = await self._adapter.admin_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def scoped_search(
        self,
        body: BodyParam[ScopedSearchIdleCheckerAssignmentsInput],
    ) -> APIResponse:
        """Search idle checker assignments within the given scopes (per-item RBAC)."""
        result = await self._adapter.scoped_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update(
        self,
        path: PathParam[IdleCheckerAssignmentIdPathParam],
        body: BodyParam[UpdateIdleCheckerAssignmentInput],
    ) -> APIResponse:
        """Update an idle checker assignment's enabled state by id."""
        merged = body.parsed.model_copy(update={"id": path.parsed.idle_checker_assignment_id})
        result = await self._adapter.update(merged)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def purge(
        self,
        path: PathParam[IdleCheckerAssignmentIdPathParam],
    ) -> APIResponse:
        """Permanently remove an idle checker assignment by id."""
        result = await self._adapter.purge(
            PurgeIdleCheckerAssignmentInput(
                id=IdleCheckerAssignmentID(path.parsed.idle_checker_assignment_id)
            )
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
