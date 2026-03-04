"""
REST API handler class for fair share operations.
Uses constructor DI and RouteRegistry middleware for auth.
"""

from __future__ import annotations

from http import HTTPStatus

from aiohttp import web

from ai.backend.common.api_handlers import APIResponse, BodyParam, PathParam
from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.common.dto.manager.fair_share import (
    BulkUpsertDomainFairShareWeightRequest,
    BulkUpsertDomainFairShareWeightResponse,
    BulkUpsertProjectFairShareWeightRequest,
    BulkUpsertProjectFairShareWeightResponse,
    BulkUpsertUserFairShareWeightRequest,
    BulkUpsertUserFairShareWeightResponse,
    DomainUsageBucketFilter,
    GetDomainFairSharePathParam,
    GetDomainFairShareResponse,
    GetProjectFairSharePathParam,
    GetProjectFairShareResponse,
    GetResourceGroupFairShareSpecPathParam,
    GetResourceGroupFairShareSpecResponse,
    GetUserFairSharePathParam,
    GetUserFairShareResponse,
    PaginationInfo,
    ProjectUsageBucketFilter,
    ResourceGroupFairShareSpecItemDTO,
    RGDomainFairSharePathParam,
    RGDomainFairShareSearchPathParam,
    RGDomainUsageBucketSearchPathParam,
    RGProjectFairSharePathParam,
    RGProjectFairShareSearchPathParam,
    RGProjectUsageBucketSearchPathParam,
    RGUserFairSharePathParam,
    RGUserFairShareSearchPathParam,
    RGUserUsageBucketSearchPathParam,
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
    UpdateResourceGroupFairShareSpecPathParam,
    UpdateResourceGroupFairShareSpecRequest,
    UpdateResourceGroupFairShareSpecResponse,
    UpsertDomainFairShareWeightPathParam,
    UpsertDomainFairShareWeightRequest,
    UpsertDomainFairShareWeightResponse,
    UpsertProjectFairShareWeightPathParam,
    UpsertProjectFairShareWeightRequest,
    UpsertProjectFairShareWeightResponse,
    UpsertUserFairShareWeightPathParam,
    UpsertUserFairShareWeightRequest,
    UpsertUserFairShareWeightResponse,
    UserUsageBucketFilter,
)
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    NoPagination,
)
from ai.backend.manager.repositories.fair_share.types import (
    DomainFairShareSearchScope,
    ProjectFairShareSearchScope,
    UserFairShareSearchScope,
)
from ai.backend.manager.repositories.scaling_group.options import (
    ScalingGroupConditions,
)
from ai.backend.manager.services.fair_share.actions import (
    BulkUpsertDomainFairShareWeightAction,
    BulkUpsertProjectFairShareWeightAction,
    BulkUpsertUserFairShareWeightAction,
    DomainWeightInput,
    GetDomainFairShareAction,
    GetProjectFairShareAction,
    GetUserFairShareAction,
    ProjectWeightInput,
    SearchDomainFairSharesAction,
    SearchProjectFairSharesAction,
    SearchRGDomainFairSharesAction,
    SearchRGProjectFairSharesAction,
    SearchRGUserFairSharesAction,
    SearchUserFairSharesAction,
    UpsertDomainFairShareWeightAction,
    UpsertProjectFairShareWeightAction,
    UpsertUserFairShareWeightAction,
    UserWeightInput,
)
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.services.resource_usage.actions import (
    SearchDomainUsageBucketsAction,
    SearchProjectUsageBucketsAction,
    SearchUserUsageBucketsAction,
)
from ai.backend.manager.services.scaling_group.actions.list_scaling_groups import (
    SearchScalingGroupsAction,
)
from ai.backend.manager.services.scaling_group.actions.update_fair_share_spec import (
    ResourceWeightInput,
    UpdateFairShareSpecAction,
)

from .adapter import FairShareAdapter


