from __future__ import annotations

from uuid import UUID

from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.common.dto.manager.fair_share import (
    BulkUpsertDomainFairShareWeightRequest,
    BulkUpsertDomainFairShareWeightResponse,
    BulkUpsertProjectFairShareWeightRequest,
    BulkUpsertProjectFairShareWeightResponse,
    BulkUpsertUserFairShareWeightRequest,
    BulkUpsertUserFairShareWeightResponse,
    GetDomainFairShareResponse,
    GetProjectFairShareResponse,
    GetResourceGroupFairShareSpecResponse,
    GetUserFairShareResponse,
    SearchDomainFairSharesRequest,
    SearchDomainFairSharesResponse,
    SearchDomainUsageBucketsRequest,
    SearchDomainUsageBucketsResponse,
    SearchProjectFairSharesRequest,
    SearchProjectFairSharesResponse,
    SearchProjectUsageBucketsRequest,
    SearchProjectUsageBucketsResponse,
    SearchResourceGroupFairShareSpecsResponse,
    SearchUserFairSharesRequest,
    SearchUserFairSharesResponse,
    SearchUserUsageBucketsRequest,
    SearchUserUsageBucketsResponse,
    UpdateResourceGroupFairShareSpecRequest,
    UpdateResourceGroupFairShareSpecResponse,
    UpsertDomainFairShareWeightRequest,
    UpsertDomainFairShareWeightResponse,
    UpsertProjectFairShareWeightRequest,
    UpsertProjectFairShareWeightResponse,
    UpsertUserFairShareWeightRequest,
    UpsertUserFairShareWeightResponse,
)


