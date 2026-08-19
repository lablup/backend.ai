from dataclasses import dataclass

from ai.backend.manager.services.scaling_group.actions.base import ScalingGroupAction


@dataclass(frozen=True)
class ScalingGroupKeypairAction(ScalingGroupAction):
    """Base for an operation on the keypairs a resource group serves."""
