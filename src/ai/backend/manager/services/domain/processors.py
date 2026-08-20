from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.registry.group import ProcessorGroup
from ai.backend.manager.actions.v2.global_scope.processor import (
    GlobalActionProcessor,
    PublicActionProcessor,
)
from ai.backend.manager.actions.v2.lookup.processor import LookupActionProcessor
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    EntityOpsResult,
    LookupOpsResult,
)
from ai.backend.manager.actions.v2.single_entity.processor import SingleEntityActionProcessor
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.services.domain.actions.create_domain import (
    CreateDomainAction,
    CreateDomainActionResult,
)
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
from ai.backend.manager.services.domain.actions.lookup import LookupDomainAction
from ai.backend.manager.services.domain.actions.purge_domain import (
    PurgeDomainAction,
    PurgeDomainActionResult,
)
from ai.backend.manager.services.domain.actions.restore_domain import RestoreDomainAction
from ai.backend.manager.services.domain.actions.search_domains import GlobalSearchDomainsAction
from ai.backend.manager.services.domain.actions.search_rg_domains import SearchRGDomainsAction
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
    lookup: LookupActionProcessor[LookupDomainAction, LookupOpsResult[DomainData]]
    global_search: GlobalActionProcessor[GlobalSearchDomainsAction, BatchOpsResult[DomainData]]
    public_search_rg_domains: PublicActionProcessor[
        SearchRGDomainsAction, BatchOpsResult[DomainData]
    ]
    update_domain: SingleEntityActionProcessor[UpdateDomainAction, EntityOpsResult[DomainData]]
    delete_domain: SingleEntityActionProcessor[DeleteDomainAction, EntityOpsResult[DomainData]]
    restore_domain: SingleEntityActionProcessor[RestoreDomainAction, EntityOpsResult[DomainData]]
    create_domain: GlobalActionProcessor[CreateDomainAction, CreateDomainActionResult]
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
        self.lookup = group.public_lookup_ops(LookupDomainAction)
        self.global_search = group.global_search_ops(GlobalSearchDomainsAction)
        self.public_search_rg_domains = group.public_search_ops(SearchRGDomainsAction)
        self.update_domain = group.single_update_ops(UpdateDomainAction)
        self.delete_domain = group.single_delete_ops(DeleteDomainAction)
        self.restore_domain = group.single_restore_ops(RestoreDomainAction)
        self.create_domain = group.global_scope(CreateDomainAction, service.create_domain)
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
