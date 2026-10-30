"""REST v2 handler for the system session environ domain."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from pydantic import Field

from ai.backend.common.api_handlers import APIResponse, BaseRequestModel, BodyParam, PathParam
from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironID
from ai.backend.common.dto.manager.v2.system_session_environ.request import (
    AdminSearchSystemSessionEnvironsInput,
    CreateSystemSessionEnvironInput,
    UpdateSystemSessionEnvironInput,
)

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.system_session_environ.adapter import (
        SystemSessionEnvironAdapter,
    )


class SystemSessionEnvironIdPathParam(BaseRequestModel):
    environ_id: SystemSessionEnvironID = Field(description="The id of the row.")


class V2SystemSessionEnvironHandler:
    """REST v2 handler for the system session environ domain."""

    _adapter: SystemSessionEnvironAdapter

    def __init__(self, *, adapter: SystemSessionEnvironAdapter) -> None:
        self._adapter = adapter

    async def admin_search(
        self,
        body: BodyParam[AdminSearchSystemSessionEnvironsInput],
    ) -> APIResponse:
        """Search every system session environ row, at every scope (superadmin only)."""
        payload = await self._adapter.global_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=payload)

    async def list_value_sources(self) -> APIResponse:
        """List every value source a system session environ row can carry."""
        payload = await self._adapter.public_list_value_sources()
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=payload)

    async def create(self, body: BodyParam[CreateSystemSessionEnvironInput]) -> APIResponse:
        """Bind a value source to an environment variable name at one scope."""
        payload = await self._adapter.create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=payload)

    async def update(
        self,
        path: PathParam[SystemSessionEnvironIdPathParam],
        body: BodyParam[UpdateSystemSessionEnvironInput],
    ) -> APIResponse:
        """Change a system session environ row's key."""
        payload = await self._adapter.update(path.parsed.environ_id, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=payload)

    async def delete(self, path: PathParam[SystemSessionEnvironIdPathParam]) -> APIResponse:
        """Soft-delete a system session environ row."""
        payload = await self._adapter.delete(path.parsed.environ_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=payload)

    async def restore(self, path: PathParam[SystemSessionEnvironIdPathParam]) -> APIResponse:
        """Restore a soft-deleted system session environ row."""
        payload = await self._adapter.restore(path.parsed.environ_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=payload)

    async def purge(self, path: PathParam[SystemSessionEnvironIdPathParam]) -> APIResponse:
        """Remove a system session environ row for good, soft-deleted or not."""
        payload = await self._adapter.purge(path.parsed.environ_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=payload)
