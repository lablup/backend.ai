"""Client SDK functions for resource usage history."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.request import Request
from ai.backend.common.dto.manager.fair_share import (
    SearchDomainUsageBucketsRequest,
    SearchDomainUsageBucketsResponse,
    SearchProjectUsageBucketsRequest,
    SearchProjectUsageBucketsResponse,
    SearchUserUsageBucketsRequest,
    SearchUserUsageBucketsResponse,
)

from .base import BaseFunction, api_function

__all__ = ("ResourceUsage",)


class ResourceUsage(BaseFunction):
    """
    Provides functions to interact with resource usage history data.
    Supports domain, project, and user usage buckets.
    Requires superadmin privileges.
    """

    # Domain Usage Buckets

    @api_function
    @classmethod
    async def search_domain_usage_buckets(
        cls,
        request: SearchDomainUsageBucketsRequest,
    ) -> SearchDomainUsageBucketsResponse:
        """
        Search domain usage buckets.

        :param request: Domain usage bucket search request
        :returns: List of domain usage buckets
        """
        rqst = Request("POST", "/fair-share/usage-buckets/domains/search")
        rqst.set_json(request.model_dump(mode="json", exclude_none=True))
        async with rqst.fetch() as resp:
            data = await resp.json()
            return SearchDomainUsageBucketsResponse.model_validate(data)

    # Project Usage Buckets

    @api_function
    @classmethod
    async def search_project_usage_buckets(
        cls,
        request: SearchProjectUsageBucketsRequest,
    ) -> SearchProjectUsageBucketsResponse:
        """
        Search project usage buckets.

        :param request: Project usage bucket search request
        :returns: List of project usage buckets
        """
        rqst = Request("POST", "/fair-share/usage-buckets/projects/search")
        rqst.set_json(request.model_dump(mode="json", exclude_none=True))
        async with rqst.fetch() as resp:
            data = await resp.json()
            return SearchProjectUsageBucketsResponse.model_validate(data)

    # User Usage Buckets

    @api_function
    @classmethod
    async def search_user_usage_buckets(
        cls,
        request: SearchUserUsageBucketsRequest,
    ) -> SearchUserUsageBucketsResponse:
        """
        Search user usage buckets.

        :param request: User usage bucket search request
        :returns: List of user usage buckets
        """
        rqst = Request("POST", "/fair-share/usage-buckets/users/search")
        rqst.set_json(request.model_dump(mode="json", exclude_none=True))
        async with rqst.fetch() as resp:
            data = await resp.json()
            return SearchUserUsageBucketsResponse.model_validate(data)

    # RG-Scoped Usage Bucket Search Methods

    @api_function
    @classmethod
    async def rg_search_domain_usage_buckets(
        cls,
        resource_group: str,
        request: SearchDomainUsageBucketsRequest,
    ) -> SearchDomainUsageBucketsResponse:
        """
        Search domain usage buckets within resource group scope.

        :param resource_group: Resource group name
        :param request: Domain usage bucket search request
        :returns: List of domain usage buckets
        """
        rqst = Request("POST", f"/fair-share/rg/{resource_group}/usage-buckets/domains/search")
        rqst.set_json(request.model_dump(mode="json", exclude_none=True))
        async with rqst.fetch() as resp:
            data = await resp.json()
            return SearchDomainUsageBucketsResponse.model_validate(data)

    @api_function
    @classmethod
    async def rg_search_project_usage_buckets(
        cls,
        resource_group: str,
        domain_name: str,
        request: SearchProjectUsageBucketsRequest,
    ) -> SearchProjectUsageBucketsResponse:
        """
        Search project usage buckets within resource group and domain scope.

        :param resource_group: Resource group name
        :param domain_name: Domain name
        :param request: Project usage bucket search request
        :returns: List of project usage buckets
        """
        rqst = Request(
            "POST",
            f"/fair-share/rg/{resource_group}/domains/{domain_name}/usage-buckets/projects/search",
        )
        rqst.set_json(request.model_dump(mode="json", exclude_none=True))
        async with rqst.fetch() as resp:
            data = await resp.json()
            return SearchProjectUsageBucketsResponse.model_validate(data)

    @api_function
    @classmethod
    async def rg_search_user_usage_buckets(
        cls,
        resource_group: str,
        domain_name: str,
        project_id: UUID,
        request: SearchUserUsageBucketsRequest,
    ) -> SearchUserUsageBucketsResponse:
        """
        Search user usage buckets within resource group, domain, and project scope.

        :param resource_group: Resource group name
        :param domain_name: Domain name
        :param project_id: Project ID
        :param request: User usage bucket search request
        :returns: List of user usage buckets
        """
        rqst = Request(
            "POST",
            f"/fair-share/rg/{resource_group}/domains/{domain_name}/projects/{project_id}/usage-buckets/users/search",
        )
        rqst.set_json(request.model_dump(mode="json", exclude_none=True))
        async with rqst.fetch() as resp:
            data = await resp.json()
            return SearchUserUsageBucketsResponse.model_validate(data)
