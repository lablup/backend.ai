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
from ai.backend.manager.api.context import RootContext
from ai.backend.manager.dto.context import RequestCtx, UserContext
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.models.scaling_group import query_allowed_sgroups

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ScalingGroupHandler:
    """Scaling group API handler with constructor-injected dependencies."""

    async def list_available_sgroups(
        self,
        query: QueryParam[ListScalingGroupsRequest],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        root_ctx: RootContext = req.request.app["_root.context"]
        params = query.parsed
        log.info(
            "SGROUPS.LIST(ak:{}, g:{}, d:{})",
            ctx.access_key,
            params.group,
            ctx.user_domain,
        )
        async with root_ctx.db.begin() as conn:
            sgroups = await query_allowed_sgroups(
                conn, ctx.user_domain, params.group, ctx.access_key
            )
            if not ctx.is_admin:
                sgroups = [sg for sg in sgroups if sg.is_public]
            resp = ListScalingGroupsResponse(
                scaling_groups=[ScalingGroupItem(name=sg.name) for sg in sgroups],
            )
            return APIResponse.build(HTTPStatus.OK, resp)

    async def get_wsproxy_version(
        self,
        path: PathParam[WsproxyVersionPathParam],
        query: QueryParam[WsproxyVersionQueryParam],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        root_ctx: RootContext = req.request.app["_root.context"]
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
        async with root_ctx.db.begin_readonly() as conn:
            sgroups = await query_allowed_sgroups(
                conn, ctx.user_domain, group_id_or_name or "", ctx.access_key
            )
            sgroup_filtered = [sg for sg in sgroups if sg.name == scaling_group_name]
            if not sgroup_filtered:
                raise ObjectNotFound(object_name="scaling group")
            sgroup = sgroup_filtered[0]

            if not sgroup.wsproxy_addr:
                raise ObjectNotFound(object_name="AppProxy address")
            client = root_ctx.appproxy_client_pool.load_client(
                sgroup.wsproxy_addr, sgroup.wsproxy_api_token or ""
            )
            status = await client.fetch_status()

            resp = WsproxyVersionResponse(wsproxy_version=status.api_version)
            return APIResponse.build(HTTPStatus.OK, resp)
