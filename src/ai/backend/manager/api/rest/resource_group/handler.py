"""Scaling group handler class using constructor dependency injection."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Final
from uuid import UUID

from ai.backend.common.api_handlers import APIResponse, PathParam, QueryParam
from ai.backend.common.data.entity.domain import DomainName
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dto.manager.scaling_group.request import (
    ListScalingGroupsRequest,
    WsproxyVersionPathParam,
    WsproxyVersionQueryParam,
)
from ai.backend.common.dto.manager.scaling_group.response import (
    ListScalingGroupsResponse,
    ScalingGroupItem,
    WsproxyVersionResponse,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.dto.context import UserContext
from ai.backend.manager.models.resource_group.conditions import ResourceGroupConditions
from ai.backend.manager.models.resource_group.orders import ResourceGroupOrders
from ai.backend.manager.models.resource_group.searchers import ResourceGroupSearcher
from ai.backend.manager.models.specs.pagination import NoPagination
from ai.backend.manager.services.domain.actions.lookup import LookupDomainAction
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.project.actions.lookup import LookupProjectAction
from ai.backend.manager.services.project.processors import ProjectProcessors
from ai.backend.manager.services.resource_group.actions.get_wsproxy_version import (
    GetWsproxyVersionAction,
)
from ai.backend.manager.services.resource_group.actions.scoped_search import (
    DomainResourceGroupScopeItem,
    ProjectResourceGroupScopeItem,
    ResourceGroupScopeItem,
    ScopedSearchResourceGroupsAction,
    UserResourceGroupScopeItem,
)
from ai.backend.manager.services.resource_group.processors import ResourceGroupProcessors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ResourceGroupHandler:
    """Resource group API handler with constructor-injected dependencies."""

    def __init__(
        self,
        *,
        resource_group: ResourceGroupProcessors,
        domain: DomainProcessors,
        project: ProjectProcessors,
    ) -> None:
        self._resource_group = resource_group
        self._domain = domain
        self._project = project

    async def _resolve_project_id(self, domain_name: str, group: str) -> ProjectID:
        """Resolve the group query parameter, which carries either a project id or a
        name, into the project it names."""
        try:
            return ProjectID(UUID(group))
        except ValueError:
            result = await self._project.lookup.run(
                LookupProjectAction(domain_name=DomainName(domain_name), project_name=group)
            )
            return result.resolved_entity_id

    async def list_available_sgroups(
        self,
        query: QueryParam[ListScalingGroupsRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = query.parsed
        domain_lookup = await self._domain.lookup.run(
            LookupDomainAction(name=DomainName(ctx.user_domain))
        )
        items: list[ResourceGroupScopeItem] = [
            DomainResourceGroupScopeItem(domain_id=domain_lookup.resolved_entity_id),
            ProjectResourceGroupScopeItem(
                project_id=await self._resolve_project_id(ctx.user_domain, params.group)
            ),
            UserResourceGroupScopeItem(user_id=UserID(ctx.user_uuid)),
        ]
        conditions = [ResourceGroupConditions.by_is_active(True)]
        if not ctx.is_admin:
            conditions.append(ResourceGroupConditions.by_is_public(True))
        result = await self._resource_group.scoped_search_resource_groups.run(
            ScopedSearchResourceGroupsAction(
                items=items,
                searcher=ResourceGroupSearcher(
                    pagination=NoPagination(),
                    conditions=conditions,
                    orders=[ResourceGroupOrders.name()],
                ),
            )
        )
        resp = ListScalingGroupsResponse(
            scaling_groups=[ScalingGroupItem(name=data.name) for data in result.items],
        )
        return APIResponse.build(HTTPStatus.OK, resp)

    async def get_wsproxy_version(
        self,
        path: PathParam[WsproxyVersionPathParam],
        query: QueryParam[WsproxyVersionQueryParam],
        ctx: UserContext,
    ) -> APIResponse:
        path_params = path.parsed
        query_params = query.parsed
        resource_group_name = path_params.scaling_group
        group_id_or_name = query_params.group
        action = GetWsproxyVersionAction(
            resource_group_name=resource_group_name,
            domain_name=ctx.user_domain,
            group=group_id_or_name or "",
            access_key=ctx.access_key,
        )
        result = await self._resource_group.get_wsproxy_version.run(action)
        resp = WsproxyVersionResponse(wsproxy_version=result.wsproxy_version)
        return APIResponse.build(HTTPStatus.OK, resp)
