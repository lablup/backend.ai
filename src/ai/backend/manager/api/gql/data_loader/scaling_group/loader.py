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


async def load_scaling_groups_by_names(
    processor: ScalingGroupProcessors,
    scaling_group_names: Sequence[str],
) -> list[Optional[ScalingGroupData]]:
    """Batch load scaling groups by their names.

    Args:
        processor: The scaling group processor.
        scaling_group_names: Sequence of scaling group names to load.

    Returns:
        List of ScalingGroupData (or None if not found) in the same order as scaling_group_names.
    """
    if not scaling_group_names:
        return []

    querier = BatchQuerier(
        pagination=OffsetPagination(limit=len(scaling_group_names)),
        conditions=[ScalingGroupConditions.by_names(scaling_group_names)],
    )

    action_result = await processor.search_scaling_groups.wait_for_complete(
        SearchScalingGroupsAction(querier=querier)
    )

    scaling_group_map = {sg.name: sg for sg in action_result.scaling_groups}
    return [scaling_group_map.get(name) for name in scaling_group_names]
