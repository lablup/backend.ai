"""Fair Share Service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.data.fair_share import (
    DomainFairShareData,
    FairShareCalculationSnapshot,
    FairShareMetadata,
    FairShareSpec,
    ProjectFairShareData,
    UserFairShareData,
)
from ai.backend.manager.models.scaling_group.types import FairShareScalingGroupSpec
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    BulkUpserter,
    Upserter,
)
from ai.backend.manager.repositories.fair_share import FairShareRepository
from ai.backend.manager.repositories.fair_share.upserters import (
    DomainFairShareBulkWeightUpserterSpec,
    DomainFairShareUpserterSpec,
    ProjectFairShareBulkWeightUpserterSpec,
    ProjectFairShareUpserterSpec,
    UserFairShareBulkWeightUpserterSpec,
    UserFairShareUpserterSpec,
)
from ai.backend.manager.types import TriState

from .actions import (
    BulkUpsertDomainFairShareWeightAction,
    BulkUpsertDomainFairShareWeightActionResult,
    BulkUpsertProjectFairShareWeightAction,
    BulkUpsertProjectFairShareWeightActionResult,
    BulkUpsertUserFairShareWeightAction,
    BulkUpsertUserFairShareWeightActionResult,
    GetDomainFairShareAction,
    GetDomainFairShareActionResult,
    GetProjectFairShareAction,
    GetProjectFairShareActionResult,
    GetUserFairShareAction,
    GetUserFairShareActionResult,
    SearchDomainFairSharesAction,
    SearchDomainFairSharesActionResult,
    SearchProjectFairSharesAction,
    SearchProjectFairSharesActionResult,
    SearchRGDomainFairSharesAction,
    SearchRGDomainFairSharesActionResult,
    SearchRGProjectFairSharesAction,
    SearchRGProjectFairSharesActionResult,
    SearchRGUserFairSharesAction,
    SearchRGUserFairSharesActionResult,
    SearchUserFairSharesAction,
    SearchUserFairSharesActionResult,
    UpsertDomainFairShareWeightAction,
    UpsertDomainFairShareWeightActionResult,
    UpsertProjectFairShareWeightAction,
    UpsertProjectFairShareWeightActionResult,
    UpsertUserFairShareWeightAction,
    UpsertUserFairShareWeightActionResult,
)

__all__ = ("FairShareService",)


class FairShareService:
    """Service for fair share data operations.

    Provides read operations wrapping the FairShareRepository.
    Write operations (upsert) are handled directly by sokovan using the repository.
    """

    _repository: FairShareRepository

    def __init__(self, repository: FairShareRepository) -> None:
        self._repository = repository

    # Helper methods for creating default fair share data

    def _create_default_spec(self, scaling_group_spec: FairShareScalingGroupSpec) -> FairShareSpec:
        """Create default FairShareSpec from scaling group spec."""
        return FairShareSpec(
            weight=scaling_group_spec.default_weight,
            half_life_days=scaling_group_spec.half_life_days,
            lookback_days=scaling_group_spec.lookback_days,
            decay_unit_days=scaling_group_spec.decay_unit_days,
            resource_weights=scaling_group_spec.resource_weights,
        )

    def _create_default_calculation_snapshot(
        self, scaling_group_spec: FairShareScalingGroupSpec
    ) -> FairShareCalculationSnapshot:
        """Create default FairShareCalculationSnapshot with zero values."""
        now = datetime.now(tz=UTC)
        today = now.date()
        lookback_start = today - timedelta(days=scaling_group_spec.lookback_days)
        return FairShareCalculationSnapshot(
            fair_share_factor=Decimal("1.0"),  # Default factor (no usage history)
            total_decayed_usage=ResourceSlot(),
            normalized_usage=Decimal("0.0"),
            lookback_start=lookback_start,
            lookback_end=today,
            last_calculated_at=now,
        )

    def _create_default_metadata(self) -> FairShareMetadata:
        """Create default FairShareMetadata with current timestamp."""
        now = datetime.now(tz=UTC)
        return FairShareMetadata(
            created_at=now,
            updated_at=now,
        )

    def _create_default_domain_fair_share(
        self,
        resource_group: str,
        domain_name: str,
        scaling_group_spec: FairShareScalingGroupSpec,
    ) -> DomainFairShareData:
        """Create default DomainFairShareData for domains without fair share records.

        Sets weight=None and uses_default=True to indicate this is generated from defaults.
        """
        return DomainFairShareData(
            id=uuid.UUID(int=0),  # Sentinel UUID for non-persisted records
            resource_group=resource_group,
            domain_name=domain_name,
            spec=FairShareSpec(
                weight=None,  # None indicates using resource group's default weight
                half_life_days=scaling_group_spec.half_life_days,
                lookback_days=scaling_group_spec.lookback_days,
                decay_unit_days=scaling_group_spec.decay_unit_days,
                resource_weights=scaling_group_spec.resource_weights,
            ),
            calculation_snapshot=self._create_default_calculation_snapshot(scaling_group_spec),
            metadata=self._create_default_metadata(),
            default_weight=scaling_group_spec.default_weight,
            uses_default=True,
        )

    def _create_default_project_fair_share(
        self,
        resource_group: str,
        project_id: uuid.UUID,
        domain_name: str,
        scaling_group_spec: FairShareScalingGroupSpec,
    ) -> ProjectFairShareData:
        """Create default ProjectFairShareData for projects without fair share records.

        Sets uses_default=True to indicate this is generated from defaults.
        """
        return ProjectFairShareData(
            id=uuid.UUID(int=0),
            resource_group=resource_group,
            project_id=project_id,
            domain_name=domain_name,
            spec=FairShareSpec(
                weight=None,
                half_life_days=scaling_group_spec.half_life_days,
                lookback_days=scaling_group_spec.lookback_days,
                decay_unit_days=scaling_group_spec.decay_unit_days,
                resource_weights=scaling_group_spec.resource_weights,
            ),
            calculation_snapshot=self._create_default_calculation_snapshot(scaling_group_spec),
            metadata=self._create_default_metadata(),
            default_weight=scaling_group_spec.default_weight,
            uses_default=True,
        )

    def _create_default_user_fair_share(
        self,
        resource_group: str,
        user_uuid: uuid.UUID,
        project_id: uuid.UUID,
        domain_name: str,
        scaling_group_spec: FairShareScalingGroupSpec,
    ) -> UserFairShareData:
        """Create default UserFairShareData for users without fair share records.

        Sets uses_default=True to indicate this is generated from defaults.
        """
        return UserFairShareData(
            id=uuid.UUID(int=0),
            resource_group=resource_group,
            user_uuid=user_uuid,
            project_id=project_id,
            domain_name=domain_name,
            spec=FairShareSpec(
                weight=None,
                half_life_days=scaling_group_spec.half_life_days,
                lookback_days=scaling_group_spec.lookback_days,
                decay_unit_days=scaling_group_spec.decay_unit_days,
                resource_weights=scaling_group_spec.resource_weights,
            ),
            calculation_snapshot=self._create_default_calculation_snapshot(scaling_group_spec),
            metadata=self._create_default_metadata(),
            default_weight=scaling_group_spec.default_weight,
            uses_default=True,
            scheduling_rank=None,  # No rank calculated yet
        )

    # Domain Fair Share

    async def get_domain_fair_share(
        self, action: GetDomainFairShareAction
    ) -> GetDomainFairShareActionResult:
        """Get a domain fair share record.

        If the record doesn't exist but the domain is connected to the resource group,
        returns default fair share data using the resource group's default configuration.

        Raises:
            DomainNotConnectedToResourceGroupError: If the domain is not connected
                to the specified resource group.
        """
        result = await self._repository.get_rg_scoped_domain_fair_share(
            resource_group=action.resource_group,
            domain_name=action.domain_name,
        )

        if result is not None:
            return GetDomainFairShareActionResult(data=result)

        # Domain is connected but has no fair share record - create default
        scaling_group_spec = await self._repository.get_scaling_group_fair_share_spec(
            action.resource_group
        )
        default_data = self._create_default_domain_fair_share(
            resource_group=action.resource_group,
            domain_name=action.domain_name,
            scaling_group_spec=scaling_group_spec,
        )
        return GetDomainFairShareActionResult(data=default_data)

    async def search_domain_fair_shares(
        self, action: SearchDomainFairSharesAction
    ) -> SearchDomainFairSharesActionResult:
        """Search domain fair shares with pagination."""
        querier = BatchQuerier(
            pagination=action.pagination,
            conditions=action.conditions,
            orders=action.orders,
        )
        result = await self._repository.search_domain_fair_shares(querier)
        return SearchDomainFairSharesActionResult(
            items=result.items,
            total_count=result.total_count,
        )

    async def search_rg_domain_fair_shares(
        self,
        action: SearchRGDomainFairSharesAction,
    ) -> SearchRGDomainFairSharesActionResult:
        """Search domain fair shares within a resource group scope.

        Returns all domains in the resource group, filling defaults for entities
        without fair share records.
        """
        # Call entity-based repository method
        entity_result = await self._repository.search_rg_scoped_domain_fair_shares(
            action.scope, action.querier
        )

        # Fetch scaling group spec once for all defaults
        scaling_group_spec = await self._repository.get_scaling_group_fair_share_spec(
            action.scope.resource_group
        )

        # Transform EntityItem → FairShareData
        items: list[DomainFairShareData] = []
        for entity_item in entity_result.items:
            if entity_item.details is not None:
                items.append(entity_item.details)
            else:
                default_data = self._create_default_domain_fair_share(
                    resource_group=entity_item.resource_group,
                    domain_name=entity_item.domain_name,
                    scaling_group_spec=scaling_group_spec,
                )
                items.append(default_data)

        return SearchRGDomainFairSharesActionResult(
            items=items,
            total_count=entity_result.total_count,
        )

    # Project Fair Share

    async def get_project_fair_share(
        self, action: GetProjectFairShareAction
    ) -> GetProjectFairShareActionResult:
        """Get a project fair share record.

        If the record doesn't exist but the project is connected to the resource group,
        returns default fair share data using the resource group's default configuration.

        Raises:
            ProjectNotConnectedToResourceGroupError: If the project is not connected
                to the specified resource group.
        """
        result = await self._repository.get_rg_scoped_project_fair_share(
            resource_group=action.resource_group,
            project_id=action.project_id,
        )

        if result is not None:
            return GetProjectFairShareActionResult(data=result)

        # Project is connected but has no fair share record - create default
        # We need domain_name for the default data
        domain_name = await self._repository.get_project_info(action.project_id)
        if domain_name is None:
            # This shouldn't happen if project is connected to resource group
            # but handle defensively
            domain_name = ""

        scaling_group_spec = await self._repository.get_scaling_group_fair_share_spec(
            action.resource_group
        )
        default_data = self._create_default_project_fair_share(
            resource_group=action.resource_group,
            project_id=action.project_id,
            domain_name=domain_name,
            scaling_group_spec=scaling_group_spec,
        )
        return GetProjectFairShareActionResult(data=default_data)

    async def search_project_fair_shares(
        self, action: SearchProjectFairSharesAction
    ) -> SearchProjectFairSharesActionResult:
        """Search project fair shares with pagination."""
        querier = BatchQuerier(
            pagination=action.pagination,
            conditions=action.conditions,
            orders=action.orders,
        )
        result = await self._repository.search_project_fair_shares(querier)
        return SearchProjectFairSharesActionResult(
            items=result.items,
            total_count=result.total_count,
        )

    async def search_rg_project_fair_shares(
        self,
        action: SearchRGProjectFairSharesAction,
    ) -> SearchRGProjectFairSharesActionResult:
        """Search project fair shares within a resource group scope.

        Returns all projects in the resource group, filling defaults for entities
        without fair share records.
        """
        # Call entity-based repository method
        entity_result = await self._repository.search_rg_scoped_project_fair_shares(
            action.scope, action.querier
        )

        # Fetch scaling group spec once for all defaults
        scaling_group_spec = await self._repository.get_scaling_group_fair_share_spec(
            action.scope.resource_group
        )

        # Transform EntityItem → FairShareData
        items: list[ProjectFairShareData] = []
        for entity_item in entity_result.items:
            if entity_item.details is not None:
                items.append(entity_item.details)
            else:
                default_data = self._create_default_project_fair_share(
                    resource_group=entity_item.resource_group,
                    project_id=entity_item.project_id,
                    domain_name=entity_item.domain_name,
                    scaling_group_spec=scaling_group_spec,
                )
                items.append(default_data)

        return SearchRGProjectFairSharesActionResult(
            items=items,
            total_count=entity_result.total_count,
        )

    # User Fair Share

    async def get_user_fair_share(
        self, action: GetUserFairShareAction
    ) -> GetUserFairShareActionResult:
        """Get a user fair share record.

        If the record doesn't exist but the user is connected to the resource group
        (via project membership), returns default fair share data using the resource
        group's default configuration.

        Raises:
            UserNotConnectedToResourceGroupError: If the user's project is not connected
                to the specified resource group.
        """
        result = await self._repository.get_rg_scoped_user_fair_share(
            resource_group=action.resource_group,
            project_id=action.project_id,
            user_uuid=action.user_uuid,
        )

        if result is not None:
            return GetUserFairShareActionResult(data=result)

        # User is connected but has no fair share record - create default
        # We need domain_name for the default data
        domain_name = await self._repository.get_user_project_info(
            action.project_id, action.user_uuid
        )
        if domain_name is None:
            # This shouldn't happen if user is connected to resource group
            # but handle defensively
            domain_name = ""

        scaling_group_spec = await self._repository.get_scaling_group_fair_share_spec(
            action.resource_group
        )
        default_data = self._create_default_user_fair_share(
            resource_group=action.resource_group,
            user_uuid=action.user_uuid,
            project_id=action.project_id,
            domain_name=domain_name,
            scaling_group_spec=scaling_group_spec,
        )
        return GetUserFairShareActionResult(data=default_data)

    async def search_user_fair_shares(
        self, action: SearchUserFairSharesAction
    ) -> SearchUserFairSharesActionResult:
        """Search user fair shares with pagination."""
        querier = BatchQuerier(
            pagination=action.pagination,
            conditions=action.conditions,
            orders=action.orders,
        )
        result = await self._repository.search_user_fair_shares(querier)
        return SearchUserFairSharesActionResult(
            items=result.items,
            total_count=result.total_count,
        )

    async def search_rg_user_fair_shares(
        self,
        action: SearchRGUserFairSharesAction,
    ) -> SearchRGUserFairSharesActionResult:
        """Search user fair shares within a resource group scope.

        Returns all users in the resource group, filling defaults for entities
        without fair share records.
        """
        # Call entity-based repository method
        entity_result = await self._repository.search_rg_scoped_user_fair_shares(
            action.scope, action.querier
        )

        # Fetch scaling group spec once for all defaults
        scaling_group_spec = await self._repository.get_scaling_group_fair_share_spec(
            action.scope.resource_group
        )

        # Transform EntityItem → FairShareData
        items: list[UserFairShareData] = []
        for entity_item in entity_result.items:
            if entity_item.details is not None:
                items.append(entity_item.details)
            else:
                default_data = self._create_default_user_fair_share(
                    resource_group=entity_item.resource_group,
                    user_uuid=entity_item.user_uuid,
                    project_id=entity_item.project_id,
                    domain_name=entity_item.domain_name,
                    scaling_group_spec=scaling_group_spec,
                )
                items.append(default_data)

        return SearchRGUserFairSharesActionResult(
            items=items,
            total_count=entity_result.total_count,
        )

    # Upsert Weight Operations

    async def upsert_domain_fair_share_weight(
        self, action: UpsertDomainFairShareWeightAction
    ) -> UpsertDomainFairShareWeightActionResult:
        """Upsert a domain fair share weight."""
        spec = DomainFairShareUpserterSpec(
            resource_group=action.resource_group,
            domain_name=action.domain_name,
            weight=TriState.from_graphql(action.weight),
        )
        upserter = Upserter(spec=spec)
        result = await self._repository.upsert_domain_fair_share(upserter)
        return UpsertDomainFairShareWeightActionResult(data=result)

    async def upsert_project_fair_share_weight(
        self, action: UpsertProjectFairShareWeightAction
    ) -> UpsertProjectFairShareWeightActionResult:
        """Upsert a project fair share weight."""
        spec = ProjectFairShareUpserterSpec(
            resource_group=action.resource_group,
            project_id=action.project_id,
            domain_name=action.domain_name,
            weight=TriState.from_graphql(action.weight),
        )
        upserter = Upserter(spec=spec)
        result = await self._repository.upsert_project_fair_share(upserter)
        return UpsertProjectFairShareWeightActionResult(data=result)

    async def upsert_user_fair_share_weight(
        self, action: UpsertUserFairShareWeightAction
    ) -> UpsertUserFairShareWeightActionResult:
        """Upsert a user fair share weight."""
        spec = UserFairShareUpserterSpec(
            resource_group=action.resource_group,
            user_uuid=action.user_uuid,
            project_id=action.project_id,
            domain_name=action.domain_name,
            weight=TriState.from_graphql(action.weight),
        )
        upserter = Upserter(spec=spec)
        result = await self._repository.upsert_user_fair_share(upserter)
        return UpsertUserFairShareWeightActionResult(data=result)

    # Bulk Upsert Weight Methods

    async def bulk_upsert_domain_fair_share_weight(
        self, action: BulkUpsertDomainFairShareWeightAction
    ) -> BulkUpsertDomainFairShareWeightActionResult:
        """Bulk upsert domain fair share weights."""
        if not action.inputs:
            return BulkUpsertDomainFairShareWeightActionResult(upserted_count=0)

        specs = [
            DomainFairShareBulkWeightUpserterSpec(
                resource_group=action.resource_group,
                domain_name=input_item.domain_name,
                weight=input_item.weight,
            )
            for input_item in action.inputs
        ]
        bulk_upserter = BulkUpserter(specs=specs)
        result = await self._repository.bulk_upsert_domain_fair_share(bulk_upserter)
        return BulkUpsertDomainFairShareWeightActionResult(upserted_count=result.upserted_count)

    async def bulk_upsert_project_fair_share_weight(
        self, action: BulkUpsertProjectFairShareWeightAction
    ) -> BulkUpsertProjectFairShareWeightActionResult:
        """Bulk upsert project fair share weights."""
        if not action.inputs:
            return BulkUpsertProjectFairShareWeightActionResult(upserted_count=0)

        specs = [
            ProjectFairShareBulkWeightUpserterSpec(
                resource_group=action.resource_group,
                project_id=input_item.project_id,
                domain_name=input_item.domain_name,
                weight=input_item.weight,
            )
            for input_item in action.inputs
        ]
        bulk_upserter = BulkUpserter(specs=specs)
        result = await self._repository.bulk_upsert_project_fair_share(bulk_upserter)
        return BulkUpsertProjectFairShareWeightActionResult(upserted_count=result.upserted_count)

    async def bulk_upsert_user_fair_share_weight(
        self, action: BulkUpsertUserFairShareWeightAction
    ) -> BulkUpsertUserFairShareWeightActionResult:
        """Bulk upsert user fair share weights."""
        if not action.inputs:
            return BulkUpsertUserFairShareWeightActionResult(upserted_count=0)

        specs = [
            UserFairShareBulkWeightUpserterSpec(
                resource_group=action.resource_group,
                user_uuid=input_item.user_uuid,
                project_id=input_item.project_id,
                domain_name=input_item.domain_name,
                weight=input_item.weight,
            )
            for input_item in action.inputs
        ]
        bulk_upserter = BulkUpserter(specs=specs)
        result = await self._repository.bulk_upsert_user_fair_share(bulk_upserter)
        return BulkUpsertUserFairShareWeightActionResult(upserted_count=result.upserted_count)
