"""Client SDK functions for resource usage history."""

from __future__ import annotations

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
