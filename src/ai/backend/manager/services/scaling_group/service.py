import logging

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.services.scaling_group.actions.list_scaling_groups import (
    SearchScalingGroupsAction,
    SearchScalingGroupsActionResult,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ScalingGroupService:
    def __init__(self) -> None:
        pass

    async def search_scaling_groups(
        self, action: SearchScalingGroupsAction
    ) -> SearchScalingGroupsActionResult:
        raise NotImplementedError("search_scaling_groups is not yet implemented")
