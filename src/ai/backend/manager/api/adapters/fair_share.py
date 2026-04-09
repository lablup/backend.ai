"""Fair share domain adapter - Pydantic-in/Pydantic-out transport layer."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from ai.backend.common.dto.manager.v2.fair_share.request import (
    BulkUpsertDomainFairShareWeightInput,
    BulkUpsertProjectFairShareWeightInput,
    BulkUpsertUserFairShareWeightInput,
    DomainFairShareFilter,
    DomainFairShareOrder,
    GetDomainFairShareInput,
    GetProjectFairShareInput,
    GetUserFairShareInput,
    ProjectFairShareFilter,
    ProjectFairShareOrder,
    SearchDomainFairSharesInput,
    SearchProjectFairSharesInput,
    SearchUserFairSharesInput,
    UpsertDomainFairShareWeightInput,
    UpsertProjectFairShareWeightInput,
    UpsertUserFairShareWeightInput,
    UserFairShareFilter,
    UserFairShareOrder,
)
from ai.backend.common.dto.manager.v2.fair_share.response import (
    BulkUpsertDomainFairShareWeightPayload,
    BulkUpsertProjectFairShareWeightPayload,
    BulkUpsertUserFairShareWeightPayload,
    DomainFairShareNode,
    GetDomainFairSharePayload,
    GetProjectFairSharePayload,
    GetUserFairSharePayload,
    ProjectFairShareNode,
    SearchDomainFairSharesPayload,
    SearchProjectFairSharesPayload,
    SearchUserFairSharesPayload,
    UpsertDomainFairShareWeightPayload,
    UpsertProjectFairShareWeightPayload,
    UpsertUserFairShareWeightPayload,
    UserFairShareNode,
)
from ai.backend.common.dto.manager.v2.fair_share.types import (
    DomainFairShareOrderField,
    FairShareCalculationSnapshotInfo,
    FairShareSpecInfo,
    OrderDirection,
    ProjectFairShareOrderField,
    ResourceSlotEntryInfo,
    ResourceSlotInfo,
    ResourceWeightEntryInfo,
    UserFairShareOrderField,
)
from ai.backend.common.types import SlotQuantity
from ai.backend.manager.api.adapters.pagination import PaginationSpec
from ai.backend.manager.data.fair_share.types import (
    DomainFairShareData,
    FairShareCalculationSnapshot,
    FairShareSpec,
    ProjectFairShareData,
    UserFairShareData,
)
from ai.backend.manager.models.fair_share.conditions import (
    DomainFairShareConditions,
    ProjectFairShareConditions,
    RGDomainFairShareConditions,
    RGProjectFairShareConditions,
    RGUserFairShareConditions,
    UserFairShareConditions,
)
from ai.backend.manager.models.fair_share.orders import (
    DomainFairShareOrders,
    ProjectFairShareOrders,
    RGDomainFairShareOrders,
    RGProjectFairShareOrders,
    RGUserFairShareOrders,
    UserFairShareOrders,
)
from ai.backend.manager.models.fair_share.row import (
    DomainFairShareRow,
    ProjectFairShareRow,
    UserFairShareRow,
)
from ai.backend.manager.repositories.base import (
    QueryCondition,
    QueryOrder,
    combine_conditions_or,
    negate_conditions,
)
from ai.backend.manager.repositories.fair_share.types import (
    DomainFairShareSearchScope,
    ProjectFairShareSearchScope,
    UserFairShareSearchScope,
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

from .base import BaseAdapter


def _domain_fair_share_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=DomainFairShareOrders.by_created_at(ascending=False),
        backward_order=DomainFairShareOrders.by_created_at(ascending=True),
        forward_condition_factory=DomainFairShareConditions.by_cursor_forward,
        backward_condition_factory=DomainFairShareConditions.by_cursor_backward,
        tiebreaker_order=DomainFairShareRow.id.asc(),
    )


def _project_fair_share_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ProjectFairShareOrders.by_created_at(ascending=False),
        backward_order=ProjectFairShareOrders.by_created_at(ascending=True),
        forward_condition_factory=ProjectFairShareConditions.by_cursor_forward,
        backward_condition_factory=ProjectFairShareConditions.by_cursor_backward,
        tiebreaker_order=ProjectFairShareRow.id.asc(),
    )


def _user_fair_share_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=UserFairShareOrders.by_created_at(ascending=False),
        backward_order=UserFairShareOrders.by_created_at(ascending=True),
        forward_condition_factory=UserFairShareConditions.by_cursor_forward,
        backward_condition_factory=UserFairShareConditions.by_cursor_backward,
        tiebreaker_order=UserFairShareRow.id.asc(),
    )


class FairShareAdapter(BaseAdapter):
    """Adapter for fair share domain operations (domain / project / user)."""

    # ------------------------------------------------------------------ domain

    async def get_domain(self, input: GetDomainFairShareInput) -> GetDomainFairSharePayload:
        """Get a single domain fair share record."""
        result = await self._processors.fair_share.get_domain_fair_share.wait_for_complete(
            GetDomainFairShareAction(
                resource_group=input.resource_group,
                domain_name=input.domain_name,
            )
        )
        return GetDomainFairSharePayload(
            item=self._domain_data_to_dto(result.data),
        )

    async def search_domain(
        self, input: SearchDomainFairSharesInput
    ) -> SearchDomainFairSharesPayload:
        """Search domain fair shares with filters and pagination (cursor/offset)."""
        conditions = self._convert_domain_filter(input.filter) if input.filter else []
        orders = self._convert_domain_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_domain_fair_share_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

        result = await self._processors.fair_share.search_domain_fair_shares.wait_for_complete(
            SearchDomainFairSharesAction(
                pagination=querier.pagination,
                conditions=querier.conditions,
                orders=querier.orders,
            )
        )
        return SearchDomainFairSharesPayload(
            items=[self._domain_data_to_dto(d) for d in result.items],
            total_count=result.total_count,
        )

    async def search_rg_domain(
        self,
        input: SearchDomainFairSharesInput,
        resource_group: str,
    ) -> SearchDomainFairSharesPayload:
        """Search domain fair shares within a resource group (entity-based, cursor/offset)."""
        conditions = self._convert_domain_filter_rg(input.filter) if input.filter else []
        orders = self._convert_domain_orders_rg(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_domain_fair_share_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

        result = await self._processors.fair_share.search_rg_domain_fair_shares.wait_for_complete(
            SearchRGDomainFairSharesAction(
                scope=DomainFairShareSearchScope(resource_group=resource_group),
                querier=querier,
            )
        )
        return SearchDomainFairSharesPayload(
            items=[self._domain_data_to_dto(d) for d in result.items],
            total_count=result.total_count,
        )

    async def upsert_domain(
        self,
        input: UpsertDomainFairShareWeightInput,
    ) -> UpsertDomainFairShareWeightPayload:
        """Upsert domain fair share weight."""
        result = (
            await self._processors.fair_share.upsert_domain_fair_share_weight.wait_for_complete(
                UpsertDomainFairShareWeightAction(
                    resource_group=input.resource_group_name,
                    domain_name=input.domain_name,
                    weight=input.weight,
                )
            )
        )
        return UpsertDomainFairShareWeightPayload(
            domain_fair_share=self._domain_data_to_dto(result.data)
        )

    async def bulk_upsert_domain(
        self,
        input: BulkUpsertDomainFairShareWeightInput,
    ) -> BulkUpsertDomainFairShareWeightPayload:
        """Bulk upsert domain fair share weights."""
        result = await self._processors.fair_share.bulk_upsert_domain_fair_share_weight.wait_for_complete(
            BulkUpsertDomainFairShareWeightAction(
                resource_group=input.resource_group_name,
                inputs=[
                    DomainWeightInput(domain_name=e.domain_name, weight=e.weight)
                    for e in input.inputs
                ],
            )
        )
        return BulkUpsertDomainFairShareWeightPayload(upserted_count=result.upserted_count)

    # ------------------------------------------------------------------ project

    async def get_project(self, input: GetProjectFairShareInput) -> GetProjectFairSharePayload:
        """Get a single project fair share record."""
        result = await self._processors.fair_share.get_project_fair_share.wait_for_complete(
            GetProjectFairShareAction(
                resource_group=input.resource_group,
                project_id=input.project_id,
            )
        )
        return GetProjectFairSharePayload(item=self._project_data_to_dto(result.data))

    async def search_project(
        self, input: SearchProjectFairSharesInput
    ) -> SearchProjectFairSharesPayload:
        """Search project fair shares with filters and pagination (cursor/offset)."""
        conditions = self._convert_project_filter(input.filter) if input.filter else []
        orders = self._convert_project_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_project_fair_share_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

        result = await self._processors.fair_share.search_project_fair_shares.wait_for_complete(
            SearchProjectFairSharesAction(
                pagination=querier.pagination,
                conditions=querier.conditions,
                orders=querier.orders,
            )
        )
        return SearchProjectFairSharesPayload(
            items=[self._project_data_to_dto(d) for d in result.items],
            total_count=result.total_count,
        )

    async def search_rg_project(
        self,
        input: SearchProjectFairSharesInput,
        resource_group: str,
        domain_name: str,
    ) -> SearchProjectFairSharesPayload:
        """Search project fair shares within a resource group scope (entity-based, cursor/offset)."""
        conditions = self._convert_project_filter_rg(input.filter) if input.filter else []
        orders = self._convert_project_orders_rg(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_project_fair_share_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

        result = await self._processors.fair_share.search_rg_project_fair_shares.wait_for_complete(
            SearchRGProjectFairSharesAction(
                scope=ProjectFairShareSearchScope(
                    resource_group=resource_group,
                    domain_name=domain_name,
                ),
                querier=querier,
            )
        )
        return SearchProjectFairSharesPayload(
            items=[self._project_data_to_dto(d) for d in result.items],
            total_count=result.total_count,
        )

    async def upsert_project(
        self,
        input: UpsertProjectFairShareWeightInput,
    ) -> UpsertProjectFairShareWeightPayload:
        """Upsert project fair share weight."""
        result = (
            await self._processors.fair_share.upsert_project_fair_share_weight.wait_for_complete(
                UpsertProjectFairShareWeightAction(
                    resource_group=input.resource_group_name,
                    project_id=input.project_id,
                    domain_name=input.domain_name,
                    weight=input.weight,
                )
            )
        )
        return UpsertProjectFairShareWeightPayload(
            project_fair_share=self._project_data_to_dto(result.data)
        )

    async def bulk_upsert_project(
        self,
        input: BulkUpsertProjectFairShareWeightInput,
    ) -> BulkUpsertProjectFairShareWeightPayload:
        """Bulk upsert project fair share weights."""
        result = await self._processors.fair_share.bulk_upsert_project_fair_share_weight.wait_for_complete(
            BulkUpsertProjectFairShareWeightAction(
                resource_group=input.resource_group_name,
                inputs=[
                    ProjectWeightInput(
                        project_id=e.project_id,
                        domain_name=e.domain_name,
                        weight=e.weight,
                    )
                    for e in input.inputs
                ],
            )
        )
        return BulkUpsertProjectFairShareWeightPayload(upserted_count=result.upserted_count)

    # ------------------------------------------------------------------ user

    async def get_user(self, input: GetUserFairShareInput) -> GetUserFairSharePayload:
        """Get a single user fair share record."""
        result = await self._processors.fair_share.get_user_fair_share.wait_for_complete(
            GetUserFairShareAction(
                resource_group=input.resource_group,
                project_id=input.project_id,
                user_uuid=input.user_uuid,
            )
        )
        return GetUserFairSharePayload(item=self._user_data_to_dto(result.data))

    async def search_user(self, input: SearchUserFairSharesInput) -> SearchUserFairSharesPayload:
        """Search user fair shares with filters and pagination (cursor/offset)."""
        conditions = self._convert_user_filter(input.filter) if input.filter else []
        orders = self._convert_user_orders(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_user_fair_share_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

        result = await self._processors.fair_share.search_user_fair_shares.wait_for_complete(
            SearchUserFairSharesAction(
                pagination=querier.pagination,
                conditions=querier.conditions,
                orders=querier.orders,
            )
        )
        return SearchUserFairSharesPayload(
            items=[self._user_data_to_dto(d) for d in result.items],
            total_count=result.total_count,
        )

    async def search_rg_user(
        self,
        input: SearchUserFairSharesInput,
        resource_group: str,
        domain_name: str,
        project_id: UUID,
    ) -> SearchUserFairSharesPayload:
        """Search user fair shares within a resource group scope (entity-based, cursor/offset)."""
        conditions = self._convert_user_filter_rg(input.filter) if input.filter else []
        orders = self._convert_user_orders_rg(input.order) if input.order else []
        querier = self._build_querier(
            conditions=conditions,
            orders=orders,
            pagination_spec=_user_fair_share_pagination_spec(),
            first=input.first,
            after=input.after,
            last=input.last,
            before=input.before,
            limit=input.limit,
            offset=input.offset,
        )

        result = await self._processors.fair_share.search_rg_user_fair_shares.wait_for_complete(
            SearchRGUserFairSharesAction(
                scope=UserFairShareSearchScope(
                    resource_group=resource_group,
                    domain_name=domain_name,
                    project_id=project_id,
                ),
                querier=querier,
            )
        )
        return SearchUserFairSharesPayload(
            items=[self._user_data_to_dto(d) for d in result.items],
            total_count=result.total_count,
        )

    async def upsert_user(
        self,
        input: UpsertUserFairShareWeightInput,
    ) -> UpsertUserFairShareWeightPayload:
        """Upsert user fair share weight."""
        result = await self._processors.fair_share.upsert_user_fair_share_weight.wait_for_complete(
            UpsertUserFairShareWeightAction(
                resource_group=input.resource_group_name,
                project_id=input.project_id,
                user_uuid=input.user_uuid,
                domain_name=input.domain_name,
                weight=input.weight,
            )
        )
        return UpsertUserFairShareWeightPayload(user_fair_share=self._user_data_to_dto(result.data))

    async def bulk_upsert_user(
        self,
        input: BulkUpsertUserFairShareWeightInput,
    ) -> BulkUpsertUserFairShareWeightPayload:
        """Bulk upsert user fair share weights."""
        result = (
            await self._processors.fair_share.bulk_upsert_user_fair_share_weight.wait_for_complete(
                BulkUpsertUserFairShareWeightAction(
                    resource_group=input.resource_group_name,
                    inputs=[
                        UserWeightInput(
                            user_uuid=e.user_uuid,
                            project_id=e.project_id,
                            domain_name=e.domain_name,
                            weight=e.weight,
                        )
                        for e in input.inputs
                    ],
                )
            )
        )
        return BulkUpsertUserFairShareWeightPayload(upserted_count=result.upserted_count)

    # ------------------------------------------------------------------ filter helpers (domain)

    @staticmethod
    def _convert_domain_filter(filter: DomainFairShareFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter.resource_group is not None:
            cond = filter.resource_group.build_query_condition(
                contains_factory=DomainFairShareConditions.by_resource_group_contains,
                equals_factory=DomainFairShareConditions.by_resource_group_equals,
                starts_with_factory=DomainFairShareConditions.by_resource_group_starts_with,
                ends_with_factory=DomainFairShareConditions.by_resource_group_ends_with,
                in_factory=DomainFairShareConditions.by_resource_group_in,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.domain_name is not None:
            cond = filter.domain_name.build_query_condition(
                contains_factory=DomainFairShareConditions.by_domain_name_contains,
                equals_factory=DomainFairShareConditions.by_domain_name_equals,
                starts_with_factory=DomainFairShareConditions.by_domain_name_starts_with,
                ends_with_factory=DomainFairShareConditions.by_domain_name_ends_with,
                in_factory=DomainFairShareConditions.by_domain_name_in,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.domain is not None and filter.domain.is_active is not None:
            conditions.append(
                DomainFairShareConditions.by_domain_is_active(filter.domain.is_active)
            )
        if filter.AND:
            for sub_filter in filter.AND:
                conditions.extend(FairShareAdapter._convert_domain_filter(sub_filter))
        if filter.OR:
            or_conditions: list[QueryCondition] = []
            for sub_filter in filter.OR:
                or_conditions.extend(FairShareAdapter._convert_domain_filter(sub_filter))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if filter.NOT:
            not_conditions: list[QueryCondition] = []
            for sub_filter in filter.NOT:
                not_conditions.extend(FairShareAdapter._convert_domain_filter(sub_filter))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    @staticmethod
    def _convert_domain_filter_rg(filter: DomainFairShareFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter.resource_group is not None:
            cond = filter.resource_group.build_query_condition(
                contains_factory=RGDomainFairShareConditions.by_resource_group_contains,
                equals_factory=RGDomainFairShareConditions.by_resource_group_equals,
                starts_with_factory=RGDomainFairShareConditions.by_resource_group_starts_with,
                ends_with_factory=RGDomainFairShareConditions.by_resource_group_ends_with,
                in_factory=RGDomainFairShareConditions.by_resource_group_in,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.domain_name is not None:
            cond = filter.domain_name.build_query_condition(
                contains_factory=RGDomainFairShareConditions.by_domain_name_contains,
                equals_factory=RGDomainFairShareConditions.by_domain_name_equals,
                starts_with_factory=RGDomainFairShareConditions.by_domain_name_starts_with,
                ends_with_factory=RGDomainFairShareConditions.by_domain_name_ends_with,
                in_factory=RGDomainFairShareConditions.by_domain_name_in,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.domain is not None and filter.domain.is_active is not None:
            conditions.append(
                DomainFairShareConditions.by_domain_is_active(filter.domain.is_active)
            )
        if filter.AND:
            for sub_filter in filter.AND:
                conditions.extend(FairShareAdapter._convert_domain_filter_rg(sub_filter))
        if filter.OR:
            or_conditions: list[QueryCondition] = []
            for sub_filter in filter.OR:
                or_conditions.extend(FairShareAdapter._convert_domain_filter_rg(sub_filter))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if filter.NOT:
            not_conditions: list[QueryCondition] = []
            for sub_filter in filter.NOT:
                not_conditions.extend(FairShareAdapter._convert_domain_filter_rg(sub_filter))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    @staticmethod
    def _convert_domain_orders(orders: list[DomainFairShareOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case DomainFairShareOrderField.FAIR_SHARE_FACTOR:
                    result.append(DomainFairShareOrders.by_fair_share_factor(ascending=ascending))
                case DomainFairShareOrderField.DOMAIN_NAME:
                    result.append(DomainFairShareOrders.by_domain_name(ascending=ascending))
                case DomainFairShareOrderField.CREATED_AT:
                    result.append(DomainFairShareOrders.by_created_at(ascending=ascending))
                case DomainFairShareOrderField.DOMAIN_IS_ACTIVE:
                    result.append(DomainFairShareOrders.by_domain_is_active(ascending=ascending))
        return result

    @staticmethod
    def _convert_domain_orders_rg(orders: list[DomainFairShareOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case DomainFairShareOrderField.FAIR_SHARE_FACTOR:
                    result.append(RGDomainFairShareOrders.by_fair_share_factor(ascending=ascending))
                case DomainFairShareOrderField.DOMAIN_NAME:
                    result.append(RGDomainFairShareOrders.by_domain_name(ascending=ascending))
                case DomainFairShareOrderField.CREATED_AT:
                    result.append(RGDomainFairShareOrders.by_created_at(ascending=ascending))
                case DomainFairShareOrderField.DOMAIN_IS_ACTIVE:
                    result.append(DomainFairShareOrders.by_domain_is_active(ascending=ascending))
        return result

    # ------------------------------------------------------------------ filter helpers (project)

    @staticmethod
    def _convert_project_filter(filter: ProjectFairShareFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter.resource_group is not None:
            cond = filter.resource_group.build_query_condition(
                contains_factory=ProjectFairShareConditions.by_resource_group_contains,
                equals_factory=ProjectFairShareConditions.by_resource_group_equals,
                starts_with_factory=ProjectFairShareConditions.by_resource_group_starts_with,
                ends_with_factory=ProjectFairShareConditions.by_resource_group_ends_with,
                in_factory=ProjectFairShareConditions.by_resource_group_in,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.project_id is not None:
            cond = filter.project_id.build_query_condition(
                equals_factory=ProjectFairShareConditions.by_project_id,
                in_factory=ProjectFairShareConditions.by_project_ids,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.domain_name is not None:
            cond = filter.domain_name.build_query_condition(
                contains_factory=ProjectFairShareConditions.by_domain_name_contains,
                equals_factory=ProjectFairShareConditions.by_domain_name_equals,
                starts_with_factory=ProjectFairShareConditions.by_domain_name_starts_with,
                ends_with_factory=ProjectFairShareConditions.by_domain_name_ends_with,
                in_factory=ProjectFairShareConditions.by_domain_name_in,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.project is not None and filter.project.is_active is not None:
            conditions.append(
                ProjectFairShareConditions.by_project_is_active(filter.project.is_active)
            )
        if filter.AND:
            for sub_filter in filter.AND:
                conditions.extend(FairShareAdapter._convert_project_filter(sub_filter))
        if filter.OR:
            or_conditions: list[QueryCondition] = []
            for sub_filter in filter.OR:
                or_conditions.extend(FairShareAdapter._convert_project_filter(sub_filter))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if filter.NOT:
            not_conditions: list[QueryCondition] = []
            for sub_filter in filter.NOT:
                not_conditions.extend(FairShareAdapter._convert_project_filter(sub_filter))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    @staticmethod
    def _convert_project_filter_rg(filter: ProjectFairShareFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter.resource_group is not None:
            cond = filter.resource_group.build_query_condition(
                contains_factory=RGProjectFairShareConditions.by_resource_group_contains,
                equals_factory=RGProjectFairShareConditions.by_resource_group_equals,
                starts_with_factory=RGProjectFairShareConditions.by_resource_group_starts_with,
                ends_with_factory=RGProjectFairShareConditions.by_resource_group_ends_with,
                in_factory=RGProjectFairShareConditions.by_resource_group_in,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.project_id is not None:
            cond = filter.project_id.build_query_condition(
                equals_factory=RGProjectFairShareConditions.by_project_id,
                in_factory=RGProjectFairShareConditions.by_project_ids,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.domain_name is not None:
            cond = filter.domain_name.build_query_condition(
                contains_factory=RGProjectFairShareConditions.by_domain_name_contains,
                equals_factory=RGProjectFairShareConditions.by_domain_name_equals,
                starts_with_factory=RGProjectFairShareConditions.by_domain_name_starts_with,
                ends_with_factory=RGProjectFairShareConditions.by_domain_name_ends_with,
                in_factory=RGProjectFairShareConditions.by_domain_name_in,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.project is not None and filter.project.is_active is not None:
            conditions.append(
                ProjectFairShareConditions.by_project_is_active(filter.project.is_active)
            )
        if filter.AND:
            for sub_filter in filter.AND:
                conditions.extend(FairShareAdapter._convert_project_filter_rg(sub_filter))
        if filter.OR:
            or_conditions: list[QueryCondition] = []
            for sub_filter in filter.OR:
                or_conditions.extend(FairShareAdapter._convert_project_filter_rg(sub_filter))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if filter.NOT:
            not_conditions: list[QueryCondition] = []
            for sub_filter in filter.NOT:
                not_conditions.extend(FairShareAdapter._convert_project_filter_rg(sub_filter))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    @staticmethod
    def _convert_project_orders(orders: list[ProjectFairShareOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case ProjectFairShareOrderField.FAIR_SHARE_FACTOR:
                    result.append(ProjectFairShareOrders.by_fair_share_factor(ascending=ascending))
                case ProjectFairShareOrderField.CREATED_AT:
                    result.append(ProjectFairShareOrders.by_created_at(ascending=ascending))
        return result

    @staticmethod
    def _convert_project_orders_rg(orders: list[ProjectFairShareOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case ProjectFairShareOrderField.FAIR_SHARE_FACTOR:
                    result.append(
                        RGProjectFairShareOrders.by_fair_share_factor(ascending=ascending)
                    )
                case ProjectFairShareOrderField.CREATED_AT:
                    result.append(RGProjectFairShareOrders.by_created_at(ascending=ascending))
        return result

    # ------------------------------------------------------------------ filter helpers (user)

    @staticmethod
    def _convert_user_filter(filter: UserFairShareFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter.resource_group is not None:
            cond = filter.resource_group.build_query_condition(
                contains_factory=UserFairShareConditions.by_resource_group_contains,
                equals_factory=UserFairShareConditions.by_resource_group_equals,
                starts_with_factory=UserFairShareConditions.by_resource_group_starts_with,
                ends_with_factory=UserFairShareConditions.by_resource_group_ends_with,
                in_factory=UserFairShareConditions.by_resource_group_in,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.user_uuid is not None:
            cond = filter.user_uuid.build_query_condition(
                equals_factory=UserFairShareConditions.by_user_uuid,
                in_factory=UserFairShareConditions.by_user_uuids,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.project_id is not None:
            cond = filter.project_id.build_query_condition(
                equals_factory=UserFairShareConditions.by_project_id,
                in_factory=UserFairShareConditions.by_project_ids,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.domain_name is not None:
            cond = filter.domain_name.build_query_condition(
                contains_factory=UserFairShareConditions.by_domain_name_contains,
                equals_factory=UserFairShareConditions.by_domain_name_equals,
                starts_with_factory=UserFairShareConditions.by_domain_name_starts_with,
                ends_with_factory=UserFairShareConditions.by_domain_name_ends_with,
                in_factory=UserFairShareConditions.by_domain_name_in,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.user is not None and filter.user.is_active is not None:
            conditions.append(UserFairShareConditions.by_user_is_active(filter.user.is_active))
        if filter.AND:
            for sub_filter in filter.AND:
                conditions.extend(FairShareAdapter._convert_user_filter(sub_filter))
        if filter.OR:
            or_conditions: list[QueryCondition] = []
            for sub_filter in filter.OR:
                or_conditions.extend(FairShareAdapter._convert_user_filter(sub_filter))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if filter.NOT:
            not_conditions: list[QueryCondition] = []
            for sub_filter in filter.NOT:
                not_conditions.extend(FairShareAdapter._convert_user_filter(sub_filter))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    @staticmethod
    def _convert_user_filter_rg(filter: UserFairShareFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        if filter.resource_group is not None:
            cond = filter.resource_group.build_query_condition(
                contains_factory=RGUserFairShareConditions.by_resource_group_contains,
                equals_factory=RGUserFairShareConditions.by_resource_group_equals,
                starts_with_factory=RGUserFairShareConditions.by_resource_group_starts_with,
                ends_with_factory=RGUserFairShareConditions.by_resource_group_ends_with,
                in_factory=RGUserFairShareConditions.by_resource_group_in,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.user_uuid is not None:
            cond = filter.user_uuid.build_query_condition(
                equals_factory=RGUserFairShareConditions.by_user_uuid,
                in_factory=RGUserFairShareConditions.by_user_uuids,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.project_id is not None:
            cond = filter.project_id.build_query_condition(
                equals_factory=RGUserFairShareConditions.by_project_id,
                in_factory=RGUserFairShareConditions.by_project_ids,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.domain_name is not None:
            cond = filter.domain_name.build_query_condition(
                contains_factory=RGUserFairShareConditions.by_domain_name_contains,
                equals_factory=RGUserFairShareConditions.by_domain_name_equals,
                starts_with_factory=RGUserFairShareConditions.by_domain_name_starts_with,
                ends_with_factory=RGUserFairShareConditions.by_domain_name_ends_with,
                in_factory=RGUserFairShareConditions.by_domain_name_in,
            )
            if cond is not None:
                conditions.append(cond)
        if filter.user is not None and filter.user.is_active is not None:
            conditions.append(UserFairShareConditions.by_user_is_active(filter.user.is_active))
        if filter.AND:
            for sub_filter in filter.AND:
                conditions.extend(FairShareAdapter._convert_user_filter_rg(sub_filter))
        if filter.OR:
            or_conditions: list[QueryCondition] = []
            for sub_filter in filter.OR:
                or_conditions.extend(FairShareAdapter._convert_user_filter_rg(sub_filter))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if filter.NOT:
            not_conditions: list[QueryCondition] = []
            for sub_filter in filter.NOT:
                not_conditions.extend(FairShareAdapter._convert_user_filter_rg(sub_filter))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    @staticmethod
    def _convert_user_orders(orders: list[UserFairShareOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case UserFairShareOrderField.FAIR_SHARE_FACTOR:
                    result.append(UserFairShareOrders.by_fair_share_factor(ascending=ascending))
                case UserFairShareOrderField.CREATED_AT:
                    result.append(UserFairShareOrders.by_created_at(ascending=ascending))
        return result

    @staticmethod
    def _convert_user_orders_rg(orders: list[UserFairShareOrder]) -> list[QueryOrder]:
        result: list[QueryOrder] = []
        for o in orders:
            ascending = o.direction == OrderDirection.ASC
            match o.field:
                case UserFairShareOrderField.FAIR_SHARE_FACTOR:
                    result.append(RGUserFairShareOrders.by_fair_share_factor(ascending=ascending))
                case UserFairShareOrderField.CREATED_AT:
                    result.append(RGUserFairShareOrders.by_created_at(ascending=ascending))
        return result

    # ------------------------------------------------------------------ data → DTO converters

    @staticmethod
    def _domain_data_to_dto(data: DomainFairShareData) -> DomainFairShareNode:
        id_str = f"{data.resource_group}:{data.domain_name}"
        return DomainFairShareNode(
            id=id_str,
            resource_group_name=data.resource_group,
            domain_name=data.domain_name,
            spec=FairShareAdapter._convert_spec(
                data.data.spec, data.data.use_default, data.data.uses_default_resources
            ),
            calculation_snapshot=FairShareAdapter._convert_snapshot(data.data.calculation_snapshot),
            created_at=(
                data.data.metadata.created_at
                if data.data.metadata
                else data.data.calculation_snapshot.last_calculated_at
            ),
            updated_at=(
                data.data.metadata.updated_at
                if data.data.metadata
                else data.data.calculation_snapshot.last_calculated_at
            ),
        )

    @staticmethod
    def _project_data_to_dto(data: ProjectFairShareData) -> ProjectFairShareNode:
        id_str = f"{data.resource_group}:{data.project_id}"
        return ProjectFairShareNode(
            id=id_str,
            resource_group_name=data.resource_group,
            project_id=data.project_id,
            domain_name=data.domain_name,
            spec=FairShareAdapter._convert_spec(
                data.data.spec, data.data.use_default, data.data.uses_default_resources
            ),
            calculation_snapshot=FairShareAdapter._convert_snapshot(data.data.calculation_snapshot),
            created_at=(
                data.data.metadata.created_at
                if data.data.metadata
                else data.data.calculation_snapshot.last_calculated_at
            ),
            updated_at=(
                data.data.metadata.updated_at
                if data.data.metadata
                else data.data.calculation_snapshot.last_calculated_at
            ),
        )

    @staticmethod
    def _user_data_to_dto(data: UserFairShareData) -> UserFairShareNode:
        id_str = f"{data.resource_group}:{data.user_uuid}:{data.project_id}"
        return UserFairShareNode(
            id=id_str,
            resource_group_name=data.resource_group,
            user_uuid=data.user_uuid,
            project_id=data.project_id,
            domain_name=data.domain_name,
            spec=FairShareAdapter._convert_spec(
                data.data.spec, data.data.use_default, data.data.uses_default_resources
            ),
            calculation_snapshot=FairShareAdapter._convert_snapshot(data.data.calculation_snapshot),
            created_at=(
                data.data.metadata.created_at
                if data.data.metadata
                else data.data.calculation_snapshot.last_calculated_at
            ),
            updated_at=(
                data.data.metadata.updated_at
                if data.data.metadata
                else data.data.calculation_snapshot.last_calculated_at
            ),
        )

    @staticmethod
    def _convert_spec(
        spec: FairShareSpec,
        use_default: bool,
        uses_default_resources: frozenset[str] = frozenset(),
    ) -> FairShareSpecInfo:
        return FairShareSpecInfo(
            weight=spec.weight,
            uses_default=use_default,
            half_life_days=spec.half_life_days,
            lookback_days=spec.lookback_days,
            decay_unit_days=spec.decay_unit_days,
            resource_weights=[
                ResourceWeightEntryInfo(
                    resource_type=k,
                    weight=v,
                    uses_default=k in uses_default_resources,
                )
                for k, v in spec.resource_weights.items()
            ],
        )

    @staticmethod
    def _convert_snapshot(
        snapshot: FairShareCalculationSnapshot,
    ) -> FairShareCalculationSnapshotInfo:
        return FairShareCalculationSnapshotInfo(
            fair_share_factor=snapshot.fair_share_factor,
            total_decayed_usage=FairShareAdapter._convert_slot_quantities(
                snapshot.total_decayed_usage
            ),
            normalized_usage=snapshot.normalized_usage,
            lookback_start=snapshot.lookback_start,
            lookback_end=snapshot.lookback_end,
            last_calculated_at=snapshot.last_calculated_at,
        )

    @staticmethod
    def _convert_slot_quantities(quantities: Sequence[SlotQuantity]) -> ResourceSlotInfo:
        return ResourceSlotInfo(
            entries=[
                ResourceSlotEntryInfo(resource_type=sq.slot_name, quantity=sq.quantity)
                for sq in quantities
            ]
        )
