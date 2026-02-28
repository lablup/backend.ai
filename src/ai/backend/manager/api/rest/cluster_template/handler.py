"""Cluster template handler class using constructor dependency injection.

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
    CreateClusterTemplateRequest,
    DeleteClusterTemplateRequest,
    GetClusterTemplateRequest,
    ListClusterTemplatesRequest,
    TemplatePathParam,
    UpdateClusterTemplateRequest,
)
from ai.backend.common.dto.manager.template.response import (
    ClusterTemplateListItemDTO,
    CreateClusterTemplateResponse,
    DeleteClusterTemplateResponse,
    GetClusterTemplateResponse,
    ListClusterTemplatesResponse,
    UpdateClusterTemplateResponse,
)
from ai.backend.common.json import load_json
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.utils import get_access_key_scopes
from ai.backend.manager.dto.context import RequestCtx, UserContext
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.resource import DBOperationFailed, TaskTemplateNotFound
from ai.backend.manager.models.domain import domains
from ai.backend.manager.models.group import association_groups_users as agus
from ai.backend.manager.models.group import groups
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.session_template import (
    TemplateType,
    check_cluster_template,
    query_accessible_session_templates,
    session_templates,
)
from ai.backend.manager.models.user import UserRole, users

if TYPE_CHECKING:
    from ai.backend.manager.api.context import RootContext
    from ai.backend.manager.services.processors import Processors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ClusterTemplateHandler:
    """Cluster template API handler with constructor-injected dependencies."""

    def __init__(self, *, processors: Processors | None = None) -> None:
        self._processors = processors

    async def create(
        self,
        body: BodyParam[CreateClusterTemplateRequest],
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
            "CLUSTER_TEMPLATE.CREATE (ak:{0}/{1})",
            requester_access_key,
            owner_access_key if owner_access_key != requester_access_key else "*",
        )
        user_uuid = ctx.user_uuid

        async with root_ctx.db.begin() as conn:
            if requester_access_key != owner_access_key:
                query = (
                    sa.select(keypairs.c.user, users.c.role, users.c.domain_name)
                    .select_from(sa.join(keypairs, users, keypairs.c.user == users.c.uuid))
                    .where(keypairs.c.access_key == owner_access_key)
                )
                result = await conn.execute(query)
                row = result.first()
                if row is None:
                    raise InvalidAPIParameters("Owner access key not found")
                owner_domain = row.domain_name
                owner_uuid = row.user
                owner_role = row.role
            else:
                owner_domain = ctx.user_domain
                owner_uuid = ctx.user_uuid
                owner_role = UserRole.USER

            query = (
                sa.select(domains.c.name)
                .select_from(domains)
                .where(
                    (domains.c.name == owner_domain) & (domains.c.is_active),
                )
            )
            qresult = await conn.execute(query)
            domain_name = qresult.scalar()
            if domain_name is None:
                raise InvalidAPIParameters("Invalid domain")

            if owner_role == UserRole.SUPERADMIN:
                query = (
                    sa.select(groups.c.id)
                    .select_from(groups)
                    .where(
                        (groups.c.domain_name == domain)
                        & (groups.c.name == params.group)
                        & (groups.c.is_active),
                    )
                )
                qresult = await conn.execute(query)
                group_id = qresult.scalar()
            elif owner_role == UserRole.ADMIN:
                if domain != owner_domain:
                    raise InvalidAPIParameters("You can only set the domain to the owner's domain.")
                query = (
                    sa.select(groups.c.id)
                    .select_from(groups)
                    .where(
                        (groups.c.domain_name == owner_domain)
                        & (groups.c.name == params.group)
                        & (groups.c.is_active),
                    )
                )
                qresult = await conn.execute(query)
                group_id = qresult.scalar()
            else:
                if domain != owner_domain:
                    raise InvalidAPIParameters("You can only set the domain to your domain.")
                query = (
                    sa.select(agus.c.group_id)
                    .select_from(agus.join(groups, agus.c.group_id == groups.c.id))
                    .where(
                        (agus.c.user_id == owner_uuid)
                        & (groups.c.domain_name == owner_domain)
                        & (groups.c.name == params.group)
                        & (groups.c.is_active),
                    )
                )
                qresult = await conn.execute(query)
                group_id = qresult.scalar()
            if group_id is None:
                raise InvalidAPIParameters("Invalid group")

            log.debug("Params: {0}", params)
            try:
                payload = load_json(params.payload)
            except json.JSONDecodeError:
                try:
                    payload = yaml.safe_load(params.payload)
                except (yaml.YAMLError, yaml.MarkedYAMLError) as e:
                    raise InvalidAPIParameters("Malformed payload") from e
            template_data = check_cluster_template(payload)
            template_id = uuid.uuid4().hex
            insert_query = session_templates.insert().values({
                "id": template_id,
                "domain_name": domain,
                "group_id": group_id,
                "user_uuid": user_uuid,
                "name": template_data["metadata"]["name"],
                "template": template_data,
                "type": TemplateType.CLUSTER,
            })
            result = await conn.execute(insert_query)
            if result.rowcount != 1:
                raise DBOperationFailed(f"Failed to create cluster template: {template_id}")

        return APIResponse.build(
            HTTPStatus.OK,
            CreateClusterTemplateResponse(id=template_id, user=user_uuid.hex),
        )

    async def list_templates(
        self,
        query: QueryParam[ListClusterTemplatesRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = query.parsed
        root_ctx: RootContext = req.request.app["_root.context"]
        domain_name = ctx.user_domain
        user_uuid = ctx.user_uuid
        user_role = req.request["user"]["role"]

        log.info("CLUSTER_TEMPLATE.LIST (ak:{})", ctx.access_key)
        async with root_ctx.db.begin() as conn:
            entries: list[Mapping[str, Any]]
            if ctx.is_superadmin and params.all:
                j = session_templates.join(
                    users, session_templates.c.user_uuid == users.c.uuid, isouter=True
                ).join(groups, session_templates.c.group_id == groups.c.id, isouter=True)
                q = (
                    sa.select(session_templates, users.c.email, groups.c.name)
                    .set_label_style(sa.LABEL_STYLE_TABLENAME_PLUS_COL)
                    .select_from(j)
                    .where(
                        (session_templates.c.is_active)
                        & (session_templates.c.type == TemplateType.CLUSTER),
                    )
                )
                result = await conn.execute(q)
                entries = []
                for row in result:
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
                    })
            else:
                extra_conds = None
                if params.group_id is not None:
                    extra_conds = session_templates.c.group_id == params.group_id
                entries = await query_accessible_session_templates(
                    conn,
                    user_uuid,
                    TemplateType.CLUSTER,
                    user_role=user_role,
                    domain_name=domain_name,
                    allowed_types=["user", "group"],
                    extra_conds=extra_conds,
                )

            items = [
                ClusterTemplateListItemDTO(
                    name=entry["name"],
                    id=entry["id"].hex if hasattr(entry["id"], "hex") else str(entry["id"]),
                    created_at=entry["created_at"],
                    is_owner=entry["is_owner"],
                    user=str(entry["user"]) if entry["user"] is not None else None,
                    group=str(entry["group"]) if entry["group"] is not None else None,
                    user_email=entry["user_email"],
                    group_name=entry["group_name"],
                    type="user" if entry["user"] is not None else "group",
                )
                for entry in entries
            ]
            return APIResponse.build(
                HTTPStatus.OK,
                ListClusterTemplatesResponse(root=items),
            )

    async def get(
        self,
        path: PathParam[TemplatePathParam],
        query: QueryParam[GetClusterTemplateRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = query.parsed
        if params.format not in ("yaml", "json"):
            raise InvalidAPIParameters('format should be "yaml" or "json"')
        requester_access_key, owner_access_key = await get_access_key_scopes(
            req.request, {"owner_access_key": params.owner_access_key}
        )
        log.info(
            "CLUSTER_TEMPLATE.GET (ak:{0}/{1})",
            requester_access_key,
            owner_access_key if owner_access_key != requester_access_key else "*",
        )

        template_id = path.parsed.template_id
        root_ctx: RootContext = req.request.app["_root.context"]

        async with root_ctx.db.begin() as conn:
            q = (
                sa.select(session_templates.c.template)
                .select_from(session_templates)
                .where(
                    (session_templates.c.id == template_id)
                    & (session_templates.c.is_active)
                    & (session_templates.c.type == TemplateType.CLUSTER),
                )
            )
            template = await conn.scalar(q)
            if not template:
                raise TaskTemplateNotFound
        if not isinstance(template, dict):
            template = load_json(template)
        return APIResponse.build(
            HTTPStatus.OK,
            GetClusterTemplateResponse(root=template),
        )

    async def update(
        self,
        path: PathParam[TemplatePathParam],
        body: BodyParam[UpdateClusterTemplateRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        root_ctx: RootContext = req.request.app["_root.context"]
        template_id = path.parsed.template_id
        params = body.parsed

        requester_access_key, owner_access_key = await get_access_key_scopes(
            req.request, {"owner_access_key": params.owner_access_key}
        )
        log.info(
            "CLUSTER_TEMPLATE.PUT (ak:{0}/{1})",
            requester_access_key,
            owner_access_key if owner_access_key != requester_access_key else "*",
        )

        async with root_ctx.db.begin() as conn:
            select_query = (
                sa.select(session_templates.c.id)
                .select_from(session_templates)
                .where(
                    (session_templates.c.id == template_id)
                    & (session_templates.c.is_active)
                    & (session_templates.c.type == TemplateType.CLUSTER),
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
            template_data = check_cluster_template(payload)
            update_query = (
                sa.update(session_templates)
                .values(template=template_data, name=template_data["metadata"]["name"])
                .where(session_templates.c.id == template_id)
            )
            result = await conn.execute(update_query)
            if result.rowcount != 1:
                raise DBOperationFailed(f"Failed to update cluster template: {template_id}")

            return APIResponse.build(
                HTTPStatus.OK,
                UpdateClusterTemplateResponse(success=True),
            )

    async def delete(
        self,
        path: PathParam[TemplatePathParam],
        query: QueryParam[DeleteClusterTemplateRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        root_ctx: RootContext = req.request.app["_root.context"]
        template_id = path.parsed.template_id
        params = query.parsed

        requester_access_key, owner_access_key = await get_access_key_scopes(
            req.request, {"owner_access_key": params.owner_access_key}
        )
        log.info(
            "CLUSTER_TEMPLATE.DELETE (ak:{0}/{1})",
            requester_access_key,
            owner_access_key if owner_access_key != requester_access_key else "*",
        )

        async with root_ctx.db.begin() as conn:
            select_query = (
                sa.select(session_templates.c.id)
                .select_from(session_templates)
                .where(
                    (session_templates.c.id == template_id)
                    & (session_templates.c.is_active)
                    & (session_templates.c.type == TemplateType.CLUSTER),
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
                raise DBOperationFailed(f"Failed to delete cluster template: {template_id}")

            return APIResponse.build(
                HTTPStatus.OK,
                DeleteClusterTemplateResponse(success=True),
            )
