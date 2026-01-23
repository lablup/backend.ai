"""
Adapters to convert fair share DTOs to repository BatchQuerier objects.
Handles conversion of filter, order, and pagination parameters.
Also provides data-to-DTO conversion functions.
"""

from __future__ import annotations

from ai.backend.common.dto.manager.fair_share import (
    DomainFairShareDTO,
    DomainFairShareFilter,
    DomainFairShareOrder,
    DomainFairShareOrderField,
    DomainUsageBucketDTO,
    DomainUsageBucketFilter,
    DomainUsageBucketOrder,
    DomainUsageBucketOrderField,
    FairShareCalculationSnapshotDTO,
    FairShareSpecDTO,
    OrderDirection,
    ProjectFairShareDTO,
    ProjectFairShareFilter,
    ProjectFairShareOrder,
    ProjectFairShareOrderField,
    ProjectUsageBucketDTO,
    ProjectUsageBucketFilter,
    ProjectUsageBucketOrder,
    ProjectUsageBucketOrderField,
    ResourceGroupFairShareSpecDTO,
    ResourceSlotDTO,
    ResourceSlotEntryDTO,
    SearchDomainFairSharesRequest,
    SearchDomainUsageBucketsRequest,
    SearchProjectFairSharesRequest,
    SearchProjectUsageBucketsRequest,
    SearchUserFairSharesRequest,
    SearchUserUsageBucketsRequest,
    UpdateResourceGroupFairShareSpecRequest,
    UsageBucketMetadataDTO,
    UserFairShareDTO,
    UserFairShareFilter,
    UserFairShareOrder,
    UserFairShareOrderField,
    UserUsageBucketDTO,
    UserUsageBucketFilter,
    UserUsageBucketOrder,
    UserUsageBucketOrderField,
)
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.fair_share.types import (
    DomainFairShareData,
    FairShareCalculationSnapshot,
    FairShareSpec,
    ProjectFairShareData,
    UserFairShareData,
)
from ai.backend.manager.models.scaling_group.types import FairShareScalingGroupSpec
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    OffsetPagination,
    QueryCondition,
    QueryOrder,
)
from ai.backend.manager.repositories.fair_share.options import (
    DomainFairShareConditions,
    DomainFairShareOrders,
    ProjectFairShareConditions,
    ProjectFairShareOrders,
    UserFairShareConditions,
    UserFairShareOrders,
)
from ai.backend.manager.repositories.resource_usage_history.options import (
    DomainUsageBucketConditions,
    DomainUsageBucketOrders,
    ProjectUsageBucketConditions,
    ProjectUsageBucketOrders,
    UserUsageBucketConditions,
    UserUsageBucketOrders,
)
from ai.backend.manager.repositories.resource_usage_history.types import (
    DomainUsageBucketData,
    ProjectUsageBucketData,
    UserUsageBucketData,
)

__all__ = ("FairShareAdapter",)


