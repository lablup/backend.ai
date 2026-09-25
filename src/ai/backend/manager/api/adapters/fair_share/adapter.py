"""Fair share domain adapter - Pydantic-in/Pydantic-out transport layer."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from ai.backend.common.data.entity.resource_group import ResourceGroupName
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
from ai.backend.manager.api.adapter_options.pagination.pagination import PaginationSpec
from ai.backend.manager.api.adapters.base import BaseAdapter
from ai.backend.manager.data.fair_share.types import (
    DomainFairShareData,
    FairShareCalculationSnapshot,
    FairShareSpec,
    ProjectFairShareData,
    UserFairShareData,
)
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.clauses import QueryCondition, QueryOrder
from ai.backend.manager.models.condition_utils import combine_conditions_or, negate_conditions
from ai.backend.manager.models.fair_share.deprecated_search import (
    DeprecatedDomainFairShareFields,
    DeprecatedProjectFairShareFields,
    DeprecatedUserFairShareFields,
)
from ai.backend.manager.models.fair_share.row import (
    DomainFairShareRow,
    ProjectFairShareRow,
    UserFairShareRow,
)
from ai.backend.manager.models.fair_share.scopes import (
    DomainFairShareTarget,
    ProjectFairShareTarget,
    UserFairShareTarget,
)
from ai.backend.manager.models.fair_share.searchable_fields import (
    DomainFairShareSearchableFields,
    ProjectFairShareSearchableFields,
    UserFairShareSearchableFields,
)
from ai.backend.manager.services.fair_share.actions import (
    BulkUpsertDomainFairShareWeightAction,
    BulkUpsertProjectFairShareWeightAction,
    BulkUpsertUserFairShareWeightAction,
    DomainWeightInput,
    GetDomainFairShareAction,
    GetProjectFairShareAction,
    GetUserFairShareAction,
    GlobalSearchDomainFairSharesAction,
    GlobalSearchProjectFairSharesAction,
    GlobalSearchUserFairSharesAction,
    ProjectWeightInput,
    SearchRGDomainFairSharesAction,
    SearchRGProjectFairSharesAction,
    SearchRGUserFairSharesAction,
    UpsertDomainFairShareWeightAction,
    UpsertProjectFairShareWeightAction,
    UpsertUserFairShareWeightAction,
    UserWeightInput,
)
from ai.backend.manager.services.fair_share.processors import FairShareProcessors
from ai.backend.manager.services.resource_group.actions.lookup import LookupResourceGroupAction
from ai.backend.manager.services.resource_group.processors import ResourceGroupProcessors


def _domain_fair_share_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=DomainFairShareSearchableFields.own.created_at.order.apply(ascending=False),
        cursor_column=DomainFairShareRow.id,
    )


def _project_fair_share_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=ProjectFairShareSearchableFields.own.created_at.order.apply(ascending=False),
        cursor_column=ProjectFairShareRow.id,
    )


def _user_fair_share_pagination_spec() -> PaginationSpec:
    return PaginationSpec(
        forward_order=UserFairShareSearchableFields.own.created_at.order.apply(ascending=False),
        cursor_column=UserFairShareRow.id,
    )


class FairShareAdapter(BaseAdapter):
    """Adapter for fair share domain operations (domain / project / user)."""

    _fair_share: FairShareProcessors
    _resource_group: ResourceGroupProcessors

    def __init__(
        self,
        fair_share: FairShareProcessors,
        resource_group: ResourceGroupProcessors,
    ) -> None:
        self._fair_share = fair_share
        self._resource_group = resource_group

    # ------------------------------------------------------------------ domain

    async def get_domain(self, input: GetDomainFairShareInput) -> GetDomainFairSharePayload:
        """Get a single domain fair share record."""
        resource_group_id_result = await self._resource_group.lookup.run(
            LookupResourceGroupAction(name=ResourceGroupName(input.resource_group))
        )
        result = await self._fair_share.get_domain_fair_share.run(
            GetDomainFairShareAction(
                resource_group_id=resource_group_id_result.entity_id(),
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

        result = await self._fair_share.search_domain_fair_shares.run(
            GlobalSearchDomainFairSharesAction(
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
        resource_group_id_result = await self._resource_group.lookup.run(
            LookupResourceGroupAction(name=ResourceGroupName(resource_group))
        )
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

        result = await self._fair_share.search_rg_domain_fair_shares.run(
            SearchRGDomainFairSharesAction(
                resource_group_id=resource_group_id_result.entity_id(),
                scope=DomainFairShareTarget(
                    resource_group_id=resource_group_id_result.entity_id(),
                ),
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
        resource_group_id_result = await self._resource_group.lookup.run(
            LookupResourceGroupAction(name=ResourceGroupName(input.resource_group_name))
        )
        result = await self._fair_share.upsert_domain_fair_share_weight.run(
            UpsertDomainFairShareWeightAction(
                resource_group=input.resource_group_name,
                resource_group_id=resource_group_id_result.entity_id(),
                domain_name=input.domain_name,
                weight=input.weight,
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
        resource_group_id_result = await self._resource_group.lookup.run(
            LookupResourceGroupAction(name=ResourceGroupName(input.resource_group_name))
        )
        result = await self._fair_share.bulk_upsert_domain_fair_share_weight.run(
            BulkUpsertDomainFairShareWeightAction(
                resource_group=input.resource_group_name,
                resource_group_id=resource_group_id_result.entity_id(),
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
        resource_group_id_result = await self._resource_group.lookup.run(
            LookupResourceGroupAction(name=ResourceGroupName(input.resource_group))
        )
        result = await self._fair_share.get_project_fair_share.run(
            GetProjectFairShareAction(
                resource_group_id=resource_group_id_result.entity_id(),
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

        result = await self._fair_share.search_project_fair_shares.run(
            GlobalSearchProjectFairSharesAction(
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
        resource_group_id_result = await self._resource_group.lookup.run(
            LookupResourceGroupAction(name=ResourceGroupName(resource_group))
        )
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

        result = await self._fair_share.search_rg_project_fair_shares.run(
            SearchRGProjectFairSharesAction(
                resource_group_id=resource_group_id_result.entity_id(),
                scope=ProjectFairShareTarget(
                    domain_name=domain_name,
                    resource_group_id=resource_group_id_result.entity_id(),
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
        resource_group_id_result = await self._resource_group.lookup.run(
            LookupResourceGroupAction(name=ResourceGroupName(input.resource_group_name))
        )
        result = await self._fair_share.upsert_project_fair_share_weight.run(
            UpsertProjectFairShareWeightAction(
                resource_group=input.resource_group_name,
                resource_group_id=resource_group_id_result.entity_id(),
                project_id=input.project_id,
                domain_name=input.domain_name,
                weight=input.weight,
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
        resource_group_id_result = await self._resource_group.lookup.run(
            LookupResourceGroupAction(name=ResourceGroupName(input.resource_group_name))
        )
        result = await self._fair_share.bulk_upsert_project_fair_share_weight.run(
            BulkUpsertProjectFairShareWeightAction(
                resource_group=input.resource_group_name,
                resource_group_id=resource_group_id_result.entity_id(),
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
        resource_group_id_result = await self._resource_group.lookup.run(
            LookupResourceGroupAction(name=ResourceGroupName(input.resource_group))
        )
        result = await self._fair_share.get_user_fair_share.run(
            GetUserFairShareAction(
                resource_group_id=resource_group_id_result.entity_id(),
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

        result = await self._fair_share.search_user_fair_shares.run(
            GlobalSearchUserFairSharesAction(
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
        resource_group_id_result = await self._resource_group.lookup.run(
            LookupResourceGroupAction(name=ResourceGroupName(resource_group))
        )
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

        result = await self._fair_share.search_rg_user_fair_shares.run(
            SearchRGUserFairSharesAction(
                resource_group_id=resource_group_id_result.entity_id(),
                scope=UserFairShareTarget(
                    domain_name=domain_name,
                    project_id=project_id,
                    resource_group_id=resource_group_id_result.entity_id(),
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
        resource_group_id_result = await self._resource_group.lookup.run(
            LookupResourceGroupAction(name=ResourceGroupName(input.resource_group_name))
        )
        result = await self._fair_share.upsert_user_fair_share_weight.run(
            UpsertUserFairShareWeightAction(
                resource_group=input.resource_group_name,
                resource_group_id=resource_group_id_result.entity_id(),
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
        resource_group_id_result = await self._resource_group.lookup.run(
            LookupResourceGroupAction(name=ResourceGroupName(input.resource_group_name))
        )
        result = await self._fair_share.bulk_upsert_user_fair_share_weight.run(
            BulkUpsertUserFairShareWeightAction(
                resource_group=input.resource_group_name,
                resource_group_id=resource_group_id_result.entity_id(),
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
        return BulkUpsertUserFairShareWeightPayload(upserted_count=result.upserted_count)

    # ------------------------------------------------------------------ filter helpers (domain)

    def _convert_domain_filter(self, filter: DomainFairShareFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        conditions.extend(
            self.apply_string_filter(
                filter.resource_group, DomainFairShareSearchableFields.own.resource_group.filter
            )
        )
        conditions.extend(
            self.apply_string_filter(
                filter.domain_name, DomainFairShareSearchableFields.own.domain_name.filter
            )
        )
        if filter.domain is not None:
            conditions.extend(
                self.apply_bool_filter(
                    filter.domain.is_active, DeprecatedDomainFairShareFields.is_active.filter
                )
            )
        if filter.AND:
            for sub_filter in filter.AND:
                conditions.extend(self._convert_domain_filter(sub_filter))
        if filter.OR:
            or_conditions: list[QueryCondition] = []
            for sub_filter in filter.OR:
                or_conditions.extend(self._convert_domain_filter(sub_filter))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if filter.NOT:
            not_conditions: list[QueryCondition] = []
            for sub_filter in filter.NOT:
                not_conditions.extend(self._convert_domain_filter(sub_filter))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    def _convert_domain_filter_rg(self, filter: DomainFairShareFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        conditions.extend(
            self.apply_string_filter(
                filter.resource_group, DomainFairShareSearchableFields.own.resource_group.filter
            )
        )
        conditions.extend(
            self.apply_string_filter(
                filter.domain_name, DeprecatedDomainFairShareFields.name.filter
            )
        )
        if filter.domain is not None:
            conditions.extend(
                self.apply_bool_filter(
                    filter.domain.is_active, DeprecatedDomainFairShareFields.is_active.filter
                )
            )
        if filter.AND:
            for sub_filter in filter.AND:
                conditions.extend(self._convert_domain_filter_rg(sub_filter))
        if filter.OR:
            or_conditions: list[QueryCondition] = []
            for sub_filter in filter.OR:
                or_conditions.extend(self._convert_domain_filter_rg(sub_filter))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if filter.NOT:
            not_conditions: list[QueryCondition] = []
            for sub_filter in filter.NOT:
                not_conditions.extend(self._convert_domain_filter_rg(sub_filter))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    def _convert_domain_orders(self, orders: list[DomainFairShareOrder]) -> list[QueryOrder]:
        return [self._convert_domain_order(o) for o in orders]

    def _convert_domain_order(self, order: DomainFairShareOrder) -> QueryOrder:
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case DomainFairShareOrderField.FAIR_SHARE_FACTOR:
                return DomainFairShareSearchableFields.own.fair_share_factor.order.apply(ascending)
            case DomainFairShareOrderField.DOMAIN_NAME:
                return DomainFairShareSearchableFields.own.domain_name.order.apply(ascending)
            case DomainFairShareOrderField.CREATED_AT:
                return DomainFairShareSearchableFields.own.created_at.order.apply(ascending)
            case DomainFairShareOrderField.DOMAIN_IS_ACTIVE:
                return DeprecatedDomainFairShareFields.is_active.order.apply(ascending)

    def _convert_domain_orders_rg(self, orders: list[DomainFairShareOrder]) -> list[QueryOrder]:
        return [self._convert_domain_order_rg(o) for o in orders]

    def _convert_domain_order_rg(self, order: DomainFairShareOrder) -> QueryOrder:
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case DomainFairShareOrderField.FAIR_SHARE_FACTOR:
                return DomainFairShareSearchableFields.own.fair_share_factor.order.apply(ascending)
            case DomainFairShareOrderField.DOMAIN_NAME:
                return DeprecatedDomainFairShareFields.name.order.apply(ascending)
            case DomainFairShareOrderField.CREATED_AT:
                return DomainFairShareSearchableFields.own.created_at.order.apply(ascending)
            case DomainFairShareOrderField.DOMAIN_IS_ACTIVE:
                return DeprecatedDomainFairShareFields.is_active.order.apply(ascending)

    # ------------------------------------------------------------------ filter helpers (project)

    def _convert_project_filter(self, filter: ProjectFairShareFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        conditions.extend(
            self.apply_string_filter(
                filter.resource_group, ProjectFairShareSearchableFields.own.resource_group.filter
            )
        )
        conditions.extend(
            self.apply_uuid_filter(
                filter.project_id, ProjectFairShareSearchableFields.own.project_id.filter
            )
        )
        conditions.extend(
            self.apply_string_filter(
                filter.domain_name, ProjectFairShareSearchableFields.own.domain_name.filter
            )
        )
        if filter.project is not None:
            conditions.extend(
                self.apply_bool_filter(
                    filter.project.is_active, DeprecatedProjectFairShareFields.is_active.filter
                )
            )
        if filter.AND:
            for sub_filter in filter.AND:
                conditions.extend(self._convert_project_filter(sub_filter))
        if filter.OR:
            or_conditions: list[QueryCondition] = []
            for sub_filter in filter.OR:
                or_conditions.extend(self._convert_project_filter(sub_filter))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if filter.NOT:
            not_conditions: list[QueryCondition] = []
            for sub_filter in filter.NOT:
                not_conditions.extend(self._convert_project_filter(sub_filter))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    def _convert_project_filter_rg(self, filter: ProjectFairShareFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        conditions.extend(
            self.apply_string_filter(
                filter.resource_group, ProjectFairShareSearchableFields.own.resource_group.filter
            )
        )
        conditions.extend(
            self.apply_uuid_filter(filter.project_id, DeprecatedProjectFairShareFields.id.filter)
        )
        conditions.extend(
            self.apply_string_filter(
                filter.domain_name, DeprecatedProjectFairShareFields.domain_name.filter
            )
        )
        if filter.project is not None:
            conditions.extend(
                self.apply_bool_filter(
                    filter.project.is_active, DeprecatedProjectFairShareFields.is_active.filter
                )
            )
        if filter.AND:
            for sub_filter in filter.AND:
                conditions.extend(self._convert_project_filter_rg(sub_filter))
        if filter.OR:
            or_conditions: list[QueryCondition] = []
            for sub_filter in filter.OR:
                or_conditions.extend(self._convert_project_filter_rg(sub_filter))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if filter.NOT:
            not_conditions: list[QueryCondition] = []
            for sub_filter in filter.NOT:
                not_conditions.extend(self._convert_project_filter_rg(sub_filter))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    def _convert_project_orders(self, orders: list[ProjectFairShareOrder]) -> list[QueryOrder]:
        return [self._convert_project_order(o) for o in orders]

    def _convert_project_order(self, order: ProjectFairShareOrder) -> QueryOrder:
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case ProjectFairShareOrderField.FAIR_SHARE_FACTOR:
                return ProjectFairShareSearchableFields.own.fair_share_factor.order.apply(ascending)
            case ProjectFairShareOrderField.CREATED_AT:
                return ProjectFairShareSearchableFields.own.created_at.order.apply(ascending)
            case ProjectFairShareOrderField.PROJECT_NAME:
                return DeprecatedProjectFairShareFields.name.order.apply(ascending)
            case ProjectFairShareOrderField.PROJECT_IS_ACTIVE:
                return DeprecatedProjectFairShareFields.is_active.order.apply(ascending)

    def _convert_project_orders_rg(self, orders: list[ProjectFairShareOrder]) -> list[QueryOrder]:
        return [self._convert_project_order_rg(o) for o in orders]

    def _convert_project_order_rg(self, order: ProjectFairShareOrder) -> QueryOrder:
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case ProjectFairShareOrderField.FAIR_SHARE_FACTOR:
                return ProjectFairShareSearchableFields.own.fair_share_factor.order.apply(ascending)
            case ProjectFairShareOrderField.CREATED_AT:
                return ProjectFairShareSearchableFields.own.created_at.order.apply(ascending)
            case ProjectFairShareOrderField.PROJECT_NAME:
                return DeprecatedProjectFairShareFields.name.order.apply(ascending)
            case ProjectFairShareOrderField.PROJECT_IS_ACTIVE:
                return DeprecatedProjectFairShareFields.is_active.order.apply(ascending)

    def _user_active_conditions(self, is_active: bool | None) -> list[QueryCondition]:
        """Active means the account status is ACTIVE; inactive means it is anything else."""
        if is_active is None:
            return []
        status = DeprecatedUserFairShareFields.status.filter
        if is_active:
            return [status.equals(UserStatus.ACTIVE)]
        return [status.not_equals(UserStatus.ACTIVE)]

    # ------------------------------------------------------------------ filter helpers (user)

    def _convert_user_filter(self, filter: UserFairShareFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        conditions.extend(
            self.apply_string_filter(
                filter.resource_group, UserFairShareSearchableFields.own.resource_group.filter
            )
        )
        conditions.extend(
            self.apply_uuid_filter(
                filter.user_uuid, UserFairShareSearchableFields.own.user_uuid.filter
            )
        )
        conditions.extend(
            self.apply_uuid_filter(
                filter.project_id, UserFairShareSearchableFields.own.project_id.filter
            )
        )
        conditions.extend(
            self.apply_string_filter(
                filter.domain_name, UserFairShareSearchableFields.own.domain_name.filter
            )
        )
        if filter.user is not None:
            conditions.extend(self._user_active_conditions(filter.user.is_active))
        if filter.AND:
            for sub_filter in filter.AND:
                conditions.extend(self._convert_user_filter(sub_filter))
        if filter.OR:
            or_conditions: list[QueryCondition] = []
            for sub_filter in filter.OR:
                or_conditions.extend(self._convert_user_filter(sub_filter))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if filter.NOT:
            not_conditions: list[QueryCondition] = []
            for sub_filter in filter.NOT:
                not_conditions.extend(self._convert_user_filter(sub_filter))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    def _convert_user_filter_rg(self, filter: UserFairShareFilter) -> list[QueryCondition]:
        conditions: list[QueryCondition] = []
        conditions.extend(
            self.apply_string_filter(
                filter.resource_group, UserFairShareSearchableFields.own.resource_group.filter
            )
        )
        conditions.extend(
            self.apply_uuid_filter(
                filter.user_uuid, DeprecatedUserFairShareFields.membership_user_id.filter
            )
        )
        conditions.extend(
            self.apply_uuid_filter(
                filter.project_id, DeprecatedUserFairShareFields.membership_project_id.filter
            )
        )
        conditions.extend(
            self.apply_string_filter(
                filter.domain_name, DeprecatedUserFairShareFields.domain_name.filter
            )
        )
        if filter.user is not None:
            conditions.extend(self._user_active_conditions(filter.user.is_active))
        if filter.AND:
            for sub_filter in filter.AND:
                conditions.extend(self._convert_user_filter_rg(sub_filter))
        if filter.OR:
            or_conditions: list[QueryCondition] = []
            for sub_filter in filter.OR:
                or_conditions.extend(self._convert_user_filter_rg(sub_filter))
            if or_conditions:
                conditions.append(combine_conditions_or(or_conditions))
        if filter.NOT:
            not_conditions: list[QueryCondition] = []
            for sub_filter in filter.NOT:
                not_conditions.extend(self._convert_user_filter_rg(sub_filter))
            if not_conditions:
                conditions.append(negate_conditions(not_conditions))
        return conditions

    def _convert_user_orders(self, orders: list[UserFairShareOrder]) -> list[QueryOrder]:
        return [self._convert_user_order(o) for o in orders]

    def _convert_user_order(self, order: UserFairShareOrder) -> QueryOrder:
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case UserFairShareOrderField.FAIR_SHARE_FACTOR:
                return UserFairShareSearchableFields.own.fair_share_factor.order.apply(ascending)
            case UserFairShareOrderField.CREATED_AT:
                return UserFairShareSearchableFields.own.created_at.order.apply(ascending)
            case UserFairShareOrderField.USER_USERNAME:
                return DeprecatedUserFairShareFields.username.order.apply(ascending)
            case UserFairShareOrderField.USER_EMAIL:
                return DeprecatedUserFairShareFields.email.order.apply(ascending)

    def _convert_user_orders_rg(self, orders: list[UserFairShareOrder]) -> list[QueryOrder]:
        return [self._convert_user_order_rg(o) for o in orders]

    def _convert_user_order_rg(self, order: UserFairShareOrder) -> QueryOrder:
        ascending = order.direction == OrderDirection.ASC
        match order.field:
            case UserFairShareOrderField.FAIR_SHARE_FACTOR:
                return UserFairShareSearchableFields.own.fair_share_factor.order.apply(ascending)
            case UserFairShareOrderField.CREATED_AT:
                return UserFairShareSearchableFields.own.created_at.order.apply(ascending)
            case UserFairShareOrderField.USER_USERNAME:
                return DeprecatedUserFairShareFields.username.order.apply(ascending)
            case UserFairShareOrderField.USER_EMAIL:
                return DeprecatedUserFairShareFields.email.order.apply(ascending)

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
