import logging

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.repositories.scaling_group import ScalingGroupRepository
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
