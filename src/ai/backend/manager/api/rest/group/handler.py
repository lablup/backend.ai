"""Group handler class using constructor dependency injection.

All handlers use the new ApiHandler pattern: typed parameters
(``BodyParam``, ``UserContext``, ``ServicesCtx``) are automatically
extracted by ``_wrap_api_handler`` and responses are returned as
``APIResponse`` objects.
"""

from __future__ import annotations

import logging
import uuid
from http import HTTPStatus
from typing import Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, QueryParam
from ai.backend.common.dto.manager.group.request import (
    RegistryQuotaModifyRequest,
    RegistryQuotaRequest,
)
from ai.backend.common.dto.manager.group.response import ReadRegistryQuotaResponse
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.rbac import ProjectScope
from ai.backend.manager.service.base import ServicesContext

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class GroupHandler:
    """Group API handler with constructor-injected dependencies."""

    def __init__(self, *, services_ctx: ServicesContext) -> None:
        self._services_ctx = services_ctx

    # ------------------------------------------------------------------
    # create_registry_quota (POST /group/registry-quota)
    # ------------------------------------------------------------------

    async def create_registry_quota(
        self,
        body: BodyParam[RegistryQuotaModifyRequest],
    ) -> APIResponse:
        params = body.parsed
        log.info("CREATE_REGISTRY_QUOTA (group:{})", params.group_id)
        scope_id = ProjectScope(project_id=uuid.UUID(params.group_id), domain_name=None)
        await self._services_ctx.per_project_container_registries_quota.create_quota(
            scope_id, params.quota
        )
        return APIResponse.no_content(HTTPStatus.NO_CONTENT)

    # ------------------------------------------------------------------
    # read_registry_quota (GET /group/registry-quota)
    # ------------------------------------------------------------------

    async def read_registry_quota(
        self,
        query: QueryParam[RegistryQuotaRequest],
    ) -> APIResponse:
        params = query.parsed
        log.info("READ_REGISTRY_QUOTA (group:{})", params.group_id)
        scope_id = ProjectScope(project_id=uuid.UUID(params.group_id), domain_name=None)
        quota = await self._services_ctx.per_project_container_registries_quota.read_quota(
            scope_id,
        )
        resp = ReadRegistryQuotaResponse(result=quota)
        return APIResponse.build(HTTPStatus.OK, resp)

    # ------------------------------------------------------------------
    # update_registry_quota (PATCH /group/registry-quota)
    # ------------------------------------------------------------------

    async def update_registry_quota(
        self,
        body: BodyParam[RegistryQuotaModifyRequest],
    ) -> APIResponse:
        params = body.parsed
        log.info("UPDATE_REGISTRY_QUOTA (group:{})", params.group_id)
        scope_id = ProjectScope(project_id=uuid.UUID(params.group_id), domain_name=None)
        await self._services_ctx.per_project_container_registries_quota.update_quota(
            scope_id, params.quota
        )
        return APIResponse.no_content(HTTPStatus.NO_CONTENT)

    # ------------------------------------------------------------------
    # delete_registry_quota (DELETE /group/registry-quota)
    # ------------------------------------------------------------------

    async def delete_registry_quota(
        self,
        body: BodyParam[RegistryQuotaRequest],
    ) -> APIResponse:
        params = body.parsed
        log.info("DELETE_REGISTRY_QUOTA (group:{})", params.group_id)
        scope_id = ProjectScope(project_id=uuid.UUID(params.group_id), domain_name=None)
        await self._services_ctx.per_project_container_registries_quota.delete_quota(scope_id)
        return APIResponse.no_content(HTTPStatus.NO_CONTENT)
