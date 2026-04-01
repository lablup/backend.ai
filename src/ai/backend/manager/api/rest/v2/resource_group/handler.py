"""REST v2 handler for the resource group domain."""

from __future__ import annotations

import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.dto.manager.v2.resource_group.request import (
    AdminSearchResourceGroupsInput,
    CreateResourceGroupInput,
    UpdateAllowedDomainsForResourceGroupInput,
    UpdateAllowedProjectsForResourceGroupInput,
    UpdateAllowedResourceGroupsForDomainInput,
    UpdateAllowedResourceGroupsForProjectInput,
    UpdateResourceGroupConfigInput,
    UpdateResourceGroupFairShareSpecInput,
    UpdateResourceGroupInput,
)
from ai.backend.common.dto.manager.v2.resource_group.response import (
    AdminSearchResourceGroupsPayload,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.api.rest.v2.path_params import (
    DomainNamePathParam,
    ProjectIdPathParam,
    ResourceGroupNamePathParam,
)
from ai.backend.manager.errors.resource import ScalingGroupNotFound

if TYPE_CHECKING:
    from ai.backend.manager.api.adapters.resource_group import ResourceGroupAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class V2ResourceGroupHandler:
    """REST v2 handler for resource group operations."""

    def __init__(self, *, adapter: ResourceGroupAdapter) -> None:
        self._adapter = adapter

    async def search(
        self,
        body: BodyParam[AdminSearchResourceGroupsInput],
    ) -> APIResponse:
        """Search resource groups with filters, orders, and pagination."""
        result = await self._adapter.search(body.parsed)
        payload = AdminSearchResourceGroupsPayload(
            items=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=payload)

    async def create(
        self,
        body: BodyParam[CreateResourceGroupInput],
    ) -> APIResponse:
        """Create a new resource group."""
        result = await self._adapter.create(body.parsed)
        return APIResponse.build(status_code=HTTPStatus.CREATED, response_model=result)

    async def get(
        self,
        path: PathParam[ResourceGroupNamePathParam],
    ) -> APIResponse:
        """Retrieve a single resource group by name."""
        results = await self._adapter.batch_load_by_names([path.parsed.name])
        result = results[0]
        if result is None:
            raise ScalingGroupNotFound(path.parsed.name)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update(
        self,
        path: PathParam[ResourceGroupNamePathParam],
        body: BodyParam[UpdateResourceGroupInput],
    ) -> APIResponse:
        """Update an existing resource group."""
        result = await self._adapter.update(path.parsed.name, body.parsed)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def delete(
        self,
        path: PathParam[ResourceGroupNamePathParam],
    ) -> APIResponse:
        """Purge a resource group by name."""
        result = await self._adapter.purge(path.parsed.name)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def get_resource_info(
        self,
        path: PathParam[ResourceGroupNamePathParam],
    ) -> APIResponse:
        """Get resource information for a resource group."""
        result = await self._adapter.get_resource_info(path.parsed.name)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update_fair_share_spec(
        self,
        path: PathParam[ResourceGroupNamePathParam],
        body: BodyParam[UpdateResourceGroupFairShareSpecInput],
    ) -> APIResponse:
        """Update fair share spec for a resource group."""
        merged_input = body.parsed.model_copy(
            update={"resource_group_name": path.parsed.name},
        )
        result = await self._adapter.update_fair_share_spec(merged_input)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update_config(
        self,
        path: PathParam[ResourceGroupNamePathParam],
        body: BodyParam[UpdateResourceGroupConfigInput],
    ) -> APIResponse:
        """Update resource group configuration."""
        merged_input = body.parsed.model_copy(
            update={"resource_group_name": path.parsed.name},
        )
        result = await self._adapter.update_config(merged_input)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    # Allow / Disallow endpoints

    async def get_allowed_rgs_for_domain(
        self,
        path: PathParam[DomainNamePathParam],
    ) -> APIResponse:
        """Get allowed resource groups for a domain."""
        result = await self._adapter.get_allowed_resource_groups_for_domain(path.parsed.domain_name)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update_allowed_rgs_for_domain(
        self,
        path: PathParam[DomainNamePathParam],
        body: BodyParam[UpdateAllowedResourceGroupsForDomainInput],
    ) -> APIResponse:
        """Update allowed resource groups for a domain."""
        merged_input = body.parsed.model_copy(
            update={"domain_name": path.parsed.domain_name},
        )
        result = await self._adapter.update_allowed_resource_groups_for_domain(merged_input)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def get_allowed_rgs_for_project(
        self,
        path: PathParam[ProjectIdPathParam],
    ) -> APIResponse:
        """Get allowed resource groups for a project."""
        result = await self._adapter.get_allowed_resource_groups_for_project(path.parsed.project_id)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update_allowed_rgs_for_project(
        self,
        path: PathParam[ProjectIdPathParam],
        body: BodyParam[UpdateAllowedResourceGroupsForProjectInput],
    ) -> APIResponse:
        """Update allowed resource groups for a project."""
        merged_input = body.parsed.model_copy(
            update={"project_id": path.parsed.project_id},
        )
        result = await self._adapter.update_allowed_resource_groups_for_project(merged_input)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def get_allowed_domains_for_rg(
        self,
        path: PathParam[ResourceGroupNamePathParam],
    ) -> APIResponse:
        """Get allowed domains for a resource group."""
        result = await self._adapter.get_allowed_domains_for_resource_group(path.parsed.name)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update_allowed_domains_for_rg(
        self,
        path: PathParam[ResourceGroupNamePathParam],
        body: BodyParam[UpdateAllowedDomainsForResourceGroupInput],
    ) -> APIResponse:
        """Update allowed domains for a resource group."""
        merged_input = body.parsed.model_copy(
            update={"resource_group_name": path.parsed.name},
        )
        result = await self._adapter.update_allowed_domains_for_resource_group(merged_input)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def get_allowed_projects_for_rg(
        self,
        path: PathParam[ResourceGroupNamePathParam],
    ) -> APIResponse:
        """Get allowed projects for a resource group."""
        result = await self._adapter.get_allowed_projects_for_resource_group(path.parsed.name)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)

    async def update_allowed_projects_for_rg(
        self,
        path: PathParam[ResourceGroupNamePathParam],
        body: BodyParam[UpdateAllowedProjectsForResourceGroupInput],
    ) -> APIResponse:
        """Update allowed projects for a resource group."""
        merged_input = body.parsed.model_copy(
            update={"resource_group_name": path.parsed.name},
        )
        result = await self._adapter.update_allowed_projects_for_resource_group(merged_input)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=result)
