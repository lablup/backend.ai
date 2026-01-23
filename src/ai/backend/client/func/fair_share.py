"""Client SDK functions for fair share system."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from ai.backend.client.request import Request
from ai.backend.common.dto.manager.fair_share import (
    GetDomainFairShareResponse,
    GetProjectFairShareResponse,
    GetResourceGroupFairShareSpecResponse,
    GetUserFairShareResponse,
    ResourceWeightEntryInput,
    SearchDomainFairSharesRequest,
    SearchDomainFairSharesResponse,
    SearchProjectFairSharesRequest,
    SearchProjectFairSharesResponse,
    SearchResourceGroupFairShareSpecsResponse,
    SearchUserFairSharesRequest,
    SearchUserFairSharesResponse,
    UpdateResourceGroupFairShareSpecResponse,
    UpsertDomainFairShareWeightResponse,
    UpsertProjectFairShareWeightResponse,
    UpsertUserFairShareWeightResponse,
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

    # Upsert Weight Methods

    @api_function
    @classmethod
    async def upsert_domain_fair_share_weight(
        cls,
        resource_group: str,
        domain_name: str,
        weight: Decimal | None = None,
    ) -> UpsertDomainFairShareWeightResponse:
        """
        Upsert domain fair share weight.

        Creates a new domain fair share record or updates the weight of an existing one.
        If weight is None, the resource group's default_weight will be used.

        :param resource_group: Resource group (scaling group) name
        :param domain_name: Domain name
        :param weight: Weight value (None to use resource group's default_weight)
        :returns: Updated domain fair share data
        """
        rqst = Request("PUT", f"/fair-share/domains/{resource_group}/{domain_name}/weight")
        body: dict[str, str | None] = {"weight": str(weight) if weight is not None else None}
        rqst.set_json(body)
        async with rqst.fetch() as resp:
            data = await resp.json()
            return UpsertDomainFairShareWeightResponse.model_validate(data)

    @api_function
    @classmethod
    async def upsert_project_fair_share_weight(
        cls,
        resource_group: str,
        project_id: UUID,
        domain_name: str,
        weight: Decimal | None = None,
    ) -> UpsertProjectFairShareWeightResponse:
        """
        Upsert project fair share weight.

        Creates a new project fair share record or updates the weight of an existing one.
        If weight is None, the resource group's default_weight will be used.

        :param resource_group: Resource group (scaling group) name
        :param project_id: Project ID
        :param domain_name: Domain name the project belongs to
        :param weight: Weight value (None to use resource group's default_weight)
        :returns: Updated project fair share data
        """
        rqst = Request("PUT", f"/fair-share/projects/{resource_group}/{project_id}/weight")
        body: dict[str, str | None] = {
            "domain_name": domain_name,
            "weight": str(weight) if weight is not None else None,
        }
        rqst.set_json(body)
        async with rqst.fetch() as resp:
            data = await resp.json()
            return UpsertProjectFairShareWeightResponse.model_validate(data)

    @api_function
    @classmethod
    async def upsert_user_fair_share_weight(
        cls,
        resource_group: str,
        project_id: UUID,
        user_uuid: UUID,
        domain_name: str,
        weight: Decimal | None = None,
    ) -> UpsertUserFairShareWeightResponse:
        """
        Upsert user fair share weight.

        Creates a new user fair share record or updates the weight of an existing one.
        If weight is None, the resource group's default_weight will be used.

        :param resource_group: Resource group (scaling group) name
        :param project_id: Project ID
        :param user_uuid: User UUID
        :param domain_name: Domain name the user belongs to
        :param weight: Weight value (None to use resource group's default_weight)
        :returns: Updated user fair share data
        """
        rqst = Request("PUT", f"/fair-share/users/{resource_group}/{project_id}/{user_uuid}/weight")
        body: dict[str, str | None] = {
            "domain_name": domain_name,
            "weight": str(weight) if weight is not None else None,
        }
        rqst.set_json(body)
        async with rqst.fetch() as resp:
            data = await resp.json()
            return UpsertUserFairShareWeightResponse.model_validate(data)

    # Resource Group Fair Share Spec Methods

    @api_function
    @classmethod
    async def update_resource_group_fair_share_spec(
        cls,
        resource_group: str,
        half_life_days: int | None = None,
        lookback_days: int | None = None,
        decay_unit_days: int | None = None,
        default_weight: Decimal | None = None,
        resource_weights: list[ResourceWeightEntryInput] | None = None,
    ) -> UpdateResourceGroupFairShareSpecResponse:
        """
        Update resource group fair share specification.

        Performs a partial update - only provided fields are updated.
        Other fields retain their existing values.

        :param resource_group: Resource group (scaling group) name
        :param half_life_days: Half-life for exponential decay in days
        :param lookback_days: Total lookback period in days
        :param decay_unit_days: Granularity of decay buckets in days
        :param default_weight: Default weight for entities
        :param resource_weights: List of resource weight entries (resource_type and weight)
        :returns: Updated resource group fair share spec
        """
        rqst = Request("PATCH", f"/fair-share/resource-groups/{resource_group}/spec")
        body: dict[str, int | str | list[dict[str, str | None]] | None] = {}
        if half_life_days is not None:
            body["half_life_days"] = half_life_days
        if lookback_days is not None:
            body["lookback_days"] = lookback_days
        if decay_unit_days is not None:
            body["decay_unit_days"] = decay_unit_days
        if default_weight is not None:
            body["default_weight"] = str(default_weight)
        if resource_weights is not None:
            body["resource_weights"] = [
                {
                    "resource_type": entry.resource_type,
                    "weight": str(entry.weight) if entry.weight is not None else None,
                }
                for entry in resource_weights
            ]
        rqst.set_json(body)
        async with rqst.fetch() as resp:
            data = await resp.json()
            return UpdateResourceGroupFairShareSpecResponse.model_validate(data)

    @api_function
    @classmethod
    async def get_resource_group_fair_share_spec(
        cls,
        resource_group: str,
    ) -> GetResourceGroupFairShareSpecResponse:
        """
        Get resource group fair share specification.

        :param resource_group: Resource group (scaling group) name
        :returns: Resource group fair share spec
        """
        rqst = Request("GET", f"/fair-share/resource-groups/{resource_group}/spec")
        async with rqst.fetch() as resp:
            data = await resp.json()
            return GetResourceGroupFairShareSpecResponse.model_validate(data)

    @api_function
    @classmethod
    async def list_resource_group_fair_share_specs(
        cls,
    ) -> SearchResourceGroupFairShareSpecsResponse:
        """
        List all resource groups with their fair share specifications.

        :returns: List of resource groups with fair share specs
        """
        rqst = Request("GET", "/fair-share/resource-groups/specs")
        async with rqst.fetch() as resp:
            data = await resp.json()
            return SearchResourceGroupFairShareSpecsResponse.model_validate(data)
