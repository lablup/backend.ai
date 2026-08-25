from dataclasses import dataclass

from ai.backend.manager.services.resource_group.actions.base import ResourceGroupAction


@dataclass(frozen=True)
class ResourceGroupKeypairAction(ResourceGroupAction):
    """Base for an operation on the keypairs a resource group serves."""
