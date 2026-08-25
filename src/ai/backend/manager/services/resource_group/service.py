from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

from ai.backend.common.types import ResourceSlot
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.data.resource_group.types import FairShareResourceGroupSpec
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.errors.fair_share import InvalidResourceWeightError
from ai.backend.manager.models.resource_group.updaters import ResourceGroupUpdater
from ai.backend.manager.repositories.resource_group import ResourceGroupRepository

if TYPE_CHECKING:
    from ai.backend.manager.clients.appproxy.client import AppProxyClientPool
from ai.backend.manager.services.resource_group.actions.associate_with_domain import (
    AssociateResourceGroupWithDomainsAction,
    AssociateResourceGroupWithDomainsActionResult,
)
from ai.backend.manager.services.resource_group.actions.associate_with_keypair import (
    AssociateResourceGroupWithKeypairsAction,
    AssociateResourceGroupWithKeypairsActionResult,
)
from ai.backend.manager.services.resource_group.actions.associate_with_user_group import (
    AssociateResourceGroupWithUserGroupsAction,
    AssociateResourceGroupWithUserGroupsActionResult,
)
from ai.backend.manager.services.resource_group.actions.create import (
    CreateResourceGroupAction,
    CreateResourceGroupActionResult,
)
from ai.backend.manager.services.resource_group.actions.disassociate_with_domain import (
    DisassociateResourceGroupWithDomainsAction,
    DisassociateResourceGroupWithDomainsActionResult,
)
from ai.backend.manager.services.resource_group.actions.disassociate_with_keypair import (
    DisassociateResourceGroupWithKeypairsAction,
    DisassociateResourceGroupWithKeypairsActionResult,
)
from ai.backend.manager.services.resource_group.actions.disassociate_with_user_group import (
    DisassociateResourceGroupWithUserGroupsAction,
    DisassociateResourceGroupWithUserGroupsActionResult,
)
from ai.backend.manager.services.resource_group.actions.get_allowed_domains_for_rg import (
    GetAllowedDomainsForResourceGroupAction,
    GetAllowedDomainsForResourceGroupActionResult,
)
from ai.backend.manager.services.resource_group.actions.get_allowed_projects_for_rg import (
    GetAllowedProjectsForResourceGroupAction,
    GetAllowedProjectsForResourceGroupActionResult,
)
from ai.backend.manager.services.resource_group.actions.get_resource_info import (
    GetResourceInfoAction,
    GetResourceInfoActionResult,
)
from ai.backend.manager.services.resource_group.actions.get_wsproxy_version import (
    GetWsproxyVersionAction,
    GetWsproxyVersionActionResult,
)
from ai.backend.manager.services.resource_group.actions.list_resource_groups import (
    SearchResourceGroupsAction,
    SearchResourceGroupsActionResult,
)
from ai.backend.manager.services.resource_group.actions.purge_resource_group import (
    PurgeResourceGroupAction,
    PurgeResourceGroupActionResult,
)
from ai.backend.manager.services.resource_group.actions.replace_default_deployment_options import (
    ReplaceDefaultDeploymentOptionsAction,
    ReplaceDefaultDeploymentOptionsActionResult,
)
from ai.backend.manager.services.resource_group.actions.replace_default_session_options import (
    ReplaceDefaultSessionOptionsAction,
    ReplaceDefaultSessionOptionsActionResult,
)
from ai.backend.manager.services.resource_group.actions.resolve_resource_group_ids_by_names import (
    ResolveResourceGroupIDsByNamesAction,
    ResolveResourceGroupIDsByNamesActionResult,
)
from ai.backend.manager.services.resource_group.actions.update import (
    UpdateResourceGroupAction,
    UpdateResourceGroupActionResult,
)
from ai.backend.manager.services.resource_group.actions.update_allowed_domains_for_rg import (
    UpdateAllowedDomainsForResourceGroupAction,
    UpdateAllowedDomainsForResourceGroupActionResult,
)
from ai.backend.manager.services.resource_group.actions.update_allowed_projects_for_rg import (
    UpdateAllowedProjectsForResourceGroupAction,
    UpdateAllowedProjectsForResourceGroupActionResult,
)
from ai.backend.manager.services.resource_group.actions.update_allowed_rgs_for_domain import (
    UpdateAllowedResourceGroupsForDomainAction,
    UpdateAllowedResourceGroupsForDomainActionResult,
)
from ai.backend.manager.services.resource_group.actions.update_allowed_rgs_for_project import (
    UpdateAllowedResourceGroupsForProjectAction,
    UpdateAllowedResourceGroupsForProjectActionResult,
)
from ai.backend.manager.services.resource_group.actions.update_fair_share_spec import (
    UpdateFairShareSpecAction,
    UpdateFairShareSpecActionResult,
)
from ai.backend.manager.types import TriState

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

