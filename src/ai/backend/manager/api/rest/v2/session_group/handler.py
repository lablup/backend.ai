"""REST v2 handler for the session group domain."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.dto.manager.v2.session_group.request import (
    AdminSearchSessionGroupsInput,
    CreateSessionGroupInput,
    PurgeSessionGroupInput,
    ScopedSearchSessionGroupsInput,
    UpdateSessionGroupInput,
)
from ai.backend.manager.api.rest.v2.path_params import SessionGroupIdPathParam

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.session_group.adapter import SessionGroupAdapter


class V2SessionGroupHandler:
    """REST v2 handler for session group reads, the creation, the placement policy update and the purge."""

    def __init__(self, *, adapter: SessionGroupAdapter) -> None:
        self._adapter = adapter

    async def create(
        self,
        body: BodyParam[CreateSessionGroupInput],
    ) -> APIResponse:
        """Create a session group in a project, owned by the caller."""
        result = await self._adapter.create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def get(
        self,
        path: PathParam[SessionGroupIdPathParam],
    ) -> APIResponse:
        """Retrieve a single session group by id."""
        result = await self._adapter.get(SessionGroupID(path.parsed.session_group_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_search(
        self,
        body: BodyParam[AdminSearchSessionGroupsInput],
    ) -> APIResponse:
        """Search every session group, deployment groups included (superadmin only)."""
        result = await self._adapter.global_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def scoped_search(
        self,
        body: BodyParam[ScopedSearchSessionGroupsInput],
    ) -> APIResponse:
        """Search the session groups the named scopes reach, combined with OR."""
        result = await self._adapter.scoped_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update(
        self,
        path: PathParam[SessionGroupIdPathParam],
        body: BodyParam[UpdateSessionGroupInput],
    ) -> APIResponse:
        """Change a session group's placement direction and enforcement."""
        input_ = body.parsed.model_copy(update={"id": path.parsed.session_group_id})
        result = await self._adapter.update(input_)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def purge(
        self,
        path: PathParam[SessionGroupIdPathParam],
    ) -> APIResponse:
        """Remove a session group; its member sessions stay with their group cleared."""
        result = await self._adapter.purge(PurgeSessionGroupInput(id=path.parsed.session_group_id))
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
