from typing import override

from ai.backend.manager.actions.monitors.monitor import ActionMonitor
from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.actions.types import AbstractProcessorPackage, ActionSpec
from ai.backend.manager.services.domain.actions.create_domain import (
    CreateDomainAction,
    CreateDomainActionResult,
)
from ai.backend.manager.services.domain.actions.create_domain_node import (
    CreateDomainNodeAction,
    CreateDomainNodeActionResult,
)
from ai.backend.manager.services.domain.actions.delete_domain import (
    DeleteDomainAction,
    DeleteDomainActionResult,
)
from ai.backend.manager.services.domain.actions.modify_domain import (
    ModifyDomainAction,
    ModifyDomainActionResult,
)
from ai.backend.manager.services.domain.actions.modify_domain_node import (
    ModifyDomainNodeAction,
    ModifyDomainNodeActionResult,
)
from ai.backend.manager.services.domain.actions.purge_domain import (
    PurgeDomainAction,
    PurgeDomainActionResult,
)

from .service import DomainService


class DomainProcessors(AbstractProcessorPackage):
    create_domain_node: ActionProcessor[CreateDomainNodeAction, CreateDomainNodeActionResult]
    modify_domain_node: ActionProcessor[ModifyDomainNodeAction, ModifyDomainNodeActionResult]
    create_domain: ActionProcessor[CreateDomainAction, CreateDomainActionResult]
    modify_domain: ActionProcessor[ModifyDomainAction, ModifyDomainActionResult]
    delete_domain: ActionProcessor[DeleteDomainAction, DeleteDomainActionResult]
    purge_domain: ActionProcessor[PurgeDomainAction, PurgeDomainActionResult]

    def __init__(self, service: DomainService, action_monitors: list[ActionMonitor]) -> None:
        self.create_domain_node = ActionProcessor(service.create_domain_node, action_monitors)
        self.modify_domain_node = ActionProcessor(service.modify_domain_node, action_monitors)
        self.create_domain = ActionProcessor(service.create_domain, action_monitors)
        self.modify_domain = ActionProcessor(service.modify_domain, action_monitors)
        self.delete_domain = ActionProcessor(service.delete_domain, action_monitors)
        self.purge_domain = ActionProcessor(service.purge_domain, action_monitors)

    @override
    def supported_actions(self) -> list[ActionSpec]:
        return [
            CreateDomainNodeAction.spec(),
            ModifyDomainNodeAction.spec(),
            CreateDomainAction.spec(),
            ModifyDomainAction.spec(),
            DeleteDomainAction.spec(),
            PurgeDomainAction.spec(),
        ]