class FairShareAdapter:
    """Adapter for converting fair share requests to repository queries."""

    # Domain Fair Share

    def build_domain_fair_share_querier(
        self, request: SearchDomainFairSharesRequest
    ) -> BatchQuerier:
        """Build a BatchQuerier for domain fair shares from search request."""
        conditions = (
            self._convert_domain_fair_share_filter(request.filter) if request.filter else []
        )
        orders = (
            [self._convert_domain_fair_share_order(o) for o in request.order]
            if request.order
            else []
        )
        pagination = OffsetPagination(limit=request.limit, offset=request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_domain_fair_share_filter(
        self, filter: DomainFairShareFilter
    ) -> list[QueryCondition]:
        """Convert domain fair share filter to list of query conditions."""
        conditions: list[QueryCondition] = []

        if filter.resource_group is not None and filter.resource_group.equals is not None:
            conditions.append(
                DomainFairShareConditions.by_resource_group(filter.resource_group.equals)
            )

        if filter.domain_name is not None and filter.domain_name.equals is not None:
            conditions.append(DomainFairShareConditions.by_domain_name(filter.domain_name.equals))

        return conditions

    def _convert_domain_fair_share_order(self, order: DomainFairShareOrder) -> QueryOrder:
        """Convert domain fair share order specification to query order."""
        ascending = order.direction == OrderDirection.ASC

        match order.field:
            case DomainFairShareOrderField.FAIR_SHARE_FACTOR:
                return DomainFairShareOrders.by_fair_share_factor(ascending=ascending)
            case DomainFairShareOrderField.DOMAIN_NAME:
                return DomainFairShareOrders.by_domain_name(ascending=ascending)
            case DomainFairShareOrderField.CREATED_AT:
                return DomainFairShareOrders.by_created_at(ascending=ascending)

        raise ValueError(f"Unknown order field: {order.field}")

    def convert_domain_fair_share_to_dto(self, data: DomainFairShareData) -> DomainFairShareDTO:
        """Convert DomainFairShareData to DTO."""
        return DomainFairShareDTO(
            id=data.id,
            resource_group=data.resource_group,
            domain_name=data.domain_name,
            spec=self._convert_spec_to_dto(data.spec),
            calculation_snapshot=self._convert_calculation_snapshot_to_dto(
                data.calculation_snapshot
            ),
            created_at=data.metadata.created_at,
            updated_at=data.metadata.updated_at,
        )

    # Project Fair Share

    def build_project_fair_share_querier(
        self, request: SearchProjectFairSharesRequest
    ) -> BatchQuerier:
        """Build a BatchQuerier for project fair shares from search request."""
        conditions = (
            self._convert_project_fair_share_filter(request.filter) if request.filter else []
        )
        orders = (
            [self._convert_project_fair_share_order(o) for o in request.order]
            if request.order
            else []
        )
        pagination = OffsetPagination(limit=request.limit, offset=request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_project_fair_share_filter(
        self, filter: ProjectFairShareFilter
    ) -> list[QueryCondition]:
        """Convert project fair share filter to list of query conditions."""
        conditions: list[QueryCondition] = []

        if filter.resource_group is not None and filter.resource_group.equals is not None:
            conditions.append(
                ProjectFairShareConditions.by_resource_group(filter.resource_group.equals)
            )

        if filter.project_id is not None:
            if filter.project_id.equals is not None:
                conditions.append(
                    ProjectFairShareConditions.by_project_id(filter.project_id.equals)
                )
            elif filter.project_id.in_ is not None:
                conditions.append(ProjectFairShareConditions.by_project_ids(filter.project_id.in_))

        if filter.domain_name is not None and filter.domain_name.equals is not None:
            conditions.append(ProjectFairShareConditions.by_domain_name(filter.domain_name.equals))

        return conditions

    def _convert_project_fair_share_order(self, order: ProjectFairShareOrder) -> QueryOrder:
        """Convert project fair share order specification to query order."""
        ascending = order.direction == OrderDirection.ASC

        match order.field:
            case ProjectFairShareOrderField.FAIR_SHARE_FACTOR:
                return ProjectFairShareOrders.by_fair_share_factor(ascending=ascending)
            case ProjectFairShareOrderField.CREATED_AT:
                return ProjectFairShareOrders.by_created_at(ascending=ascending)

        raise ValueError(f"Unknown order field: {order.field}")

    def convert_project_fair_share_to_dto(self, data: ProjectFairShareData) -> ProjectFairShareDTO:
        """Convert ProjectFairShareData to DTO."""
        return ProjectFairShareDTO(
            id=data.id,
            resource_group=data.resource_group,
            project_id=data.project_id,
            domain_name=data.domain_name,
            spec=self._convert_spec_to_dto(data.spec),
            calculation_snapshot=self._convert_calculation_snapshot_to_dto(
                data.calculation_snapshot
            ),
            created_at=data.metadata.created_at,
            updated_at=data.metadata.updated_at,
        )

    # User Fair Share

    def build_user_fair_share_querier(self, request: SearchUserFairSharesRequest) -> BatchQuerier:
        """Build a BatchQuerier for user fair shares from search request."""
        conditions = self._convert_user_fair_share_filter(request.filter) if request.filter else []
        orders = (
            [self._convert_user_fair_share_order(o) for o in request.order] if request.order else []
        )
        pagination = OffsetPagination(limit=request.limit, offset=request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_user_fair_share_filter(self, filter: UserFairShareFilter) -> list[QueryCondition]:
        """Convert user fair share filter to list of query conditions."""
        conditions: list[QueryCondition] = []

        if filter.resource_group is not None and filter.resource_group.equals is not None:
            conditions.append(
                UserFairShareConditions.by_resource_group(filter.resource_group.equals)
            )

        if filter.user_uuid is not None:
            if filter.user_uuid.equals is not None:
                conditions.append(UserFairShareConditions.by_user_uuid(filter.user_uuid.equals))
            elif filter.user_uuid.in_ is not None:
                conditions.append(UserFairShareConditions.by_user_uuids(filter.user_uuid.in_))

        if filter.project_id is not None:
            if filter.project_id.equals is not None:
                conditions.append(UserFairShareConditions.by_project_id(filter.project_id.equals))
            elif filter.project_id.in_ is not None:
                conditions.append(UserFairShareConditions.by_project_ids(filter.project_id.in_))

        if filter.domain_name is not None and filter.domain_name.equals is not None:
            conditions.append(UserFairShareConditions.by_domain_name(filter.domain_name.equals))

        return conditions

    def _convert_user_fair_share_order(self, order: UserFairShareOrder) -> QueryOrder:
        """Convert user fair share order specification to query order."""
        ascending = order.direction == OrderDirection.ASC

        match order.field:
            case UserFairShareOrderField.FAIR_SHARE_FACTOR:
                return UserFairShareOrders.by_fair_share_factor(ascending=ascending)
            case UserFairShareOrderField.CREATED_AT:
                return UserFairShareOrders.by_created_at(ascending=ascending)

        raise ValueError(f"Unknown order field: {order.field}")

    def convert_user_fair_share_to_dto(self, data: UserFairShareData) -> UserFairShareDTO:
        """Convert UserFairShareData to DTO."""
        return UserFairShareDTO(
            id=data.id,
            resource_group=data.resource_group,
            user_uuid=data.user_uuid,
            project_id=data.project_id,
            domain_name=data.domain_name,
            spec=self._convert_spec_to_dto(data.spec),
            calculation_snapshot=self._convert_calculation_snapshot_to_dto(
                data.calculation_snapshot
            ),
            created_at=data.metadata.created_at,
            updated_at=data.metadata.updated_at,
        )

    # Domain Usage Bucket

    def build_domain_usage_bucket_querier(
        self, request: SearchDomainUsageBucketsRequest
    ) -> BatchQuerier:
        """Build a BatchQuerier for domain usage buckets from search request."""
        conditions = (
            self._convert_domain_usage_bucket_filter(request.filter) if request.filter else []
        )
        orders = (
            [self._convert_domain_usage_bucket_order(o) for o in request.order]
            if request.order
            else []
        )
        pagination = OffsetPagination(limit=request.limit, offset=request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_domain_usage_bucket_filter(
        self, filter: DomainUsageBucketFilter
    ) -> list[QueryCondition]:
        """Convert domain usage bucket filter to list of query conditions."""
        conditions: list[QueryCondition] = []

        if filter.resource_group is not None and filter.resource_group.equals is not None:
            conditions.append(
                DomainUsageBucketConditions.by_resource_group(filter.resource_group.equals)
            )

        if filter.domain_name is not None and filter.domain_name.equals is not None:
            conditions.append(DomainUsageBucketConditions.by_domain_name(filter.domain_name.equals))

        return conditions

    def _convert_domain_usage_bucket_order(self, order: DomainUsageBucketOrder) -> QueryOrder:
        """Convert domain usage bucket order specification to query order."""
        ascending = order.direction == OrderDirection.ASC

        match order.field:
            case DomainUsageBucketOrderField.PERIOD_START:
                return DomainUsageBucketOrders.by_period_start(ascending=ascending)

        raise ValueError(f"Unknown order field: {order.field}")

    def convert_domain_usage_bucket_to_dto(
        self, data: DomainUsageBucketData
    ) -> DomainUsageBucketDTO:
        """Convert DomainUsageBucketData to DTO."""
        return DomainUsageBucketDTO(
            id=data.id,
            domain_name=data.domain_name,
            resource_group=data.resource_group,
            metadata=UsageBucketMetadataDTO(
                period_start=data.period_start,
                period_end=data.period_end,
                decay_unit_days=data.decay_unit_days,
                created_at=data.created_at,
                updated_at=data.updated_at,
            ),
            resource_usage=self._convert_resource_slot(data.resource_usage),
            capacity_snapshot=self._convert_resource_slot(data.capacity_snapshot),
        )

    # Project Usage Bucket

    def build_project_usage_bucket_querier(
        self, request: SearchProjectUsageBucketsRequest
    ) -> BatchQuerier:
        """Build a BatchQuerier for project usage buckets from search request."""
        conditions = (
            self._convert_project_usage_bucket_filter(request.filter) if request.filter else []
        )
        orders = (
            [self._convert_project_usage_bucket_order(o) for o in request.order]
            if request.order
            else []
        )
        pagination = OffsetPagination(limit=request.limit, offset=request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_project_usage_bucket_filter(
        self, filter: ProjectUsageBucketFilter
    ) -> list[QueryCondition]:
        """Convert project usage bucket filter to list of query conditions."""
        conditions: list[QueryCondition] = []

        if filter.resource_group is not None and filter.resource_group.equals is not None:
            conditions.append(
                ProjectUsageBucketConditions.by_resource_group(filter.resource_group.equals)
            )

        if filter.project_id is not None and filter.project_id.equals is not None:
            conditions.append(ProjectUsageBucketConditions.by_project_id(filter.project_id.equals))

        return conditions

    def _convert_project_usage_bucket_order(self, order: ProjectUsageBucketOrder) -> QueryOrder:
        """Convert project usage bucket order specification to query order."""
        ascending = order.direction == OrderDirection.ASC

        match order.field:
            case ProjectUsageBucketOrderField.PERIOD_START:
                return ProjectUsageBucketOrders.by_period_start(ascending=ascending)

        raise ValueError(f"Unknown order field: {order.field}")

    def convert_project_usage_bucket_to_dto(
        self, data: ProjectUsageBucketData
    ) -> ProjectUsageBucketDTO:
        """Convert ProjectUsageBucketData to DTO."""
        return ProjectUsageBucketDTO(
            id=data.id,
            project_id=data.project_id,
            domain_name=data.domain_name,
            resource_group=data.resource_group,
            metadata=UsageBucketMetadataDTO(
                period_start=data.period_start,
                period_end=data.period_end,
                decay_unit_days=data.decay_unit_days,
                created_at=data.created_at,
                updated_at=data.updated_at,
            ),
            resource_usage=self._convert_resource_slot(data.resource_usage),
            capacity_snapshot=self._convert_resource_slot(data.capacity_snapshot),
        )

    # User Usage Bucket

    def build_user_usage_bucket_querier(
        self, request: SearchUserUsageBucketsRequest
    ) -> BatchQuerier:
        """Build a BatchQuerier for user usage buckets from search request."""
        conditions = (
            self._convert_user_usage_bucket_filter(request.filter) if request.filter else []
        )
        orders = (
            [self._convert_user_usage_bucket_order(o) for o in request.order]
            if request.order
            else []
        )
        pagination = OffsetPagination(limit=request.limit, offset=request.offset)

        return BatchQuerier(conditions=conditions, orders=orders, pagination=pagination)

    def _convert_user_usage_bucket_filter(
        self, filter: UserUsageBucketFilter
    ) -> list[QueryCondition]:
        """Convert user usage bucket filter to list of query conditions."""
        conditions: list[QueryCondition] = []

        if filter.resource_group is not None and filter.resource_group.equals is not None:
            conditions.append(
                UserUsageBucketConditions.by_resource_group(filter.resource_group.equals)
            )

        if filter.user_uuid is not None and filter.user_uuid.equals is not None:
            conditions.append(UserUsageBucketConditions.by_user_uuid(filter.user_uuid.equals))

        if filter.project_id is not None and filter.project_id.equals is not None:
            conditions.append(UserUsageBucketConditions.by_project_id(filter.project_id.equals))

        return conditions

    def _convert_user_usage_bucket_order(self, order: UserUsageBucketOrder) -> QueryOrder:
        """Convert user usage bucket order specification to query order."""
        ascending = order.direction == OrderDirection.ASC

        match order.field:
            case UserUsageBucketOrderField.PERIOD_START:
                return UserUsageBucketOrders.by_period_start(ascending=ascending)

        raise ValueError(f"Unknown order field: {order.field}")

    def convert_user_usage_bucket_to_dto(self, data: UserUsageBucketData) -> UserUsageBucketDTO:
        """Convert UserUsageBucketData to DTO."""
        return UserUsageBucketDTO(
            id=data.id,
            user_uuid=data.user_uuid,
            project_id=data.project_id,
            domain_name=data.domain_name,
            resource_group=data.resource_group,
            metadata=UsageBucketMetadataDTO(
                period_start=data.period_start,
                period_end=data.period_end,
                decay_unit_days=data.decay_unit_days,
                created_at=data.created_at,
                updated_at=data.updated_at,
            ),
            resource_usage=self._convert_resource_slot(data.resource_usage),
            capacity_snapshot=self._convert_resource_slot(data.capacity_snapshot),
        )

    # Common helpers

    def _convert_spec_to_dto(self, spec: FairShareSpec) -> FairShareSpecDTO:
        """Convert FairShareSpec to DTO."""
        return FairShareSpecDTO(
            weight=spec.weight,
            half_life_days=spec.half_life_days,
            lookback_days=spec.lookback_days,
            decay_unit_days=spec.decay_unit_days,
            resource_weights=self._convert_resource_slot(spec.resource_weights),
        )

    def _convert_calculation_snapshot_to_dto(
        self, snapshot: FairShareCalculationSnapshot
    ) -> FairShareCalculationSnapshotDTO:
        """Convert FairShareCalculationSnapshot to DTO."""
        return FairShareCalculationSnapshotDTO(
            fair_share_factor=snapshot.fair_share_factor,
            total_decayed_usage=self._convert_resource_slot(snapshot.total_decayed_usage),
            normalized_usage=snapshot.normalized_usage,
            lookback_start=snapshot.lookback_start,
            lookback_end=snapshot.lookback_end,
            last_calculated_at=snapshot.last_calculated_at,
        )

    @staticmethod
    def _convert_resource_slot(slot: ResourceSlot) -> ResourceSlotDTO:
        """Convert ResourceSlot to ResourceSlotDTO."""
        entries = [
            ResourceSlotEntryDTO(resource_type=key, quantity=str(value))
            for key, value in slot.items()
        ]
        return ResourceSlotDTO(entries=entries)

    # Resource Group Fair Share Spec

    def merge_fair_share_spec(
        self,
        request: UpdateResourceGroupFairShareSpecRequest,
        existing: FairShareScalingGroupSpec,
    ) -> FairShareScalingGroupSpec:
        """Merge partial update request with existing spec.

        Only provided fields are updated; others retain existing values.
        """
        # Merge resource_weights: partial update with deletion support
        merged_resource_weights = existing.resource_weights
        if request.resource_weights is not None:
            # Start with existing weights
            merged_weights_dict = dict(existing.resource_weights)
            for entry in request.resource_weights:
                if entry.weight is None:
                    # Remove the resource type (revert to default)
                    merged_weights_dict.pop(entry.resource_type, None)
                else:
                    # Update or add the resource type
                    merged_weights_dict[entry.resource_type] = entry.weight
            merged_resource_weights = ResourceSlot(merged_weights_dict)

        return FairShareScalingGroupSpec(
            half_life_days=(
                request.half_life_days
                if request.half_life_days is not None
                else existing.half_life_days
            ),
            lookback_days=(
                request.lookback_days
                if request.lookback_days is not None
                else existing.lookback_days
            ),
            decay_unit_days=(
                request.decay_unit_days
                if request.decay_unit_days is not None
                else existing.decay_unit_days
            ),
            default_weight=(
                request.default_weight
                if request.default_weight is not None
                else existing.default_weight
            ),
            resource_weights=merged_resource_weights,
        )

    def convert_scaling_group_spec_to_dto(
        self,
        spec: FairShareScalingGroupSpec,
    ) -> ResourceGroupFairShareSpecDTO:
        """Convert FairShareScalingGroupSpec to DTO."""
        return ResourceGroupFairShareSpecDTO(
            half_life_days=spec.half_life_days,
            lookback_days=spec.lookback_days,
            decay_unit_days=spec.decay_unit_days,
            default_weight=spec.default_weight,
            resource_weights=self._convert_resource_slot(spec.resource_weights),
        )
