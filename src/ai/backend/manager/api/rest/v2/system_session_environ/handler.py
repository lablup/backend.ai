"""REST v2 handler for the system session environ domain."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Final
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import APIResponse, BaseRequestModel, BodyParam, PathParam
from ai.backend.common.contexts.user import current_user
from ai.backend.common.data.entity.system_session_environ import SystemSessionEnvironID
from ai.backend.common.dto.manager.query import NullableDateTimeFilter
from ai.backend.common.dto.manager.v2.group.request import ScopedSearchProjectsInput
from ai.backend.common.dto.manager.v2.group.types import ProjectScope
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.common.dto.manager.v2.system_session_environ.request import (
    AdminSearchSystemSessionEnvironsInput,
    CreateSystemSessionEnvironInput,
    MySearchSystemSessionEnvironsInput,
    ScopedSearchSystemSessionEnvironsInput,
    SystemSessionEnvironFilter,
    UpdateSystemSessionEnvironInput,
)
from ai.backend.common.dto.manager.v2.system_session_environ.types import (
    SystemSessionEnvironScope,
)
from ai.backend.common.exception import UnreachableError

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.project.adapter import ProjectAdapter
    from ai.backend.manager.api.adapters.system_session_environ.adapter import (
        SystemSessionEnvironAdapter,
    )

_MY_PROJECTS_PAGE_SIZE: Final[int] = 100


class SystemSessionEnvironIdPathParam(BaseRequestModel):
    environ_id: SystemSessionEnvironID = Field(description="The id of the row.")


class V2SystemSessionEnvironHandler:
    """REST v2 handler for the system session environ domain."""

    _adapter: SystemSessionEnvironAdapter
    _project_adapter: ProjectAdapter

    def __init__(
        self, *, adapter: SystemSessionEnvironAdapter, project_adapter: ProjectAdapter
    ) -> None:
        self._adapter = adapter
        self._project_adapter = project_adapter

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

    async def scoped_search(
        self,
        body: BodyParam[ScopedSearchSystemSessionEnvironsInput],
    ) -> APIResponse:
        """Search the system session environ rows the named scopes reach."""
        payload = await self._adapter.scoped_search(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=payload)

    async def my_search(
        self,
        body: BodyParam[MySearchSystemSessionEnvironsInput],
    ) -> APIResponse:
        """Search the rows bound to public, the caller's domain and the caller's projects,
        soft-deleted ones excluded."""
        me = current_user()
        if me is None:
            raise UnreachableError("User context is not available")
        my_project_ids = await self._project_ids_of(me.user_id)
        my_input = body.parsed
        payload = await self._adapter.scoped_search(
            ScopedSearchSystemSessionEnvironsInput(
                scope=SystemSessionEnvironScope(
                    domain=[UUIDScope(value=me.domain_id)],
                    project=[UUIDScope(value=project_id) for project_id in my_project_ids],
                    public=True,
                ),
                filter=SystemSessionEnvironFilter(
                    deleted_at=NullableDateTimeFilter(is_null=True),
                    AND=[my_input.filter] if my_input.filter else None,
                ),
                order=my_input.order,
                first=my_input.first,
                after=my_input.after,
                last=my_input.last,
                before=my_input.before,
                limit=my_input.limit,
                offset=my_input.offset,
            )
        )
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

    async def _project_ids_of(self, user_id: UUID) -> list[UUID]:
        project_ids: list[UUID] = []
        while True:
            page = await self._project_adapter.scoped_search(
                ScopedSearchProjectsInput(
                    scope=ProjectScope(user=[UUIDScope(value=user_id)]),
                    limit=_MY_PROJECTS_PAGE_SIZE,
                    offset=len(project_ids),
                )
            )
            project_ids.extend(project.id for project in page.items)
            if not page.has_next_page:
                return project_ids
