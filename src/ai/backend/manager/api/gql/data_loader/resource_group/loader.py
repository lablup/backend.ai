from __future__ import annotations

from collections.abc import Sequence
from typing import Optional

from ai.backend.manager.data.scaling_group.types import ScalingGroupData
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.scaling_group.options import ScalingGroupConditions
from ai.backend.manager.services.scaling_group.actions.list_scaling_groups import (
    SearchScalingGroupsAction,
)
from ai.backend.manager.services.scaling_group.processors import ScalingGroupProcessors


async def load_resource_groups_by_names(
    processor: ScalingGroupProcessors,
    resource_group_names: Sequence[str],
) -> list[Optional[ScalingGroupData]]:
    """Batch load resource groups by their names.

    Args:
        processor: The scaling group processor.
        resource_group_names: Sequence of resource group names to load.

    Returns:
        List of ScalingGroupData (or None if not found) in the same order as resource_group_names.
    """
    if not resource_group_names:
        return []

    querier = BatchQuerier(
        pagination=OffsetPagination(limit=len(resource_group_names)),
        conditions=[ScalingGroupConditions.by_names(resource_group_names)],
    )

    action_result = await processor.search_scaling_groups.wait_for_complete(
        SearchScalingGroupsAction(querier=querier)
    )

    resource_group_map = {sg.name: sg for sg in action_result.scaling_groups}
    return [resource_group_map.get(name) for name in resource_group_names]
