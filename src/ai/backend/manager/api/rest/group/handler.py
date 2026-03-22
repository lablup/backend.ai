"""Group handler class using constructor dependency injection.

All handlers use the new ApiHandler pattern: typed parameters
(``BodyParam``, ``UserContext``) are automatically
extracted by ``_wrap_api_handler`` and responses are returned as
``APIResponse`` objects.
"""

from __future__ import annotations

import logging
import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, QueryParam
from ai.backend.common.dto.manager.group.request import (
    RegistryQuotaModifyRequest,
    RegistryQuotaRequest,
)
from ai.backend.common.dto.manager.group.response import ReadRegistryQuotaResponse
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.rbac import ProjectScope
from ai.backend.manager.services.container_registry.actions.create_registry_quota import (
    CreateRegistryQuotaAction,
)
from ai.backend.manager.services.container_registry.actions.delete_registry_quota import (
    DeleteRegistryQuotaAction,
)
from ai.backend.manager.services.container_registry.actions.read_registry_quota import (
    ReadRegistryQuotaAction,
)
from ai.backend.manager.services.container_registry.actions.update_registry_quota import (
    UpdateRegistryQuotaAction,
)

if TYPE_CHECKING:
    from ai.backend.manager.services.container_registry.processors import (
        ContainerRegistryProcessors,
    )

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class GroupHandler:
    """Group API handler with constructor-injected dependencies."""

    def __init__(self, *, container_registry: ContainerRegistryProcessors) -> None:
        self._container_registry = container_registry

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
        await self._container_registry.create_registry_quota.wait_for_complete(
            CreateRegistryQuotaAction(scope_id=scope_id, quota=params.quota)
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
        result = await self._container_registry.read_registry_quota.wait_for_complete(
            ReadRegistryQuotaAction(scope_id=scope_id)
        )
        resp = ReadRegistryQuotaResponse(result=result.quota)
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
        await self._container_registry.update_registry_quota.wait_for_complete(
            UpdateRegistryQuotaAction(scope_id=scope_id, quota=params.quota)
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
        await self._container_registry.delete_registry_quota.wait_for_complete(
            DeleteRegistryQuotaAction(scope_id=scope_id)
        )
        return APIResponse.no_content(HTTPStatus.NO_CONTENT)
