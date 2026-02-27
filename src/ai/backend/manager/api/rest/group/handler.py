"""Group handler class using constructor dependency injection.

All handlers use the new ApiHandler pattern: typed parameters
(``BodyParam``, ``QueryParam``) are automatically extracted by
``_wrap_api_handler`` and responses are returned as ``APIResponse``
objects.
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
from ai.backend.manager.service.container_registry.harbor import (
    AbstractPerProjectContainerRegistryQuotaService,
)
from ai.backend.manager.services.processors import Processors

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class GroupHandler:
    """Group API handler with constructor-injected dependencies.

    Manages per-project container registry quotas.
    """

    def __init__(
        self,
        *,
        processors: Processors | None = None,
        quota_service: AbstractPerProjectContainerRegistryQuotaService,
    ) -> None:
        self._processors = processors
        self._quota_service = quota_service

    # ------------------------------------------------------------------
    # Business logic (shared between new-style and shim handlers)
    # ------------------------------------------------------------------

    async def create_quota(self, group_id: str, quota: int) -> None:
        scope_id = ProjectScope(project_id=uuid.UUID(group_id), domain_name=None)
        await self._quota_service.create_quota(scope_id, quota)

    async def read_quota(self, group_id: str) -> int:
        scope_id = ProjectScope(project_id=uuid.UUID(group_id), domain_name=None)
        return await self._quota_service.read_quota(scope_id)

    async def update_quota(self, group_id: str, quota: int) -> None:
        scope_id = ProjectScope(project_id=uuid.UUID(group_id), domain_name=None)
        await self._quota_service.update_quota(scope_id, quota)

    async def delete_quota(self, group_id: str) -> None:
        scope_id = ProjectScope(project_id=uuid.UUID(group_id), domain_name=None)
        await self._quota_service.delete_quota(scope_id)

    # ------------------------------------------------------------------
    # New-style API handlers (for register_routes)
    # ------------------------------------------------------------------

    async def create_registry_quota(
        self, body: BodyParam[RegistryQuotaModifyRequest]
    ) -> APIResponse:
        params = body.parsed
        log.info("CREATE_REGISTRY_QUOTA (group:{})", params.group_id)
        await self.create_quota(params.group_id, params.quota)
        return APIResponse.no_content(HTTPStatus.NO_CONTENT)

    async def read_registry_quota(self, query: QueryParam[RegistryQuotaRequest]) -> APIResponse:
        params = query.parsed
        log.info("READ_REGISTRY_QUOTA (group:{})", params.group_id)
        quota = await self.read_quota(params.group_id)
        resp = ReadRegistryQuotaResponse(result=quota)
        return APIResponse.build(HTTPStatus.OK, resp)

    async def update_registry_quota(
        self, body: BodyParam[RegistryQuotaModifyRequest]
    ) -> APIResponse:
        params = body.parsed
        log.info("UPDATE_REGISTRY_QUOTA (group:{})", params.group_id)
        await self.update_quota(params.group_id, params.quota)
        return APIResponse.no_content(HTTPStatus.NO_CONTENT)

    async def delete_registry_quota(self, body: BodyParam[RegistryQuotaRequest]) -> APIResponse:
        params = body.parsed
        log.info("DELETE_REGISTRY_QUOTA (group:{})", params.group_id)
        await self.delete_quota(params.group_id)
        return APIResponse.no_content(HTTPStatus.NO_CONTENT)
