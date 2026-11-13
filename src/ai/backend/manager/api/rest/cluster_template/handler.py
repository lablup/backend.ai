"""Cluster template handler class using constructor dependency injection.

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
from ai.backend.common.data.entity.domain import DomainName
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
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
from ai.backend.common.exception import UnreachableError
from ai.backend.common.json import load_json
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.data.session_template.types import SessionTemplateData
from ai.backend.manager.dto.context import RequestCtx, UserContext
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.errors.auth import InsufficientPrivilege
from ai.backend.manager.services.project.actions.lookup import LookupProjectAction
from ai.backend.manager.services.template.actions.create_cluster_template import (
    CreateClusterTemplateAction,
)
from ai.backend.manager.services.template.actions.delete_cluster_template import (
    DeleteClusterTemplateAction,
)
from ai.backend.manager.services.template.actions.get_cluster_template import (
    GetClusterTemplateAction,
)
from ai.backend.manager.services.template.actions.global_list_cluster_templates import (
    GlobalListClusterTemplatesAction,
)
from ai.backend.manager.services.template.actions.list_cluster_templates import (
    ListClusterTemplatesAction,
)
from ai.backend.manager.services.template.actions.update_cluster_template import (
    UpdateClusterTemplateAction,
)

if TYPE_CHECKING:
    from ai.backend.manager.services.project.processors import ProjectProcessors
    from ai.backend.manager.services.template.processors import TemplateProcessors

log: Final = StructuredLogger(logging.getLogger(__spec__.name))


class ClusterTemplateHandler:
    """Cluster template API handler with constructor-injected dependencies."""

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
        body: BodyParam[CreateClusterTemplateRequest],
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
                payload = yaml.safe_load(params.payload)
            except (yaml.YAMLError, yaml.MarkedYAMLError) as e:
                raise InvalidAPIParameters("Malformed payload") from e

        project_id = await self._resolve_project_id(domain, params.group)
        action = CreateClusterTemplateAction(
            domain_name=domain,
            requesting_project=project_id,
            requester_uuid=UserID(ctx.user_uuid),
            requester_access_key=ctx.access_key,
            requester_role=req.request["user"]["role"],
            requester_domain=ctx.user_domain,
            owner_access_key=owner_access_key,
            template_data=payload,
        )
        create_result = await self._template.create_cluster.run(action)
        return APIResponse.build(
            HTTPStatus.OK,
            CreateClusterTemplateResponse(id=create_result.id.hex, user=create_result.user.hex),
        )

    async def list_templates(
        self,
        query: QueryParam[ListClusterTemplatesRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        params = query.parsed
        if params.all and not ctx.is_superadmin:
            raise InsufficientPrivilege("Only a superadmin may list every template")
        if params.all:
            global_result = await self._template.global_list_cluster.run(
                GlobalListClusterTemplatesAction()
            )
            entries = global_result.entries
        else:
            scoped_result = await self._template.list_cluster.run(
                ListClusterTemplatesAction(
                    user_uuid=UserID(ctx.user_uuid), group_id_filter=params.group_id
                )
            )
            entries = scoped_result.entries

        items = [
            ClusterTemplateListItemDTO(
                name=self._stored_template_name(entry.template),
                id=entry.template.id.hex,
                created_at=entry.template.created_at,
                is_owner=entry.template.user_uuid == ctx.user_uuid,
                user=str(entry.template.user_uuid),
                group=str(entry.template.group_id) if entry.template.group_id is not None else None,
                user_email=entry.owner_email,
                group_name=entry.project_name,
                type="user",
            )
            for entry in entries
        ]
        return APIResponse.build(
            HTTPStatus.OK,
            ListClusterTemplatesResponse(root=items),
        )

    def _stored_template_name(self, template: SessionTemplateData) -> str:
        if template.name is None:
            raise UnreachableError(f"Session template {template.id} was stored without a name")
        return template.name

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

        template_id = path.parsed.template_id
        action = GetClusterTemplateAction(template_id=template_id)
        result = await self._template.get_cluster.run(action)
        return APIResponse.build(
            HTTPStatus.OK,
            GetClusterTemplateResponse(root=result.template.template),
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
        await self._template.update_cluster.run(action)
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

        action = DeleteClusterTemplateAction(template_id=template_id)
        await self._template.delete_cluster.run(action)
        return APIResponse.build(
            HTTPStatus.OK,
            DeleteClusterTemplateResponse(success=True),
        )
