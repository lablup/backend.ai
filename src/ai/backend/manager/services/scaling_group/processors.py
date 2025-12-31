from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.scaling_group.actions.associate_with_domain import (
    AssociateScalingGroupWithDomainAction,
    AssociateScalingGroupWithDomainActionResult,
)
from ai.backend.manager.services.scaling_group.actions.create import (
    CreateScalingGroupAction,
    CreateScalingGroupActionResult,
)
from ai.backend.manager.services.scaling_group.actions.disassociate_with_domain import (
    DisassociateScalingGroupWithDomainAction,
    DisassociateScalingGroupWithDomainActionResult,
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
from ai.backend.manager.services.scaling_group.service import ScalingGroupService


class ScalingGroupProcessors(AbstractProcessorPackage):
    create_scaling_group: ActionProcessor[CreateScalingGroupAction, CreateScalingGroupActionResult]
    purge_scaling_group: ActionProcessor[PurgeScalingGroupAction, PurgeScalingGroupActionResult]
    modify_scaling_group: ActionProcessor[ModifyScalingGroupAction, ModifyScalingGroupActionResult]
    search_scaling_groups: ActionProcessor[
        SearchScalingGroupsAction, SearchScalingGroupsActionResult
    ]
    associate_scaling_group_with_domain: ActionProcessor[
        AssociateScalingGroupWithDomainAction, AssociateScalingGroupWithDomainActionResult
    ]
    disassociate_scaling_group_with_domain: ActionProcessor[
        DisassociateScalingGroupWithDomainAction, DisassociateScalingGroupWithDomainActionResult
    ]

    def __init__(self, service: ScalingGroupService, action_monitors: list[ActionMonitor]) -> None:
        self.create_scaling_group = ActionProcessor(service.create_scaling_group, action_monitors)
        self.purge_scaling_group = ActionProcessor(service.purge_scaling_group, action_monitors)
        self.modify_scaling_group = ActionProcessor(service.modify_scaling_group, action_monitors)
        self.search_scaling_groups = ActionProcessor(service.search_scaling_groups, action_monitors)
        self.associate_scaling_group_with_domain = ActionProcessor(
            service.associate_scaling_group_with_domain, action_monitors
        )
        self.disassociate_scaling_group_with_domain = ActionProcessor(
            service.disassociate_scaling_group_with_domain, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateScalingGroupAction.spec(),
            PurgeScalingGroupAction.spec(),
            ModifyScalingGroupAction.spec(),
            SearchScalingGroupsAction.spec(),
            AssociateScalingGroupWithDomainAction.spec(),
            DisassociateScalingGroupWithDomainAction.spec(),
        ]
