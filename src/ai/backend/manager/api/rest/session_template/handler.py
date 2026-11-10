"""Session template handler class using constructor dependency injection.

All handlers use the new ApiHandler pattern: typed parameters
(``BodyParam``, ``QueryParam``, ``PathParam``, ``UserContext``, ``RequestCtx``)
are automatically extracted by ``_wrap_api_handler`` and responses are
returned as ``APIResponse`` objects.
"""

from __future__ import annotations

import json
import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final
from uuid import UUID

import yaml

from ai.backend.common.api_handlers import (
    APIResponse,
    BodyParam,
    PathParam,
    QueryParam,
)
from ai.backend.common.data.entity.domain import DomainName
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.template.request import (
    CreateSessionTemplateRequest,
    DeleteSessionTemplateRequest,
    GetSessionTemplateRequest,
    ListSessionTemplatesRequest,
    TemplatePathParam,
    UpdateSessionTemplateRequest,
)
from ai.backend.common.dto.manager.template.response import (
    CreateSessionTemplateItemDTO,
    CreateSessionTemplateResponse,
    DeleteSessionTemplateResponse,
    GetSessionTemplateResponse,
    ListSessionTemplatesResponse,
    SessionTemplateListItemDTO,
    UpdateSessionTemplateResponse,
)
from ai.backend.common.exception import UnreachableError
from ai.backend.common.json import load_json
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.data.session_template.types import SessionTemplateData
from ai.backend.manager.dto.context import RequestCtx, UserContext
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.services.project.actions.lookup import LookupProjectAction
from ai.backend.manager.services.template.actions.create_task_template import (
    CreateTaskTemplateAction,
    TaskTemplateItemInput,
)
from ai.backend.manager.services.template.actions.delete_task_template import (
    DeleteTaskTemplateAction,
)
from ai.backend.manager.services.template.actions.get_task_template import (
    GetTaskTemplateAction,
)
from ai.backend.manager.services.template.actions.global_list_task_templates import (
    GlobalListTaskTemplatesAction,
)
from ai.backend.manager.services.template.actions.list_task_templates import (
    ListTaskTemplatesAction,
)
from ai.backend.manager.services.template.actions.update_task_template import (
    UpdateTaskTemplateAction,
)

if TYPE_CHECKING:
    from ai.backend.manager.services.project.processors import ProjectProcessors
    from ai.backend.manager.services.template.processors import TemplateProcessors

log: Final = StructuredLogger(logging.getLogger(__spec__.name))


