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
from ai.backend.manager.dto.context import RequestCtx, UserContext
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.services.template.actions.create_cluster_template import (
    CreateClusterTemplateAction,
)
from ai.backend.manager.services.template.actions.delete_cluster_template import (
    DeleteClusterTemplateAction,
)
from ai.backend.manager.services.template.actions.get_cluster_template import (
    GetClusterTemplateAction,
)
from ai.backend.manager.services.template.actions.list_cluster_templates import (
    ListClusterTemplatesAction,
)
from ai.backend.manager.services.template.actions.update_cluster_template import (
    UpdateClusterTemplateAction,
)

if TYPE_CHECKING:
    from ai.backend.manager.services.template.processors import TemplateProcessors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ClusterTemplateHandler:
    """Cluster template API handler with constructor-injected dependencies."""

    def __init__(self, *, template: TemplateProcessors) -> None:
        self._template = template

    async def create(
        self,
        body: BodyParam[CreateClusterTemplateRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = body.parsed
        domain = params.domain or ctx.user_domain
        owner_access_key = params.owner_access_key
        log.info(
            "CLUSTER_TEMPLATE.CREATE (ak:{0}/{1})",
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

        action = CreateClusterTemplateAction(
            domain_name=domain,
            requesting_group=params.group,
            requester_uuid=ctx.user_uuid,
            requester_access_key=ctx.access_key,
            requester_role=req.request["user"]["role"],
            requester_domain=ctx.user_domain,
            owner_access_key=owner_access_key,
            template_data=payload,
        )
        create_result = await self._template.create_cluster.wait_for_complete(action)
        return APIResponse.build(
            HTTPStatus.OK,
            CreateClusterTemplateResponse(id=create_result.id, user=create_result.user),
        )

    async def list_templates(
        self,
        query: QueryParam[ListClusterTemplatesRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = query.parsed
        user_role = req.request["user"]["role"]

        log.info("CLUSTER_TEMPLATE.LIST (ak:{})", ctx.access_key)

        raw_group_id = params.group_id if hasattr(params, "group_id") else None
        group_id_filter = uuid.UUID(raw_group_id) if raw_group_id is not None else None
        action = ListClusterTemplatesAction(
            user_uuid=ctx.user_uuid,
            user_role=user_role,
            domain_name=ctx.user_domain,
            is_superadmin=ctx.is_superadmin,
            list_all=params.all if hasattr(params, "all") else False,
            group_id_filter=group_id_filter,
        )
        result = await self._template.list_cluster.wait_for_complete(action)

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
            for entry in result.entries
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
        log.info(
            "CLUSTER_TEMPLATE.GET (ak:{0}/{1})",
            ctx.access_key,
            params.owner_access_key
            if params.owner_access_key and params.owner_access_key != ctx.access_key
            else "*",
        )

        template_id = path.parsed.template_id
        action = GetClusterTemplateAction(template_id=template_id)
        result = await self._template.get_cluster.wait_for_complete(action)
        return APIResponse.build(
            HTTPStatus.OK,
            GetClusterTemplateResponse(root=result.template),
        )

    async def update(
        self,
        path: PathParam[TemplatePathParam],
        body: BodyParam[UpdateClusterTemplateRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        template_id = path.parsed.template_id
        params = body.parsed
        log.info(
            "CLUSTER_TEMPLATE.PUT (ak:{0}/{1})",
            ctx.access_key,
            params.owner_access_key
            if params.owner_access_key and params.owner_access_key != ctx.access_key
            else "*",
        )

        try:
            payload = load_json(params.payload)
        except json.JSONDecodeError:
            try:
                payload = yaml.safe_load(params.payload)
            except (yaml.YAMLError, yaml.MarkedYAMLError) as e:
                raise InvalidAPIParameters("Malformed payload") from e

        action = UpdateClusterTemplateAction(
            template_id=template_id,
            template_data=payload,
        )
        await self._template.update_cluster.wait_for_complete(action)
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
        template_id = path.parsed.template_id
        params = query.parsed
        log.info(
            "CLUSTER_TEMPLATE.DELETE (ak:{0}/{1})",
            ctx.access_key,
            params.owner_access_key
            if params.owner_access_key and params.owner_access_key != ctx.access_key
            else "*",
        )

        action = DeleteClusterTemplateAction(template_id=template_id)
        await self._template.delete_cluster.wait_for_complete(action)
        return APIResponse.build(
            HTTPStatus.OK,
            DeleteClusterTemplateResponse(success=True),
        )
