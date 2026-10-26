"""REST v2 handler for the system session environ domain."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Final
from uuid import UUID

from ai.backend.common.api_handlers import APIResponse, BodyParam
from ai.backend.common.contexts.user import current_user
from ai.backend.common.dto.manager.v2.group.request import ScopedSearchProjectsInput
from ai.backend.common.dto.manager.v2.group.types import ProjectScope
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope
from ai.backend.common.dto.manager.v2.system_session_environ.request import (
    AdminSearchSystemSessionEnvironsInput,
    MySearchSystemSessionEnvironsInput,
    ScopedSearchSystemSessionEnvironsInput,
    SystemSessionEnvironFilter,
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
        """Search the enabled rows bound to public, the caller's domain and their projects."""
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
                    enabled=True, AND=[my_input.filter] if my_input.filter else None
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
