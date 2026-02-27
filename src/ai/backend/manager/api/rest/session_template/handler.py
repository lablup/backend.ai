"""Session template handler class using constructor dependency injection.

All handlers use the new ApiHandler pattern: typed parameters
(``BodyParam``, ``QueryParam``, ``PathParam``, ``UserContext``, ``RequestCtx``)
are automatically extracted by ``_wrap_api_handler`` and responses are
returned as ``APIResponse`` objects.
"""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, Final

import sqlalchemy as sa
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
from ai.backend.manager.api.session import query_userinfo
from ai.backend.manager.api.utils import get_access_key_scopes
from ai.backend.manager.dto.context import RequestCtx, UserContext
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.resource import DBOperationFailed, TaskTemplateNotFound
from ai.backend.manager.models.group import groups
from ai.backend.manager.models.session_template import (
    TemplateType,
    check_task_template,
    session_templates,
)
from ai.backend.manager.models.user import users

if TYPE_CHECKING:
    from ai.backend.manager.api.context import RootContext
    from ai.backend.manager.services.processors import Processors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class SessionTemplateHandler:
    """Session template API handler with constructor-injected dependencies."""

    def __init__(self, *, processors: Processors | None = None) -> None:
        self._processors = processors

    async def create(
        self,
        body: BodyParam[CreateSessionTemplateRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        request = req.request
        root_ctx: RootContext = request.app["_root.context"]

        domain = params.domain or ctx.user_domain
        requester_access_key, owner_access_key = await get_access_key_scopes(
            request, {"owner_access_key": params.owner_access_key}
        )
        log.info(
            "SESSION_TEMPLATE.CREATE (ak:{0}/{1})",
            requester_access_key,
            owner_access_key if owner_access_key != requester_access_key else "*",
        )
        resp: list[CreateSessionTemplateItemDTO] = []
        async with root_ctx.db.begin() as conn:
            params_dict = {
                "domain": domain,
                "group": params.group,
                "owner_access_key": params.owner_access_key,
            }
            user_uuid, group_id, _ = await query_userinfo(request, params_dict, conn)
            log.debug("Params: {0}", params)
            try:
                payload = load_json(params.payload)
            except json.JSONDecodeError:
                try:
                    payload = yaml.safe_load_all(params.payload)
                except (yaml.YAMLError, yaml.MarkedYAMLError) as e:
                    raise InvalidAPIParameters("Malformed payload") from e
            for st in payload:
                template_data = check_task_template(st["template"])
                template_id = uuid.uuid4().hex
                name = st["name"] if "name" in st else template_data["metadata"]["name"]
                if "group_id" in st:
                    group_id = st["group_id"]
                if "user_uuid" in st:
                    user_uuid = st["user_uuid"]
                query = session_templates.insert().values({
                    "id": template_id,
                    "created_at": datetime.now(UTC),
                    "domain_name": domain,
                    "group_id": group_id,
                    "user_uuid": user_uuid,
                    "name": name,
                    "template": template_data,
                    "type": TemplateType.TASK,
                })
                result = await conn.execute(query)
                resp.append(CreateSessionTemplateItemDTO(id=template_id, user=str(user_uuid)))
                if result.rowcount != 1:
                    raise DBOperationFailed(f"Failed to create session template: {template_id}")
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
        root_ctx: RootContext = req.request.app["_root.context"]
        domain_name = ctx.user_domain
        user_uuid = ctx.user_uuid

        log.info("SESSION_TEMPLATE.LIST (ak:{})", ctx.access_key)
        async with root_ctx.db.begin() as conn:
            entries: list[Mapping[str, Any]]
            j = session_templates.join(
                users, session_templates.c.user_uuid == users.c.uuid, isouter=True
            ).join(groups, session_templates.c.group_id == groups.c.id, isouter=True)
            q = (
                sa.select(session_templates, users.c.email, groups.c.name)
                .set_label_style(sa.LABEL_STYLE_TABLENAME_PLUS_COL)
                .select_from(j)
                .where(
                    (session_templates.c.is_active)
                    & (session_templates.c.type == TemplateType.TASK),
                )
            )
            result = await conn.execute(q)
            entries = []
            for row in result.fetchall():
                is_owner = row.session_templates_user_uuid == user_uuid
                entries.append({
                    "name": row.session_templates_name,
                    "id": row.session_templates_id,
                    "created_at": row.session_templates_created_at,
                    "is_owner": is_owner,
                    "user": (
                        str(row.session_templates_user_uuid)
                        if row.session_templates_user_uuid
                        else None
                    ),
                    "group": (
                        str(row.session_templates_group_id)
                        if row.session_templates_group_id
                        else None
                    ),
                    "user_email": row.users_email,
                    "group_name": row.groups_name,
                    "domain_name": domain_name,
                    "type": row.session_templates_type,
                    "template": row.session_templates_template,
                })

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
                    domain_name=entry["domain_name"],
                    type=str(entry["type"]),
                    template=entry["template"],
                )
                for entry in entries
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
        domain_name = ctx.user_domain
        requester_access_key, owner_access_key = await get_access_key_scopes(
            req.request, {"owner_access_key": params.owner_access_key}
        )
        log.info(
            "SESSION_TEMPLATE.GET (ak:{0}/{1})",
            requester_access_key,
            owner_access_key if owner_access_key != requester_access_key else "*",
        )
        template_id = path.parsed.template_id
        root_ctx: RootContext = req.request.app["_root.context"]
        async with root_ctx.db.begin() as conn:
            q = (
                sa.select(
                    session_templates.c.template,
                    session_templates.c.name,
                    session_templates.c.user_uuid,
                    session_templates.c.group_id,
                )
                .select_from(session_templates)
                .where(
                    (session_templates.c.id == template_id)
                    & (session_templates.c.is_active)
                    & (session_templates.c.type == TemplateType.TASK),
                )
            )
            result = await conn.execute(q)
            row = result.first()
            if row is None:
                raise TaskTemplateNotFound
            return APIResponse.build(
                HTTPStatus.OK,
                GetSessionTemplateResponse(
                    template=row.template
                    if isinstance(row.template, dict)
                    else load_json(row.template),
                    name=row.name,
                    user_uuid=str(row.user_uuid),
                    group_id=str(row.group_id),
                    domain_name=domain_name,
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
        request = req.request
        root_ctx: RootContext = request.app["_root.context"]
        template_id = path.parsed.template_id

        domain = params.domain or ctx.user_domain
        requester_access_key, owner_access_key = await get_access_key_scopes(
            request, {"owner_access_key": params.owner_access_key}
        )
        log.info(
            "SESSION_TEMPLATE.PUT (ak:{0}/{1})",
            requester_access_key,
            owner_access_key if owner_access_key != requester_access_key else "*",
        )
        async with root_ctx.db.begin() as conn:
            params_dict = {
                "domain": domain,
                "group": params.group,
                "owner_access_key": params.owner_access_key,
            }
            user_uuid, group_id, _ = await query_userinfo(request, params_dict, conn)
            select_query = (
                sa.select(session_templates.c.id)
                .select_from(session_templates)
                .where(
                    (session_templates.c.id == template_id)
                    & (session_templates.c.is_active)
                    & (session_templates.c.type == TemplateType.TASK),
                )
            )
            result = await conn.scalar(select_query)
            if not result:
                raise TaskTemplateNotFound
            try:
                payload = load_json(params.payload)
            except json.JSONDecodeError:
                try:
                    payload = yaml.safe_load(params.payload)
                except (yaml.YAMLError, yaml.MarkedYAMLError) as e:
                    raise InvalidAPIParameters("Malformed payload") from e
            for st in payload:
                template_data = check_task_template(st["template"])
                name = st["name"] if "name" in st else template_data["metadata"]["name"]
                if "group_id" in st:
                    group_id = st["group_id"]
                if "user_uuid" in st:
                    user_uuid = st["user_uuid"]
                update_query = (
                    sa.update(session_templates)
                    .values({
                        "group_id": group_id,
                        "user_uuid": user_uuid,
                        "name": name,
                        "template": template_data,
                    })
                    .where(session_templates.c.id == template_id)
                )
                result = await conn.execute(update_query)
                if result.rowcount != 1:
                    raise DBOperationFailed(f"Failed to update session template: {template_id}")
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
        requester_access_key, owner_access_key = await get_access_key_scopes(
            req.request, {"owner_access_key": params.owner_access_key}
        )
        log.info(
            "SESSION_TEMPLATE.DELETE (ak:{0}/{1})",
            requester_access_key,
            owner_access_key if owner_access_key != requester_access_key else "*",
        )
        root_ctx: RootContext = req.request.app["_root.context"]
        async with root_ctx.db.begin() as conn:
            select_query = (
                sa.select(session_templates.c.id)
                .select_from(session_templates)
                .where(
                    (session_templates.c.id == template_id)
                    & (session_templates.c.is_active)
                    & (session_templates.c.type == TemplateType.TASK),
                )
            )
            result = await conn.scalar(select_query)
            if not result:
                raise TaskTemplateNotFound
            update_query = (
                sa.update(session_templates)
                .values(is_active=False)
                .where(session_templates.c.id == template_id)
            )
            result = await conn.execute(update_query)
            if result.rowcount != 1:
                raise DBOperationFailed(f"Failed to delete session template: {template_id}")

            return APIResponse.build(
                HTTPStatus.OK,
                DeleteSessionTemplateResponse(success=True),
            )
