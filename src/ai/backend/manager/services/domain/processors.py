from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.services.domain.actions import (
    CreateDomainAction,
    CreateDomainActionResult,
    CreateDomainNodeAction,
    CreateDomainNodeActionResult,
    ModifyDomainAction,
    ModifyDomainActionResult,
    ModifyDomainNodeAction,
    ModifyDomainNodeActionResult,
)

from .service import DomainService


class DomainProcessors:
    create_domain_node: ActionProcessor[CreateDomainNodeAction, CreateDomainNodeActionResult]
    modify_domain_node: ActionProcessor[ModifyDomainNodeAction, ModifyDomainNodeActionResult]
    create_domain: ActionProcessor[CreateDomainAction, CreateDomainActionResult]
    modify_domain: ActionProcessor[ModifyDomainAction, ModifyDomainActionResult]

    def __init__(self, service: DomainService) -> None:
        self.create_domain_node = ActionProcessor(service.create_domain_node)
        self.modify_domain_node = ActionProcessor(service.modify_domain_node)
        self.create_domain = ActionProcessor(service.create_domain)
        self.modify_domain = ActionProcessor(service.modify_domain)
