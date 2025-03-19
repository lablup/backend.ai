from ai.backend.manager.actions.processor import ActionProcessor
from ai.backend.manager.services.domain.actions import (
    CreateDomainNodeAction,
    CreateDomainNodeActionResult,
    ModifyDomainNodeAction,
    ModifyDomainNodeActionResult,
)

from .service import DomainService


class DomainProcessors:
    create_domain_node: ActionProcessor[CreateDomainNodeAction, CreateDomainNodeActionResult]
    modify_domain_node: ActionProcessor[ModifyDomainNodeAction, ModifyDomainNodeActionResult]

    def __init__(self, service: DomainService) -> None:
        self.create_domain_node = ActionProcessor(service.create_domain_node)
        self.modify_domain_node = ActionProcessor(service.modify_domain_node)