WSPROXY_V1_VERSION = "v1"


class ResourceGroupService:
    _repository: ResourceGroupRepository
    _appproxy_client_pool: AppProxyClientPool | None

    def __init__(
        self,
        repository: ResourceGroupRepository,
        appproxy_client_pool: AppProxyClientPool | None = None,
    ) -> None:
        self._repository = repository
        self._appproxy_client_pool = appproxy_client_pool

    async def get_wsproxy_version(
        self, action: GetWsproxyVersionAction
    ) -> GetWsproxyVersionActionResult:
        """Get wsproxy version for a specific resource group."""
        if self._appproxy_client_pool is None:
            raise ObjectNotFound(object_name="AppProxy client pool")
        sgroups = await self._repository.list_allowed_sgroups(
            domain_name=action.domain_name,
            group=action.group,
            access_key=action.access_key,
        )
        sgroup_filtered = [sg for sg in sgroups if sg.name == action.resource_group_name]
        if not sgroup_filtered:
            raise ObjectNotFound(object_name="scaling group")
        sgroup = sgroup_filtered[0]

        if not sgroup.network.wsproxy_addr:
            return GetWsproxyVersionActionResult(wsproxy_version=WSPROXY_V1_VERSION)
        client = self._appproxy_client_pool.load_client(
            sgroup.network.wsproxy_addr, sgroup.network.wsproxy_api_token or ""
        )
        status = await client.fetch_status()
        return GetWsproxyVersionActionResult(wsproxy_version=status.api_version)

    async def resolve_resource_group_ids_by_names(
        self, action: ResolveResourceGroupIDsByNamesAction
    ) -> ResolveResourceGroupIDsByNamesActionResult:
        ids_by_name = await self._repository.get_resource_group_ids_by_names(action.names)
        return ResolveResourceGroupIDsByNamesActionResult(ids_by_name=ids_by_name)

    async def search_resource_groups(
        self, action: SearchResourceGroupsAction
    ) -> SearchResourceGroupsActionResult:
        """Searches resource groups."""
        result = await self._repository.search_resource_groups(
            querier=action.querier,
        )

        return SearchResourceGroupsActionResult(
            resource_groups=result.items,
            total_count=result.total_count,
            has_next_page=result.has_next_page,
            has_previous_page=result.has_previous_page,
        )

    async def create_resource_group(
        self, action: CreateResourceGroupAction
    ) -> CreateResourceGroupActionResult:
        """Creates a resource group."""
        resource_group_data = await self._repository.create_resource_group(action.creator)
        return CreateResourceGroupActionResult(resource_group=resource_group_data)

    async def purge_resource_group(
        self, action: PurgeResourceGroupAction
    ) -> PurgeResourceGroupActionResult:
        """Purges a resource group and all related sessions and routes."""
        data = await self._repository.purge_resource_group(action.resource_group_id)
        return PurgeResourceGroupActionResult(data=data)

    async def update_resource_group(
        self, action: UpdateResourceGroupAction
    ) -> UpdateResourceGroupActionResult:
        """Modifies a resource group."""
        resource_group_data = await self._repository.update_resource_group(action.updater)
        return UpdateResourceGroupActionResult(resource_group=resource_group_data)

    async def replace_default_deployment_options(
        self, action: ReplaceDefaultDeploymentOptionsAction
    ) -> ReplaceDefaultDeploymentOptionsActionResult:
        """Fully replace a resource group's ``default_deployment_options``.

        Admin-only. The new default applies to deployments created after
        this call; existing deployments snapshot-copy the old default.
        The repository returns the persisted :class:`DeploymentOptions`
        via ``UPDATE ... RETURNING`` so this path does a single round-trip
        and does not re-materialise the surrounding resource group node.
        """
        options = await self._repository.replace_default_deployment_options(
            action.resource_group, action.options
        )
        return ReplaceDefaultDeploymentOptionsActionResult(
            resource_group=action.resource_group,
            options=options,
        )

    async def replace_default_session_options(
        self, action: ReplaceDefaultSessionOptionsAction
    ) -> ReplaceDefaultSessionOptionsActionResult:
        """Fully replace a resource group's ``default_session_options``.

        Admin-only. The new default is consulted at session enqueue
        time by the scheduling controller's options resolver; already-
        enqueued sessions keep the values frozen onto them earlier.
        """
        options = await self._repository.replace_default_session_options(
            action.resource_group, action.options
        )
        return ReplaceDefaultSessionOptionsActionResult(
            resource_group=action.resource_group,
            options=options,
        )

    async def associate_resource_group_with_domains(
        self, action: AssociateResourceGroupWithDomainsAction
    ) -> AssociateResourceGroupWithDomainsActionResult:
        """Associates a resource group with multiple domains."""
        await self._repository.associate_resource_group_with_domains(action.binder)
        return AssociateResourceGroupWithDomainsActionResult()

    async def disassociate_resource_group_with_domains(
        self, action: DisassociateResourceGroupWithDomainsAction
    ) -> DisassociateResourceGroupWithDomainsActionResult:
        """Disassociates a resource group from multiple domains."""
        await self._repository.disassociate_resource_group_with_domains(action.unbinder)
        return DisassociateResourceGroupWithDomainsActionResult()

    async def associate_resource_group_with_keypairs(
        self, action: AssociateResourceGroupWithKeypairsAction
    ) -> AssociateResourceGroupWithKeypairsActionResult:
        """Associates a resource group with multiple keypairs."""
        await self._repository.associate_resource_group_with_keypairs(action.bulk_creator)
        return AssociateResourceGroupWithKeypairsActionResult()

    async def disassociate_resource_group_with_keypairs(
        self, action: DisassociateResourceGroupWithKeypairsAction
    ) -> DisassociateResourceGroupWithKeypairsActionResult:
        """Disassociates a resource group from multiple keypairs."""
        await self._repository.disassociate_resource_group_with_keypairs(action.purger)
        return DisassociateResourceGroupWithKeypairsActionResult()

    async def associate_resource_group_with_user_groups(
        self, action: AssociateResourceGroupWithUserGroupsAction
    ) -> AssociateResourceGroupWithUserGroupsActionResult:
        """Associates a resource group with multiple user groups (projects)."""
        await self._repository.associate_resource_group_with_user_groups(action.binder)
        return AssociateResourceGroupWithUserGroupsActionResult()

    async def disassociate_resource_group_with_user_groups(
        self, action: DisassociateResourceGroupWithUserGroupsAction
    ) -> DisassociateResourceGroupWithUserGroupsActionResult:
        """Disassociates a single resource group from a user group (project)."""
        await self._repository.disassociate_resource_group_with_user_groups(action.unbinder)
        return DisassociateResourceGroupWithUserGroupsActionResult()

    async def get_resource_info(self, action: GetResourceInfoAction) -> GetResourceInfoActionResult:
        """Get aggregated resource information for a resource group.

        Raises:
            ScalingGroupNotFound: If the resource group does not exist.
        """
        resource_info = await self._repository.get_resource_info(action.resource_group)
        return GetResourceInfoActionResult(resource_info=resource_info)

    async def update_fair_share_spec(
        self, action: UpdateFairShareSpecAction
    ) -> UpdateFairShareSpecActionResult:
        """Update fair share spec for a resource group.

        Supports partial updates with resource weight validation and filtering.

        Validation: Input resource_weights must contain only resource types
        that exist in the resource group's capacity.

        Filtering: After merging, resource_weights are filtered to only include
        types that exist in capacity (to remove stale resource types).

        Raises:
            ScalingGroupNotFound: If the resource group does not exist.
            InvalidResourceWeightError: If input contains invalid resource types.
        """
        # 1. Get existing resource group (raises ResourceGroupNotFound if not found)
        existing_sg = await self._repository.get_resource_group_by_name(action.resource_group)
        existing_spec = existing_sg.fair_share_spec

        # 2. Get ResourceInfo for capacity
        resource_info = await self._repository.get_resource_info(action.resource_group)
        capacity_keys = {sq.slot_name for sq in resource_info.capacity}

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
        new_spec = FairShareResourceGroupSpec(
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
        result = await self._repository.update_resource_group(
            ResourceGroupUpdater(
                resource_group_id=action.resource_group_id,
                fair_share_spec=TriState.update(new_spec),
            )
        )

        return UpdateFairShareSpecActionResult(resource_group=result)

    # Allow / Disallow operations

    async def update_allowed_resource_groups_for_domain(
        self,
        action: UpdateAllowedResourceGroupsForDomainAction,
    ) -> UpdateAllowedResourceGroupsForDomainActionResult:
        """Atomically add/remove allowed resource groups for a domain."""
        items = await self._repository.update_allowed_resource_groups_for_domain(
            domain_name=action.domain_name,
            add=action.add,
            remove=action.remove,
        )
        return UpdateAllowedResourceGroupsForDomainActionResult(allowed_resource_groups=items)

    async def update_allowed_resource_groups_for_project(
        self,
        action: UpdateAllowedResourceGroupsForProjectAction,
    ) -> UpdateAllowedResourceGroupsForProjectActionResult:
        """Atomically add/remove allowed resource groups for a project."""
        items = await self._repository.update_allowed_resource_groups_for_project(
            project_id=action.project_id,
            add=action.add,
            remove=action.remove,
        )
        return UpdateAllowedResourceGroupsForProjectActionResult(allowed_resource_groups=items)

    async def update_allowed_domains_for_resource_group(
        self,
        action: UpdateAllowedDomainsForResourceGroupAction,
    ) -> UpdateAllowedDomainsForResourceGroupActionResult:
        """Atomically add/remove allowed domains for a resource group."""
        items = await self._repository.update_allowed_domains_for_resource_group(
            resource_group_id=action.resource_group_id,
            add=action.add,
            remove=action.remove,
        )
        return UpdateAllowedDomainsForResourceGroupActionResult(allowed_domains=items)

    async def update_allowed_projects_for_resource_group(
        self,
        action: UpdateAllowedProjectsForResourceGroupAction,
    ) -> UpdateAllowedProjectsForResourceGroupActionResult:
        """Atomically add/remove allowed projects for a resource group."""
        items = await self._repository.update_allowed_projects_for_resource_group(
            resource_group_id=action.resource_group_id,
            add=action.add,
            remove=action.remove,
        )
        return UpdateAllowedProjectsForResourceGroupActionResult(allowed_projects=items)

    async def get_allowed_domains_for_resource_group(
        self,
        action: GetAllowedDomainsForResourceGroupAction,
    ) -> GetAllowedDomainsForResourceGroupActionResult:
        """Get allowed domains for a resource group."""
        items = await self._repository.get_allowed_domains_for_resource_group(
            action.resource_group_id,
        )
        return GetAllowedDomainsForResourceGroupActionResult(items=items)

    async def get_allowed_projects_for_resource_group(
        self,
        action: GetAllowedProjectsForResourceGroupAction,
    ) -> GetAllowedProjectsForResourceGroupActionResult:
        """Get allowed projects for a resource group."""
        items = await self._repository.get_allowed_projects_for_resource_group(
            action.resource_group_id,
        )
        return GetAllowedProjectsForResourceGroupActionResult(items=items)