class FairShareClient(BaseDomainClient):
    """SDK v2 client for fair share scheduling endpoints."""

    # ---- Domain Fair Share ----

    async def get_domain_fair_share(
        self,
        resource_group: str,
        domain_name: str,
    ) -> GetDomainFairShareResponse:
        return await self._client.typed_request(
            "GET",
            f"/fair-share/domains/{resource_group}/{domain_name}",
            response_model=GetDomainFairShareResponse,
        )

    async def search_domain_fair_shares(
        self,
        request: SearchDomainFairSharesRequest,
    ) -> SearchDomainFairSharesResponse:
        return await self._client.typed_request(
            "POST",
            "/fair-share/domains/search",
            request=request,
            response_model=SearchDomainFairSharesResponse,
        )

    async def rg_get_domain_fair_share(
        self,
        resource_group: str,
        domain_name: str,
    ) -> GetDomainFairShareResponse:
        return await self._client.typed_request(
            "GET",
            f"/fair-share/rg/{resource_group}/domains/{domain_name}",
            response_model=GetDomainFairShareResponse,
        )

    async def rg_search_domain_fair_shares(
        self,
        resource_group: str,
        request: SearchDomainFairSharesRequest,
    ) -> SearchDomainFairSharesResponse:
        return await self._client.typed_request(
            "POST",
            f"/fair-share/rg/{resource_group}/domains/search",
            request=request,
            response_model=SearchDomainFairSharesResponse,
        )

    # ---- Project Fair Share ----

    async def get_project_fair_share(
        self,
        resource_group: str,
        project_id: UUID,
    ) -> GetProjectFairShareResponse:
        return await self._client.typed_request(
            "GET",
            f"/fair-share/projects/{resource_group}/{project_id}",
            response_model=GetProjectFairShareResponse,
        )

    async def search_project_fair_shares(
        self,
        request: SearchProjectFairSharesRequest,
    ) -> SearchProjectFairSharesResponse:
        return await self._client.typed_request(
            "POST",
            "/fair-share/projects/search",
            request=request,
            response_model=SearchProjectFairSharesResponse,
        )

    async def rg_get_project_fair_share(
        self,
        resource_group: str,
        domain_name: str,
        project_id: UUID,
    ) -> GetProjectFairShareResponse:
        return await self._client.typed_request(
            "GET",
            f"/fair-share/rg/{resource_group}/domains/{domain_name}/projects/{project_id}",
            response_model=GetProjectFairShareResponse,
        )

    async def rg_search_project_fair_shares(
        self,
        resource_group: str,
        domain_name: str,
        request: SearchProjectFairSharesRequest,
    ) -> SearchProjectFairSharesResponse:
        return await self._client.typed_request(
            "POST",
            f"/fair-share/rg/{resource_group}/domains/{domain_name}/projects/search",
            request=request,
            response_model=SearchProjectFairSharesResponse,
        )

    # ---- User Fair Share ----

    async def get_user_fair_share(
        self,
        resource_group: str,
        project_id: UUID,
        user_uuid: UUID,
    ) -> GetUserFairShareResponse:
        return await self._client.typed_request(
            "GET",
            f"/fair-share/users/{resource_group}/{project_id}/{user_uuid}",
            response_model=GetUserFairShareResponse,
        )

    async def search_user_fair_shares(
        self,
        request: SearchUserFairSharesRequest,
    ) -> SearchUserFairSharesResponse:
        return await self._client.typed_request(
            "POST",
            "/fair-share/users/search",
            request=request,
            response_model=SearchUserFairSharesResponse,
        )

    async def rg_get_user_fair_share(
        self,
        resource_group: str,
        domain_name: str,
        project_id: UUID,
        user_uuid: UUID,
    ) -> GetUserFairShareResponse:
        return await self._client.typed_request(
            "GET",
            f"/fair-share/rg/{resource_group}/domains/{domain_name}/projects/{project_id}/users/{user_uuid}",
            response_model=GetUserFairShareResponse,
        )

    async def rg_search_user_fair_shares(
        self,
        resource_group: str,
        domain_name: str,
        project_id: UUID,
        request: SearchUserFairSharesRequest,
    ) -> SearchUserFairSharesResponse:
        return await self._client.typed_request(
            "POST",
            f"/fair-share/rg/{resource_group}/domains/{domain_name}/projects/{project_id}/users/search",
            request=request,
            response_model=SearchUserFairSharesResponse,
        )

    # ---- Usage Buckets ----

    async def search_domain_usage_buckets(
        self,
        request: SearchDomainUsageBucketsRequest,
    ) -> SearchDomainUsageBucketsResponse:
        return await self._client.typed_request(
            "POST",
            "/fair-share/usage-buckets/domains/search",
            request=request,
            response_model=SearchDomainUsageBucketsResponse,
        )

    async def search_project_usage_buckets(
        self,
        request: SearchProjectUsageBucketsRequest,
    ) -> SearchProjectUsageBucketsResponse:
        return await self._client.typed_request(
            "POST",
            "/fair-share/usage-buckets/projects/search",
            request=request,
            response_model=SearchProjectUsageBucketsResponse,
        )

    async def search_user_usage_buckets(
        self,
        request: SearchUserUsageBucketsRequest,
    ) -> SearchUserUsageBucketsResponse:
        return await self._client.typed_request(
            "POST",
            "/fair-share/usage-buckets/users/search",
            request=request,
            response_model=SearchUserUsageBucketsResponse,
        )

    async def rg_search_domain_usage_buckets(
        self,
        resource_group: str,
        request: SearchDomainUsageBucketsRequest,
    ) -> SearchDomainUsageBucketsResponse:
        return await self._client.typed_request(
            "POST",
            f"/fair-share/rg/{resource_group}/usage-buckets/domains/search",
            request=request,
            response_model=SearchDomainUsageBucketsResponse,
        )

    async def rg_search_project_usage_buckets(
        self,
        resource_group: str,
        domain_name: str,
        request: SearchProjectUsageBucketsRequest,
    ) -> SearchProjectUsageBucketsResponse:
        return await self._client.typed_request(
            "POST",
            f"/fair-share/rg/{resource_group}/domains/{domain_name}/usage-buckets/projects/search",
            request=request,
            response_model=SearchProjectUsageBucketsResponse,
        )

    async def rg_search_user_usage_buckets(
        self,
        resource_group: str,
        domain_name: str,
        project_id: UUID,
        request: SearchUserUsageBucketsRequest,
    ) -> SearchUserUsageBucketsResponse:
        return await self._client.typed_request(
            "POST",
            f"/fair-share/rg/{resource_group}/domains/{domain_name}/projects/{project_id}/usage-buckets/users/search",
            request=request,
            response_model=SearchUserUsageBucketsResponse,
        )

    # ---- Upsert Weights ----

    async def upsert_domain_fair_share_weight(
        self,
        resource_group: str,
        domain_name: str,
        request: UpsertDomainFairShareWeightRequest,
    ) -> UpsertDomainFairShareWeightResponse:
        return await self._client.typed_request(
            "PUT",
            f"/fair-share/domains/{resource_group}/{domain_name}/weight",
            request=request,
            response_model=UpsertDomainFairShareWeightResponse,
        )

    async def upsert_project_fair_share_weight(
        self,
        resource_group: str,
        project_id: UUID,
        request: UpsertProjectFairShareWeightRequest,
    ) -> UpsertProjectFairShareWeightResponse:
        return await self._client.typed_request(
            "PUT",
            f"/fair-share/projects/{resource_group}/{project_id}/weight",
            request=request,
            response_model=UpsertProjectFairShareWeightResponse,
        )

    async def upsert_user_fair_share_weight(
        self,
        resource_group: str,
        project_id: UUID,
        user_uuid: UUID,
        request: UpsertUserFairShareWeightRequest,
    ) -> UpsertUserFairShareWeightResponse:
        return await self._client.typed_request(
            "PUT",
            f"/fair-share/users/{resource_group}/{project_id}/{user_uuid}/weight",
            request=request,
            response_model=UpsertUserFairShareWeightResponse,
        )

    # ---- Bulk Upsert Weights ----

    async def bulk_upsert_domain_fair_share_weight(
        self,
        request: BulkUpsertDomainFairShareWeightRequest,
    ) -> BulkUpsertDomainFairShareWeightResponse:
        return await self._client.typed_request(
            "POST",
            "/fair-share/domains/bulk-upsert-weight",
            request=request,
            response_model=BulkUpsertDomainFairShareWeightResponse,
        )

    async def bulk_upsert_project_fair_share_weight(
        self,
        request: BulkUpsertProjectFairShareWeightRequest,
    ) -> BulkUpsertProjectFairShareWeightResponse:
        return await self._client.typed_request(
            "POST",
            "/fair-share/projects/bulk-upsert-weight",
            request=request,
            response_model=BulkUpsertProjectFairShareWeightResponse,
        )

    async def bulk_upsert_user_fair_share_weight(
        self,
        request: BulkUpsertUserFairShareWeightRequest,
    ) -> BulkUpsertUserFairShareWeightResponse:
        return await self._client.typed_request(
            "POST",
            "/fair-share/users/bulk-upsert-weight",
            request=request,
            response_model=BulkUpsertUserFairShareWeightResponse,
        )

    # ---- Resource Group Fair Share Spec ----

    async def get_resource_group_fair_share_spec(
        self,
        resource_group: str,
    ) -> GetResourceGroupFairShareSpecResponse:
        return await self._client.typed_request(
            "GET",
            f"/fair-share/resource-groups/{resource_group}/spec",
            response_model=GetResourceGroupFairShareSpecResponse,
        )

    async def search_resource_group_fair_share_specs(
        self,
    ) -> SearchResourceGroupFairShareSpecsResponse:
        return await self._client.typed_request(
            "GET",
            "/fair-share/resource-groups/specs",
            response_model=SearchResourceGroupFairShareSpecsResponse,
        )

    async def update_resource_group_fair_share_spec(
        self,
        resource_group: str,
        request: UpdateResourceGroupFairShareSpecRequest,
    ) -> UpdateResourceGroupFairShareSpecResponse:
        return await self._client.typed_request(
            "PATCH",
            f"/fair-share/resource-groups/{resource_group}/spec",
            request=request,
            response_model=UpdateResourceGroupFairShareSpecResponse,
        )