class FairShareAPIHandler:
    """REST API handler class for fair share operations with constructor DI."""

    def __init__(self, processors: Processors) -> None:
        self._processors = processors
        self._adapter = FairShareAdapter()

    # Domain Fair Share

    async def get_domain_fair_share(
        self,
        path: PathParam[GetDomainFairSharePathParam],
    ) -> APIResponse:
        """Get a single domain fair share."""
        processors = self._processors

        action_result = await processors.fair_share.get_domain_fair_share.wait_for_complete(
            GetDomainFairShareAction(
                resource_group=path.parsed.resource_group, domain_name=path.parsed.domain_name
            )
        )

        item = None
        if action_result.data is not None:
            item = self._adapter.convert_domain_fair_share_to_dto(action_result.data)

        resp = GetDomainFairShareResponse(item=item)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def search_domain_fair_shares(
        self,
        body: BodyParam[SearchDomainFairSharesRequest],
    ) -> APIResponse:
        """Search domain fair shares."""
        processors = self._processors

        querier = self._adapter.build_domain_fair_share_querier(body.parsed)

        action_result = await processors.fair_share.search_domain_fair_shares.wait_for_complete(
            SearchDomainFairSharesAction(
                pagination=querier.pagination,
                conditions=querier.conditions,
                orders=querier.orders,
            )
        )

        resp = SearchDomainFairSharesResponse(
            items=[
                self._adapter.convert_domain_fair_share_to_dto(fs) for fs in action_result.items
            ],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # Project Fair Share

    async def get_project_fair_share(
        self,
        path: PathParam[GetProjectFairSharePathParam],
    ) -> APIResponse:
        """Get a single project fair share."""
        processors = self._processors

        action_result = await processors.fair_share.get_project_fair_share.wait_for_complete(
            GetProjectFairShareAction(
                resource_group=path.parsed.resource_group, project_id=path.parsed.project_id
            )
        )

        item = None
        if action_result.data is not None:
            item = self._adapter.convert_project_fair_share_to_dto(action_result.data)

        resp = GetProjectFairShareResponse(item=item)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def search_project_fair_shares(
        self,
        body: BodyParam[SearchProjectFairSharesRequest],
    ) -> APIResponse:
        """Search project fair shares."""
        processors = self._processors

        querier = self._adapter.build_project_fair_share_querier(body.parsed)

        action_result = await processors.fair_share.search_project_fair_shares.wait_for_complete(
            SearchProjectFairSharesAction(
                pagination=querier.pagination,
                conditions=querier.conditions,
                orders=querier.orders,
            )
        )

        resp = SearchProjectFairSharesResponse(
            items=[
                self._adapter.convert_project_fair_share_to_dto(fs) for fs in action_result.items
            ],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # User Fair Share

    async def get_user_fair_share(
        self,
        path: PathParam[GetUserFairSharePathParam],
    ) -> APIResponse:
        """Get a single user fair share."""
        processors = self._processors

        action_result = await processors.fair_share.get_user_fair_share.wait_for_complete(
            GetUserFairShareAction(
                resource_group=path.parsed.resource_group,
                project_id=path.parsed.project_id,
                user_uuid=path.parsed.user_uuid,
            )
        )

        item = None
        if action_result.data is not None:
            item = self._adapter.convert_user_fair_share_to_dto(action_result.data)

        resp = GetUserFairShareResponse(item=item)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def search_user_fair_shares(
        self,
        body: BodyParam[SearchUserFairSharesRequest],
    ) -> APIResponse:
        """Search user fair shares."""
        processors = self._processors

        querier = self._adapter.build_user_fair_share_querier(body.parsed)

        action_result = await processors.fair_share.search_user_fair_shares.wait_for_complete(
            SearchUserFairSharesAction(
                pagination=querier.pagination,
                conditions=querier.conditions,
                orders=querier.orders,
            )
        )

        resp = SearchUserFairSharesResponse(
            items=[self._adapter.convert_user_fair_share_to_dto(fs) for fs in action_result.items],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # Domain Usage Bucket

    async def search_domain_usage_buckets(
        self,
        body: BodyParam[SearchDomainUsageBucketsRequest],
    ) -> APIResponse:
        """Search domain usage buckets."""
        processors = self._processors

        querier = self._adapter.build_domain_usage_bucket_querier(body.parsed)

        action_result = (
            await processors.resource_usage.search_domain_usage_buckets.wait_for_complete(
                SearchDomainUsageBucketsAction(
                    pagination=querier.pagination,
                    conditions=querier.conditions,
                    orders=querier.orders,
                )
            )
        )

        resp = SearchDomainUsageBucketsResponse(
            items=[
                self._adapter.convert_domain_usage_bucket_to_dto(b) for b in action_result.items
            ],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # Project Usage Bucket

    async def search_project_usage_buckets(
        self,
        body: BodyParam[SearchProjectUsageBucketsRequest],
    ) -> APIResponse:
        """Search project usage buckets."""
        processors = self._processors

        querier = self._adapter.build_project_usage_bucket_querier(body.parsed)

        action_result = (
            await processors.resource_usage.search_project_usage_buckets.wait_for_complete(
                SearchProjectUsageBucketsAction(
                    pagination=querier.pagination,
                    conditions=querier.conditions,
                    orders=querier.orders,
                )
            )
        )

        resp = SearchProjectUsageBucketsResponse(
            items=[
                self._adapter.convert_project_usage_bucket_to_dto(b) for b in action_result.items
            ],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # User Usage Bucket

    async def search_user_usage_buckets(
        self,
        body: BodyParam[SearchUserUsageBucketsRequest],
    ) -> APIResponse:
        """Search user usage buckets."""
        processors = self._processors

        querier = self._adapter.build_user_usage_bucket_querier(body.parsed)

        action_result = await processors.resource_usage.search_user_usage_buckets.wait_for_complete(
            SearchUserUsageBucketsAction(
                pagination=querier.pagination,
                conditions=querier.conditions,
                orders=querier.orders,
            )
        )

        resp = SearchUserUsageBucketsResponse(
            items=[self._adapter.convert_user_usage_bucket_to_dto(b) for b in action_result.items],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # RG-Scoped Domain Usage Bucket

    async def rg_search_domain_usage_buckets(
        self,
        path: PathParam[RGDomainUsageBucketSearchPathParam],
        body: BodyParam[SearchDomainUsageBucketsRequest],
    ) -> APIResponse:
        """Search domain usage buckets within resource group scope."""
        processors = self._processors

        filter = body.parsed.filter
        if filter is None:
            filter = DomainUsageBucketFilter(
                resource_group=StringFilter(equals=path.parsed.resource_group)
            )
        else:
            if filter.resource_group is None:
                filter.resource_group = StringFilter(equals=path.parsed.resource_group)
            elif filter.resource_group.equals != path.parsed.resource_group:
                raise web.HTTPBadRequest(reason="Filter resource_group must match path parameter")

        modified_request = SearchDomainUsageBucketsRequest(
            filter=filter,
            order=body.parsed.order,
            limit=body.parsed.limit,
            offset=body.parsed.offset,
        )

        querier = self._adapter.build_domain_usage_bucket_querier(modified_request)

        action_result = (
            await processors.resource_usage.search_domain_usage_buckets.wait_for_complete(
                SearchDomainUsageBucketsAction(
                    pagination=querier.pagination,
                    conditions=querier.conditions,
                    orders=querier.orders,
                )
            )
        )

        resp = SearchDomainUsageBucketsResponse(
            items=[
                self._adapter.convert_domain_usage_bucket_to_dto(b) for b in action_result.items
            ],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # RG-Scoped Project Usage Bucket

    async def rg_search_project_usage_buckets(
        self,
        path: PathParam[RGProjectUsageBucketSearchPathParam],
        body: BodyParam[SearchProjectUsageBucketsRequest],
    ) -> APIResponse:
        """Search project usage buckets within resource group and domain scope."""
        processors = self._processors

        filter = body.parsed.filter
        if filter is None:
            filter = ProjectUsageBucketFilter(
                resource_group=StringFilter(equals=path.parsed.resource_group),
                domain_name=StringFilter(equals=path.parsed.domain_name),
            )
        else:
            if filter.resource_group is None:
                filter.resource_group = StringFilter(equals=path.parsed.resource_group)
            elif filter.resource_group.equals != path.parsed.resource_group:
                raise web.HTTPBadRequest(reason="Filter resource_group must match path parameter")

            if filter.domain_name is None:
                filter.domain_name = StringFilter(equals=path.parsed.domain_name)
            elif filter.domain_name.equals != path.parsed.domain_name:
                raise web.HTTPBadRequest(reason="Filter domain_name must match path parameter")

        modified_request = SearchProjectUsageBucketsRequest(
            filter=filter,
            order=body.parsed.order,
            limit=body.parsed.limit,
            offset=body.parsed.offset,
        )

        querier = self._adapter.build_project_usage_bucket_querier(modified_request)

        action_result = (
            await processors.resource_usage.search_project_usage_buckets.wait_for_complete(
                SearchProjectUsageBucketsAction(
                    pagination=querier.pagination,
                    conditions=querier.conditions,
                    orders=querier.orders,
                )
            )
        )

        resp = SearchProjectUsageBucketsResponse(
            items=[
                self._adapter.convert_project_usage_bucket_to_dto(b) for b in action_result.items
            ],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # RG-Scoped User Usage Bucket

    async def rg_search_user_usage_buckets(
        self,
        path: PathParam[RGUserUsageBucketSearchPathParam],
        body: BodyParam[SearchUserUsageBucketsRequest],
    ) -> APIResponse:
        """Search user usage buckets within resource group, domain, and project scope."""
        processors = self._processors

        filter = body.parsed.filter
        if filter is None:
            filter = UserUsageBucketFilter(
                resource_group=StringFilter(equals=path.parsed.resource_group),
                domain_name=StringFilter(equals=path.parsed.domain_name),
                project_id=UUIDFilter(equals=path.parsed.project_id),
            )
        else:
            if filter.resource_group is None:
                filter.resource_group = StringFilter(equals=path.parsed.resource_group)
            elif filter.resource_group.equals != path.parsed.resource_group:
                raise web.HTTPBadRequest(reason="Filter resource_group must match path parameter")

            if filter.domain_name is None:
                filter.domain_name = StringFilter(equals=path.parsed.domain_name)
            elif filter.domain_name.equals != path.parsed.domain_name:
                raise web.HTTPBadRequest(reason="Filter domain_name must match path parameter")

            if filter.project_id is None:
                filter.project_id = UUIDFilter(equals=path.parsed.project_id)
            elif filter.project_id.equals != path.parsed.project_id:
                raise web.HTTPBadRequest(reason="Filter project_id must match path parameter")

        modified_request = SearchUserUsageBucketsRequest(
            filter=filter,
            order=body.parsed.order,
            limit=body.parsed.limit,
            offset=body.parsed.offset,
        )

        querier = self._adapter.build_user_usage_bucket_querier(modified_request)

        action_result = await processors.resource_usage.search_user_usage_buckets.wait_for_complete(
            SearchUserUsageBucketsAction(
                pagination=querier.pagination,
                conditions=querier.conditions,
                orders=querier.orders,
            )
        )

        resp = SearchUserUsageBucketsResponse(
            items=[self._adapter.convert_user_usage_bucket_to_dto(b) for b in action_result.items],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # RG-Scoped Domain Fair Share

    async def rg_get_domain_fair_share(
        self,
        path: PathParam[RGDomainFairSharePathParam],
    ) -> APIResponse:
        """Get a single domain fair share within RG scope."""
        processors = self._processors

        action_result = await processors.fair_share.get_domain_fair_share.wait_for_complete(
            GetDomainFairShareAction(
                resource_group=path.parsed.resource_group, domain_name=path.parsed.domain_name
            )
        )

        item = None
        if action_result.data is not None:
            item = self._adapter.convert_domain_fair_share_to_dto(action_result.data)

        resp = GetDomainFairShareResponse(item=item)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def rg_search_domain_fair_shares(
        self,
        path: PathParam[RGDomainFairShareSearchPathParam],
        body: BodyParam[SearchDomainFairSharesRequest],
    ) -> APIResponse:
        """Search domain fair shares within RG scope."""
        processors = self._processors

        querier = self._adapter.build_domain_fair_share_querier_rg(body.parsed)
        scope = DomainFairShareSearchScope(resource_group=path.parsed.resource_group)

        action_result = await processors.fair_share.search_rg_domain_fair_shares.wait_for_complete(
            SearchRGDomainFairSharesAction(
                scope=scope,
                querier=querier,
            )
        )

        resp = SearchDomainFairSharesResponse(
            items=[
                self._adapter.convert_domain_fair_share_to_dto(fs) for fs in action_result.items
            ],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # RG-Scoped Project Fair Share

    async def rg_get_project_fair_share(
        self,
        path: PathParam[RGProjectFairSharePathParam],
    ) -> APIResponse:
        """Get a single project fair share within RG scope."""
        processors = self._processors

        action_result = await processors.fair_share.get_project_fair_share.wait_for_complete(
            GetProjectFairShareAction(
                resource_group=path.parsed.resource_group, project_id=path.parsed.project_id
            )
        )

        item = None
        if action_result.data is not None:
            item = self._adapter.convert_project_fair_share_to_dto(action_result.data)

        resp = GetProjectFairShareResponse(item=item)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def rg_search_project_fair_shares(
        self,
        path: PathParam[RGProjectFairShareSearchPathParam],
        body: BodyParam[SearchProjectFairSharesRequest],
    ) -> APIResponse:
        """Search project fair shares within RG scope."""
        processors = self._processors

        querier = self._adapter.build_project_fair_share_querier_rg(body.parsed)
        scope = ProjectFairShareSearchScope(
            resource_group=path.parsed.resource_group,
            domain_name=path.parsed.domain_name,
        )

        action_result = await processors.fair_share.search_rg_project_fair_shares.wait_for_complete(
            SearchRGProjectFairSharesAction(
                scope=scope,
                querier=querier,
            )
        )

        resp = SearchProjectFairSharesResponse(
            items=[
                self._adapter.convert_project_fair_share_to_dto(fs) for fs in action_result.items
            ],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # RG-Scoped User Fair Share

    async def rg_get_user_fair_share(
        self,
        path: PathParam[RGUserFairSharePathParam],
    ) -> APIResponse:
        """Get a single user fair share within RG scope."""
        processors = self._processors

        action_result = await processors.fair_share.get_user_fair_share.wait_for_complete(
            GetUserFairShareAction(
                resource_group=path.parsed.resource_group,
                project_id=path.parsed.project_id,
                user_uuid=path.parsed.user_uuid,
            )
        )

        item = None
        if action_result.data is not None:
            item = self._adapter.convert_user_fair_share_to_dto(action_result.data)

        resp = GetUserFairShareResponse(item=item)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def rg_search_user_fair_shares(
        self,
        path: PathParam[RGUserFairShareSearchPathParam],
        body: BodyParam[SearchUserFairSharesRequest],
    ) -> APIResponse:
        """Search user fair shares within RG scope."""
        processors = self._processors

        querier = self._adapter.build_user_fair_share_querier_rg(body.parsed)
        scope = UserFairShareSearchScope(
            resource_group=path.parsed.resource_group,
            domain_name=path.parsed.domain_name,
            project_id=path.parsed.project_id,
        )

        action_result = await processors.fair_share.search_rg_user_fair_shares.wait_for_complete(
            SearchRGUserFairSharesAction(
                scope=scope,
                querier=querier,
            )
        )

        resp = SearchUserFairSharesResponse(
            items=[self._adapter.convert_user_fair_share_to_dto(fs) for fs in action_result.items],
            pagination=PaginationInfo(
                total=action_result.total_count,
                offset=body.parsed.offset,
                limit=body.parsed.limit,
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # Upsert Domain Fair Share Weight

    async def upsert_domain_fair_share_weight(
        self,
        path: PathParam[UpsertDomainFairShareWeightPathParam],
        body: BodyParam[UpsertDomainFairShareWeightRequest],
    ) -> APIResponse:
        """Upsert domain fair share weight."""
        processors = self._processors

        action_result = (
            await processors.fair_share.upsert_domain_fair_share_weight.wait_for_complete(
                UpsertDomainFairShareWeightAction(
                    resource_group=path.parsed.resource_group,
                    domain_name=path.parsed.domain_name,
                    weight=body.parsed.weight,
                )
            )
        )

        item = self._adapter.convert_domain_fair_share_to_dto(action_result.data)
        resp = UpsertDomainFairShareWeightResponse(item=item)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # Upsert Project Fair Share Weight

    async def upsert_project_fair_share_weight(
        self,
        path: PathParam[UpsertProjectFairShareWeightPathParam],
        body: BodyParam[UpsertProjectFairShareWeightRequest],
    ) -> APIResponse:
        """Upsert project fair share weight."""
        processors = self._processors

        action_result = (
            await processors.fair_share.upsert_project_fair_share_weight.wait_for_complete(
                UpsertProjectFairShareWeightAction(
                    resource_group=path.parsed.resource_group,
                    project_id=path.parsed.project_id,
                    domain_name=body.parsed.domain_name,
                    weight=body.parsed.weight,
                )
            )
        )

        item = self._adapter.convert_project_fair_share_to_dto(action_result.data)
        resp = UpsertProjectFairShareWeightResponse(item=item)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # Upsert User Fair Share Weight

    async def upsert_user_fair_share_weight(
        self,
        path: PathParam[UpsertUserFairShareWeightPathParam],
        body: BodyParam[UpsertUserFairShareWeightRequest],
    ) -> APIResponse:
        """Upsert user fair share weight."""
        processors = self._processors

        action_result = await processors.fair_share.upsert_user_fair_share_weight.wait_for_complete(
            UpsertUserFairShareWeightAction(
                resource_group=path.parsed.resource_group,
                project_id=path.parsed.project_id,
                user_uuid=path.parsed.user_uuid,
                domain_name=body.parsed.domain_name,
                weight=body.parsed.weight,
            )
        )

        item = self._adapter.convert_user_fair_share_to_dto(action_result.data)
        resp = UpsertUserFairShareWeightResponse(item=item)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # Bulk Upsert Domain Fair Share Weight

    async def bulk_upsert_domain_fair_share_weight(
        self,
        body: BodyParam[BulkUpsertDomainFairShareWeightRequest],
    ) -> APIResponse:
        """Bulk upsert domain fair share weights."""
        processors = self._processors

        inputs = [
            DomainWeightInput(
                domain_name=entry.domain_name,
                weight=entry.weight,
            )
            for entry in body.parsed.inputs
        ]

        action_result = (
            await processors.fair_share.bulk_upsert_domain_fair_share_weight.wait_for_complete(
                BulkUpsertDomainFairShareWeightAction(
                    resource_group=body.parsed.resource_group,
                    inputs=inputs,
                )
            )
        )

        resp = BulkUpsertDomainFairShareWeightResponse(upserted_count=action_result.upserted_count)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # Bulk Upsert Project Fair Share Weight

    async def bulk_upsert_project_fair_share_weight(
        self,
        body: BodyParam[BulkUpsertProjectFairShareWeightRequest],
    ) -> APIResponse:
        """Bulk upsert project fair share weights."""
        processors = self._processors

        inputs = [
            ProjectWeightInput(
                project_id=entry.project_id,
                domain_name=entry.domain_name,
                weight=entry.weight,
            )
            for entry in body.parsed.inputs
        ]

        action_result = (
            await processors.fair_share.bulk_upsert_project_fair_share_weight.wait_for_complete(
                BulkUpsertProjectFairShareWeightAction(
                    resource_group=body.parsed.resource_group,
                    inputs=inputs,
                )
            )
        )

        resp = BulkUpsertProjectFairShareWeightResponse(upserted_count=action_result.upserted_count)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # Bulk Upsert User Fair Share Weight

    async def bulk_upsert_user_fair_share_weight(
        self,
        body: BodyParam[BulkUpsertUserFairShareWeightRequest],
    ) -> APIResponse:
        """Bulk upsert user fair share weights."""
        processors = self._processors

        inputs = [
            UserWeightInput(
                user_uuid=entry.user_uuid,
                project_id=entry.project_id,
                domain_name=entry.domain_name,
                weight=entry.weight,
            )
            for entry in body.parsed.inputs
        ]

        action_result = (
            await processors.fair_share.bulk_upsert_user_fair_share_weight.wait_for_complete(
                BulkUpsertUserFairShareWeightAction(
                    resource_group=body.parsed.resource_group,
                    inputs=inputs,
                )
            )
        )

        resp = BulkUpsertUserFairShareWeightResponse(upserted_count=action_result.upserted_count)
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    # Resource Group Fair Share Spec

    async def get_resource_group_fair_share_spec(
        self,
        path: PathParam[GetResourceGroupFairShareSpecPathParam],
    ) -> APIResponse:
        """Get resource group fair share spec."""
        processors = self._processors

        name_spec = StringMatchSpec(
            value=path.parsed.resource_group,
            case_insensitive=False,
            negated=False,
        )
        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[ScalingGroupConditions.by_name_equals(name_spec)],
        )
        search_result = await processors.scaling_group.search_scaling_groups.wait_for_complete(
            SearchScalingGroupsAction(querier=querier)
        )

        if not search_result.scaling_groups:
            raise web.HTTPNotFound(
                reason=f"Resource group '{path.parsed.resource_group}' not found"
            )

        scaling_group = search_result.scaling_groups[0]

        resp = GetResourceGroupFairShareSpecResponse(
            resource_group=scaling_group.name,
            fair_share_spec=self._adapter.convert_scaling_group_spec_to_dto(
                scaling_group.fair_share_spec
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def search_resource_group_fair_share_specs(
        self,
    ) -> APIResponse:
        """Search all resource groups with their fair share specs."""
        processors = self._processors

        querier = BatchQuerier(
            pagination=NoPagination(),
            conditions=[],
        )
        search_result = await processors.scaling_group.search_scaling_groups.wait_for_complete(
            SearchScalingGroupsAction(querier=querier)
        )

        items = [
            ResourceGroupFairShareSpecItemDTO(
                resource_group=sg.name,
                fair_share_spec=self._adapter.convert_scaling_group_spec_to_dto(sg.fair_share_spec),
            )
            for sg in search_result.scaling_groups
        ]

        resp = SearchResourceGroupFairShareSpecsResponse(
            items=items,
            total_count=len(items),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)

    async def update_resource_group_fair_share_spec(
        self,
        path: PathParam[UpdateResourceGroupFairShareSpecPathParam],
        body: BodyParam[UpdateResourceGroupFairShareSpecRequest],
    ) -> APIResponse:
        """Update resource group fair share spec with partial update and validation."""
        processors = self._processors

        resource_weights = None
        if body.parsed.resource_weights is not None:
            resource_weights = [
                ResourceWeightInput(
                    resource_type=entry.resource_type,
                    weight=entry.weight,
                )
                for entry in body.parsed.resource_weights
            ]

        action = UpdateFairShareSpecAction(
            resource_group=path.parsed.resource_group,
            half_life_days=body.parsed.half_life_days,
            lookback_days=body.parsed.lookback_days,
            decay_unit_days=body.parsed.decay_unit_days,
            default_weight=body.parsed.default_weight,
            resource_weights=resource_weights,
        )

        result = await processors.scaling_group.update_fair_share_spec.wait_for_complete(action)

        resp = UpdateResourceGroupFairShareSpecResponse(
            resource_group=result.scaling_group.name,
            fair_share_spec=self._adapter.convert_scaling_group_spec_to_dto(
                result.scaling_group.fair_share_spec
            ),
        )
        return APIResponse.build(status_code=HTTPStatus.OK, response_model=resp)
