from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import (
    GlobalActionProcessor,
    PublicActionProcessor,
)
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.ops.result import LookupOpsResult, ScopedBatchOpsResult
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.resource_group.types import ResourceGroupData
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
from ai.backend.manager.services.resource_group.actions.lookup import LookupResourceGroupAction
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
from ai.backend.manager.services.resource_group.actions.scoped_search import (
    ScopedSearchResourceGroupsAction,
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
from ai.backend.manager.services.resource_group.service import ResourceGroupService


class ResourceGroupProcessors:
    lookup: LookupActionProcessor[LookupResourceGroupAction, LookupOpsResult[ResourceGroupID]]
    create_resource_group: GlobalActionProcessor[
        CreateResourceGroupAction, CreateResourceGroupActionResult
    ]
    purge_resource_group: SingleEntityActionProcessor[
        PurgeResourceGroupAction, PurgeResourceGroupActionResult
    ]
    update_resource_group: SingleEntityActionProcessor[
        UpdateResourceGroupAction, UpdateResourceGroupActionResult
    ]
    search_resource_groups: GlobalActionProcessor[
        SearchResourceGroupsAction, SearchResourceGroupsActionResult
    ]
    scoped_search_resource_groups: ScopeActionProcessor[
        ScopedSearchResourceGroupsAction, ScopedBatchOpsResult[ResourceGroupData]
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
    associate_resource_group_with_domains: SingleEntityActionProcessor[
        AssociateResourceGroupWithDomainsAction, AssociateResourceGroupWithDomainsActionResult
    ]
    disassociate_resource_group_with_domains: SingleEntityActionProcessor[
        DisassociateResourceGroupWithDomainsAction, DisassociateResourceGroupWithDomainsActionResult
    ]
    associate_resource_group_with_keypairs: SingleEntityActionProcessor[
        AssociateResourceGroupWithKeypairsAction, AssociateResourceGroupWithKeypairsActionResult
    ]
    disassociate_resource_group_with_keypairs: SingleEntityActionProcessor[
        DisassociateResourceGroupWithKeypairsAction,
        DisassociateResourceGroupWithKeypairsActionResult,
    ]
    associate_resource_group_with_user_groups: SingleEntityActionProcessor[
        AssociateResourceGroupWithUserGroupsAction, AssociateResourceGroupWithUserGroupsActionResult
    ]
    disassociate_resource_group_with_user_groups: SingleEntityActionProcessor[
        DisassociateResourceGroupWithUserGroupsAction,
        DisassociateResourceGroupWithUserGroupsActionResult,
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
        self, group: ProcessorGroup[ResourceGroupData], service: ResourceGroupService
    ) -> None:
        self.lookup = group.public_lookup_ops(LookupResourceGroupAction)
        self.create_resource_group = group.global_scope(
            CreateResourceGroupAction, service.create_resource_group
        )
        self.purge_resource_group = group.single_entity(
            PurgeResourceGroupAction, service.purge_resource_group
        )
        self.update_resource_group = group.single_entity(
            UpdateResourceGroupAction, service.update_resource_group
        )
        self.search_resource_groups = group.global_scope(
            SearchResourceGroupsAction, service.search_resource_groups
        )
        self.scoped_search_resource_groups = group.scope_search_ops(
            ScopedSearchResourceGroupsAction
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
        self.associate_resource_group_with_domains = group.single_entity(
            AssociateResourceGroupWithDomainsAction, service.associate_resource_group_with_domains
        )
        self.disassociate_resource_group_with_domains = group.single_entity(
            DisassociateResourceGroupWithDomainsAction,
            service.disassociate_resource_group_with_domains,
        )
        self.associate_resource_group_with_keypairs = group.single_entity(
            AssociateResourceGroupWithKeypairsAction, service.associate_resource_group_with_keypairs
        )
        self.disassociate_resource_group_with_keypairs = group.single_entity(
            DisassociateResourceGroupWithKeypairsAction,
            service.disassociate_resource_group_with_keypairs,
        )
        self.associate_resource_group_with_user_groups = group.single_entity(
            AssociateResourceGroupWithUserGroupsAction,
            service.associate_resource_group_with_user_groups,
        )
        self.disassociate_resource_group_with_user_groups = group.single_entity(
            DisassociateResourceGroupWithUserGroupsAction,
            service.disassociate_resource_group_with_user_groups,
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
