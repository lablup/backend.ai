import logging

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.scaling_group import ScalingGroupRepository
from ai.backend.manager.services.scaling_group.actions.create import (
    CreateScalingGroupAction,
    CreateScalingGroupActionResult,
)
from ai.backend.manager.services.scaling_group.actions.list_scaling_groups import (
    SearchScalingGroupsAction,
    SearchScalingGroupsActionResult,
)
from ai.backend.manager.services.scaling_group.actions.purge_scaling_group import (
    PurgeScalingGroupAction,
    PurgeScalingGroupActionResult,
)

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
