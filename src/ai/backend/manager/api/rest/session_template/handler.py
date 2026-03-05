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

import yaml

from ai.backend.common.api_handlers import (
    APIResponse,
    BodyParam,
    PathParam,
    QueryParam,
)
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
from ai.backend.common.json import load_json
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.dto.context import RequestCtx, UserContext
from ai.backend.manager.errors.api import InvalidAPIParameters
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
from ai.backend.manager.services.template.actions.list_task_templates import (
    ListTaskTemplatesAction,
)
from ai.backend.manager.services.template.actions.update_task_template import (
    UpdateTaskTemplateAction,
)

if TYPE_CHECKING:
    from ai.backend.manager.services.template.processors import TemplateProcessors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class SessionTemplateHandler:
    """Session template API handler with constructor-injected dependencies."""

    def __init__(self, *, template: TemplateProcessors) -> None:
        self._template = template

    async def create(
        self,
        body: BodyParam[CreateSessionTemplateRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        domain = params.domain or ctx.user_domain
        owner_access_key = params.owner_access_key
        log.info(
            "SESSION_TEMPLATE.CREATE (ak:{0}/{1})",
            ctx.access_key,
            owner_access_key if owner_access_key and owner_access_key != ctx.access_key else "*",
        )

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
                group_id=st.get("group_id"),
                user_uuid=st.get("user_uuid"),
            )
            for st in payload
        ]

        action = CreateTaskTemplateAction(
            domain_name=domain,
            requesting_group=params.group,
            requester_uuid=ctx.user_uuid,
            requester_access_key=ctx.access_key,
            requester_role=req.request["user"]["role"],
            requester_domain=ctx.user_domain,
            owner_access_key=owner_access_key,
            items=items,
        )
        result = await self._template.create_task.wait_for_complete(action)
        resp = [CreateSessionTemplateItemDTO(id=item.id, user=item.user) for item in result.created]
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
        log.info("SESSION_TEMPLATE.LIST (ak:{})", ctx.access_key)

        action = ListTaskTemplatesAction(user_uuid=ctx.user_uuid)
        result = await self._template.list_task.wait_for_complete(action)

        items = [
            SessionTemplateListItemDTO(
                name=entry["name"],
                id=entry["id"].hex if hasattr(entry["id"], "hex") else str(entry["id"]),
                created_at=entry["created_at"],
                is_owner=entry["is_owner"],
                user=str(entry["user"]) if entry["user"] is not None else None,
                group=str(entry["group"]) if entry["group"] is not None else None,
                user_email=entry["user_email"],
                group_name=entry["group_name"],
                domain_name=ctx.user_domain,
                type=str(entry["type"]),
                template=entry["template"],
            )
            for entry in result.entries
        ]
        return APIResponse.build(
            HTTPStatus.OK,
            ListSessionTemplatesResponse(root=items),
        )

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
        log.info(
            "SESSION_TEMPLATE.GET (ak:{0}/{1})",
            ctx.access_key,
            params.owner_access_key
            if params.owner_access_key and params.owner_access_key != ctx.access_key
            else "*",
        )

        template_id = path.parsed.template_id
        action = GetTaskTemplateAction(template_id=template_id)
        result = await self._template.get_task.wait_for_complete(action)
        return APIResponse.build(
            HTTPStatus.OK,
            GetSessionTemplateResponse(
                template=result.template,
                name=result.name,
                user_uuid=str(result.user_uuid),
                group_id=str(result.group_id),
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
        log.info(
            "SESSION_TEMPLATE.PUT (ak:{0}/{1})",
            ctx.access_key,
            owner_access_key if owner_access_key and owner_access_key != ctx.access_key else "*",
        )

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
                group_id=st.get("group_id"),
                user_uuid=st.get("user_uuid"),
            )
            for st in payload
        ]

        action = UpdateTaskTemplateAction(
            template_id=template_id,
            domain_name=domain,
            requesting_group=params.group,
            requester_uuid=ctx.user_uuid,
            requester_access_key=ctx.access_key,
            requester_role=req.request["user"]["role"],
            requester_domain=ctx.user_domain,
            owner_access_key=owner_access_key,
            items=items,
        )
        await self._template.update_task.wait_for_complete(action)
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
        params = query.parsed
        log.info(
            "SESSION_TEMPLATE.DELETE (ak:{0}/{1})",
            ctx.access_key,
            params.owner_access_key
            if params.owner_access_key and params.owner_access_key != ctx.access_key
            else "*",
        )

        action = DeleteTaskTemplateAction(template_id=template_id)
        await self._template.delete_task.wait_for_complete(action)
        return APIResponse.build(
            HTTPStatus.OK,
            DeleteSessionTemplateResponse(success=True),
        )
