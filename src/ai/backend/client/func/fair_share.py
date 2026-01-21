"""Client SDK functions for fair share system."""

from __future__ import annotations

from uuid import UUID

from ai.backend.client.request import Request
from ai.backend.common.dto.manager.fair_share import (
    GetDomainFairShareResponse,
    GetProjectFairShareResponse,
    GetUserFairShareResponse,
    SearchDomainFairSharesRequest,
    SearchDomainFairSharesResponse,
    SearchProjectFairSharesRequest,
    SearchProjectFairSharesResponse,
    SearchUserFairSharesRequest,
    SearchUserFairSharesResponse,
)

from .base import BaseFunction, api_function

__all__ = ("FairShare",)


class FairShare(BaseFunction):
    """
    Provides functions to interact with fair share data.
    Supports domain, project, and user fair shares.
    Requires superadmin privileges.
    """

    # Domain Fair Share

    @api_function
    @classmethod
    async def get_domain_fair_share(
        cls,
        resource_group: str,
        domain_name: str,
    ) -> GetDomainFairShareResponse:
        """
        Get a single domain fair share.

        :param resource_group: Resource group name
        :param domain_name: Domain name
        :returns: Domain fair share data
        """
        rqst = Request("GET", f"/fair-share/domains/{resource_group}/{domain_name}")
        async with rqst.fetch() as resp:
            data = await resp.json()
            return GetDomainFairShareResponse.model_validate(data)

    @api_function
    @classmethod
    async def search_domain_fair_shares(
        cls,
        request: SearchDomainFairSharesRequest,
    ) -> SearchDomainFairSharesResponse:
        """
        Search domain fair shares.

        :param request: Domain fair share search request
        :returns: List of domain fair shares
        """
        rqst = Request("POST", "/fair-share/domains/search")
        rqst.set_json(request.model_dump(mode="json", exclude_none=True))
        async with rqst.fetch() as resp:
            data = await resp.json()
            return SearchDomainFairSharesResponse.model_validate(data)

    # Project Fair Share

    @api_function
    @classmethod
    async def get_project_fair_share(
        cls,
        resource_group: str,
        project_id: UUID,
    ) -> GetProjectFairShareResponse:
        """
        Get a single project fair share.

        :param resource_group: Resource group name
        :param project_id: Project ID
        :returns: Project fair share data
        """
        rqst = Request("GET", f"/fair-share/projects/{resource_group}/{project_id}")
        async with rqst.fetch() as resp:
            data = await resp.json()
            return GetProjectFairShareResponse.model_validate(data)

    @api_function
    @classmethod
    async def search_project_fair_shares(
        cls,
        request: SearchProjectFairSharesRequest,
    ) -> SearchProjectFairSharesResponse:
        """
        Search project fair shares.

        :param request: Project fair share search request
        :returns: List of project fair shares
        """
        rqst = Request("POST", "/fair-share/projects/search")
        rqst.set_json(request.model_dump(mode="json", exclude_none=True))
        async with rqst.fetch() as resp:
            data = await resp.json()
            return SearchProjectFairSharesResponse.model_validate(data)

    # User Fair Share

    @api_function
    @classmethod
    async def get_user_fair_share(
        cls,
        resource_group: str,
        project_id: UUID,
        user_uuid: UUID,
    ) -> GetUserFairShareResponse:
        """
        Get a single user fair share.

        :param resource_group: Resource group name
        :param project_id: Project ID
        :param user_uuid: User UUID
        :returns: User fair share data
        """
        rqst = Request("GET", f"/fair-share/users/{resource_group}/{project_id}/{user_uuid}")
        async with rqst.fetch() as resp:
            data = await resp.json()
            return GetUserFairShareResponse.model_validate(data)

    @api_function
    @classmethod
    async def search_user_fair_shares(
        cls,
        request: SearchUserFairSharesRequest,
    ) -> SearchUserFairSharesResponse:
        """
        Search user fair shares.

        :param request: User fair share search request
        :returns: List of user fair shares
        """
        rqst = Request("POST", "/fair-share/users/search")
        rqst.set_json(request.model_dump(mode="json", exclude_none=True))
        async with rqst.fetch() as resp:
            data = await resp.json()
            return SearchUserFairSharesResponse.model_validate(data)
