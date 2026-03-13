"""ACL handler class using constructor dependency injection."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import Final

from ai.backend.common.api_handlers import APIResponse
from ai.backend.common.dto.manager.acl.response import GetPermissionsResponse
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.gql_legacy.acl import get_all_vfolder_host_permissions
from ai.backend.manager.dto.context import UserContext

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AclHandler:
    """ACL API handler with constructor-injected dependencies."""

    async def get_permission(self, ctx: UserContext) -> APIResponse:
        log.info("GET_PERMISSION (ak:{})", ctx.access_key)
        resp = GetPermissionsResponse(
            vfolder_host_permission_list=get_all_vfolder_host_permissions(),
        )
        return APIResponse.build(HTTPStatus.OK, resp)
