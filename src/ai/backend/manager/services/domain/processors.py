from ai.backend.common.data.entity.domain import DomainID, DomainName
from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.bulk.partial_processor import PartialBulkActionProcessor
from ai.backend.manager.actions.v2.global_scope.processor import GlobalActionProcessor
from ai.backend.manager.actions.v2.lookup.bulk_processor import BulkLookupActionProcessor
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    BulkLookupOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
    LookupOpsResult,
    ScopedBatchOpsResult,
)
from ai.backend.manager.actions.v2.scope.processor import ScopeActionProcessor
from ai.backend.manager.actions.v2.single_entity.processor import (
    SingleEntityActionProcessor,
)
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.services.domain.actions.bulk_get import BulkGetDomainsAction
from ai.backend.manager.services.domain.actions.bulk_lookup import BulkLookupDomainsAction
from ai.backend.manager.services.domain.actions.create_domain import CreateDomainAction
from ai.backend.manager.services.domain.actions.create_domain_dotfile import (
    CreateDomainDotfileAction,
    CreateDomainDotfileActionResult,
)
from ai.backend.manager.services.domain.actions.create_domain_node import (
    CreateDomainNodeAction,
    CreateDomainNodeActionResult,
)
from ai.backend.manager.services.domain.actions.delete_domain import DeleteDomainAction
from ai.backend.manager.services.domain.actions.delete_domain_dotfile import (
    DeleteDomainDotfileAction,
    DeleteDomainDotfileActionResult,
)
from ai.backend.manager.services.domain.actions.get import GetDomainAction
from ai.backend.manager.services.domain.actions.lookup import LookupDomainAction
from ai.backend.manager.services.domain.actions.purge_domain import (
    PurgeDomainAction,
    PurgeDomainActionResult,
)
from ai.backend.manager.services.domain.actions.restore_domain import RestoreDomainAction
from ai.backend.manager.services.domain.actions.scoped_search import ScopedSearchDomainsAction
from ai.backend.manager.services.domain.actions.search_domains import GlobalSearchDomainsAction
from ai.backend.manager.services.domain.actions.update_domain import UpdateDomainAction
from ai.backend.manager.services.domain.actions.update_domain_dotfile import (
    UpdateDomainDotfileAction,
    UpdateDomainDotfileActionResult,
)
from ai.backend.manager.services.domain.actions.update_domain_node import (
    UpdateDomainNodeAction,
    UpdateDomainNodeActionResult,
)
from ai.backend.manager.services.domain.service import DomainService


class DomainProcessors:
    get: SingleEntityActionProcessor[GetDomainAction, EntityOpsResult[DomainData]]
    lookup: LookupActionProcessor[LookupDomainAction, LookupOpsResult[DomainID]]
    bulk_lookup: BulkLookupActionProcessor[
        BulkLookupDomainsAction, BulkLookupOpsResult[DomainName, DomainID]
    ]
    # What the DataLoaders read: open to every authenticated caller.
    bulk_get: PartialBulkActionProcessor[BulkGetDomainsAction, DomainData]
    global_search: GlobalActionProcessor[GlobalSearchDomainsAction, BatchOpsResult[DomainData]]
    scoped_search: ScopeActionProcessor[ScopedSearchDomainsAction, ScopedBatchOpsResult[DomainData]]
    update_domain: SingleEntityActionProcessor[UpdateDomainAction, EntityOpsResult[DomainData]]
    delete_domain: SingleEntityActionProcessor[DeleteDomainAction, EntityOpsResult[DomainData]]
    restore_domain: SingleEntityActionProcessor[RestoreDomainAction, EntityOpsResult[DomainData]]
    create_domain: GlobalActionProcessor[CreateDomainAction, CreatedEntityOpsResult[DomainData]]
    create_domain_node: GlobalActionProcessor[CreateDomainNodeAction, CreateDomainNodeActionResult]
    update_domain_node: SingleEntityActionProcessor[
        UpdateDomainNodeAction, UpdateDomainNodeActionResult
    ]
    purge_domain: SingleEntityActionProcessor[PurgeDomainAction, PurgeDomainActionResult]
    create_dotfile: SingleEntityActionProcessor[
        CreateDomainDotfileAction, CreateDomainDotfileActionResult
    ]
    update_dotfile: SingleEntityActionProcessor[
        UpdateDomainDotfileAction, UpdateDomainDotfileActionResult
    ]
    delete_dotfile: SingleEntityActionProcessor[
        DeleteDomainDotfileAction, DeleteDomainDotfileActionResult
    ]

    def __init__(
        self,
        group: ProcessorGroup[DomainData],
        service: DomainService,
        action_monitors: list[ActionMonitor],
    ) -> None:
        self.get = group.single_get_ops(GetDomainAction)
        self.lookup = group.public_lookup_ops(LookupDomainAction)
        self.bulk_lookup = group.public_bulk_lookup_ops(BulkLookupDomainsAction)
        self.bulk_get = group.public_partial_bulk_get_ops(BulkGetDomainsAction)
        self.global_search = group.global_search_ops(GlobalSearchDomainsAction)
        self.scoped_search = group.scope_search_ops(ScopedSearchDomainsAction)
        self.update_domain = group.single_update_ops(UpdateDomainAction)
        self.delete_domain = group.single_delete_ops(DeleteDomainAction)
        self.restore_domain = group.single_restore_ops(RestoreDomainAction)
        self.create_domain = group.global_role_managed_create_ops(CreateDomainAction)
        self.create_domain_node = group.global_scope(
            CreateDomainNodeAction, service.create_domain_node
        )
        self.update_domain_node = group.single_entity(
            UpdateDomainNodeAction, service.update_domain_node
        )
        self.purge_domain = group.single_entity(PurgeDomainAction, service.purge_domain)
        self.create_dotfile = group.single_entity(CreateDomainDotfileAction, service.create_dotfile)
        self.update_dotfile = group.single_entity(UpdateDomainDotfileAction, service.update_dotfile)
        self.delete_dotfile = group.single_entity(DeleteDomainDotfileAction, service.delete_dotfile)
