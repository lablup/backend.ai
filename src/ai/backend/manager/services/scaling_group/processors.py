from ai.backend.manager.actions.registry import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import (
    GlobalActionProcessor,
    PublicActionProcessor,
)
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.ops.result import LookupOpsResult
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.scaling_group.types import ScalingGroupData
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
from ai.backend.manager.services.scaling_group.actions.get_allowed_domains_for_rg import (
    GetAllowedDomainsForResourceGroupAction,
    GetAllowedDomainsForResourceGroupActionResult,
)
from ai.backend.manager.services.scaling_group.actions.get_allowed_projects_for_rg import (
    GetAllowedProjectsForResourceGroupAction,
    GetAllowedProjectsForResourceGroupActionResult,
)
from ai.backend.manager.services.scaling_group.actions.get_allowed_rgs_for_domain import (
    GetAllowedResourceGroupsForDomainAction,
    GetAllowedResourceGroupsForDomainActionResult,
)
from ai.backend.manager.services.scaling_group.actions.get_allowed_rgs_for_project import (
    GetAllowedResourceGroupsForProjectAction,
    GetAllowedResourceGroupsForProjectActionResult,
)
from ai.backend.manager.services.scaling_group.actions.get_resource_info import (
    GetResourceInfoAction,
    GetResourceInfoActionResult,
)
from ai.backend.manager.services.scaling_group.actions.get_wsproxy_version import (
    GetWsproxyVersionAction,
    GetWsproxyVersionActionResult,
)
from ai.backend.manager.services.scaling_group.actions.list_allowed import (
    ListAllowedScalingGroupsAction,
    ListAllowedScalingGroupsActionResult,
)
from ai.backend.manager.services.scaling_group.actions.list_scaling_groups import (
    SearchScalingGroupsAction,
    SearchScalingGroupsActionResult,
)
from ai.backend.manager.services.scaling_group.actions.lookup import LookupResourceGroupAction
from ai.backend.manager.services.scaling_group.actions.purge_scaling_group import (
    PurgeScalingGroupAction,
    PurgeScalingGroupActionResult,
)
from ai.backend.manager.services.scaling_group.actions.replace_default_deployment_options import (
    ReplaceDefaultDeploymentOptionsAction,
    ReplaceDefaultDeploymentOptionsActionResult,
)
from ai.backend.manager.services.scaling_group.actions.replace_default_session_options import (
    ReplaceDefaultSessionOptionsAction,
    ReplaceDefaultSessionOptionsActionResult,
)
from ai.backend.manager.services.scaling_group.actions.resolve_resource_group_ids_by_names import (
    ResolveResourceGroupIDsByNamesAction,
    ResolveResourceGroupIDsByNamesActionResult,
)
from ai.backend.manager.services.scaling_group.actions.update import (
    UpdateScalingGroupAction,
    UpdateScalingGroupActionResult,
)
from ai.backend.manager.services.scaling_group.actions.update_allowed_domains_for_rg import (
    UpdateAllowedDomainsForResourceGroupAction,
    UpdateAllowedDomainsForResourceGroupActionResult,
)
from ai.backend.manager.services.scaling_group.actions.update_allowed_projects_for_rg import (
    UpdateAllowedProjectsForResourceGroupAction,
    UpdateAllowedProjectsForResourceGroupActionResult,
)
from ai.backend.manager.services.scaling_group.actions.update_allowed_rgs_for_domain import (
    UpdateAllowedResourceGroupsForDomainAction,
    UpdateAllowedResourceGroupsForDomainActionResult,
)
from ai.backend.manager.services.scaling_group.actions.update_allowed_rgs_for_project import (
    UpdateAllowedResourceGroupsForProjectAction,
    UpdateAllowedResourceGroupsForProjectActionResult,
)
from ai.backend.manager.services.scaling_group.actions.update_fair_share_spec import (
    UpdateFairShareSpecAction,
    UpdateFairShareSpecActionResult,
)
from ai.backend.manager.services.scaling_group.service import ScalingGroupService