class SessionTemplateHandler:
    """Session template API handler with constructor-injected dependencies."""

    def __init__(
        self,
        *,
        template: TemplateProcessors,
        project: ProjectProcessors,
    ) -> None:
        self._template = template
        self._project = project

    async def _resolve_project_id(self, domain_name: str, project_name: str) -> ProjectID:
        result = await self._project.lookup.run(
            LookupProjectAction(domain_name=DomainName(domain_name), project_name=project_name)
        )
        return ProjectID(result.entity_id())

    async def create(
        self,
        body: BodyParam[CreateSessionTemplateRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        domain = params.domain or ctx.user_domain
        owner_access_key = params.owner_access_key

        try:
            payload = load_json(params.payload)
        except json.JSONDecodeError:
            try:
                payload = yaml.safe_load_all(params.payload)
            except (yaml.YAMLError, yaml.MarkedYAMLError) as e:
                raise InvalidAPIParameters("Malformed payload") from e

        items = [
            TaskTemplateItemInput(
                template=st["template"],
                name=st.get("name"),
                group_id=ProjectID(UUID(st["group_id"])) if st.get("group_id") else None,
                user_uuid=UserID(UUID(st["user_uuid"])) if st.get("user_uuid") else None,
            )
            for st in payload
        ]

        project_id = await self._resolve_project_id(domain, params.group)
        action = CreateTaskTemplateAction(
            domain_name=domain,
            requesting_project=project_id,
            requester_uuid=UserID(ctx.user_uuid),
            requester_access_key=ctx.access_key,
            requester_role=req.request["user"]["role"],
            requester_domain=ctx.user_domain,
            owner_access_key=owner_access_key,
            items=items,
        )
        result = await self._template.create_task.run(action)
        resp = [
            CreateSessionTemplateItemDTO(id=item.id.hex, user=str(item.user))
            for item in result.created
        ]
        return APIResponse.build(
            HTTPStatus.OK,
            CreateSessionTemplateResponse(root=resp),
        )

    async def list_templates(
        self,
        query: QueryParam[ListSessionTemplatesRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = query.parsed
        if params.all and not ctx.is_superadmin:
            raise InsufficientPrivilege("Only a superadmin may list every template")
        if params.all:
            global_result = await self._template.global_list_task.run(
                GlobalListTaskTemplatesAction()
            )
            entries = global_result.entries
        else:
            scoped_result = await self._template.list_task.run(
                ListTaskTemplatesAction(
                    user_uuid=UserID(ctx.user_uuid), group_id_filter=params.group_id
                )
            )
            entries = scoped_result.entries

        items = [
            SessionTemplateListItemDTO(
                name=self._stored_template_name(entry.template),
                id=entry.template.id.hex,
                created_at=entry.template.created_at,
                is_owner=entry.template.user_uuid == ctx.user_uuid,
                user=str(entry.template.user_uuid),
                group=str(entry.template.group_id) if entry.template.group_id is not None else None,
                user_email=entry.owner_email,
                group_name=entry.project_name,
                domain_name=ctx.user_domain,
                type=str(entry.template.type),
                template=entry.template.template,
            )
            for entry in entries
        ]
        return APIResponse.build(
            HTTPStatus.OK,
            ListSessionTemplatesResponse(root=items),
        )

    def _stored_template_name(self, template: SessionTemplateData) -> str:
        if template.name is None:
            raise UnreachableError(f"Session template {template.id} was stored without a name")
        return template.name

    async def get(
        self,
        path: PathParam[TemplatePathParam],
        query: QueryParam[GetSessionTemplateRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = query.parsed
        if params.format not in ("yaml", "json"):
            raise InvalidAPIParameters('format should be "yaml" or "json"')

        template_id = path.parsed.template_id
        action = GetTaskTemplateAction(template_id=template_id)
        result = await self._template.get_task.run(action)
        return APIResponse.build(
            HTTPStatus.OK,
            GetSessionTemplateResponse(
                template=result.template.template,
                name=self._stored_template_name(result.template),
                user_uuid=str(result.template.user_uuid),
                group_id=str(result.template.group_id),
                domain_name=ctx.user_domain,
            ),
        )

    async def update(
        self,
        path: PathParam[TemplatePathParam],
        body: BodyParam[UpdateSessionTemplateRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        template_id = path.parsed.template_id
        domain = params.domain or ctx.user_domain
        owner_access_key = params.owner_access_key

        try:
            payload = load_json(params.payload)
        except json.JSONDecodeError:
            try:
                payload = yaml.safe_load(params.payload)
            except (yaml.YAMLError, yaml.MarkedYAMLError) as e:
                raise InvalidAPIParameters("Malformed payload") from e

        items = [
            TaskTemplateItemInput(
                template=st["template"],
                name=st.get("name"),
                group_id=ProjectID(UUID(st["group_id"])) if st.get("group_id") else None,
                user_uuid=UserID(UUID(st["user_uuid"])) if st.get("user_uuid") else None,
            )
            for st in payload
        ]

        project_id = await self._resolve_project_id(domain, params.group)
        action = UpdateTaskTemplateAction(
            template_id=template_id,
            domain_name=domain,
            requesting_project=project_id,
            requester_uuid=UserID(ctx.user_uuid),
            requester_access_key=ctx.access_key,
            requester_role=req.request["user"]["role"],
            requester_domain=ctx.user_domain,
            owner_access_key=owner_access_key,
            items=items,
        )
        await self._template.update_task.run(action)
        return APIResponse.build(
            HTTPStatus.OK,
            UpdateSessionTemplateResponse(success=True),
        )

    async def delete(
        self,
        path: PathParam[TemplatePathParam],
        query: QueryParam[DeleteSessionTemplateRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        template_id = path.parsed.template_id

        action = DeleteTaskTemplateAction(template_id=template_id)
        await self._template.delete_task.run(action)
        return APIResponse.build(
            HTTPStatus.OK,
            DeleteSessionTemplateResponse(success=True),
        )
