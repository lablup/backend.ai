"""Scaling group handler class using constructor dependency injection."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Final

from ai.backend.common.api_handlers import APIResponse, PathParam, QueryParam
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
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.services.scaling_group.actions.get_wsproxy_version import (
    GetWsproxyVersionAction,
)
from ai.backend.manager.services.scaling_group.actions.list_allowed import (
    ListAllowedScalingGroupsAction,
)

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ScalingGroupHandler:
    """Scaling group API handler with constructor-injected dependencies."""

    def __init__(self, *, processors: Processors) -> None:
        self._processors = processors

    async def list_available_sgroups(
        self,
        query: QueryParam[ListScalingGroupsRequest],
        ctx: UserContext,
    ) -> APIResponse:
        params = query.parsed
        log.info(
            "SGROUPS.LIST(ak:{}, g:{}, d:{})",
            ctx.access_key,
            params.group,
            ctx.user_domain,
        )
        action = ListAllowedScalingGroupsAction(
            domain_name=ctx.user_domain,
            group=params.group,
            access_key=ctx.access_key,
            is_admin=ctx.is_admin,
        )
        result = await self._processors.scaling_group.list_allowed_sgroups.wait_for_complete(action)
        resp = ListScalingGroupsResponse(
            scaling_groups=[ScalingGroupItem(name=name) for name in result.scaling_group_names],
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
        scaling_group_name = path_params.scaling_group
        group_id_or_name = query_params.group
        log.info(
            "SGROUPS.LIST(ak:{}, g:{}, d:{})",
            ctx.access_key,
            group_id_or_name,
            ctx.user_domain,
        )
        action = GetWsproxyVersionAction(
            scaling_group_name=scaling_group_name,
            domain_name=ctx.user_domain,
            group=group_id_or_name or "",
            access_key=ctx.access_key,
        )
        result = await self._processors.scaling_group.get_wsproxy_version.wait_for_complete(action)
        resp = WsproxyVersionResponse(wsproxy_version=result.wsproxy_version)
        return APIResponse.build(HTTPStatus.OK, resp)
