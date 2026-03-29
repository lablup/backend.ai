"""REST v2 handler for the resource allocation domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.resource_allocation.request import (
    AdminEffectiveResourceAllocationInput,
    CheckPresetAvailabilityInput,
    EffectiveResourceAllocationInput,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import (
    DomainNamePathParam,
    ProjectIdPathParam,
    ResourceGroupNamePathParam,
)
from ai.backend.manager.dto.context import RequestCtx, UserContext

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.resource_allocation import ResourceAllocationAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2ResourceAllocationHandler:
    """REST v2 handler for resource allocation operations."""

    def __init__(self, *, adapter: ResourceAllocationAdapter) -> None:
        self._adapter = adapter

    async def my_keypair_usage(
        self,
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        """Get keypair resource usage for the current user."""
        resource_policy = req.request["keypair"]["resource_policy"]
        result = await self._adapter.my_keypair_usage(
            access_key=ctx.access_key,
            resource_policy=resource_policy,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def project_usage(
        self,
        path: PathParam[ProjectIdPathParam],
    ) -> APIResponse:
        """Get project resource usage."""
        result = await self._adapter.project_usage(
            project_id=path.parsed.project_id,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_domain_usage(
        self,
        path: PathParam[DomainNamePathParam],
    ) -> APIResponse:
        """Get domain resource usage (superadmin only)."""
        result = await self._adapter.admin_domain_usage(
            domain_name=path.parsed.domain_name,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def resource_group_usage(
        self,
        path: PathParam[ResourceGroupNamePathParam],
    ) -> APIResponse:
        """Get resource group usage."""
        result = await self._adapter.resource_group_usage(
            rg_name=path.parsed.name,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def effective_allocation(
        self,
        body: BodyParam[EffectiveResourceAllocationInput],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        """Get effective assignable resources for the current user."""
        resource_policy = req.request["keypair"]["resource_policy"]
        result = await self._adapter.effective_allocation(
            input=body.parsed,
            access_key=ctx.access_key,
            resource_policy=resource_policy,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def admin_effective_allocation(
        self,
        body: BodyParam[AdminEffectiveResourceAllocationInput],
    ) -> APIResponse:
        """Get effective assignable resources for a specific user (superadmin only)."""
        result = await self._adapter.admin_effective_allocation_resolved(
            input=body.parsed,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def check_preset_availability(
        self,
        body: BodyParam[CheckPresetAvailabilityInput],
        ctx: UserContext,
        req: RequestCtx,
    ) -> APIResponse:
        """Check which resource presets are available for session creation."""
        resource_policy = req.request["keypair"]["resource_policy"]
        result = await self._adapter.check_preset_availability(
            input=body.parsed,
            access_key=ctx.access_key,
            resource_policy=resource_policy,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
