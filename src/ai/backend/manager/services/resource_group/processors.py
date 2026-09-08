from ai.backend.common.data.entity.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.bulk.partial_processor import PartialBulkActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import (
    GlobalActionProcessor,
    PublicActionProcessor,
)
from ai.backend.manager.actions.v2.lookup.bulk_processor import BulkLookupActionProcessor
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BulkLookupOpsResult,
    LookupOpsResult,
    ScopedBatchOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.services.resource_group.actions.bulk_get import (
    BulkGetResourceGroupsAction,
)
from ai.backend.manager.services.resource_group.actions.bulk_lookup import (
    BulkLookupResourceGroupsAction,
)
from ai.backend.manager.services.resource_group.actions.create import (
    CreateResourceGroupAction,
    CreateResourceGroupActionResult,
)
from ai.backend.manager.services.resource_group.actions.get_allowed_domains_for_rg import (
    GetAllowedDomainsForResourceGroupAction,
    GetAllowedDomainsForResourceGroupActionResult,
)
from ai.backend.manager.services.resource_group.actions.get_allowed_projects_for_rg import (
    GetAllowedProjectsForResourceGroupAction,
    GetAllowedProjectsForResourceGroupActionResult,
)
from ai.backend.manager.services.resource_group.actions.get_allowed_rgs_for_domain import (
    GetAllowedResourceGroupsForDomainAction,
    GetAllowedResourceGroupsForDomainActionResult,
)
from ai.backend.manager.services.resource_group.actions.get_allowed_rgs_for_project import (
    GetAllowedResourceGroupsForProjectAction,
    GetAllowedResourceGroupsForProjectActionResult,
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
from ai.backend.manager.services.resource_group.actions.update_fair_share_spec import (
    UpdateFairShareSpecAction,
    UpdateFairShareSpecActionResult,
)
from ai.backend.manager.services.resource_group.service import ResourceGroupService


class ResourceGroupProcessors:
    lookup: LookupActionProcessor[LookupResourceGroupAction, LookupOpsResult[ResourceGroupID]]
    bulk_lookup: BulkLookupActionProcessor[
        BulkLookupResourceGroupsAction, BulkLookupOpsResult[ResourceGroupName, ResourceGroupID]
    ]
    # What the DataLoaders read: checked per resource group.
    bulk_get: PartialBulkActionProcessor[BulkGetResourceGroupsAction, ResourceGroupData]
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
        self, group: ProcessorGroup[ResourceGroupData], service: ResourceGroupService
    ) -> None:
        self.lookup = group.public_lookup_ops(LookupResourceGroupAction)
        self.bulk_lookup = group.public_bulk_lookup_ops(BulkLookupResourceGroupsAction)
        self.bulk_get = group.partial_bulk_get_ops(BulkGetResourceGroupsAction)
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
        self.get_allowed_rgs_for_domain = group.single_entity(
            GetAllowedResourceGroupsForDomainAction,
            service.get_allowed_resource_groups_for_domain,
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
