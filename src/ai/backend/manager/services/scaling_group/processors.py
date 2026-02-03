from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
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
from ai.backend.manager.services.scaling_group.service import ScalingGroupService


class ScalingGroupProcessors(AbstractProcessorPackage):
    create_scaling_group: ActionProcessor[CreateScalingGroupAction, CreateScalingGroupActionResult]
    purge_scaling_group: ActionProcessor[PurgeScalingGroupAction, PurgeScalingGroupActionResult]
    modify_scaling_group: ActionProcessor[ModifyScalingGroupAction, ModifyScalingGroupActionResult]
    search_scaling_groups: ActionProcessor[
        SearchScalingGroupsAction, SearchScalingGroupsActionResult
    ]
    get_resource_info: ActionProcessor[GetResourceInfoAction, GetResourceInfoActionResult]
    update_fair_share_spec: ActionProcessor[
        UpdateFairShareSpecAction, UpdateFairShareSpecActionResult
    ]
    associate_scaling_group_with_domains: ActionProcessor[
        AssociateScalingGroupWithDomainsAction, AssociateScalingGroupWithDomainsActionResult
    ]
    disassociate_scaling_group_with_domains: ActionProcessor[
        DisassociateScalingGroupWithDomainsAction, DisassociateScalingGroupWithDomainsActionResult
    ]
    associate_scaling_group_with_keypairs: ActionProcessor[
        AssociateScalingGroupWithKeypairsAction, AssociateScalingGroupWithKeypairsActionResult
    ]
    disassociate_scaling_group_with_keypairs: ActionProcessor[
        DisassociateScalingGroupWithKeypairsAction, DisassociateScalingGroupWithKeypairsActionResult
    ]
    associate_scaling_group_with_user_groups: ActionProcessor[
        AssociateScalingGroupWithUserGroupsAction, AssociateScalingGroupWithUserGroupsActionResult
    ]
    disassociate_scaling_group_with_user_groups: ActionProcessor[
        DisassociateScalingGroupWithUserGroupsAction,
        DisassociateScalingGroupWithUserGroupsActionResult,
    ]

    def __init__(self, service: ScalingGroupService, action_monitors: list[ActionMonitor]) -> None:
        self.create_scaling_group = ActionProcessor(service.create_scaling_group, action_monitors)
        self.purge_scaling_group = ActionProcessor(service.purge_scaling_group, action_monitors)
        self.modify_scaling_group = ActionProcessor(service.modify_scaling_group, action_monitors)
        self.search_scaling_groups = ActionProcessor(service.search_scaling_groups, action_monitors)
        self.get_resource_info = ActionProcessor(service.get_resource_info, action_monitors)
        self.update_fair_share_spec = ActionProcessor(
            service.update_fair_share_spec, action_monitors
        )
        self.associate_scaling_group_with_domains = ActionProcessor(
            service.associate_scaling_group_with_domains, action_monitors
        )
        self.disassociate_scaling_group_with_domains = ActionProcessor(
            service.disassociate_scaling_group_with_domains, action_monitors
        )
        self.associate_scaling_group_with_keypairs = ActionProcessor(
            service.associate_scaling_group_with_keypairs, action_monitors
        )
        self.disassociate_scaling_group_with_keypairs = ActionProcessor(
            service.disassociate_scaling_group_with_keypairs, action_monitors
        )
        self.associate_scaling_group_with_user_groups = ActionProcessor(
            service.associate_scaling_group_with_user_groups, action_monitors
        )
        self.disassociate_scaling_group_with_user_groups = ActionProcessor(
            service.disassociate_scaling_group_with_user_groups, action_monitors
        )

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateScalingGroupAction.spec(),
            PurgeScalingGroupAction.spec(),
            ModifyScalingGroupAction.spec(),
            SearchScalingGroupsAction.spec(),
            GetResourceInfoAction.spec(),
            UpdateFairShareSpecAction.spec(),
            AssociateScalingGroupWithDomainsAction.spec(),
            DisassociateScalingGroupWithDomainsAction.spec(),
            AssociateScalingGroupWithKeypairsAction.spec(),
            DisassociateScalingGroupWithKeypairsAction.spec(),
            AssociateScalingGroupWithUserGroupsAction.spec(),
            DisassociateScalingGroupWithUserGroupsAction.spec(),
        ]
