from __future__ import annotations

import logging
from decimal import Decimal

from ai.backend.common.types import ResourceSlot
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.errors.fair_share import InvalidResourceWeightError
from ai.backend.manager.models.scaling_group import ScalingGroupRow
from ai.backend.manager.models.scaling_group.types import FairShareScalingGroupSpec
from ai.backend.manager.repositories.base import Updater
from ai.backend.manager.repositories.scaling_group import ScalingGroupRepository
from ai.backend.manager.repositories.scaling_group.updaters import (
    ResourceGroupFairShareUpdaterSpec,
    ScalingGroupUpdaterSpec,
)
from ai.backend.manager.services.scaling_group.actions.associate_with_domain import (
    AssociateScalingGroupWithDomainsAction,
    AssociateScalingGroupWithDomainsActionResult,
)
from ai.backend.manager.services.scaling_group.actions.associate_with_keypair import (
    AssociateScalingGroupWithKeypairsAction,
    AssociateScalingGroupWithKeypairsActionResult,
)
from ai.backend.manager.services.scaling_group.actions.associate_with_user_group import (
    AssociateScalingGroupWithUserGroupsAction,
    AssociateScalingGroupWithUserGroupsActionResult,
)
from ai.backend.manager.services.scaling_group.actions.create import (
    CreateScalingGroupAction,
    CreateScalingGroupActionResult,
)
from ai.backend.manager.services.scaling_group.actions.disassociate_with_domain import (
    DisassociateScalingGroupWithDomainsAction,
    DisassociateScalingGroupWithDomainsActionResult,
)
from ai.backend.manager.services.scaling_group.actions.disassociate_with_keypair import (
    DisassociateScalingGroupWithKeypairsAction,
    DisassociateScalingGroupWithKeypairsActionResult,
)
from ai.backend.manager.services.scaling_group.actions.disassociate_with_user_group import (
    DisassociateScalingGroupWithUserGroupsAction,
    DisassociateScalingGroupWithUserGroupsActionResult,
)
from ai.backend.manager.services.scaling_group.actions.get_resource_info import (
    GetResourceInfoAction,
    GetResourceInfoActionResult,
)
from ai.backend.manager.services.scaling_group.actions.list_scaling_groups import (
    SearchScalingGroupsAction,
    SearchScalingGroupsActionResult,
)
from ai.backend.manager.services.scaling_group.actions.modify import (
    ModifyScalingGroupAction,
    ModifyScalingGroupActionResult,
)
from ai.backend.manager.services.scaling_group.actions.purge_scaling_group import (
    PurgeScalingGroupAction,
    PurgeScalingGroupActionResult,
)
from ai.backend.manager.services.scaling_group.actions.update_fair_share_spec import (
    UpdateFairShareSpecAction,
    UpdateFairShareSpecActionResult,
)
from ai.backend.manager.types import TriState

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ScalingGroupService:
    _repository: ScalingGroupRepository

    def __init__(self, repository: ScalingGroupRepository) -> None:
        self._repository = repository

    async def search_scaling_groups(
        self, action: SearchScalingGroupsAction
    ) -> SearchScalingGroupsActionResult:
        """Searches scaling groups."""
        result = await self._repository.search_scaling_groups(
            querier=action.querier,
        )

        return SearchScalingGroupsActionResult(
            scaling_groups=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def create_scaling_group(
        self, action: CreateScalingGroupAction
    ) -> CreateScalingGroupActionResult:
        """Creates a scaling group."""
        scaling_group_data = await self._repository.create_scaling_group(action.creator)
        return CreateScalingGroupActionResult(scaling_group=scaling_group_data)

    async def purge_scaling_group(
        self, action: PurgeScalingGroupAction
    ) -> PurgeScalingGroupActionResult:
        """Purges a scaling group and all related sessions and routes."""
        data = await self._repository.purge_scaling_group(action.purger)
        return PurgeScalingGroupActionResult(data=data)

    async def modify_scaling_group(
        self, action: ModifyScalingGroupAction
    ) -> ModifyScalingGroupActionResult:
        """Modifies a scaling group."""
        scaling_group_data = await self._repository.update_scaling_group(action.updater)
        return ModifyScalingGroupActionResult(scaling_group=scaling_group_data)

    async def associate_scaling_group_with_domains(
        self, action: AssociateScalingGroupWithDomainsAction
    ) -> AssociateScalingGroupWithDomainsActionResult:
        """Associates a scaling group with multiple domains."""
        await self._repository.associate_scaling_group_with_domains(action.bulk_creator)
        return AssociateScalingGroupWithDomainsActionResult()

    async def disassociate_scaling_group_with_domains(
        self, action: DisassociateScalingGroupWithDomainsAction
    ) -> DisassociateScalingGroupWithDomainsActionResult:
        """Disassociates a scaling group from multiple domains."""
        await self._repository.disassociate_scaling_group_with_domains(action.purger)
        return DisassociateScalingGroupWithDomainsActionResult()

    async def associate_scaling_group_with_keypairs(
        self, action: AssociateScalingGroupWithKeypairsAction
    ) -> AssociateScalingGroupWithKeypairsActionResult:
        """Associates a scaling group with multiple keypairs."""
        await self._repository.associate_scaling_group_with_keypairs(action.bulk_creator)
        return AssociateScalingGroupWithKeypairsActionResult()

    async def disassociate_scaling_group_with_keypairs(
        self, action: DisassociateScalingGroupWithKeypairsAction
    ) -> DisassociateScalingGroupWithKeypairsActionResult:
        """Disassociates a scaling group from multiple keypairs."""
        await self._repository.disassociate_scaling_group_with_keypairs(action.purger)
        return DisassociateScalingGroupWithKeypairsActionResult()

    async def associate_scaling_group_with_user_groups(
        self, action: AssociateScalingGroupWithUserGroupsAction
    ) -> AssociateScalingGroupWithUserGroupsActionResult:
        """Associates a scaling group with multiple user groups (projects)."""
        await self._repository.associate_scaling_group_with_user_groups(action.bulk_creator)
        return AssociateScalingGroupWithUserGroupsActionResult()

    async def disassociate_scaling_group_with_user_groups(
        self, action: DisassociateScalingGroupWithUserGroupsAction
    ) -> DisassociateScalingGroupWithUserGroupsActionResult:
        """Disassociates a single scaling group from a user group (project)."""
        await self._repository.disassociate_scaling_group_with_user_groups(action.purger)
        return DisassociateScalingGroupWithUserGroupsActionResult()

    async def get_resource_info(self, action: GetResourceInfoAction) -> GetResourceInfoActionResult:
        """Get aggregated resource information for a scaling group.

        Raises:
            ScalingGroupNotFound: If the scaling group does not exist.
        """
        resource_info = await self._repository.get_resource_info(action.scaling_group)
        return GetResourceInfoActionResult(resource_info=resource_info)

    async def update_fair_share_spec(
        self, action: UpdateFairShareSpecAction
    ) -> UpdateFairShareSpecActionResult:
        """Update fair share spec for a scaling group.

        Supports partial updates with resource weight validation and filtering.

        Validation: Input resource_weights must contain only resource types
        that exist in the scaling group's capacity.

        Filtering: After merging, resource_weights are filtered to only include
        types that exist in capacity (to remove stale resource types).

        Raises:
            ScalingGroupNotFound: If the scaling group does not exist.
            InvalidResourceWeightError: If input contains invalid resource types.
        """
        # 1. Get existing scaling group (raises ScalingGroupNotFound if not found)
        existing_sg = await self._repository.get_scaling_group_by_name(action.resource_group)
        existing_spec = existing_sg.fair_share_spec or FairShareScalingGroupSpec()

        # 2. Get ResourceInfo for capacity
        resource_info = await self._repository.get_resource_info(action.resource_group)
        capacity_keys = set(resource_info.capacity.data.keys())

        # 3. Validate: input resource_weights with non-None weight must exist in capacity
        if action.resource_weights:
            # Only validate types that are being set (not deleted)
            input_types = {
                rw.resource_type for rw in action.resource_weights if rw.weight is not None
            }
            invalid_types = input_types - capacity_keys
            if invalid_types:
                raise InvalidResourceWeightError(sorted(invalid_types))

        # 4. Merge: partial input with existing fair_share_spec
        merged_resource_weights = dict(existing_spec.resource_weights.data)
        if action.resource_weights:
            for rw in action.resource_weights:
                if rw.weight is None:
                    # None means delete
                    merged_resource_weights.pop(rw.resource_type, None)
                else:
                    merged_resource_weights[rw.resource_type] = rw.weight

        # 5. Filter: keep only resource types in capacity
        filtered_resource_weights = {
            k: v for k, v in merged_resource_weights.items() if k in capacity_keys
        }

        # 6. Build new spec with merged values
        new_spec = FairShareScalingGroupSpec(
            half_life_days=action.half_life_days
            if action.half_life_days is not None
            else existing_spec.half_life_days,
            lookback_days=action.lookback_days
            if action.lookback_days is not None
            else existing_spec.lookback_days,
            decay_unit_days=action.decay_unit_days
            if action.decay_unit_days is not None
            else existing_spec.decay_unit_days,
            default_weight=action.default_weight
            if action.default_weight is not None
            else existing_spec.default_weight,
            resource_weights=ResourceSlot({
                k: Decimal(str(v)) for k, v in filtered_resource_weights.items()
            }),
        )

        # 7. Save via repository
        fair_share_updater = ResourceGroupFairShareUpdaterSpec(
            fair_share_spec=TriState.update(new_spec),
        )
        updater = Updater[ScalingGroupRow](
            pk_value=action.resource_group,
            spec=ScalingGroupUpdaterSpec(fair_share=fair_share_updater),
        )
        result = await self._repository.update_scaling_group(updater)

        return UpdateFairShareSpecActionResult(scaling_group=result)