class ScalingGroupProcessors:
    lookup: LookupActionProcessor[LookupResourceGroupAction, LookupOpsResult[ScalingGroupData]]
    create_scaling_group: GlobalActionProcessor[
        CreateScalingGroupAction, CreateScalingGroupActionResult
    ]
    purge_scaling_group: SingleEntityActionProcessor[
        PurgeScalingGroupAction, PurgeScalingGroupActionResult
    ]
    update_scaling_group: SingleEntityActionProcessor[
        UpdateScalingGroupAction, UpdateScalingGroupActionResult
    ]
    search_scaling_groups: GlobalActionProcessor[
        SearchScalingGroupsAction, SearchScalingGroupsActionResult
    ]
    list_allowed_sgroups: PublicActionProcessor[
        ListAllowedScalingGroupsAction, ListAllowedScalingGroupsActionResult
    ]
    get_wsproxy_version: PublicActionProcessor[
        GetWsproxyVersionAction, GetWsproxyVersionActionResult
    ]
    get_resource_info: SingleEntityActionProcessor[
        GetResourceInfoAction, GetResourceInfoActionResult
    ]
    update_fair_share_spec: SingleEntityActionProcessor[
        UpdateFairShareSpecAction, UpdateFairShareSpecActionResult
    ]
    replace_default_deployment_options: SingleEntityActionProcessor[
        ReplaceDefaultDeploymentOptionsAction,
        ReplaceDefaultDeploymentOptionsActionResult,
    ]
    replace_default_session_options: SingleEntityActionProcessor[
        ReplaceDefaultSessionOptionsAction,
        ReplaceDefaultSessionOptionsActionResult,
    ]
    associate_scaling_group_with_domains: SingleEntityActionProcessor[
        AssociateScalingGroupWithDomainsAction, AssociateScalingGroupWithDomainsActionResult
    ]
    disassociate_scaling_group_with_domains: SingleEntityActionProcessor[
        DisassociateScalingGroupWithDomainsAction, DisassociateScalingGroupWithDomainsActionResult
    ]
    associate_scaling_group_with_keypairs: SingleEntityActionProcessor[
        AssociateScalingGroupWithKeypairsAction, AssociateScalingGroupWithKeypairsActionResult
    ]
    disassociate_scaling_group_with_keypairs: SingleEntityActionProcessor[
        DisassociateScalingGroupWithKeypairsAction, DisassociateScalingGroupWithKeypairsActionResult
    ]
    associate_scaling_group_with_user_groups: SingleEntityActionProcessor[
        AssociateScalingGroupWithUserGroupsAction, AssociateScalingGroupWithUserGroupsActionResult
    ]
    disassociate_scaling_group_with_user_groups: SingleEntityActionProcessor[
        DisassociateScalingGroupWithUserGroupsAction,
        DisassociateScalingGroupWithUserGroupsActionResult,
    ]
    update_allowed_rgs_for_domain: SingleEntityActionProcessor[
        UpdateAllowedResourceGroupsForDomainAction,
        UpdateAllowedResourceGroupsForDomainActionResult,
    ]
    update_allowed_rgs_for_project: SingleEntityActionProcessor[
        UpdateAllowedResourceGroupsForProjectAction,
        UpdateAllowedResourceGroupsForProjectActionResult,
    ]
    update_allowed_domains_for_rg: SingleEntityActionProcessor[
        UpdateAllowedDomainsForResourceGroupAction,
        UpdateAllowedDomainsForResourceGroupActionResult,
    ]
    update_allowed_projects_for_rg: SingleEntityActionProcessor[
        UpdateAllowedProjectsForResourceGroupAction,
        UpdateAllowedProjectsForResourceGroupActionResult,
    ]
    get_allowed_rgs_for_domain: SingleEntityActionProcessor[
        GetAllowedResourceGroupsForDomainAction,
        GetAllowedResourceGroupsForDomainActionResult,
    ]
    get_allowed_rgs_for_project: SingleEntityActionProcessor[
        GetAllowedResourceGroupsForProjectAction,
        GetAllowedResourceGroupsForProjectActionResult,
    ]
    get_allowed_domains_for_rg: SingleEntityActionProcessor[
        GetAllowedDomainsForResourceGroupAction,
        GetAllowedDomainsForResourceGroupActionResult,
    ]
    get_allowed_projects_for_rg: SingleEntityActionProcessor[
        GetAllowedProjectsForResourceGroupAction,
        GetAllowedProjectsForResourceGroupActionResult,
    ]
    resolve_resource_group_ids_by_names: GlobalActionProcessor[
        ResolveResourceGroupIDsByNamesAction,
        ResolveResourceGroupIDsByNamesActionResult,
    ]

    def __init__(
        self, group: ProcessorGroup[ScalingGroupData], service: ScalingGroupService
    ) -> None:
        self.lookup = group.public_lookup_ops(LookupResourceGroupAction)
        self.create_scaling_group = group.global_scope(
            CreateScalingGroupAction, service.create_scaling_group
        )
        self.purge_scaling_group = group.single_entity(
            PurgeScalingGroupAction, service.purge_scaling_group
        )
        self.update_scaling_group = group.single_entity(
            UpdateScalingGroupAction, service.update_scaling_group
        )
        self.search_scaling_groups = group.global_scope(
            SearchScalingGroupsAction, service.search_scaling_groups
        )
        self.list_allowed_sgroups = group.public(
            ListAllowedScalingGroupsAction, service.list_allowed_sgroups
        )
        self.get_wsproxy_version = group.public(
            GetWsproxyVersionAction, service.get_wsproxy_version
        )
        self.get_resource_info = group.single_entity(
            GetResourceInfoAction, service.get_resource_info
        )
        self.update_fair_share_spec = group.single_entity(
            UpdateFairShareSpecAction, service.update_fair_share_spec
        )
        self.replace_default_deployment_options = group.single_entity(
            ReplaceDefaultDeploymentOptionsAction, service.replace_default_deployment_options
        )
        self.replace_default_session_options = group.single_entity(
            ReplaceDefaultSessionOptionsAction, service.replace_default_session_options
        )
        self.associate_scaling_group_with_domains = group.single_entity(
            AssociateScalingGroupWithDomainsAction, service.associate_scaling_group_with_domains
        )
        self.disassociate_scaling_group_with_domains = group.single_entity(
            DisassociateScalingGroupWithDomainsAction,
            service.disassociate_scaling_group_with_domains,
        )
        self.associate_scaling_group_with_keypairs = group.single_entity(
            AssociateScalingGroupWithKeypairsAction, service.associate_scaling_group_with_keypairs
        )
        self.disassociate_scaling_group_with_keypairs = group.single_entity(
            DisassociateScalingGroupWithKeypairsAction,
            service.disassociate_scaling_group_with_keypairs,
        )
        self.associate_scaling_group_with_user_groups = group.single_entity(
            AssociateScalingGroupWithUserGroupsAction,
            service.associate_scaling_group_with_user_groups,
        )
        self.disassociate_scaling_group_with_user_groups = group.single_entity(
            DisassociateScalingGroupWithUserGroupsAction,
            service.disassociate_scaling_group_with_user_groups,
        )
        self.update_allowed_rgs_for_domain = group.single_entity(
            UpdateAllowedResourceGroupsForDomainAction,
            service.update_allowed_resource_groups_for_domain,
        )
        self.update_allowed_rgs_for_project = group.single_entity(
            UpdateAllowedResourceGroupsForProjectAction,
            service.update_allowed_resource_groups_for_project,
        )
        self.update_allowed_domains_for_rg = group.single_entity(
            UpdateAllowedDomainsForResourceGroupAction,
            service.update_allowed_domains_for_resource_group,
        )
        self.update_allowed_projects_for_rg = group.single_entity(
            UpdateAllowedProjectsForResourceGroupAction,
            service.update_allowed_projects_for_resource_group,
        )
        self.get_allowed_rgs_for_domain = group.single_entity(
            GetAllowedResourceGroupsForDomainAction, service.get_allowed_resource_groups_for_domain
        )
        self.get_allowed_rgs_for_project = group.single_entity(
            GetAllowedResourceGroupsForProjectAction,
            service.get_allowed_resource_groups_for_project,
        )
        self.get_allowed_domains_for_rg = group.single_entity(
            GetAllowedDomainsForResourceGroupAction, service.get_allowed_domains_for_resource_group
        )
        self.get_allowed_projects_for_rg = group.single_entity(
            GetAllowedProjectsForResourceGroupAction,
            service.get_allowed_projects_for_resource_group,
        )
        self.resolve_resource_group_ids_by_names = group.global_scope(
            ResolveResourceGroupIDsByNamesAction, service.resolve_resource_group_ids_by_names
        )
